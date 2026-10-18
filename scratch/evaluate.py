"""Compare real generated answers with frozen local evaluation files."""
import argparse
import json
from pathlib import Path
import time
import torch
from .conversation import prompt_for, normalize
from .training import load_checkpoint


def evaluate(model, pairs):
    results = []
    for index, pair in enumerate(pairs):
        actual = model.generate(prompt_for(pair['question']), max_bytes=512, temperature=0)
        results.append({'question': pair['question'], 'expected': pair['answer'],
                        'actual': actual, 'exact': actual.strip() == pair['answer'].strip()})
        if (index + 1) % 50 == 0:
            print(f'Evaluated {index+1}/{len(pairs)}', flush=True)
    return {'correct': sum(row['exact'] for row in results), 'total': len(results), 'results': results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('model')
    parser.add_argument('--heldout', default='training/heldout.jsonl')
    parser.add_argument('--output', default='data/expanded-evaluation.json')
    args = parser.parse_args()
    torch.set_num_threads(4)
    model, info = load_checkpoint(args.model, 'cuda' if torch.cuda.is_available() else 'cpu')
    heldout = [json.loads(line) for line in Path(args.heldout).read_text('utf-8').splitlines() if line.strip()]
    assert not ({normalize(p['question']) for p in heldout} & {normalize(p['question']) for p in info['conversation_pairs']})
    began = time.monotonic()
    report = {'model': args.model, 'steps': info['steps'], 'trained': evaluate(model, info['conversation_pairs']),
              'heldout': evaluate(model, heldout), 'note': 'Exact reproduction is not a general intelligence benchmark.'}
    report['seconds'] = round(time.monotonic() - began, 2)
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: {k:v for k,v in report[key].items() if k != 'results'} for key in ('trained','heldout')}), flush=True)


if __name__ == '__main__':
    main()
