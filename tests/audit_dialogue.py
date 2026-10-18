"""End-to-end app routing audit; scores are not raw-model generalisation."""
import json
from pathlib import Path
import torch
import argparse
import hashlib
from scratch.training import load_checkpoint
from scratch.dialogue import Dialogue

parser = argparse.ArgumentParser()
parser.add_argument('--model', default='models/terra-trained.pt')
parser.add_argument('--output', default='data/dialogue-audit.json')
args = parser.parse_args()
torch.set_num_threads(4)
model, info = load_checkpoint(args.model, 'cuda' if torch.cuda.is_available() else 'cpu')
session = Dialogue(model, info)
known = {p['question']:p['answer'] for p in info['conversation_pairs']}
positive = [
    ('bir değişkeni anlatır mısın', 'değişken nedir'),
    ('fonksiyonları açıklar mısın', 'fonksiyon nedir'),
    ('veriyi json olarak tutmak ne demek', 'json nedir'),
    ('değişkenler hakkında bilgi ver', 'değişken nedir'),
    ('lütfen algoritmayı anlat', 'algoritma nedir'),
    ('veritabanını açıkla', 'veritabanı nedir'),
    ('JSON hakkında kısa bilgi verir misin', 'json nedir'),
    ('python listelerini anlatır mısın', 'python listesi nedir'),
]
negative = ['kuantum bilgisayar nedir', 'fonksiyon silmek ne demek', 'değişken ve fonksiyon arasındaki fark nedir',
            'python kullanmak istemiyorum', '2 - 3 kaç eder', '6 + 2 kaç eder',
            'json dosyalarımı sil', 'css zararlı mı', 'fonksiyon değil değişken anlat',
            'python ile işletim sistemi yaz', 'virüs fonksiyon nedir', 'hesabımdaki para ne kadar',
            'minecraft ne demek', 'json şifremi açıkla', 'değişken fiyatı ne kadar']
results = []
for query, canonical in positive:
    result = session.reply(query)
    results.append({'query':query, 'kind':'paraphrase', 'correct':result['source']=='model' and result['text']==known[canonical], **result})
for query in negative:
    result = session.reply(query)
    results.append({'query':query, 'kind':'unsupported', 'correct':result['source']=='application', **result})
for query in ['merhaba','hello','nasılsın','değişken nedir','python merhaba dünya yaz']:
    result = session.reply(query)
    results.append({'query':query,'kind':'regression','correct':result['source']=='model' and result['text']==known[query],**result})
session.reply('değişken nedir')
result = session.reply('tekrar anlat')
target = info.get('followup_links', {}).get('değişken nedir', 'değişken nedir')
results.append({'query':'tekrar anlat','kind':'context','correct':result['text']==known[target] and 'context_note' in result,**result})
session.clear()
results.append({'query':'anlamadım after clear','kind':'context','correct':session.reply('anlamadım')['source']=='application'})
summary = {kind:{'passed':sum(r['correct'] for r in results if r['kind']==kind),'total':sum(r['kind']==kind for r in results)}
           for kind in ('paraphrase','unsupported','regression','context')}
Path(args.output).write_text(json.dumps({'sha256':hashlib.sha256(Path(args.model).read_bytes()).hexdigest(),'summary':summary,'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary))
for result in results:
    if not result['correct']:
        print(json.dumps(result,ensure_ascii=True))
assert all(r['correct'] for r in results if r['kind'] != 'paraphrase')
