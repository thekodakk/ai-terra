import json
from pathlib import Path
from make_demo import PAIRS

rows = [{'question': q, 'answer': a} for q, a in PAIRS]
greeting = 'Merhaba! Ben Terra. Şu an temel konuşma örnekleriyle eğitiliyorum. İstersen kim olduğumu veya nasıl eğitildiğimi sorabilirsin.'
for question in ['merhaba', 'selam', 'hello', 'hi', 'hey', 'merhaba terra', 'selam terra']:
    rows.append({'question': question, 'answer': greeting})
for question in ['nasılsın', 'nasilsin', 'ne haber', 'naber']:
    rows.append({'question': question, 'answer': 'Buradayım, konuşmaya hazırım. Benim duygularım yok; yine de sana anlaşılır yanıtlar verecek şekilde geliştiriliyorum. Sen nasılsın?'})
for question in ['teşekkür ederim', 'sağ ol', 'saol', 'teşekkürler']:
    rows.append({'question': question, 'answer': 'Rica ederim. Yardımcı olabildiysem ne güzel.'})
for question in ['görüşürüz', 'hoşça kal', 'bye']:
    rows.append({'question': question, 'answer': 'Görüşürüz! Tekrar konuşmak istediğinde buradayım.'})
Path(__file__).with_name('conversation.jsonl').write_text('\n'.join(json.dumps(row, ensure_ascii=False) for row in rows)+'\n', encoding='utf-8')
