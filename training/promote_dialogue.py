"""Hash-bound activation of the evaluated 0.4 candidate, retaining the old model."""
import hashlib
import argparse
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scratch.training import load_checkpoint, atomic_save


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report',default=str(ROOT/'data/dialogue-candidate-evaluation.json'))
    parser.add_argument('--baseline',default=str(ROOT/'data/dialogue-baseline.json'))
    parser.add_argument('--audit',required=True)
    parser.add_argument('--backup',default=str(ROOT/'models/terra-before-0.4.pt'))
    parser.add_argument('--extra-heldout')
    parser.add_argument('--probe')
    args = parser.parse_args()
    report_path = Path(args.report)
    report = json.loads(report_path.read_text('utf-8'))
    if report.get('status', 'complete') != 'complete':
        raise ValueError('Evaluation is incomplete')
    source = Path(report['model'])
    if hashlib.sha256(source.read_bytes()).hexdigest() != report['sha256']:
        raise ValueError('Evaluated weights have changed')
    audit = json.loads(Path(args.audit).read_text('utf-8'))
    if audit.get('sha256') != report['sha256']:
        raise ValueError('Application audit belongs to other weights')
    if any(audit['summary'][key]['passed'] != audit['summary'][key]['total'] for key in ('unsupported','regression','context')):
        raise ValueError('Application regression')
    _, payload = load_checkpoint(source)
    rows = report['trained']['results']
    if len(rows) != len(payload['conversation_pairs']) or not all(row['exact'] for row in rows):
        raise ValueError('Taught-example regression')
    for result, pair in zip(rows,payload['conversation_pairs']):
        if result['question'] != pair['question'] or result['expected'] != pair['answer'] or result['actual'].strip() != pair['answer'].strip():
            raise ValueError('Evaluation does not describe this corpus')
    baseline = json.loads(Path(args.baseline).read_text('utf-8'))
    sets = [('heldout',ROOT/'training/heldout.jsonl'),('dialogue_heldout',ROOT/'training/dialogue-heldout.jsonl')]
    if args.extra_heldout:
        sets.append(('extra_heldout',Path(args.extra_heldout)))
    if args.probe:
        sets.append(('probe_heldout',Path(args.probe)))
    for key,filename in sets:
        digest = hashlib.sha256(filename.read_bytes()).hexdigest()
        if digest != report[key]['data_sha256'] or digest != baseline[key]['data_sha256']:
            raise ValueError('Development set changed')
        if report[key]['correct'] < baseline[key]['correct']:
            raise ValueError('Development-set regression')
    target = ROOT/'models/terra-trained.pt'
    backup = Path(args.backup)
    if backup.resolve() in (target.resolve(),source.resolve()):
        raise ValueError('Backup must have its own path')
    if target.exists():
        current_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        if baseline['sha256'] != current_hash:
            raise ValueError('Baseline no longer describes the active model')
        _, current = load_checkpoint(target)
        new_pairs = {p['question']:p['answer'] for p in payload['conversation_pairs']}
        if any(new_pairs.get(p['question']) != p['answer'] for p in current['conversation_pairs']):
            raise ValueError('Candidate changed or removed an existing taught answer')
    if target.exists() and not backup.exists():
        shutil.copy2(target,backup)
        if target.with_suffix('.json').exists():
            shutil.copy2(target.with_suffix('.json'),backup.with_suffix('.json'))
    atomic_save(payload,target)
    summary = {k:v for k,v in payload.items() if k not in ('weights','optimizer','rng','conversation_pairs')}
    summary['supported_questions'] = [p['question'] for p in payload['conversation_pairs']]
    summary['evaluation'] = {key:{k:v for k,v in report[key].items() if k!='results'} for key in ['trained']+[name for name,_ in sets]}
    summary['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf-8')
    (ROOT/'docs/OGRETILEN-SORULAR.txt').write_text('\n'.join(summary['supported_questions']),'utf-8')
    print(json.dumps(summary['evaluation']))


if __name__ == '__main__':
    main()
