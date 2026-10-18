import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest
from scratch.model import ModelConfig
from scratch.qa_training import read_pairs, train_qa
from scratch.training import load_checkpoint


class QATrainingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root/'pairs.jsonl'
        self.data.write_text(json.dumps({'question':'hi','answer':'hello'})+'\n','utf-8')
        self.cfg = ModelConfig(width=32, layers=1, heads=2, context=64)

    def test_stop_saves_completed_step_and_fine_tune_preserves_parent(self):
        stop = threading.Event()
        events = []
        def emit(event):
            events.append(event)
            if event['kind']=='progress':
                stop.set()
        source = self.root/'source.pt'
        result = train_qa([self.data], source, steps=5, stop=stop, emit=emit, device='cpu', cfg=self.cfg)
        self.assertEqual(result['steps'],1)
        _, checkpoint = load_checkpoint(source)
        self.assertEqual(checkpoint['phase_steps'],1)
        self.assertTrue(checkpoint['stopped'])
        original = hashlib.sha256(source.read_bytes()).hexdigest()
        target = self.root/'candidate.pt'
        train_qa([self.data],target,steps=2,resume_from=source,device='cpu')
        _, checkpoint = load_checkpoint(target)
        self.assertEqual(checkpoint['steps'],3)
        self.assertEqual(checkpoint['parent_sha256'],original)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
        self.assertIsNone(checkpoint['validation_loss'])

    def test_cancel_before_first_step_does_not_create_weights(self):
        stop = threading.Event()
        stop.set()
        target = self.root/'cancelled.pt'
        result = train_qa([self.data],target,steps=2,stop=stop,device='cpu',cfg=self.cfg)
        self.assertFalse(result['saved'])
        self.assertFalse(target.exists())

    def test_conflicting_or_malformed_data_rejected(self):
        for text in ['{}', '[]', '{"question":"hi","answer":""}',
                     '{"question":"Hi!","answer":"a"}\n{"question":"hi","answer":"b"}']:
            self.data.write_text(text,'utf-8')
            with self.assertRaises(ValueError):
                read_pairs([self.data])

    def test_cannot_overwrite_parent(self):
        path = self.root/'model.pt'
        with self.assertRaises(ValueError):
            train_qa([self.data],path,resume_from=path)
