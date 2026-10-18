"""Full-example, answer-masked supervised training from random weights.

The small bundled corpus is a memorisation exercise, not a language benchmark.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import torch
from .model import BOS, EOS, ModelConfig, TerraModel, encode
from .training import FORMAT, atomic_save, load_checkpoint
from .conversation import prompt_for


def batch_for(pairs, context=512):
    sequences, labels = [], []
    for pair in pairs:
        prefix = [BOS] + encode(prompt_for(pair['question']))
        sequence = prefix + encode(pair['answer']) + [EOS]
        if len(sequence) - 1 > context:
            raise ValueError('Örnek bağlama sığmıyor; soruyu/yanıtı kısalt veya bağlamı artır.')
        x, y = sequence[:-1], sequence[1:]
        y[:len(prefix)-1] = [-100] * (len(prefix)-1)
        sequences.append(x)
        labels.append(y)
    length = max(map(len, sequences))
    return (torch.tensor([x + [EOS]*(length-len(x)) for x in sequences]),
            torch.tensor([y + [-100]*(length-len(y)) for y in labels]))


def sampling_weights(pairs, balance=0.0):
    """At 1, each distinct taught answer receives equal sampling mass.

    Intermediate exponents reduce over-representation without removing examples.
    This changes training frequency, not inference or the evaluation answers.
    """
    if not 0 <= balance <= 1 or not pairs:
        raise ValueError('Denge 0–1 arasında ve veri dolu olmalı.')
    counts = Counter(p['answer'].strip() for p in pairs)
    return torch.tensor([counts[p['answer'].strip()] ** -balance for p in pairs], dtype=torch.float)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--steps', type=int, default=1600)
    parser.add_argument('--data', default='training/conversation.jsonl')
    parser.add_argument('--output', default='models/terra-chat.pt')
    parser.add_argument('--resume', help='Continue from a locally trained Terra checkpoint')
    parser.add_argument('--lr', type=float, default=.001)
    parser.add_argument('--followup-links', help='Explicit application topic-to-explanation links')
    parser.add_argument('--position-jitter', type=int, default=0, help='Experimental random position offset during training')
    parser.add_argument('--anchor-probability', type=float, default=0, help='Fraction of jitter training steps kept at normal positions')
    parser.add_argument('--answer-balance', type=float, default=0, help='0: uniform questions; 1: uniform answer groups')
    args = parser.parse_args()
    if not 1 <= args.steps <= 10000:
        raise ValueError('Adım sınırı: 1–10000')
    if args.position_jitter < 0:
        raise ValueError('Konum kaydırma negatif olamaz.')
    if not 0 <= args.anchor_probability <= 1:
        raise ValueError('Normal konum oranı 0 ile 1 arasında olmalı.')
    if args.resume and Path(args.resume).resolve() == Path(args.output).resolve():
        raise ValueError('Eğitim adayını kaynak modelden ayrı bir dosyaya kaydet.')
    torch.manual_seed(42)
    torch.set_num_threads(4)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    raw = Path(args.data).read_bytes()
    pairs = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    if not pairs:
        raise ValueError('Eğitim verisi boş.')
    weights = sampling_weights(pairs, args.answer_balance).to(device)
    links = json.loads(Path(args.followup_links).read_text('utf-8')) if args.followup_links else {}
    from .conversation import normalize
    questions = {normalize(p['question']) for p in pairs}
    if any(k not in questions or normalize(v) not in questions for k,v in links.items()):
        raise ValueError('Takip sorusu bağlantısı eğitim verisinde bulunamadı.')
    previous = {}
    if args.resume:
        model, previous = load_checkpoint(args.resume, device)
        cfg = model.cfg
    else:
        cfg = ModelConfig(context=512)
        model = TerraModel(cfg).to(device)
    x, y = batch_for(pairs, cfg.context)
    if x.shape[1] + args.position_jitter > cfg.context:
        raise ValueError('Konum kaydırma için bağlamda yeterli yer yok.')
    x, y = x.to(device), y.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, args.steps, eta_min=args.lr * .1)
    began = time.monotonic()
    for step in range(1, args.steps + 1):
        indices = (torch.multinomial(weights, 16, replacement=True) if args.answer_balance
                   else torch.randint(len(pairs), (16,), device=device))
        optimizer.zero_grad(set_to_none=True)
        offset = int(torch.randint(args.position_jitter+1, (1,))) if args.position_jitter else 0
        if args.anchor_probability and float(torch.rand(())) < args.anchor_probability:
            offset = 0
        _, loss = model(x[indices], y[indices], position_offset=offset)
        if not torch.isfinite(loss):
            raise ValueError('Geçersiz eğitim kaybı.')
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        if step % 500 == 0 or step == 1 or step == args.steps:
            print(json.dumps({'step': step, 'loss': float(loss.detach()), 'seconds': round(time.monotonic()-began, 1)}), flush=True)
    payload = {'format': FORMAT, 'origin': 'random_initialization', 'config': model.config_dict(),
               'weights': model.state_dict(), 'optimizer': optimizer.state_dict(), 'rng': torch.get_rng_state(),
               'steps': previous.get('steps', 0) + args.steps, 'phase_steps': args.steps,
               'parent_sha256': hashlib.sha256(Path(args.resume).read_bytes()).hexdigest() if args.resume else None,
               'train_loss': float(loss.detach()), 'validation_loss': None,
               'parameters': sum(p.numel() for p in model.parameters()), 'conversation_pairs': pairs,
               'training_method': 'full_qa_answer_masked', 'capability': 'taught_examples_only', 'followup_links': links,
               'sources': [{'name': Path(args.data).name, 'sha256': hashlib.sha256(raw).hexdigest()}],
               'evaluation_note': 'Training-example reproduction only; no generalisation claim.',
               'position_jitter':args.position_jitter,'anchor_probability':args.anchor_probability,
               'answer_balance':args.answer_balance}
    if previous.get('growth'):
        payload['growth'] = dict(previous['growth'])
        payload['growth']['new_layer_steps'] += args.steps
    atomic_save(payload, args.output)
    summary = {k:v for k,v in payload.items() if k not in ('weights', 'optimizer', 'rng', 'conversation_pairs')}
    summary['supported_questions'] = [pair['question'] for pair in pairs]
    summary['training_hyperparameters'] = {'initial_lr': args.lr, 'final_lr': args.lr * .1, 'batch_size': 16, 'schedule': 'cosine', 'seed': 42, 'position_jitter':args.position_jitter,'anchor_probability':args.anchor_probability,'answer_balance':args.answer_balance}
    Path(args.output).with_suffix('.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
