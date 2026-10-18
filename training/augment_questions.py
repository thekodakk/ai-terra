"""Deterministic paraphrase templates; the frozen held-out file is unchanged."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scratch.conversation import normalize

directory = Path(__file__).parent
rows = [json.loads(line) for line in (directory/'expanded.jsonl').read_text('utf-8').splitlines()]
heldout = {normalize(json.loads(line)['question']) for line in (directory/'heldout.jsonl').read_text('utf-8').splitlines()}
known = {normalize(row['question']): row for row in rows}
templates = ['{} hakkında bilgi ver', '{} konusunu açıkla', '{} ne anlama gelir', '{} hakkında kısa bilgi',
             '{} nasıl açıklanır', 'bana {} anlat', '{} açıklaması', 'lütfen {} açıkla',
             '{} nedir anlatır mısın', '{} nedir açıklar mısın', '{} ne demek açıklayabilir misin',
             '{} hakkında ne biliyorsun']
for row in rows:
    question = row['question'].rstrip('?.')
    if not question.endswith(' nedir'):
        continue
    concept = question[:-6]
    for template in templates:
        query = template.format(concept)
        key = normalize(query)
        if key in heldout:
            continue
        known.setdefault(key, {'question': query, 'answer': row['answer']})
(directory/'augmented.jsonl').write_text('\n'.join(json.dumps(row, ensure_ascii=False) for row in known.values())+'\n', encoding='utf-8')
print('Augmented examples:', len(known))
