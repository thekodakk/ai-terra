"""A small causal Transformer, initialized randomly; UTF-8 byte vocabulary."""
from dataclasses import asdict, dataclass
import torch
from torch import nn
from torch.nn import functional as F

BOS, EOS, VOCAB = 256, 257, 258


@dataclass
class ModelConfig:
    width: int = 128
    heads: int = 4
    layers: int = 4
    context: int = 256

    def validate(self):
        if not (32 <= self.width <= 1024 and 1 <= self.heads <= 16 and self.width % self.heads == 0
                and 1 <= self.layers <= 16 and 32 <= self.context <= 4096):
            raise ValueError('Desteklenmeyen model boyutları.')


def encode(text):
    return list(text.encode('utf-8'))


def decode(tokens):
    return bytes(t for t in tokens if 0 <= t < 256).decode('utf-8', errors='replace')


class Block(nn.Module):
    def __init__(self, cfg):
        super().__init__()
        self.heads = cfg.heads
        self.norm1 = nn.LayerNorm(cfg.width)
        self.qkv = nn.Linear(cfg.width, 3 * cfg.width)
        self.proj = nn.Linear(cfg.width, cfg.width)
        self.norm2 = nn.LayerNorm(cfg.width)
        self.mlp = nn.Sequential(nn.Linear(cfg.width, 4 * cfg.width), nn.GELU(), nn.Linear(4 * cfg.width, cfg.width))

    def forward(self, x):
        b, t, c = x.shape
        q, k, v = self.qkv(self.norm1(x)).chunk(3, dim=-1)
        q, k, v = [z.view(b, t, self.heads, c // self.heads).transpose(1, 2) for z in (q, k, v)]
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True)
        x = x + self.proj(a.transpose(1, 2).contiguous().view(b, t, c))
        return x + self.mlp(self.norm2(x))


class TerraModel(nn.Module):
    def __init__(self, cfg=None):
        super().__init__()
        self.cfg = cfg or ModelConfig()
        self.cfg.validate()
        self.embedding = nn.Embedding(VOCAB, self.cfg.width)
        self.position = nn.Embedding(self.cfg.context, self.cfg.width)
        self.blocks = nn.Sequential(*(Block(self.cfg) for _ in range(self.cfg.layers)))
        self.norm = nn.LayerNorm(self.cfg.width)
        self.head = nn.Linear(self.cfg.width, VOCAB, bias=False)
        self.apply(self._init)
        self.head.weight = self.embedding.weight

    @staticmethod
    def _init(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                nn.init.zeros_(module.bias)

    def forward(self, tokens, targets=None, position_offset=0):
        if not isinstance(position_offset, int) or position_offset < 0 or tokens.shape[1] + position_offset > self.cfg.context:
            raise ValueError('Bağlam sınırı aşıldı.')
        pos = torch.arange(position_offset, position_offset + tokens.shape[1], device=tokens.device)
        x = self.embedding(tokens) + self.position(pos)
        logits = self.head(self.norm(self.blocks(x)))
        loss = None if targets is None else F.cross_entropy(logits.reshape(-1, VOCAB), targets.reshape(-1))
        return logits, loss

    @torch.inference_mode()
    def generate(self, prompt, max_bytes=768, temperature=0.7, stop=None, emit=None):
        self.eval()
        device = next(self.parameters()).device
        tokens = [BOS] + encode(prompt)
        output = []
        for _ in range(max_bytes):
            if stop is not None and stop.is_set():
                break
            inputs = torch.tensor([tokens[-self.cfg.context:]], dtype=torch.long, device=device)
            logits, _ = self(inputs)
            scores = logits[0, -1].float() / max(0.1, temperature)
            scores[BOS] = -float('inf')
            cutoff = torch.topk(scores, 40).values[-1]
            scores[scores < cutoff] = -float('inf')
            token = int(scores.argmax()) if temperature == 0 else int(torch.multinomial(scores.softmax(-1), 1))
            if token == EOS:
                break
            tokens.append(token)
            output.append(token)
            if emit and len(output) % 12 == 0:
                emit(decode(output))
        result = decode(output)
        if emit:
            emit(result)
        return result

    def config_dict(self):
        return asdict(self.cfg)
