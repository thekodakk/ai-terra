"""Double-click launcher: reuse an existing Terra instance and start local model service if needed."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8844'


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=1) as response:
            return json.load(response)
    except Exception:
        return None


def main():
    if (get(URL + '/health') or {}).get('app') == 'ai-terra':
        webbrowser.open(URL)
        return
    try:
        config = json.loads((ROOT / 'data/settings.json').read_text('utf-8'))
    except (OSError, ValueError):
        config = {}
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    if config.get('provider') == 'ollama' and config.get('ollama_url', 'http://127.0.0.1:11434').rstrip('/') == 'http://127.0.0.1:11434' and get('http://127.0.0.1:11434/api/tags') is None:
        ollama = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs/Ollama/ollama.exe'
        if ollama.exists():
            subprocess.Popen([str(ollama), 'serve'], creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    (ROOT / 'data').mkdir(exist_ok=True)
    with (ROOT / 'data/server.log').open('a', encoding='utf-8') as log:
        process = subprocess.Popen([sys.executable, str(ROOT / 'app.py'), '--no-browser'], cwd=ROOT,
                                   creationflags=flags, stdout=log, stderr=log)
    for _ in range(50):
        if (get(URL + '/health') or {}).get('app') == 'ai-terra':
            webbrowser.open(URL)
            return
        if process.poll() is not None:
            break
        time.sleep(.2)
    from tkinter import messagebox
    messagebox.showerror('AI Terra', 'Uygulama başlatılamadı. 8844 portu başka bir uygulamada açık olabilir. Ayrıntılar: data/server.log')


if __name__ == '__main__':
    main()
