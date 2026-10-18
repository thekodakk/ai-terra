"""Integration checks on real weights; reports memorisation, not intelligence."""
import json
from pathlib import Path
import torch
from scratch.training import load_checkpoint
from scratch.conversation import respond, prompt_for

torch.set_num_threads(4)
model, info = load_checkpoint('models/terra-chat.pt', 'cuda' if torch.cuda.is_available() else 'cpu')
results = []
for pair in info['conversation_pairs']:
    actual = model.generate(prompt_for(pair['question']), 700, temperature=0)
    results.append({'question': pair['question'], 'exact': actual.strip() == pair['answer'].strip(), 'actual': actual})
    print(json.dumps(results[-1], ensure_ascii=True), flush=True)
for query in ['MERHABA!!!', 'hello', 'nasılsın?', 'bana işletim sistemi yaz', 'asdlkjqwe', '2+2 kaç', 'Ankara hakkında bir şiir yaz']:
    result = respond(model, info, query)
    results.append({'input': query, **result})
Path('data/chat-evaluation.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
failed = [r for r in results if r.get('exact') is False]
print('FAILED', len(failed), 'TRAINING EXAMPLES', len(info['conversation_pairs']))
raise SystemExit(bool(failed))
