"""Greedy evaluation grouped by equal prompt length; no padding changes positions."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import torch
from .model import BOS, EOS, encode, decode
from .conversation import normalize, prompt_for
from .training import load_checkpoint


@torch.inference_mode()
def generate_many(model, prompts, max_bytes=512, batch_size=32, progress=None):
    model.eval()
    groups = defaultdict(list)
    outputs = [''] * len(prompts)
    for i, prompt in enumerate(prompts):
        seq = [BOS]+encode(prompt)
        groups[len(seq)].append((i, seq))
    device = next(model.parameters()).device
    completed = 0
    for rows in groups.values():
        for start in range(0, len(rows), batch_size):
            group = rows[start:start+batch_size]
            tokens = torch.tensor([seq for _,seq in group], device=device)
            active = torch.ones(len(group), dtype=torch.bool, device=device)
            generated = []
            for _ in range(max_bytes):
                logits, _ = model(tokens[:, -model.cfg.context:])
                scores = logits[:, -1].float()
                scores[:, BOS] = -float('inf')
                nxt = scores.argmax(-1)
                nxt = torch.where(active, nxt, EOS)
                generated.append(nxt)
                active &= nxt != EOS
                if not active.any():
                    break
                tokens = torch.cat((tokens, nxt[:, None]), dim=1)
            if generated:
                for (index, _), sequence in zip(group, torch.stack(generated, 1).cpu().tolist()):
                    end = sequence.index(EOS) if EOS in sequence else len(sequence)
                    outputs[index] = decode(sequence[:end])
            completed += len(group)
            if progress:
                progress(completed,len(prompts))
    return outputs


def evaluate(model, pairs):
    previous = [0]
    def progress(completed,total):
        if total >= 100 and (completed-previous[0] >= 250 or completed==total):
            print(f'Evaluated {completed}/{total}',flush=True)
            previous[0] = completed
    actual = generate_many(model, [prompt_for(r['question']) for r in pairs],progress=progress)
    rows = [dict(question=p['question'], expected=p['answer'], actual=a,
                 exact=a.strip()==p['answer'].strip()) for p,a in zip(pairs,actual)]
    return {'correct':sum(r['exact'] for r in rows), 'total':len(rows), 'results':rows}


@torch.inference_mode()
def evaluate_taught(model, pairs, batch_size=32):
    """Certify matching greedy sequences in one causal pass; decode failures.

    Every next-answer byte AND EOS must be the argmax at its own prefix.
    This is an evaluation optimization, never used to produce chat answers.
    """
    from .train_chat import batch_for
    model.eval()
    device = next(model.parameters()).device
    rows, failed = [], []
    for start in range(0,len(pairs),batch_size):
        chunk = pairs[start:start+batch_size]
        x,y = batch_for(chunk,model.cfg.context)
        logits,_ = model(x.to(device))
        logits[:,:,BOS] = -float('inf')
        top = logits.float().topk(2,dim=-1)
        labels = y.to(device)
        # Near ties use ordinary decoding to avoid precision-sensitive certificates.
        valid = ((top.indices[:,:,0]==labels) & ((top.values[:,:,0]-top.values[:,:,1])>0.001)) | (labels==-100)
        certified = valid.all(dim=1).cpu().tolist()
        for p,okay in zip(chunk,certified):
            row = dict(question=p['question'],expected=p['answer'],actual=p['answer'] if okay else None,
                       exact=okay,verification='causal_greedy_certificate' if okay else 'autoregressive')
            if not okay:
                failed.append((len(rows),p))
            rows.append(row)
    if failed:
        decoded = generate_many(model,[prompt_for(p['question']) for _,p in failed])
        for (i,p),actual in zip(failed,decoded):
            rows[i].update(actual=actual,exact=actual.strip()==p['answer'].strip())
    return {'correct':sum(r['exact'] for r in rows),'total':len(rows),'results':rows,
            'method':'causal greedy certification including EOS; near ties and failures decoded autoregressively'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model')
    parser.add_argument('--output', required=True)
    parser.add_argument('--trained', action='store_true')
    parser.add_argument('--extra-heldout', help='Additional frozen development JSONL')
    parser.add_argument('--probe', help='Fresh final probe file, kept separate from development')
    parser.add_argument('--fast-trained',action='store_true',help='Certify greedy trained answers in a causal pass; decode failures normally')
    args = parser.parse_args()
    torch.set_num_threads(4)
    path = Path(args.model)
    model, info = load_checkpoint(path, 'cuda' if torch.cuda.is_available() else 'cpu')
    report = {'model':str(path.resolve()), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'steps':info['steps'], 'status':'running', 'note':'Greedy exact text match, without application routing; small development sets.'}
    def save_report():
        output = Path(args.output)
        output.parent.mkdir(parents=True,exist_ok=True)
        temp = output.with_suffix(output.suffix+'.tmp')
        temp.write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
        temp.replace(output)
    training_keys = {normalize(p['question']) for p in info['conversation_pairs']}
    sets = [('heldout',Path('training/heldout.jsonl')),('dialogue_heldout',Path('training/dialogue-heldout.jsonl'))]
    if args.extra_heldout:
        sets.append(('extra_heldout',Path(args.extra_heldout)))
    if args.probe:
        sets.append(('probe_heldout',Path(args.probe)))
    for name, filename in sets:
        raw = filename.read_bytes()
        pairs = [json.loads(s) for s in raw.decode('utf-8').splitlines() if s.strip()]
        if training_keys & {normalize(p['question']) for p in pairs}:
            raise ValueError('Training/development overlap')
        report[name] = evaluate(model, pairs)
        report[name]['data_sha256'] = hashlib.sha256(raw).hexdigest()
        print(name, report[name]['correct'], '/', report[name]['total'], flush=True)
        save_report()
    if args.trained:
        report['trained'] = (evaluate_taught if args.fast_trained else evaluate)(model, info['conversation_pairs'])
        print('trained', report['trained']['correct'], '/', report['trained']['total'], flush=True)
    report['status'] = 'complete'
    save_report()


if __name__ == '__main__':
    main()
