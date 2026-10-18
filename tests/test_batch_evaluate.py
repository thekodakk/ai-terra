import unittest
import torch
import os
from scratch.model import TerraModel, ModelConfig
from scratch.batch_evaluate import generate_many


class BatchEvaluationTests(unittest.TestCase):
    def test_matches_scalar_greedy_with_unicode_and_context_rollover(self):
        torch.manual_seed(123)
        torch.set_num_threads(2)
        model = TerraModel(ModelConfig(width=32, layers=1, heads=2, context=32))
        prompts = ['selam', 'hello', 'Türkçe', 'a'*40, '']
        expected = [model.generate(p, max_bytes=36, temperature=0) for p in prompts]
        self.assertEqual(generate_many(model, prompts, max_bytes=36, batch_size=2), expected)

    def test_empty_batch_and_zero_budget(self):
        model = TerraModel(ModelConfig(width=32, layers=1, heads=2, context=32))
        self.assertEqual(generate_many(model, []), [])
        self.assertEqual(generate_many(model, ['hello'], max_bytes=0), [''])

    def test_position_offset_is_bounded_and_does_not_break_causality(self):
        model = TerraModel(ModelConfig(width=32, layers=1, heads=2, context=32))
        tokens = torch.tensor([[1,2,3,4]])
        original, _ = model(tokens, position_offset=4)
        changed = tokens.clone()
        changed[0,-1] = 5
        later, _ = model(changed, position_offset=4)
        self.assertTrue(torch.allclose(original[:,:-1],later[:,:-1]))
        for offset in [-1,29,1.5]:
            with self.assertRaises(ValueError):
                model(tokens,position_offset=offset)
                