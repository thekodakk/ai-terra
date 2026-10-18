"""Offline, real-weight dialogue checks, distinct from language evaluation."""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import torch
from scratch.dialogue import Dialogue
from scratch.conversation import normalize
from scratch.training import load_checkpoint

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='models/terra-trained.pt')
parser.add_argument('--output', default='data/topic-memory-audit.json')
args = parser.parse_args()
torch.set_num_threads(4)
rows = []
with patch('socket.socket.connect', side_effect=AssertionError('Inference must remain offline')):
    model, info = load_checkpoint(args.model, 'cuda' if torch.cuda.is_available() else 'cpu')
    session = Dialogue(model, info)
    known = {normalize(p['question']):p['answer'] for p in info['conversation_pairs']}
    def check(name, actual, expected):
        rows.append({'name':name, 'passed':actual == expected})
    session.reply('değişken nedir')
    for ack in ('teşekkürler','tamam','sağ ol'):
        response = session.reply(ack)
        check(ack+' generated', response['source'], 'model')
        check(ack+' retains topic', session.last_question, 'değişken nedir')
    response = session.reply('örnek ver')
    check('example after acknowledgements', response['text'], known['değişken için daha sade açıklama'])
    session.reply('fonksiyon nedir')
    response = session.reply('önceki konuya dön')
    check('return generates old topic', response['text'], known['değişken nedir'])
    session.reply('yanlış anladın')
    check('correction clears rejected topic', session.last_question, None)
    check('no stale followup', session.reply('örnek ver')['source'], 'application')
    session.reply('liste nedir')
    session.reply('başka konuya geçelim')
    check('explicit reset clears history', session.topic_history, [])
    check('explicit reset clears topic', session.last_question, None)
report = {'sha256':hashlib.sha256(Path(args.model).read_bytes()).hexdigest(),
          'passed':sum(r['passed'] for r in rows), 'total':len(rows), 'results':rows,
          'note':'Application memory with actual neural responses; no general-intelligence claim.'}
Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')
print(json.dumps({k:report[k] for k in ('passed','total')}))
assert report['passed'] == report['total']
