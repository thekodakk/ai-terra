"""Cancellable local question/answer fine-tuning for the desktop workshop."""
import hashlib
import json
import math
import threading
import time
from pathlib import Path
import torch
from .conversation import normalize
from .model import ModelConfig, TerraModel
from .train_chat import batch_for
from .training import FORMAT, MAX_CORPUS_BYTES, atomic_save, load_checkpoint


def read_pairs(paths):
    pairs, sources, seen, size = [], [], {}, 0
    for value in paths:
        path = Path(value)
        if path.suffix.lower() != '.jsonl':
            raise ValueError('Sohbet eğitimi için question ve answer alanlı JSONL seç.')
        if path.stat().st_size > MAX_CORPUS_BYTES-size:
            raise ValueError('Toplam eğitim dosyası sınırı 32 MB.')
        raw = path.read_bytes()
        size += len(raw)
        if size > MAX_CORPUS_BYTES:
            raise ValueError('Toplam eğitim dosyası sınırı 32 MB.')
        sources.append({'name':path.name, 'sha256':hashlib.sha256(raw).hexdigest()})
        for line in raw.decode('utf-8-sig').splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row,dict) or not all(isinstance(row.get(k),str) and row[k].strip() for k in ('question','answer')):
                raise ValueError('Her satırda boş olmayan question ve answer metinleri gerekli.')
            key = normalize(row['question'])
            if not key:
                raise ValueError('Soru yalnızca noktalama olamaz.')
            if key in seen and seen[key] != row['answer']:
                raise ValueError('Aynı soruya farklı yanıtlar verilmiş: '+row['question'])
            if key not in seen:
                pairs.append({'question':row['question'], 'answer':row['answer']})
                seen[key] = row['answer']
    if not pairs:
        raise ValueError('Eğitim dosyasında soru-cevap örneği yok.')
    return pairs, sources


def train_qa(paths, target, steps=1000, stop=None, emit=None, resume_from=None,
             device=None, cfg=None, lr=.0004, checkpoint_every=100, seed=42):
    if not 1 <= steps <= 100000 or checkpoint_every < 1 or not math.isfinite(lr) or lr <= 0:
        raise ValueError('Geçersiz eğitim ayarı.')
    target = Path(target)
    if resume_from and Path(resume_from).resolve() == target.resolve():
        raise ValueError('İnce ayar için farklı bir aday dosyası seç; kaynak model korunmalı.')
    stop = stop or threading.Event()
    emit = emit or (lambda event:None)
    torch.set_num_threads(4)
    torch.manual_seed(seed)
    device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
    pairs, sources = read_pairs(paths)
    previous = {}
    if resume_from:
        model, previous = load_checkpoint(resume_from, device)
    else:
        model = TerraModel(cfg or ModelConfig(context=512)).to(device)
    model.train()
    x, y = batch_for(pairs, model.cfg.context)
    # Keep the full corpus on CPU; only the current minibatch occupies VRAM.
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, steps, eta_min=lr*.1)
    count = sum(p.numel() for p in model.parameters())
    parent_hash = hashlib.sha256(Path(resume_from).read_bytes()).hexdigest() if resume_from else None
    available = {normalize(p['question']) for p in pairs}
    links = {k:v for k,v in previous.get('followup_links',{}).items() if k in available and normalize(v) in available}
    start = previous.get('steps',0)
    completed, loss_value = 0, None
    began = time.monotonic()
    emit({'kind':'started','device':device,'parameters':count,'start':start})

    def save():
        payload = {'format':FORMAT, 'origin':'random_initialization', 'config':model.config_dict(),
            'weights':model.state_dict(), 'optimizer':optimizer.state_dict(), 'rng':torch.get_rng_state(),
            'steps':start+completed, 'phase_steps':completed, 'parent_sha256':parent_hash,
            'train_loss':loss_value,'validation_loss':None,'parameters':count,'conversation_pairs':pairs,
            'training_method':'full_qa_answer_masked','capability':'taught_examples_only',
            'followup_links':links,'sources':sources,'stopped':stop.is_set(),
            'evaluation_note':'Not evaluated. A fine-tuning phase starts a fresh optimizer; no quality guarantee.'}
        atomic_save(payload,target)
        summary = {k:v for k,v in payload.items() if k not in ('weights','optimizer','rng','conversation_pairs')}
        summary['supported_questions'] = [p['question'] for p in pairs]
        summary['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        target.with_suffix('.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')

    for _ in range(steps):
        if stop.is_set():
            break
        indices = torch.randint(len(pairs),(16,))
        optimizer.zero_grad(set_to_none=True)
        _, loss = model(x[indices].to(device),y[indices].to(device))
        if not torch.isfinite(loss):
            raise ValueError('Geçersiz eğitim kaybı. Son düzenli kayıt korunuyor.')
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
        optimizer.step()
        scheduler.step()
        completed += 1
        loss_value = float(loss.detach())
        if completed % checkpoint_every == 0 or completed == steps or stop.is_set():
            save()
        if completed == 1 or completed % 50 == 0 or completed == steps:
            emit({'kind':'progress','step':start+completed,'target':start+steps,'loss':loss_value,
                  'validation':None,'seconds':round(time.monotonic()-began,1)})
    # A stop set by the progress callback must also persist that last completed step.
    if completed:
        save()
    emit({'kind':'finished','steps':start+completed,'stopped':stop.is_set(),
          'path':str(target),'saved':completed>0,'candidate':True})
    return {'steps':start+completed,'saved':completed>0,'path':str(target)}
