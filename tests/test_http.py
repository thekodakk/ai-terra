import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
from app import State, make_handler
from terra.config import Config
from terra.agent import Agent


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.state = State()
        cls.state.config = Config(Path(cls.temp.name))
        cls.state.agent = Agent(cls.state.config, lambda: cls.state.permissions)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), None)
        cls.port = cls.server.server_address[1]
        cls.server.RequestHandlerClass = make_handler(cls.state, cls.port)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp.cleanup()

    def call(self, path, data=None, headers=None, auth=True):
        head = {'X-Terra-Token': self.state.token} if auth else {}
        head.update(headers or {})
        req = urllib.request.Request(f'http://127.0.0.1:{self.port}'+path,
                                     data=None if data is None else json.dumps(data).encode(), headers=head)
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, response.read(), response.headers
        except urllib.error.HTTPError as e:
            try:
                return e.code, e.read(), e.headers
            finally:
                e.close()

    def test_no_auth_no_api(self):
        self.assertEqual(self.call('/api/state', auth=False)[0], 403)

    def test_cross_origin_denied(self):
        self.assertEqual(self.call('/api/stop', {}, {'Origin': 'https://example.com'})[0], 403)

    def test_dns_rebinding_denied(self):
        self.assertEqual(self.call('/', headers={'Host': 'evil.example'})[0], 403)

    def test_no_file_serving(self):
        self.assertEqual(self.call('/data/settings.json')[0], 404)
        self.assertEqual(self.call('/../app.py')[0], 404)

    def test_ui_bootstrap_csp(self):
        code, raw, headers = self.call('/')
        self.assertEqual(code, 200)
        self.assertNotIn(b'__TERRA_TOKEN__', raw)
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])

    def test_settings_revoke_permissions(self):
        self.state.permissions.update(screen=True, control=True)
        result = self.call('/api/settings', {'workspace': self.temp.name, 'provider': 'ollama', 'model': 'test'})
        self.assertEqual(result[0], 200)
        self.assertFalse(self.state.permissions['screen'])
        self.assertFalse(self.state.permissions['control'])

    def test_empty_message_rejected(self):
        self.assertEqual(self.call('/api/chat', {'text': ''})[0], 400)


if __name__ == '__main__':
    unittest.main()
