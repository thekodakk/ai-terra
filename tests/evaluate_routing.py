"""Development-set routing audit. Not a neural generalisation score."""
import json
from pathlib import Path
from scratch.routing import QuestionIndex

pairs = [json.loads(line) for line in Path('training/augmented.jsonl').read_text('utf-8').splitlines()]
index = QuestionIndex(pairs)
probes = [json.loads(line) for line in Path('training/heldout.jsonl').read_text('utf-8').splitlines()]
for probe in probes:
    match = index.match(probe['question'])
    print(json.dumps({'query':probe['question'], 'matched':match['pair']['question'] if match else None,
                      'correct': bool(match and match['pair']['answer']==probe['answer']), 'score':match['score'] if match else None}, ensure_ascii=True))
