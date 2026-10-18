"""Final same-author unseen-phrase check; not a broad language benchmark."""
import hashlib
import argparse
import json
from pathlib import Path
import torch
from scratch.batch_evaluate import evaluate
from scratch.conversation import normalize
from scratch.training import load_checkpoint

parser = argparse.ArgumentParser()
parser.add_argument('--candidate', required=True)
args = parser.parse_args()
torch.set_num_threads(4)
path = Path('training/natural-probes.jsonl')
raw = path.read_bytes()
pairs = [json.loads(s) for s in raw.decode('utf-8').splitlines() if s.strip()]
report = {'data_sha256':hashlib.sha256(raw).hexdigest(), 'models':[],
          'note':'Fresh phrases at time of first evaluation; authored by the same developer. Exact greedy text, no routing.'}
for model_path in (Path('models/terra-trained.pt'), Path(args.candidate)):
    name = model_path.stem
    model, info = load_checkpoint(model_path, 'cuda' if torch.cuda.is_available() else 'cpu')
    trained = {normalize(p['question']) for p in info['conversation_pairs']}
    assert not trained.intersection(normalize(p['question']) for p in pairs)
    result = evaluate(model,pairs)
    result.update(model=name, sha256=hashlib.sha256(model_path.read_bytes()).hexdigest())
    report['models'].append(result)
    print(name,result['correct'],result['total'],flush=True)
    del model
Path('data/natural-final-probes.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
