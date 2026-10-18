import unittest
import torch
from scratch.model import TerraModel, ModelConfig, EOS, VOCAB
from scratch.batch_evaluate import evaluate, evaluate_taught


class CausalFixture(torch.nn.Module):
    """Known causal next-token distribution: final space -> A -> B -> EOS."""
    generate = TerraModel.generate

    def __init__(self):
        super().__init__()
        self.marker = torch.nn.Parameter(torch.zeros(1))
        self.cfg = ModelConfig(context=128)

    def forward(self,tokens):
        next_token = torch.zeros_like(tokens)
        next_token[tokens==32] = 65
        next_token[tokens==65] = 66
        next_token[tokens==66] = EOS
        scores = torch.full((*tokens.shape,VOCAB),-10.,device=tokens.device)
        scores.scatter_(-1,next_token[:,:,None],10.)
        return scores,None


class CertifiedEvaluationTests(unittest.TestCase):
    def test_certificate_matches_real_autoregressive_decoding_and_checks_eos(self):
        model = CausalFixture()
        pairs = [{'question':'a question','answer':answer} for answer in ['AB','AC','A','AB!','']]
        fast, slow = evaluate_taught(model,pairs,batch_size=2), evaluate(model,pairs)
        self.assertEqual(fast['correct'],1)
        self.assertEqual([r['actual'] for r in fast['results']],[r['actual'] for r in slow['results']])
        self.assertEqual([r['exact'] for r in fast['results']],[r['exact'] for r in slow['results']])
        self.assertEqual(fast['results'][0]['verification'],'causal_greedy_certificate')
        self.assertTrue(all(r['verification']=='autoregressive' for r in fast['results'][1:]))
