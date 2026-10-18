"""Windows desktop adapter. Capture/input only happen after session permissions."""
import base64
import ctypes
import io
import os
from ctypes import wintypes


def windows():
    if os.name != 'nt':
        raise RuntimeError('Bilgisayar kontrolü Windows gerektirir.')
    return ctypes.windll.user32


def screenshot():
    from PIL import ImageGrab
    windows().GetForegroundWindow.restype = wintypes.HWND
    image = ImageGrab.grab(all_screens=False).convert('RGB')
    original = image.size
    image.thumbnail((1600, 1000))
    output = io.BytesIO()
    image.save(output, format='JPEG', quality=75)
    return {'image': base64.b64encode(output.getvalue()).decode(), '_window': int(windows().GetForegroundWindow()), 'width': original[0],
            'height': original[1], 'preview_width': image.width, 'preview_height': image.height}


def restore_target(handle):
    api = windows()
    api.GetForegroundWindow.restype = wintypes.HWND
    if not handle or not api.IsWindow(wintypes.HWND(handle)):
        raise ValueError('Hedef pencere kapandı; yeni ekran görüntüsü gerekiyor.')
    if api.GetForegroundWindow() != handle:
        api.ShowWindow(wintypes.HWND(handle), 9)
        api.SetForegroundWindow(wintypes.HWND(handle))
        if api.GetForegroundWindow() != handle:
            raise ValueError('Hedef pencereye geçilemedi. Hedef uygulamayı öne getirip tekrar dene.')


def same_scene(before, after):
    """Reject substantial screen changes between proposal and approved input."""
    from PIL import Image, ImageChops, ImageStat
    a = Image.open(io.BytesIO(base64.b64decode(before))).convert('RGB').resize((96, 60))
    b = Image.open(io.BytesIO(base64.b64decode(after))).convert('RGB').resize((96, 60))
    mean = sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3
    return mean < 12


class MouseInput(ctypes.Structure):
    _fields_ = [('dx', wintypes.LONG), ('dy', wintypes.LONG), ('mouseData', wintypes.DWORD),
                ('dwFlags', wintypes.DWORD), ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class KeyboardInput(ctypes.Structure):
    _fields_ = [('wVk', wintypes.WORD), ('wScan', wintypes.WORD), ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD), ('dwExtraInfo', ctypes.c_size_t)]


class InputUnion(ctypes.Union):
    _fields_ = [('mi', MouseInput), ('ki', KeyboardInput)]


class Input(ctypes.Structure):
    _anonymous_ = ('u',)
    _fields_ = [('type', wintypes.DWORD), ('u', InputUnion)]


def send(event):
    if windows().SendInput(1, ctypes.byref(event), ctypes.sizeof(Input)) != 1:
        raise RuntimeError('Windows girişi engelledi. Yönetici veya güvenlik ekranı olabilir.')


def key_event(code, flags=0, scan=0):
    send(Input(type=1, u=InputUnion(ki=KeyboardInput(code, scan, flags, 0, 0))))


KEYS = {'CTRL': 17, 'ALT': 18, 'SHIFT': 16, 'WIN': 91, 'ENTER': 13, 'TAB': 9,
        'ESC': 27, 'SPACE': 32, 'BACKSPACE': 8, 'DELETE': 46, 'UP': 38, 'DOWN': 40,
        'LEFT': 37, 'RIGHT': 39, 'HOME': 36, 'END': 35, 'PAGEUP': 33, 'PAGEDOWN': 34}
KEYS.update({f'F{i}': 111 + i for i in range(1, 13)})


def validate_action(args):
    action = args.get('action')
    if action not in ('click', 'double_click', 'right_click', 'move', 'scroll', 'type', 'key'):
        raise ValueError('Bilinmeyen masaüstü işlemi.')
    if action in ('click', 'double_click', 'right_click', 'move'):
        for key in ('x', 'y'):
            if not isinstance(args.get(key), (int, float)) or not 0 <= args[key] <= 1000:
                raise ValueError('Koordinatlar 0–1000 arasında olmalı.')
    if action == 'type' and len(args.get('text', '')) > 2000:
        raise ValueError('Tek seferde en fazla 2000 karakter yazılabilir.')
    if action == 'key':
        parts = args.get('text', '').upper().split('+')
        if not 1 <= len(parts) <= 4 or any(p not in KEYS and not (len(p) == 1 and p.isascii() and p.isalnum()) for p in parts):
            raise ValueError('Desteklenmeyen tuş birleşimi.')
    if action == 'scroll' and (not isinstance(args.get('amount'), int) or not -10 <= args['amount'] <= 10):
        raise ValueError('Kaydırma miktarı -10 ile 10 arasında olmalı.')


def action(args, stop):
    validate_action(args)
    if stop.is_set():
        raise InterruptedError('Durduruldu.')
    api = windows()
    kind = args['action']
    if kind in ('click', 'double_click', 'right_click', 'move'):
        x = round(args['x'] / 1000 * (api.GetSystemMetrics(0) - 1))
        y = round(args['y'] / 1000 * (api.GetSystemMetrics(1) - 1))
        if not api.SetCursorPos(x, y):
            raise RuntimeError('İmleç taşınamadı.')
        if kind != 'move':
            down, up = (8, 16) if kind == 'right_click' else (2, 4)
            for _ in range(2 if kind == 'double_click' else 1):
                if stop.is_set():
                    raise InterruptedError('Durduruldu.')
                send(Input(type=0, u=InputUnion(mi=MouseInput(0, 0, 0, down, 0, 0))))
                send(Input(type=0, u=InputUnion(mi=MouseInput(0, 0, 0, up, 0, 0))))
    elif kind == 'scroll':
        send(Input(type=0, u=InputUnion(mi=MouseInput(0, 0, args['amount'] * 120 & 0xffffffff, 0x800, 0, 0))))
    elif kind == 'type':
        encoded = args.get('text', '').encode('utf-16-le')
        for i in range(0, len(encoded), 2):
            if stop.is_set():
                raise InterruptedError('Durduruldu.')
            scan = int.from_bytes(encoded[i:i + 2], 'little')
            key_event(0, 4, scan)
            key_event(0, 6, scan)
    elif kind == 'key':
        codes = [KEYS[p] if p in KEYS else ord(p) for p in args['text'].upper().split('+')]
        held = []
        try:
            for code in codes:
                held.append(code)
                key_event(code)
        finally:
            for code in reversed(held):
                key_event(code, 2)
    return {'ok': True, 'action': kind, 'note': 'İşlem gönderildi; sonucunu yeni ekran görüntüsüyle doğrula.'}
