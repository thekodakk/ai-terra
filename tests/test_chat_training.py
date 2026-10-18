import unittest

try:
    import torch
except ImportError:
    torch = None


@unittest.skipUnless(torch is not None, 'PyTorch required')
class ChatTrainingTests(unittest.TestCase):
    def test_answer_balancing_equalizes_group_probability(self):
        from scratch.train_chat import sampling_weights
        pairs = [{'answer':'A'}] * 9 + [{'answer':'B'}]
        uniform = sampling_weights(pairs)
        balanced = sampling_weights(pairs, 1)
        self.assertEqual(uniform.tolist(), [1.] * 10)
        self.assertAlmostEqual(float(balanced[:9].sum()), float(balanced[9]), places=6)
        partial = sampling_weights(pairs, .5)
        self.assertAlmostEqual(float(partial[:9].sum()), 3., places=6)
        for invalid in (-1, 2, float('nan')):
            with self.assertRaises(ValueError):
                sampling_weights(pairs, invalid)

    def test_answer_mask_and_eos(self):
        from scratch.train_chat import batch_for
        from scratch.model import BOS, EOS, encode
        from scratch.conversation import prompt_for
        pairs = [{'question': 'hi', 'answer': 'hello'}, {'question': 'longer question', 'answer': 'short'}]
        x, y = batch_for(pairs)
        for index, pair in enumerate(pairs):
            prefix = [BOS] + encode(prompt_for(pair['question']))
            start = len(prefix) - 1
            answer = encode(pair['answer']) + [EOS]
            self.assertTrue(torch.all(y[index, :start] == -100))
            self.assertEqual(y[index, start:start+len(answer)].tolist(), answer)
            self.assertTrue(torch.all(y[index, start+len(answer):] == -100))
            self.assertEqual(x[index, 0], BOS)

    def test_long_examples_not_silently_truncated(self):
        from scratch.train_chat import batch_for
        with self.assertRaises(ValueError):
            batch_for([{'question': 'x', 'answer': 'y' * 600}], context=512)
