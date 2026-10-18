import json
from pathlib import Path
import unittest
from scratch.conversation import normalize,prompt_for

ROOT=Path(__file__).resolve().parents[1]/'training'

def read(name):
    return [json.loads(s) for s in (ROOT/name).read_text('utf-8').splitlines() if s.strip()]


class UnderstandingDataTests(unittest.TestCase):
    def test_old_answers_retained_and_all_evaluations_disjoint(self):
        pairs=read('understanding-training.jsonl')
        known={normalize(p['question']):p['answer'] for p in pairs}
        self.assertEqual(len(known),len(pairs))
        for p in read('growth-training.jsonl'):
            self.assertEqual(known[normalize(p['question'])],p['answer'])
        for name in ['heldout.jsonl','dialogue-heldout.jsonl','growth-heldout.jsonl','understanding-probes.jsonl']:
            self.assertTrue(all(normalize(p['question']) not in known for p in read(name)))

    def test_context_bound(self):
        for p in read('understanding-training.jsonl'):
            self.assertLessEqual(len((prompt_for(p['question'])+p['answer']).encode('utf-8'))+17,512)
