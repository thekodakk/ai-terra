"""Manual integration check: a synthetic image only, never the user's desktop."""
import base64
import io
import json
from PIL import Image, ImageDraw
from terra.providers import turn, user_message

image = Image.new('RGB', (600, 300), '#ffffff')
draw = ImageDraw.Draw(image)
draw.rectangle((30, 40, 260, 180), fill='#dd3030')
draw.rectangle((330, 40, 560, 180), fill='#3060dd')
draw.text((50, 220), 'TEST CODE: 4281', fill='#000000', font_size=35)
buffer = io.BytesIO()
image.save(buffer, 'JPEG')
encoded = base64.b64encode(buffer.getvalue()).decode()
settings = {'provider': 'ollama', 'model': 'qwen3.5:4b', 'ollama_url': 'http://127.0.0.1:11434'}
result = turn(settings, '', [user_message('ollama', 'Resimdeki TEST CODE nedir? Soldaki dikdörtgen hangi renk? Yalnızca kodu ve rengi yaz.', encoded)], [], 'Görüntüde gördüğün bilgiyi kısa Türkçe cevapla.')
print(json.dumps({'answer': result['text'], 'tokens': result['tokens'], 'code_found': '4281' in result['text']}, ensure_ascii=False))
