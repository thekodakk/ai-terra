import json
from pathlib import Path
import tempfile
import threading
import unittest

try:
    import torch
except ImportError:
    torch = None


@unittest.skipUnless(torch is not None, 'Native environment with PyTorch required')
class ScratchTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2)

    def test_utf8_roundtrip(self):
        from scratch.model import encode, decode
        text = 'Merhaba dünya! Öğrenci, şişe, İı 🙂'
        self.assertEqual(decode(encode(text)), text)

    def test_attention_cannot_see_future(self):
        from scratch.model import ModelConfig, TerraModel
        torch.manual_seed(4)
        model = TerraModel(ModelConfig(width=32, heads=2, layers=1, context=32)).eval()
        a = torch.tensor([[1, 2, 3, 4, 5]])
        b = torch.tensor([[1, 2, 99, 87, 66]])
        self.assertTrue(torch.allclose(model(a)[0][:, :2], model(b)[0][:, :2], atol=1e-6))

    def test_training_resume_cancel_and_validation(self):
        from scratch.model import ModelConfig
        from scratch.training import train, load_checkpoint
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / 'data.txt'
            data.write_text('Açık ve anlaşılır bir deneme metni.\n' * 100, encoding='utf-8')
            target = root / 'own.pt'
            events = []
            result = train([data], target, steps=20, cfg=ModelConfig(32, 2, 1, 32), device='cpu', emit=events.append)
            self.assertEqual(result['steps'], 20)
            progress = [e for e in events if e['kind'] == 'progress']
            self.assertLess(progress[-1]['loss'], progress[0]['loss'])
            model, saved = load_checkpoint(target)
            self.assertEqual(saved['origin'], 'random_initialization')
            self.assertEqual(saved['steps'], 20)
            x = torch.tensor([[1, 2, 3]])
            again, _ = load_checkpoint(target)
            self.assertTrue(torch.equal(model(x)[0], again(x)[0]))
            stop = threading.Event()
            def callback(event):
                if event.get('kind') == 'progress':
                    stop.set()
            done = train([data], target, steps=10, resume=True, stop=stop, emit=callback, device='cpu')
            self.assertEqual(done['steps'], 21)
            self.assertTrue(done['stopped'])
            self.assertEqual(load_checkpoint(target)[1]['steps'], 21)
            self.assertEqual(model.generate('hi', stop=stop), '')
            from unittest.mock import patch
            with patch('socket.socket.connect', side_effect=AssertionError('Network is forbidden')):
                offline, _ = load_checkpoint(target)
                self.assertIsInstance(offline.generate('Merhaba', max_bytes=8), str)
            data.write_text('different corpus ' * 300, encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'aynı dosyaları'):
                train([data], target, steps=1, resume=True, device='cpu')

    def test_reject_invalid_inputs(self):
        from scratch.training import load_corpus, load_checkpoint
        from scratch.model import ModelConfig
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'data.jsonl'
            source.write_text('{"question": 42, "answer": "x"}', encoding='utf-8')
            with self.assertRaises(ValueError):
                load_corpus([source])
            source.write_text(json.dumps({'text': 'short'}), encoding='utf-8')
            with self.assertRaises(ValueError):
                load_corpus([source])
            checkpoint = root / 'bad.pt'
            torch.save({'format': 'not-terra'}, checkpoint)
            with self.assertRaises(ValueError):
                load_checkpoint(checkpoint)
        with self.assertRaises(ValueError):
            ModelConfig(width=33, heads=4).validate()


if __name__ == '__main__':
    unittest.main()
