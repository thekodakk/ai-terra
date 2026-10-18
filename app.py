"""AI Terra — loopback-only, authenticated local desktop assistant."""
import argparse
import ctypes
import json
import mimetypes
import os
from pathlib import Path
import secrets
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from terra.config import Config, ROOT
from terra.agent import Agent
from terra import providers


class State:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self.config = Config()
        self.permissions = {'screen': False, 'control': False}
        self.agent = Agent(self.config, lambda: dict(self.permissions))


def make_handler(state, port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # No prompts, keys or screenshot data in HTTP logs.

        def reply(self, code, data, content_type='application/json; charset=utf-8'):
            raw = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, (dict, list)) else data
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(raw)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def check(self, token=False):
            if self.headers.get('Host') not in (f'127.0.0.1:{port}', f'localhost:{port}'):
                return False
            if self.headers.get('Sec-Fetch-Site') == 'cross-site':
                return False
            origin = self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{port}', f'http://localhost:{port}'):
                return False
            return not token or secrets.compare_digest(self.headers.get('X-Terra-Token', ''), state.token)

        def do_GET(self):
            path = urllib.parse.urlparse(self.path)
            if not self.check(path.path.startswith('/api/')):
                self.reply(403, {'error': 'Erişim reddedildi.'})
                return
            if path.path == '/api/state':
                self.reply(200, {'settings': state.config.public(), 'permissions': state.permissions,
                                 'job': state.agent.current.view() if state.agent.current else None,
                                 'history': state.agent.history, 'tokens': state.agent.total_tokens})
            elif path.path == '/api/job':
                job = state.agent.current
                query = urllib.parse.parse_qs(path.query)
                try:
                    after = int(query.get('after', ['0'])[0])
                except ValueError:
                    after = 0
                self.reply(200, {**job.view(after), 'permissions': state.permissions} if job else {})
            elif path.path == '/api/status':
                self.reply(200, {'permissions': state.permissions, 'busy': bool(state.agent.busy())})
            elif path.path == '/health':
                self.reply(200, {'app': 'ai-terra', 'version': '0.1'})
            elif path.path in ('/', '/index.html', '/style.css', '/main.js'):
                filename = 'index.html' if path.path in ('/', '/index.html') else path.path[1:]
                raw = (ROOT / 'web' / filename).read_bytes()
                if filename == 'index.html':
                    raw = raw.replace(b'__TERRA_TOKEN__', state.token.encode())
                mime = {'html': 'text/html', 'css': 'text/css', 'js': 'text/javascript'}[filename.rsplit('.', 1)[-1]]
                self.reply(200, raw, mime + '; charset=utf-8')
            else:
                self.reply(404, {'error': 'Bulunamadı.'})

        def do_POST(self):
            if not self.check(True):
                self.reply(403, {'error': 'Erişim reddedildi.'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1_000_000:
                    raise ValueError('İstek boyutu geçersiz.')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('Geçersiz istek.')
                if self.path == '/api/settings':
                    if state.agent.busy():
                        raise ValueError('Ayarları değiştirmeden önce görevi durdur.')
                    result = state.config.save(data)
                    state.permissions.update(screen=False, control=False)
                    self.reply(200, result)
                elif self.path == '/api/permissions':
                    screen = data.get('screen') is True
                    control = data.get('control') is True and screen
                    state.permissions.update(screen=screen, control=control)
                    if state.agent.busy() and (not screen or not control):
                        state.agent.current.cancel()
                    self.reply(200, state.permissions)
                elif self.path == '/api/chat':
                    text = data.get('text', '')
                    if not isinstance(text, str) or not text.strip() or len(text) > 16000:
                        raise ValueError('1–16000 karakter arasında bir mesaj yaz.')
                    job = state.agent.start(text.strip(), data.get('screen') is True, data.get('observation') is True)
                    self.reply(200, {'id': job.id})
                elif self.path == '/api/stop':
                    state.permissions.update(screen=False, control=False)
                    if state.agent.current and state.agent.busy():
                        state.agent.current.cancel()
                    self.reply(200, {'ok': True})
                elif self.path == '/api/approval':
                    if not state.agent.current or state.agent.current.id != data.get('job_id'):
                        raise ValueError('Görev artık geçerli değil.')
                    state.agent.current.decide(data['id'], data.get('allow') is True)
                    self.reply(200, {'ok': True})
                elif self.path == '/api/clear':
                    if state.agent.busy():
                        raise ValueError('Önce görevi durdur.')
                    state.agent.history.clear()
                    state.agent.current = None
                    self.reply(200, {'ok': True})
                elif self.path == '/api/connect':
                    config = state.config.snapshot()
                    if config['provider'] == 'ollama':
                        result = providers.request_json(config['ollama_url'].rstrip('/') + '/api/tags', timeout=10)
                        self.reply(200, {'ok': True, 'models': [m['name'] for m in result.get('models', [])]})
                    else:
                        key = state.config.key()
                        if not key:
                            raise ValueError('API anahtarı eklenmemiş.')
                        result = providers.request_json('https://api.openai.com/v1/models/' + urllib.parse.quote(config['model'], safe=''), key=key, timeout=15)
                        self.reply(200, {'ok': True, 'model': result.get('id', config['model'])})
                else:
                    self.reply(404, {'error': 'Bulunamadı.'})
            except (ValueError, KeyError, RuntimeError, OSError) as e:
                self.reply(400, {'error': str(e)[:1200]})

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8844)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if os.name == 'nt':
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
    state = State()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(state, args.port))
    def emergency_key():
        if os.name != 'nt':
            return
        while True:
            if ctypes.windll.user32.GetAsyncKeyState(0x77) & 0x8000:  # F8, global stop.
                state.permissions.update(screen=False, control=False)
                if state.agent.busy():
                    state.agent.current.cancel()
            time.sleep(.15)
    import time
    threading.Thread(target=emergency_key, daemon=True).start()
    url = f'http://127.0.0.1:{args.port}'
    print('AI Terra hazır: ' + url, flush=True)
    if not args.no_browser:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if state.agent.busy():
            state.agent.current.cancel()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
