"""Small adapters; no SDK or API credentials are needed to start the UI."""
import json
import urllib.request
import urllib.error


def request_json(url, payload=None, key='', timeout=60):
    headers = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = 'Bearer ' + key
    req = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    # Do not forward credentials via redirects.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=timeout) as response:
            return json.loads(response.read(12_000_000))
    except urllib.error.HTTPError as e:
        labels = {401: 'API anahtarı geçersiz veya yetkisiz.', 403: 'Bu modele erişim izni yok.',
                  429: 'Sağlayıcı kotası veya hız sınırına ulaşıldı.', 404: 'Model veya API adresi bulunamadı.'}
        raise RuntimeError(labels.get(e.code, f'Model servisi HTTP {e.code} hatası verdi.')) from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('Model servisine ulaşılamadı. Bağlantıyı, adresi ve servisin açık olduğunu kontrol et.') from None


def turn(settings, key, messages, tools, system):
    if settings['provider'] == 'ollama':
        data = request_json(settings['ollama_url'].rstrip('/') + '/api/chat', {
            'model': settings['model'], 'stream': False,
            'messages': [{'role': 'system', 'content': system}] + messages,
            'tools': [{'type': 'function', 'function': t} for t in tools],
            'think': False, 'options': {'num_ctx': 16384, 'num_predict': 3500, 'temperature': 0.4, 'presence_penalty': 0.3}}, timeout=180)
        msg = data.get('message', {})
        calls = [{'id': str(i), 'name': c['function']['name'], 'args': c['function'].get('arguments', {})}
                 for i, c in enumerate(msg.get('tool_calls') or [])]
        return {'text': msg.get('content', ''), 'calls': calls, 'raw': msg, 'sources': [],
                'tokens': data.get('prompt_eval_count', 0) + data.get('eval_count', 0)}
    if not key:
        raise ValueError('Önce Ayarlar bölümüne API anahtarını ekle veya yerel model seç.')
    api_tools = [{'type': 'function', **t, 'strict': True} for t in tools]
    if settings.get('web_search'):
        api_tools.append({'type': 'web_search'})
    payload = {'model': settings['model'], 'instructions': system, 'input': messages,
               'tools': api_tools, 'store': False, 'include': ['reasoning.encrypted_content'], 'max_output_tokens': 4500}
    data = request_json('https://api.openai.com/v1/responses', payload, key)
    texts, calls, sources = [], [], []
    for item in data.get('output', []):
        if item.get('type') == 'function_call':
            try:
                args = json.loads(item.get('arguments', '{}'))
            except ValueError:
                args = {}
            calls.append({'id': item['call_id'], 'name': item['name'], 'args': args})
        if item.get('type') == 'message':
            for content in item.get('content', []):
                if content.get('type') == 'output_text':
                    texts.append(content['text'])
                    sources.extend({'title': a.get('title', a.get('url', '')), 'url': a.get('url', '')}
                                   for a in content.get('annotations', []) if a.get('type') == 'url_citation')
                elif content.get('type') == 'refusal':
                    texts.append(content.get('refusal', 'Bu isteği yerine getiremiyorum.'))
    return {'text': '\n'.join(texts), 'calls': calls, 'raw': data.get('output', []),
            'sources': sources, 'tokens': data.get('usage', {}).get('total_tokens', 0)}


def user_message(provider, text, image=None):
    if provider == 'ollama':
        msg = {'role': 'user', 'content': text}
        if image:
            msg['images'] = [image]
        return msg
    content = [{'type': 'input_text', 'text': text}]
    if image:
        content.append({'type': 'input_image', 'image_url': 'data:image/jpeg;base64,' + image})
    return {'role': 'user', 'content': content}


def append_result(provider, messages, call, result):
    if provider == 'ollama':
        messages.append({'role': 'tool', 'tool_name': call['name'], 'content': json.dumps(result, ensure_ascii=False)})
    else:
        messages.append({'type': 'function_call_output', 'call_id': call['id'], 'output': json.dumps(result, ensure_ascii=False)})
