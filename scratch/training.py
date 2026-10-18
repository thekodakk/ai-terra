"""Explicit local corpus ingestion, bounded training and resumable checkpoints."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import torch
from .model import BOS, EOS, ModelConfig, TerraModel, encode

FORMAT = 'terra-byte-transformer-v1'
MAX_CORPUS_BYTES = 32 * 1024 * 1024


def load_corpus(paths):
    tokens, sources, total = [], [], 0
    for value in paths:
        path = Path(value).resolve()
        if path.suffix.lower() not in ('.txt', '.jsonl'):
            raise ValueError('Yalnızca açıkça seçilen TXT ve JSONL dosyaları okunur.')
        size = path.stat().st_size
        if size > MAX_CORPUS_BYTES - total:
            raise ValueError('Bu sürümde toplam veri sınırı 32 MB.')
        raw = path.read_bytes()
        total += len(raw)
        if total > MAX_CORPUS_BYTES:
            raise ValueError('Veri sınırı aşıldı.')
        text = raw.decode('utf-8-sig')
        sources.append({'name': path.name, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
        if path.suffix.lower() == '.jsonl':
            records = []
            for line in text.splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError('JSONL satırları nesne olmalı.')
                if isinstance(row.get('question'), str) and isinstance(row.get('answer'), str):
                    records.append(f"Kullanıcı: {row['question']}\nTerra: {row['answer']}")
                elif isinstance(row.get('text'), str):
                    records.append(row['text'])
                else:
                    raise ValueError('JSONL için text veya question + answer alanları gerekli.')
        else:
            records = [text]
        for record in records:
            if record.strip():
                tokens.extend([BOS] + encode(record) + [EOS])
    if len(tokens) < 2048:
        raise ValueError('Eğitim için en az 2048 UTF-8 baytlık metin gerekli.')
    return torch.tensor(tokens, dtype=torch.long), sources


def load_checkpoint(path, device='cpu'):
    path = Path(path)
    if path.stat().st_size > 1024 * 1024 * 1024:
        raise ValueError('Model dosyası bu sürüm için çok büyük.')
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if checkpoint.get('format') != FORMAT or checkpoint.get('origin') != 'random_initialization':
        raise ValueError('Bu dosya Terra eğitim biçiminde değil.')
    model = TerraModel(ModelConfig(**checkpoint['config']))
    model.load_state_dict(checkpoint['weights'], strict=True)
    return model.to(device), checkpoint


def atomic_save(payload, target):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(target.suffix + '.tmp')
    try:
        torch.save(payload, temp)
        os.replace(temp, target)
    finally:
        temp.unlink(missing_ok=True)


def train(paths, target, steps=200, stop=None, emit=None, resume=False, cfg=None, device=None, seed=42):
    if not 1 <= steps <= 100000:
        raise ValueError('Adım sayısı 1–100000 arasında olmalı.')
    stop = stop or threading.Event()
    emit = emit or (lambda data: None)
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    torch.manual_seed(seed)
    device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
    corpus, sources = load_corpus(paths)
    split = int(len(corpus) * .9)
    train_data, validation_data = corpus[:split], corpus[split:]
    metadata = {}
    if resume:
        model, metadata = load_checkpoint(target, device)
        if metadata.get('sources') != sources:
            raise ValueError('Devam etmek için önceki eğitimle aynı dosyaları seç. Yeni veri için yeni model oluştur.')
    else:
        model = TerraModel(cfg).to(device)
    context = min(model.cfg.context, len(validation_data) - 1)
    if context < 32:
        raise ValueError('Doğrulama metni yetersiz.')
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=.01)
    if resume:
        optimizer.load_state_dict(metadata['optimizer'])
        if 'rng' in metadata:
            torch.set_rng_state(metadata['rng'])
    start = int(metadata.get('steps', 0))
    completed = start
    loss_value = metadata.get('train_loss')
    validation = metadata.get('validation_loss')
    batch_size = 16 if device.startswith('cuda') else 4
    generator = torch.Generator().manual_seed(123)
    # Fixed held-out windows; validation never consumes training RNG.
    offsets = torch.randint(len(validation_data) - context, (8,), generator=generator)
    vx = torch.stack([validation_data[i:i+context] for i in offsets]).to(device)
    vy = torch.stack([validation_data[i+1:i+context+1] for i in offsets]).to(device)
    began = time.monotonic()

    def save():
        payload = {'format': FORMAT, 'origin': 'random_initialization', 'config': model.config_dict(),
                   'weights': model.state_dict(), 'optimizer': optimizer.state_dict(), 'rng': torch.get_rng_state(),
                   'steps': completed, 'sources': sources, 'train_loss': loss_value,
                   'validation_loss': validation, 'parameters': sum(p.numel() for p in model.parameters()),
                   'seed': seed, 'trained_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                   'capability': 'experimental_text_only', 'split': '90% train / 10% held-out contiguous bytes'}
        atomic_save(payload, target)
        sidecar = Path(target).with_suffix('.json')
        info = {k: v for k, v in payload.items() if k not in ('weights', 'optimizer', 'rng')}
        temp = sidecar.with_suffix('.json.tmp')
        temp.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, sidecar)

    emit({'kind': 'started', 'device': device, 'parameters': sum(p.numel() for p in model.parameters()), 'start': start})
    for step in range(start + 1, start + steps + 1):
        if stop.is_set():
            break
        model.train()
        indices = torch.randint(len(train_data) - context, (batch_size,))
        x = torch.stack([train_data[i:i+context] for i in indices]).to(device)
        y = torch.stack([train_data[i+1:i+context+1] for i in indices]).to(device)
        optimizer.zero_grad(set_to_none=True)
        _, loss = model(x, y)
        if not torch.isfinite(loss):
            raise ValueError('Eğitim kaybı geçersiz; son sağlam kayıt korunuyor.')
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        completed = step
        loss_value = float(loss.detach())
        if step == start + 1 or step % 10 == 0 or step == start + steps:
            model.eval()
            with torch.no_grad():
                _, vloss = model(vx, vy)
                validation = float(vloss)
            emit({'kind': 'progress', 'step': step, 'target': start + steps, 'loss': loss_value,
                  'validation': validation, 'seconds': round(time.monotonic() - began, 1)})
        if step % 100 == 0:
            save()
    save()
    result = {'kind': 'finished', 'steps': completed, 'stopped': stop.is_set(), 'path': str(target),
              'loss': loss_value, 'validation': validation}
    emit(result)
    return result


def main():
    parser = argparse.ArgumentParser(description='Terra: yalnızca seçilen metinlerle sıfırdan eğitim')
    parser.add_argument('files', nargs='+')
    parser.add_argument('--output', default='models/terra-own.pt')
    parser.add_argument('--steps', type=int, default=200)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    train(args.files, args.output, args.steps, resume=args.resume,
          emit=lambda event: print(json.dumps(event, ensure_ascii=False), flush=True))


if __name__ == '__main__':
    main()
