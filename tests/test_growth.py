import unittest
import torch
from scratch.model import TerraModel, ModelConfig
from scratch.grow_model import expand_depth


class GrowthTests(unittest.TestCase):
    def test_initial_logits_are_preserved_and_new_layers_can_learn(self):
        torch.manual_seed(5)
        torch.set_num_threads(2)
        model = TerraModel(ModelConfig(width=32,heads=2,layers=1,context=32))
        tokens = torch.tensor([[256,1,2,3],[256,4,5,6]])
        grown = expand_depth(model,3)
        old_logits,_ = model(tokens)
        new_logits,loss = grown(tokens,tokens)
        self.assertTrue(torch.equal(old_logits,new_logits))
        self.assertEqual(grown.cfg.layers,3)
        self.assertGreater(sum(p.numel() for p in grown.parameters()),sum(p.numel() for p in model.parameters()))
        loss.backward()
        self.assertGreater(grown.blocks[1].proj.weight.grad.abs().sum().item(),0)
        self.assertTrue(all(p.grad is None for p in model.parameters()))
        self.assertEqual(model.generate('hi',max_bytes=12,temperature=0),grown.generate('hi',max_bytes=12,temperature=0))

    def test_invalid_or_non_growing_depth_rejected(self):
        model = TerraModel(ModelConfig(width=32,heads=2,layers=2))
        for depth in [0,1,2,17]:
            with self.assertRaises(ValueError):
                expand_depth(model,depth)
