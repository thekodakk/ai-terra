"""Start the native app; no browser or external model service."""
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parent

def main():
    python = ROOT / '.venv/Scripts/pythonw.exe'
    if python.exists() and Path(sys.prefix).resolve() != (ROOT / '.venv').resolve():
        subprocess.Popen([str(python), str(Path(__file__).resolve())], cwd=ROOT,
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return
    try:
        from native.app import main as run
        run()
    except Exception:
        import traceback
        from tkinter import messagebox
        (ROOT / 'data').mkdir(exist_ok=True)
        (ROOT / 'data/native-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        messagebox.showerror('Terra', 'Uygulama acilamadi. Ayrintilar: data/native-error.log')
        raise

if __name__ == '__main__':
    main()
