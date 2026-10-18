"""Bounded, honestly labelled inference. Never substitutes canned model answers."""
import re
import unicodedata


def normalize(text):
    text = unicodedata.normalize('NFC', text).replace('İ', 'i').replace('I', 'ı').lower()
    # Keep operators: otherwise "2 - 3" could match a taught "2 + 3".
    return ' '.join(re.sub(r'[^\w\s+*/=<>.\-]', '', text).strip().rstrip('.!?').split())


def prompt_for(question):
    return f'Kullanıcı: {question}\nTerra: '


def respond(model, info, text, budget=1536, stop=None, emit=None, index=None):
    pairs = info.get('conversation_pairs', [])
    known = {normalize(p['question']): p for p in pairs}
    pair = known.get(normalize(text))
    match = None
    if not pair and index is not None:
        match = index.match(text)
        if match:
            pair = match['pair']
    if not pair:
        return {'source': 'application', 'reason': 'unknown_question', 'text': 'Bu soruya yanıt verecek şekilde henüz eğitilmedim. Şimdilik “merhaba”, “hello”, “nasılsın”, “sen kimsin” veya “eğitim nedir” gibi öğretilmiş örnekleri deneyebilirsin. Bu açıklama modelin ürettiği bir yanıt değil, uygulamanın kapsam bildirimidir.'}
    if budget < len(pair['answer'].encode('utf-8')) + 1:
        return {'source': 'application', 'text': 'Öğretilen yanıt bu uzunluk sınırına sığmıyor. Ayrıntılı veya Uzun seçeneğini kullan.'}
    answer = model.generate(prompt_for(pair['question']), max_bytes=budget, temperature=0, stop=stop, emit=emit)
    if stop is not None and stop.is_set():
        return {'source': 'application', 'text': 'Yanıt üretimi durduruldu.'}
    # Scope is deliberately restricted to taught examples. The model must reproduce
    # its answer itself; this is NOT evidence of generalisation or factual truth.
    if answer.strip() != pair['answer'].strip():
        return {'source': 'application', 'text': 'Model bu örneği henüz düzgün üretemedi. Bozuk çıktı yanıt olarak gösterilmedi; eğitim ve değerlendirme gerekiyor.'}
    result = {'source': 'model', 'text': answer}
    if match:
        result['matched_question'] = pair['question']
        result['match_score'] = match['score']
    return result
