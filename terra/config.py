"""Local configuration and Windows user-bound secret storage."""
import base64
import ctypes
import json
import os
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
DEFAULTS = {'provider': 'openai', 'model': 'gpt-5.6-terra',
            'ollama_url': 'http://127.0.0.1:11434', 'workspace': str(ROOT / 'projects'),
            'max_steps': 12, 'memory': '', 'web_search': False}


class Blob(ctypes.Structure):
    _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_ubyte))]


def protect(raw, decrypt=False):
    if os.name != 'nt':
        raise ValueError('Kalıcı anahtar saklama yalnızca Windows üzerinde destekleniyor.')
    buf = ctypes.create_string_buffer(raw)
    src = Blob(len(raw), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)))
    dst = Blob()
    if decrypt:
        ok = ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(src), None, None, None, None, 1, ctypes.byref(dst))
    else:
        ok = ctypes.windll.crypt32.CryptProtectData(ctypes.byref(src), None, None, None, None, 1, ctypes.byref(dst))
    if not ok:
        raise ValueError('Windows anahtar kasasına erişilemedi.')
    try:
        return ctypes.string_at(dst.data, dst.size)
    finally:
        ctypes.windll.kernel32.LocalFree(dst.data)


class Config:
    def __init__(self, directory=DATA):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.values = dict(DEFAULTS)
        try:
            self.values.update(json.loads((self.directory / 'settings.json').read_text('utf-8')))
        except (OSError, ValueError):
            pass

    def key(self):
        with self.lock:
            path = self.directory / 'key.bin'
            if path.exists():
                try:
                    return protect(path.read_bytes(), True).decode()
                except Exception:
                    return ''
            return os.environ.get('OPENAI_API_KEY', '')

    def snapshot(self):
        with self.lock:
            return dict(self.values)

    def public(self):
        return {**self.snapshot(), 'has_key': bool(self.key())}

    def save(self, update):
        with self.lock:
            new = {**self.values, **{k: v for k, v in update.items() if k in DEFAULTS}}
            if new['provider'] not in ('openai', 'ollama'):
                raise ValueError('Geçersiz sağlayıcı.')
            if not isinstance(new['model'], str) or not new['model'].strip() or len(new['model']) > 150:
                raise ValueError('Model adını gir.')
            from urllib.parse import urlparse
            u = urlparse(new['ollama_url'])
            if u.scheme != 'http' or u.hostname not in ('localhost', '127.0.0.1') or u.username or u.password or u.query or u.fragment or u.path not in ('', '/'):
                raise ValueError('Yerel model adresi http://127.0.0.1:11434 biçiminde olmalı.')
            folder = Path(new['workspace']).expanduser().resolve()
            if not folder.is_dir():
                raise ValueError('Çalışma klasörü bulunamadı.')
            new['workspace'] = str(folder)
            new['model'] = new['model'].strip()
            new['max_steps'] = max(1, min(30, int(new['max_steps'])))
            if not isinstance(new['memory'], str) or len(new['memory']) > 6000:
                raise ValueError('Tercihler en fazla 6000 karakter olabilir.')
            new['web_search'] = bool(new['web_search'])
            if update.get('api_key'):
                key = update['api_key'].strip()
                if len(key) > 512:
                    raise ValueError('Anahtar çok uzun.')
                (self.directory / 'key.bin').write_bytes(protect(key.encode()))
            elif update.get('delete_key'):
                (self.directory / 'key.bin').unlink(missing_ok=True)
            temp = self.directory / 'settings.tmp'
            temp.write_text(json.dumps(new, ensure_ascii=False, indent=2), 'utf-8')
            temp.replace(self.directory / 'settings.json')
            self.values = new
            return self.public()
