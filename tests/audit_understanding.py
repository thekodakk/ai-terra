"""Real local model: user-confirmed clarification and follow-up scenarios."""
import argparse
import hashlib
import json
from pathlib import Path
from unittest.mock import patch
import torch
from scratch.training import load_checkpoint
from scratch.dialogue import Dialogue
from scratch.conversation import normalize

parser=argparse.ArgumentParser()
parser.add_argument('--model',default='models/terra-understanding-candidate.pt')
parser.add_argument('--output',default='data/understanding-interaction-audit.json')
args=parser.parse_args()
torch.set_num_threads(4)
rows=[]
with patch('socket.socket.connect',side_effect=AssertionError('Local inference must not connect')):
    model,info=load_checkpoint(args.model,'cuda' if torch.cuda.is_available() else 'cpu')
    session=Dialogue(model,info)
    known={normalize(p['question']):p['answer'] for p in info['conversation_pairs']}
    cases=[('python listelerini anlatır mısın','python listesi nedir'),
           ('kodum hata veriiyor','kodum hata veriyor'),
           ('ders çalışmayı planlıyom','ders çalışma planı yap'),
           ('arayuz hakinda bilgi','arayüz nedir'),
           ('parametre sayın kaac','parametre sayın kaç')]
    for query,canonical in cases:
        session.clear()
        first=session.reply(query)
        choices=first.get('suggestions',[])
        correct_choice=next((i for i,q in enumerate(choices) if known[normalize(q)]==known[canonical]),None)
        result=session.reply(str(correct_choice+1)) if correct_choice is not None else first
        passed=first['source']=='application' and result['source']=='model' and result['text']==known[canonical]
        rows.append({'query':query,'choices':choices,'selected':None if correct_choice is None else correct_choice+1,
                     'passed':passed,'actual':result['text']})
    session.clear()
    session.reply('değişken kavramını anlamak istiyorum')
    followup=session.reply('peki bunun örneği var mı')
    rows.append({'query':'new taught alias then follow-up','passed':followup['source']=='model' and followup['text']==known['değişken için daha sade açıklama']})
    session.reply('kodum hata veriiyor')
    session.reply('hiçbiri')
    rows.append({'query':'cancel pending options','passed':not session.pending and session.last_question is None})
report={'sha256':hashlib.sha256(Path(args.model).read_bytes()).hexdigest(),
        'passed':sum(r['passed'] for r in rows),'total':len(rows),'results':rows,
        'note':'Application interaction audit with simulated explicit user choices; not raw-model comprehension.'}
Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps({'passed':report['passed'],'total':report['total']}))
assert report['passed']==report['total']
