"""Exercise every taught alternative using the actual active weights, offline."""
import hashlib
import argparse
import json
from pathlib import Path
from unittest.mock import patch
import torch
from scratch.training import load_checkpoint
from scratch.dialogue import Dialogue

torch.set_num_threads(4)
parser = argparse.ArgumentParser()
parser.add_argument('--model', default='models/terra-trained.pt')
parser.add_argument('--output', default='data/followup-audit.json')
args = parser.parse_args()
path = Path(args.model)
with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden in local inference')):
    model, info = load_checkpoint(path, 'cuda' if torch.cuda.is_available() else 'cpu')
    session = Dialogue(model,info)
    known = {p['question']:p['answer'] for p in info['conversation_pairs']}
    rows = []
    for topic in ['değişken','fonksiyon','döngü','liste','json','css','html','git','api','python']:
        first = session.reply(topic+' nedir')
        second = session.reply('örnek ver')
        target = topic+' için daha sade açıklama'
        okay = (first['source']=='model' and second['source']=='model'
                and second['text']==known[target] and 'context_note' in second)
        rows.append({'topic':topic,'correct':okay,'actual':second['text']})
report = {'model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'passed':sum(r['correct'] for r in rows),'total':len(rows),'results':rows}
Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'passed':report['passed'],'total':report['total']}))
assert report['passed']==report['total']
