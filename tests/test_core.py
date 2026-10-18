import copy
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from terra.config import Config
from terra.agent import Agent, Job
from terra.tools import ToolRunner, file_path
from terra.desktop import validate_action
from terra import providers


class BasicTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = Config(self.root / 'data')
        self.config.save({'workspace': str(self.root), 'provider': 'ollama', 'model': 'test'})
        self.job = Job('test')
        self.runner = ToolRunner(self.config.snapshot(), self.job, lambda: {'screen': False, 'control': False})

    def tearDown(self):
        self.temp.cleanup()

    def test_path_traversal(self):
        for name in ('../secret.txt', '../../Windows/system.ini', '.env', '.env.local', '.ssh/key', 'x/private.pem', '.git/config'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                file_path(self.root, name)

    def test_read_and_list(self):
        (self.root / 'hello.py').write_text('print("Türkçe")', 'utf-8')
        (self.root / '.env').write_text('secret')
        result = self.runner.execute('list_files', {'path': '.'})
        self.assertIn('hello.py', [x['name'] for x in result['files']])
        self.assertNotIn('.env', [x['name'] for x in result['files']])
        self.assertIn('Türkçe', self.runner.execute('read_file', {'path': 'hello.py'})['content'])

    def test_denied_write_has_no_side_effect(self):
        self.job.approve = lambda *args: False
        result = self.runner.execute('write_file', {'path': 'new.txt', 'content': 'hello'})
        self.assertTrue(result['denied'])
        self.assertFalse((self.root / 'new.txt').exists())

    def test_approved_new_file(self):
        self.job.approve = lambda *args: True
        self.runner.execute('write_file', {'path': 'nested/new.txt', 'content': 'Türkçe içerik'})
        self.assertEqual((self.root / 'nested/new.txt').read_text('utf-8'), 'Türkçe içerik')

    def test_changed_during_approval(self):
        path = self.root / 'test.txt'
        path.write_text('before')
        def approve(*args):
            path.write_text('another editor')
            return True
        self.job.approve = approve
        with self.assertRaisesRegex(ValueError, 'dosya değişti'):
            self.runner.execute('write_file', {'path': 'test.txt', 'content': 'mine'})
        self.assertEqual(path.read_text(), 'another editor')

    def test_stop_prevents_write(self):
        self.job.stop.set()
        with self.assertRaises(InterruptedError):
            self.runner.execute('write_file', {'path': 'no.txt', 'content': 'no'})

    def test_screen_requires_permission(self):
        with self.assertRaisesRegex(ValueError, 'paylaşımı kapalı'):
            self.runner.execute('capture_screen', {})

    def test_control_requires_fresh_screen(self):
        runner = ToolRunner(self.config.snapshot(), self.job, lambda: {'screen': True, 'control': True},
                            capture=lambda: {'image': 'fake', 'width': 100, 'height': 100},
                            act=lambda args, stop: {'ok': True})
        args = {'action': 'click', 'x': 100, 'y': 100, 'text': '', 'amount': 0}
        with self.assertRaisesRegex(ValueError, 'yeni ekran'):
            runner.execute('desktop_action', args)
        runner.execute('capture_screen', {})
        self.job.approve = lambda *args: True
        self.assertTrue(runner.execute('desktop_action', args)['ok'])
        with self.assertRaises(ValueError):
            runner.execute('desktop_action', args)

    def test_revocation_after_approval(self):
        permission = {'screen': True, 'control': True}
        calls = []
        runner = ToolRunner(self.config.snapshot(), self.job, lambda: permission,
                            capture=lambda: {'image': 'fake'}, act=lambda *args: calls.append(args))
        runner.execute('capture_screen', {})
        def approve(*args):
            permission['control'] = False
            return True
        self.job.approve = approve
        with self.assertRaisesRegex(ValueError, 'kaldırıldı'):
            runner.execute('desktop_action', {'action': 'key', 'text': 'CTRL+S', 'x': 0, 'y': 0, 'amount': 0})
        self.assertEqual(calls, [])

    def test_command_never_runs_without_approval(self):
        self.job.approve = lambda *args: False
        with patch('terra.tools.subprocess.Popen') as popen:
            result = self.runner.execute('run_command', {'command': 'echo hello'})
            self.assertTrue(result['denied'])
            popen.assert_not_called()

    def test_config_rejects_remote_ollama(self):
        for url in ('https://evil.example', 'http://127.0.0.1@evil.example', 'http://localhost:11434/redirect'):
            with self.assertRaises(ValueError):
                self.config.save({'ollama_url': url})

    def test_no_key_in_public_config(self):
        with patch.object(self.config, 'key', return_value='secret'):
            self.assertTrue(self.config.public()['has_key'])
            self.assertNotIn('secret', json.dumps(self.config.public()))

    def test_coordinate_validation(self):
        for x in (-1, 1001, float('nan')):
            with self.assertRaises(ValueError):
                validate_action({'action': 'click', 'x': x, 'y': 50})
        with self.assertRaises(ValueError):
            validate_action({'action': 'key', 'text': 'CTRL+BOGUS'})


class LifecycleTests(unittest.TestCase):
    def test_approval_cancel_unblocks(self):
        job = Job('test')
        answer = []
        worker = threading.Thread(target=lambda: answer.append(job.approve('test', {})))
        worker.start()
        for _ in range(100):
            if job.pending:
                break
            time.sleep(.01)
        job.cancel()
        worker.join(2)
        self.assertEqual(answer, [False])

    def test_stale_approval_rejected(self):
        job = Job('test')
        job.pending = {'id': 'a', 'decision': None}
        with self.assertRaises(ValueError):
            job.decide('b', True)
        job.decide('a', False)
        with self.assertRaises(ValueError):
            job.decide('a', True)

    def test_agent_calls_tool_then_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(Path(directory) / 'data')
            config.save({'provider': 'ollama', 'model': 'test', 'workspace': directory})
            (Path(directory) / 'sample.txt').write_text('test')
            seen = []
            def model(settings, key, messages, tools, system):
                seen.append(copy.deepcopy(messages))
                if len(seen) == 1:
                    return {'text': '', 'tokens': 1, 'sources': [], 'raw': {'role': 'assistant', 'content': '', 'tool_calls': []},
                            'calls': [{'id': '1', 'name': 'list_files', 'args': {'path': '.'}}]}
                return {'text': 'sample.txt bulundu.', 'tokens': 1, 'sources': [], 'raw': {}, 'calls': []}
            agent = Agent(config, lambda: {'screen': False, 'control': False}, provider=model)
            job = Job('Dosyaları listele')
            agent.run(job, config.snapshot(), False)
            self.assertEqual(job.status, 'done')
            self.assertEqual(len(seen), 2)
            self.assertIn('sample.txt', seen[1][-1]['content'])
            self.assertEqual(len(agent.history), 2)

    def test_observation_cannot_execute_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(Path(directory))
            def model(*args):
                return {'text': '', 'tokens': 0, 'sources': [], 'raw': {}, 'calls': [{'name': 'run_command', 'args': {'command': 'oops'}}]}
            agent = Agent(config, lambda: {'screen': False, 'control': False}, provider=model)
            job = Job('Bak', observation=True)
            agent.run(job, config.snapshot(), False)
            self.assertEqual(job.status, 'error')
            self.assertFalse(any(e['type'] == 'tool' for e in job.events))

    def test_stop_ignores_late_model_response(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Config(Path(directory))
            job = Job('test')
            def model(*args):
                job.stop.set()
                return {'text': 'should not appear', 'tokens': 1, 'calls': [], 'sources': [], 'raw': {}}
            agent = Agent(config, lambda: {'screen': False, 'control': False}, provider=model)
            agent.run(job, config.snapshot(), False)
            self.assertEqual(job.status, 'stopped')
            self.assertFalse(any(e['type'] == 'assistant' for e in job.events))


class ProviderTests(unittest.TestCase):
    def test_openai_round_trip_schema(self):
        result = {'output': [{'type': 'function_call', 'name': 'read_file', 'call_id': 'xyz', 'arguments': '{"path":"a.py"}'}], 'usage': {'total_tokens': 42}}
        with patch('terra.providers.request_json', return_value=result) as request:
            response = providers.turn({'provider': 'openai', 'model': 'gpt-5.6-terra'}, 'test', [], [], 'system')
            self.assertEqual(response['calls'][0]['args'], {'path': 'a.py'})
            self.assertFalse(request.call_args.args[1]['store'])
            self.assertIn('reasoning.encrypted_content', request.call_args.args[1]['include'])
        messages = []
        providers.append_result('openai', messages, response['calls'][0], {'content': 'test'})
        self.assertEqual(messages[0]['call_id'], 'xyz')

    def test_image_encoding(self):
        msg = providers.user_message('ollama', 'hello', 'fakebase64')
        self.assertEqual(msg['images'], ['fakebase64'])
        msg = providers.user_message('openai', 'hello', 'fakebase64')
        self.assertEqual(msg['content'][1]['image_url'], 'data:image/jpeg;base64,fakebase64')


if __name__ == '__main__':
    unittest.main()
