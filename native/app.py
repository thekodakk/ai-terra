import json
import os
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

ROOT = Path(__file__).resolve().parents[1]
BG, INK, MUTED, GREEN = '#f4f4ee', '#23392f', '#68766e', '#315c48'


class TerraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Terra — Kendi modelin · 0.7')
        self.geometry('1100x790')
        self.minsize(900, 680)
        self.configure(bg=BG)
        self.option_add('*Font', ('Segoe UI', 11))
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=INK)
        style.configure('TButton', padding=(14, 9), background='#e4e9df', foreground=INK)
        style.configure('Accent.TButton', background=GREEN, foreground='white')
        style.map('Accent.TButton', background=[('active', '#416d55')])
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', padding=(20, 12), background='#e4e9df')
        style.map('TNotebook.Tab', background=[('selected', 'white')])
        self.events, self.stop = queue.Queue(), threading.Event()
        self.worker, self.closing = None, False
        self.dialogue, self.model_cache_key = None, None
        self.model_path = ROOT / 'models/terra-trained.pt'
        self.corpus_paths, self.history, self.controls = [], [], []
        self.length = tk.StringVar(value='Ayrıntılı')
        self.status = tk.StringVar(value='Yerel • API bağlantısı yok')
        self.model_info = tk.StringVar()
        self.files_info = tk.StringVar(value='Henüz eğitim dosyası seçilmedi.')
        self.steps = tk.StringVar(value='200')
        self.training_mode = tk.StringVar(value='Soru-cevap')
        header = ttk.Frame(self)
        header.pack(fill='x', padx=32, pady=(24, 20))
        ttk.Label(header, text='terra', font=('Segoe UI', 30, 'bold')).pack(side='left')
        ttk.Label(header, text='  /  kendi modelin, kendi bilgisayarın', foreground=MUTED).pack(side='left', pady=(12, 0))
        self.book = ttk.Notebook(self)
        self.book.pack(fill='both', expand=True, padx=30)
        chat, training, card = [self.tab(title) for title in ('Sohbet', 'Eğitim atölyesi', 'Model kartı')]
        card = self.scroll_panel(card)
        self.label(chat, 'Konuşmaya başlayalım.', 23)
        self.label(chat, 'Yerel model • Benzer sorular ve öğretilmiş örnekli açıklamalar. Genel amaçlı asistan değil.', color=MUTED)
        self.transcript = self.textbox(chat, 11)
        self.transcript.tag_configure('system', foreground=MUTED)
        self.transcript.tag_configure('user', foreground=GREEN)
        self.append('Uygulama', '“Değişken nedir?” → “teşekkürler” → “bunun örneğini ver” deneyebilirsin. Yeni konuya geçtikten sonra “önceki konuya dön” yazabilirsin. Sorunu kesin eşleştiremezsem yakın soruları sunarım: numarasını yazabilir veya “hiçbiri” diyebilirsin. Konu hafızasını uygulama tutar; yanıtı yerel model üretir.', 'system')
        row = self.row(chat)
        budget_row = row
        ttk.Label(row, text='Yanıt bütçesi').pack(side='left')
        ttk.Combobox(row, textvariable=self.length, values=['Kısa', 'Ayrıntılı', 'Uzun'], state='readonly', width=13).pack(side='left', padx=10)
        self.button(row, 'Örnek sorular', self.show_examples)
        ttk.Label(row, text='Ctrl + Enter ile gönder', foreground=MUTED).pack(side='right')
        self.input = tk.Text(chat, height=3, wrap='word', bg='white', fg=INK, relief='flat', padx=12, pady=10)
        self.input.pack(fill='x')
        self.input.bind('<Control-Return>', lambda event: self.send())
        row = self.row(chat)
        self.button(row, 'Sohbeti temizle', self.clear_chat)
        self.button(row, 'Yanıt üret  →', self.send, True, 'right')
        # Allocate input controls before the expandable transcript. Otherwise Tk
        # clips buttons when the window is small or Windows text scaling is high.
        row.pack_configure(side='bottom', before=self.transcript.frame)
        self.input.pack_configure(side='bottom', before=self.transcript.frame)
        budget_row.pack_configure(side='bottom', before=self.transcript.frame)
        self.label(training, 'Modelin burada öğrenir.', 23)
        self.label(training, 'TXT veya JSONL dosyalarını sen seçersin. Dosyalar bilgisayarında kalır. Yeni model rastgele ağırlıklarla başlar; hazır model indirilmez.', color=MUTED)
        row = self.row(training)
        self.button(row, 'Metin dosyalarını seç', self.choose_corpus)
        self.button(row, 'Deneme verisini kullan', self.use_demo)
        self.button(row, 'Sohbet verisini kullan', self.use_chat_data)
        ttk.Label(training, textvariable=self.files_info, wraplength=820).pack(fill='x', pady=10)
        row = self.row(training)
        ttk.Label(row, text='Eğitim türü').pack(side='left')
        ttk.Combobox(row, textvariable=self.training_mode, values=['Soru-cevap', 'Genel metin'], state='readonly', width=16).pack(side='left', padx=12)
        ttk.Label(row, text='Soru-cevap: yalnızca yanıtı tahmin ederek öğrenir.', foreground=MUTED).pack(side='left')
        row = self.row(training)
        ttk.Label(row, text='Adım sayısı').pack(side='left')
        ttk.Spinbox(row, from_=1, to=100000, textvariable=self.steps, width=8).pack(side='left', padx=12)
        self.button(row, 'Yeni model eğit', lambda: self.start_training(False), True)
        self.button(row, 'Eğitime devam et', lambda: self.start_training(True))
        self.progress = ttk.Progressbar(training, mode='determinate')
        self.progress.pack(fill='x', pady=8)
        self.training_log = self.textbox(training, 10)
        training_note = self.label(training, 'Kaybın düşmesi zekâ testi değildir. Soru-cevap eğitimi ayrı bir aday kaydeder; otomatik etkinleştirmez. Genel metin modunda ayrılmış metnin doğrulama kaybı ölçülür.', color=MUTED)
        training_note.pack_configure(side='bottom', before=self.training_log.frame)
        self.label(card, 'Açıkça ne var, ne yok?', 23)
        ttk.Label(card, textvariable=self.model_info, wraplength=840, justify='left').pack(fill='x', pady=(0, 20))
        row = self.row(card)
        self.button(row, 'Kendi model dosyamı seç', self.choose_model)
        self.button(row, 'Proje klasörünü aç', lambda: os.startfile(ROOT))
        for title, body in [
            ('Yerel çalışma', 'Sohbet ve eğitim ağ bağlantısı kullanmaz. Kendi Transformer kodumuz, rastgele başlatılan ağırlıklar ve UTF-8 bayt sözlüğü kullanılır. Python ve PyTorch yazılım bağımlılıklarıdır; model hizmeti değildir.'),
            ('Henüz öğrenmediği beceriler', 'Görüntü anlama, ses tanıma, güvenilir kod üretimi ve otonom bilgisayar kontrolü bu modelde yok. Metin çıktısı komut olarak çalıştırılmaz. Önceki web prototipi ayrı tutuldu; otomatik geçiş yapılmaz.'),
            ('Daha uzun yanıtlar', 'Varsayılan Ayrıntılı: en fazla 1536 UTF-8 bayt. Uzun: 3072 bayt. Model bitiş işareti üretirse daha erken durur. Kısa bağlamlı deneme modeli uzun yanıtta tutarlılık garantisi vermez.')]:
            self.label(card, title, 16)
            self.label(card, body, color=MUTED)
        row = self.row(self)
        row.pack_configure(side='bottom', before=self.book)
        ttk.Label(row, textvariable=self.status).pack(side='left', padx=32)
        ttk.Button(row, text='Durdur  ·  Esc', command=self.cancel).pack(side='right', padx=32)
        self.bind('<Escape>', lambda event: self.cancel())
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.restore_preferences()
        self.refresh_model()
        self.after(100, self.poll)

    def scroll_panel(self, parent):
        canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        content = ttk.Frame(canvas)
        item = canvas.create_window(0, 0, window=content, anchor='nw')
        content.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(item, width=event.width))
        return content

    def tab(self, title):
        frame = ttk.Frame(self.book, padding=24)
        self.book.add(frame, text=title)
        return frame

    def row(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=10)
        return frame

    def label(self, parent, text, size=11, color=INK):
        widget = ttk.Label(parent, text=text, font=('Segoe UI', size), foreground=color, wraplength=810, justify='left')
        widget.pack(fill='x', pady=(0, 12))
        parent.bind('<Configure>', lambda event: widget.configure(wraplength=max(200,event.width-48)), add='+')
        return widget

    def button(self, parent, text, command, accent=False, side='left'):
        widget = ttk.Button(parent, text=text, command=command, style='Accent.TButton' if accent else 'TButton')
        widget.pack(side=side, padx=(0, 10))
        self.controls.append(widget)

    def textbox(self, parent, height):
        widget = ScrolledText(parent, wrap='word', bg='white', fg=INK, relief='flat', padx=16, pady=16, height=height, state='disabled')
        widget.pack(fill='both', expand=True, pady=(0, 8))
        return widget

    def append(self, title, text, tag='model'):
        self.transcript.configure(state='normal')
        self.transcript.insert('end', title + '\n' + text + '\n\n', tag)
        self.transcript.configure(state='disabled')
        self.transcript.see('end')

    def log(self, text):
        self.training_log.configure(state='normal')
        self.training_log.insert('end', text + '\n')
        self.training_log.configure(state='disabled')
        self.training_log.see('end')

    def refresh_model(self):
        try:
            info = json.loads(self.model_path.with_suffix('.json').read_text('utf-8'))
            architecture = info.get('config', {})
            details = f"\nMimari: {architecture.get('layers', '?')} katman · genişlik {architecture.get('width', '?')}"
            if info.get('growth'):
                details += f"\nBüyütülen sürümün ek eğitimi: {info['growth']['new_layer_steps']:,} adım; önceki kendi modelinin ağırlıkları taşındı."
            self.model_info.set(f"Dosya: {self.model_path}\nBaşlangıç: kendi rastgele ağırlıklarımız\nEğitim geçmişi: {info['steps']} adım · {info['parameters']:,} parametre{details}\nDurum: deneysel, yalnızca metin. Özet dosyadan okunur; yüklenirken ağırlık biçimi ayrıca doğrulanır.")
        except (OSError, ValueError, KeyError):
            self.model_info.set(f'Dosya: {self.model_path}\nHenüz eğitim özeti yok. Eğitim atölyesinden yeni model oluşturabilirsin.')

    def show_examples(self):
        if self.busy():
            return
        try:
            from scratch.conversation import normalize
            info = json.loads(self.model_path.with_suffix('.json').read_text('utf-8'))
            supported = {normalize(q):q for q in info.get('supported_questions', [])}
        except (OSError, ValueError, TypeError):
            supported = {}
        if getattr(self, 'examples_menu', None) is not None:
            self.examples_menu.destroy()
        menu = self.examples_menu = tk.Menu(self, tearoff=False)
        for question in ['projemi nasıl böleyim', 'hata mesajını nasıl okuyayım', 'ders çalışma planı yap',
                         'sözdizimi hatası nedir', 'değişken nedir', 'fonksiyon nedir', 'nasılsın']:
            if question in supported:
                def choose(text=supported[question]):
                    self.input.delete('1.0', 'end')
                    self.input.insert('1.0', text)
                    self.input.focus_set()
                menu.add_command(label=supported[question], command=choose)
        if menu.index('end') is not None:
            try:
                menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
            finally:
                menu.grab_release()
        else:
            menu.destroy()
            self.examples_menu = None
            messagebox.showinfo('Örnek sorular', 'Bu modelin özetinde önerilen sorular bulunamadı.')

    def restore_preferences(self):
        try:
            settings = json.loads((ROOT / 'data/native-settings.json').read_text('utf-8'))
            if settings.get('length') in ('Kısa', 'Ayrıntılı', 'Uzun'):
                self.length.set(settings['length'])
            path = settings.get('model')
            if isinstance(path, str) and Path(path).suffix == '.pt':
                self.model_path = Path(path)
                if self.model_path.resolve() == (ROOT / 'models/terra-own.pt').resolve() and (ROOT / 'models/terra-chat.pt').exists():
                    self.model_path = ROOT / 'models/terra-chat.pt'
                if self.model_path.resolve() == (ROOT / 'models/terra-chat.pt').resolve() and (ROOT / 'models/terra-trained.pt').exists():
                    self.model_path = ROOT / 'models/terra-trained.pt'
        except (OSError, ValueError, TypeError):
            pass

    def save_preferences(self):
        try:
            path = ROOT / 'data/native-settings.json'
            path.parent.mkdir(exist_ok=True)
            temp = path.with_suffix('.json.tmp')
            temp.write_text(json.dumps({'model': str(self.model_path), 'length': self.length.get()}, ensure_ascii=False), encoding='utf-8')
            os.replace(temp, path)
        except OSError as exc:
            self.status.set(f'Ayar kaydedilemedi: {exc}')

    def choose_corpus(self):
        paths = filedialog.askopenfilenames(title='Kullanma hakkına sahip olduğun metinleri seç', filetypes=[('Metin verisi', '*.txt *.jsonl')])
        if paths:
            self.corpus_paths = list(paths)
            self.files_info.set(f'{len(paths)} dosya: ' + ', '.join(Path(p).name for p in paths))

    def use_demo(self):
        self.corpus_paths = [str(ROOT / 'training/demo.jsonl')]
        self.files_info.set('demo.jsonl — yapay test verisi; genel zekâ eğitimi değil.')

    def use_chat_data(self):
        self.corpus_paths = [str(ROOT / 'training/understanding-training.jsonl')]
        self.training_mode.set('Soru-cevap')
        self.files_info.set('understanding-training.jsonl — yerel, yazılmış soru-cevap örnekleri.')

    def choose_model(self):
        path = filedialog.askopenfilename(title='Kendi eğittiğin Terra modeli', initialdir=ROOT / 'models', filetypes=[('Terra ağırlıkları', '*.pt')])
        if path:
            self.model_path = Path(path)
            self.refresh_model()

    def busy(self):
        return self.worker is not None and self.worker.is_alive()

    def start_worker(self, target, status):
        if self.busy():
            return
        self.stop.clear()
        self.status.set(status)
        for control in self.controls:
            control.state(['disabled'])
        def work():
            try:
                target()
            except Exception as exc:
                self.events.put(('error', f'{type(exc).__name__}: {exc}'))
            finally:
                self.events.put(('idle', None))
        self.worker = threading.Thread(target=work, daemon=False)
        self.worker.start()

    def start_training(self, resume):
        if self.busy():
            return
        if not self.corpus_paths:
            messagebox.showinfo('Eğitim verisi', 'Önce metin dosyalarını seç veya deneme verisini kullan.')
            return
        try:
            steps = int(self.steps.get())
            if not 1 <= steps <= 100000:
                raise ValueError()
        except ValueError:
            messagebox.showerror('Adım sayısı', '1 ile 100000 arasında tam sayı gir.')
            return
        target = self.model_path
        source = self.model_path
        qa = self.training_mode.get() == 'Soru-cevap'
        if resume and not target.exists():
            messagebox.showinfo('Model yok', 'Önce yeni model eğit.')
            return
        if not resume or qa:
            chosen = filedialog.asksaveasfilename(title='Aday modeli kaydet' if qa else 'Yeni modeli kaydet', initialdir=ROOT / 'models', initialfile='terra-user-candidate.pt' if qa else 'terra-own.pt', defaultextension='.pt', filetypes=[('Terra ağırlıkları', '*.pt')])
            if not chosen:
                return
            target = Path(chosen)
            if qa and target.resolve() == source.resolve():
                messagebox.showinfo('Kaynak modeli koru', 'Sohbet eğitimi için başka bir dosya adı seç. Şu an kullandığın model korunacak.')
                return
        paths = list(self.corpus_paths)
        self.progress['value'] = 0
        def work():
            emit = lambda event: self.events.put(('train', event))
            if qa:
                from scratch.qa_training import train_qa
                train_qa(paths, target, steps, self.stop, emit, resume_from=source if resume else None)
            else:
                from scratch.training import train
                train(paths, target, steps, self.stop, emit, resume)
        self.start_worker(work, 'Eğitim sürüyor • durdurunca son adım kaydedilir')

    def send(self):
        if self.busy():
            return 'break'
        text = self.input.get('1.0', 'end').strip()
        if not text:
            return 'break'
        if len(text) > 8000:
            messagebox.showinfo('Mesaj çok uzun', 'Mesajı 8000 karakter altında tut.')
            return 'break'
        if not self.model_path.exists():
            self.append('Uygulama', 'Henüz model eğitilmedi. Eğitim atölyesinden başlayabilirsin.', 'system')
            return 'break'
        path = self.model_path
        budget = {'Kısa': 384, 'Ayrıntılı': 1536, 'Uzun': 3072}[self.length.get()]
        self.append('Sen', text, 'user')
        self.input.delete('1.0', 'end')
        def work():
            import torch
            from scratch.training import load_checkpoint
            from scratch.dialogue import Dialogue
            torch.set_num_threads(4)
            stat = path.stat()
            cache_key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
            if self.dialogue is None or self.model_cache_key != cache_key:
                model, info = load_checkpoint(path, 'cuda' if torch.cuda.is_available() else 'cpu')
                if int(info.get('steps', 0)) <= 0:
                    raise ValueError('Model henüz eğitim adımı tamamlamadı.')
                self.dialogue = Dialogue(model, info)
                self.model_cache_key = cache_key
            result = self.dialogue.reply(text, budget, stop=self.stop, emit=lambda value: self.events.put(('generating', len(value))))
            self.events.put(('answer', (text, result, self.stop.is_set())))
        self.start_worker(work, 'Kendi modelin yükleniyor…')
        return 'break'

    def clear_chat(self):
        if self.busy():
            return
        self.history.clear()
        if self.dialogue is not None:
            self.dialogue.clear()
        self.transcript.configure(state='normal')
        self.transcript.delete('1.0', 'end')
        self.transcript.configure(state='disabled')

    def cancel(self):
        if self.busy():
            self.stop.set()
            self.status.set('Durduruluyor… Eğitim son adımı kaydedecek.')

    def poll(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == 'error':
                    self.log(data)
                    self.append('Uygulama — işlem tamamlanamadı', data, 'system')
                    self.status.set('İşlem hatası • ayrıntılar ekranda')
                elif kind == 'generating':
                    self.status.set(f'Metin üretiliyor • {data} karakter • Esc ile durdur')
                elif kind == 'answer':
                    question, result, cancelled = data
                    answer, source = result['text'], result['source']
                    if result.get('matched_question'):
                        self.append('Uygulama · benzer soru eşleştirmesi', 'Şu öğretilmiş soruyla eşleştirildi: ' + result['matched_question'], 'system')
                    if result.get('context_note'):
                        self.append('Uygulama · sohbet takibi', result['context_note'], 'system')
                    title = 'Kendi modelin · öğretilmiş örnek' if source == 'model' else 'Uygulama · kapsam bildirimi'
                    self.append(title + (' · durduruldu' if cancelled else ''), answer or '(Model metin üretmeden durdu.)', 'model' if source == 'model' else 'system')
                    if answer and not cancelled:
                        self.history = (self.history + [f'Kullanıcı: {question}\nTerra: {answer}\n'])[-4:]
                elif kind == 'train':
                    if data['kind'] == 'started':
                        self.log(f"Aygıt: {data['device']} | Parametre: {data['parameters']:,}")
                        self.train_start = data['start']
                    elif data['kind'] == 'progress':
                        self.progress['value'] = 100 * (data['step'] - self.train_start) / (data['target'] - self.train_start)
                        validation = f"{data['validation']:.4f}" if data['validation'] is not None else 'ölçülmedi (soru-cevap)'
                        self.log(f"Adım {data['step']}/{data['target']} | Eğitim {data['loss']:.4f} | Doğrulama {validation} | {data['seconds']} sn")
                    else:
                        if data.get('saved') is False:
                            self.log('İlk adımdan önce durduruldu; yeni model kaydedilmedi.')
                            continue
                        self.log(f"{'Durduruldu, kaydedildi' if data['stopped'] else 'Tamamlandı'}: {data['steps']} adım\n{data['path']}")
                        if data.get('candidate'):
                            self.log('Aday kaydedildi. Mevcut model etkin kaldı. Denemek için Model kartından aday dosyasını seçebilirsin.')
                        else:
                            self.model_path = Path(data['path'])
                            self.refresh_model()
                elif kind == 'idle':
                    for control in self.controls:
                        control.state(['!disabled'])
                    if not self.status.get().startswith('İşlem hatası'):
                        self.status.set('Hazır • yerel çalışma • API bağlantısı yok')
        except queue.Empty:
            pass
        if self.closing and not self.busy():
            self.save_preferences()
            self.destroy()
            return
        self.after(100, self.poll)

    def on_close(self):
        if self.busy():
            self.closing = True
            self.cancel()
        else:
            self.save_preferences()
            self.destroy()


def main():
    TerraApp().mainloop()


if __name__ == '__main__':
    main()
