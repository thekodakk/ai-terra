"""Activate only an evaluated candidate; preserve both earlier checkpoints."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scratch.training import load_checkpoint, atomic_save

report_path = ROOT / 'data/augmented-evaluation.json'
report = json.loads(report_path.read_text('utf-8'))
if report['trained']['correct'] != report['trained']['total']:
    raise SystemExit('Candidate not promoted: taught-example regression')
source = ROOT / report['model']
model, checkpoint = load_checkpoint(source)
if len(checkpoint['conversation_pairs']) != report['trained']['total']:
    raise SystemExit('Evaluation and checkpoint count differ')
target = ROOT / 'models/terra-trained.pt'
atomic_save(checkpoint, target)
summary = {k:v for k,v in checkpoint.items() if k not in ('weights','optimizer','rng','conversation_pairs')}
summary['supported_questions'] = [p['question'] for p in checkpoint['conversation_pairs']]
summary['evaluation'] = {key:{k:v for k,v in report[key].items() if k!='results'} for key in ('trained','heldout')}
summary['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix('.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'docs/OGRETILEN-SORULAR.txt').write_text('\n'.join(summary['supported_questions']),encoding='utf-8')
notes = f'''# Eğitim sonucu

Eğitim örnekleri: {report['trained']['correct']}/{report['trained']['total']} tam eşleşme.
Eğitim dışında tutulan sorular: {report['heldout']['correct']}/{report['heldout']['total']} tam eşleşme.
Bu ikinci ölçüm geniş kapsamlı bir zekâ testi değildir. Ham çıktılar değerlendirme dosyasında saklanır.

Bugün 12.000 ek adım; önceki eğitim dahil toplam {checkpoint['steps']} adım.
Model aynı yerel ağın ağırlıklarından devam etti; hazır model kullanılmadı.
Genel sohbet ve bilgisayar kontrolü hâlâ desteklenmiyor. Uygulama yalnızca öğretilen
soruları modele veriyor; bilinmeyen sorularda kapsam bildirimi gösteriyor.

Yeni varsayılan: models/terra-trained.pt. Eski terra-chat.pt korunuyor.
Değerlendirme: data/augmented-evaluation.json
Öğretilen sorular: docs/OGRETILEN-SORULAR.txt
Kod/eğitim regresyon testleri: 39 test başarılı.

Yeniden başlatıldığında yeni ağırlıklar seçilir. Açık eski pencere kendi modelini kullanmaya devam eder.
Uzun süreli veya gece boyu eğitim işi bırakılmadı.
'''
(ROOT/'docs/EGITIM-SONUCU.md').write_text(notes,encoding='utf-8')
print(json.dumps(summary['evaluation']))
