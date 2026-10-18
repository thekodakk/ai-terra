import json
from pathlib import Path
import unittest
from scratch.conversation import normalize

ROOT = Path(__file__).resolve().parents[1]/'training'


class NaturalDataTests(unittest.TestCase):
    def read(self, name):
        return [json.loads(s) for s in (ROOT/name).read_text('utf-8').splitlines() if s.strip()]

    def test_preserves_old_answers_and_excludes_all_evaluations(self):
        rows = self.read('natural-training.jsonl')
        known = {normalize(p['question']):p['answer'] for p in rows}
        self.assertEqual(len(known),len(rows))
        for pair in self.read('understanding-training.jsonl'):
            self.assertEqual(known[normalize(pair['question'])], pair['answer'])
        for name in ('heldout.jsonl','dialogue-heldout.jsonl','growth-heldout.jsonl',
                     'understanding-probes.jsonl','natural-probes.jsonl'):
            for pair in self.read(name):
                self.assertNotIn(normalize(pair['question']),known)

