import json
from pathlib import Path
import unittest
from scratch.conversation import normalize, prompt_for

ROOT = Path(__file__).resolve().parents[1]


class GrowthCorpusTests(unittest.TestCase):
    def read(self,name):
        return [json.loads(s) for s in (ROOT/'training'/name).read_text('utf-8').splitlines() if s.strip()]

    def test_old_answers_preserved_and_frozen_questions_excluded(self):
        pairs = self.read('growth-training.jsonl')
        known = {normalize(p['question']):p['answer'] for p in pairs}
        self.assertEqual(len(pairs),len(known))
        for pair in self.read('dialogue-training.jsonl'):
            self.assertEqual(known[normalize(pair['question'])],pair['answer'])
        for file in ['heldout.jsonl','dialogue-heldout.jsonl','growth-heldout.jsonl']:
            self.assertTrue(all(normalize(p['question']) not in known for p in self.read(file)))

    def test_new_examples_fit_context_with_position_augmentation(self):
        for pair in self.read('growth-training.jsonl'):
            size = len((prompt_for(pair['question'])+pair['answer']).encode('utf-8'))+1
            self.assertLessEqual(size+16,512,pair['question'])
