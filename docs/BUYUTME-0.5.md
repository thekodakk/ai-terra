# Terra 0.5 — model büyütme sonucu

3.271.168 parametreli, 16 katmanlı bir büyük model oluşturuldu ve eğitildi.
Eski modelin 4 katmanı, gömmeleri ve çıktı ağırlıkları taşındı. Eklenen 12
katman başlangıçta özdeşlik dönüşümü yapar. Gerçek dosyalarda beş girdinin
başlangıç logitleri birebir eşitti; maksimum fark 0.0. Hazır model kullanılmadı.

Eğitim kümesi 2.336'dan 2.801 soru biçimine çıktı; 132 farklı yanıt içerir.
30 yeni geliştirme sorusu eğitimden ayrı tutuldu. Eski iki geliştirme kümesi
korundu. Var olan öğretilmiş soruların yanıtları değiştirilmedi.

## Karar

Varsayılan, yeni verilerle eğitilen **891.904 parametreli küçük modeldir**.
Büyük model deney olarak saklandı; büyüklük tek başına daha iyi sonuç vermedi.

- Önceki aktif küçük model: eski kümelerde 4/10 ve 18/20; yeni kümede 3/30.
- Büyük model, 6.000 ek adım: 5/10, 17/20, 4/30; öğretilmişlerde 2801/2801.
- Büyük model, 3.000 ek düzeltme adımı daha: 4/10, 17/20, 5/30; öğretilmişlerde 2800/2801.
- Aynı yeni veriler ve ilk aşamayla aynı ayarlarla eğitilen küçük kontrol modeli:
  5/10, 18/20, 5/30; öğretilmişlerde 2801/2801. Bu sürüm etkinleştirildi.

Bunlar küçük, tam metin eşleşmeli geliştirme ölçümleridir. Aday seçiminde
kullanıldıkları için bağımsız son test veya genel zekâ ölçümü değildir.
Yeni ifadeleri anlamada sonuç hâlâ zayıf; daha fazla parametre bunu çözmedi.
Sohbet kapsamı uygulama tarafından sınırlanmaya devam eder.

## Dosyalar

- Aktif: `models/terra-trained.pt` — 891.904 parametre, 35.600 geçmiş eğitim adımı.
- Önceki aktif sürüm yedeği: `models/terra-before-0.5.pt`.
- Büyük deneme: `models/terra-growth-candidate.pt` — 3.271.168 parametre, yeni katmanlarda 6.000 eğitim adımı.
- Sonraki büyük deneme: `models/terra-growth-refined.pt` — yeni katmanlarda toplam 9.000 adım; etkinleştirilmedi.
- Küçük kontrol: `models/terra-small-control.pt`.
- Veri: `training/growth-training.jsonl`; ayrı sorular: `training/growth-heldout.jsonl`.
- Ölçümler: `data/growth-baseline.json`, `data/growth-candidate-evaluation.json`,
  `data/growth-refined-evaluation.json`, `data/growth-small-control-evaluation.json`.

Büyüğü denemek için Model kartı → Kendi model dosyamı seç →
`terra-growth-candidate.pt`. Tekrar dönmek için `terra-trained.pt` seç.
Seçim uygulama kapanırken kişisel ayarlara kaydedilir.

## Doğrulama ve arayüz

58 birim/regresyon testi geçti. Aktif modelde 10/10 örnekli takip açıklaması
başarılı. Uygulama kontrolünde 7/8 benzer ifade, 15/15 desteklenmeyen istekte
kapsam bildirimi, 5/5 temel yanıt ve 2/2 konu takibi başarılı.

Öğretilmiş örnekler için hızlandırılmış değerlendirme, her yanıt baytının ve
bitiş tokenının kendi ön ekinde açgözlü seçim olduğunu nedensel ileri geçişte
kontrol eder. Yakın eşitlikler ve başarısızlıklar normal üretilir. Bu yöntem
sohbet yanıtı vermek için kullanılmaz. Büyük modelde 2.801 örneğin tamamında
normal otoregresif değerlendirmeyle aynı sonuç verdi: `data/fast-evaluation-audit.json`.

Arayüzde Örnek sorular menüsü, mimari bilgisi ve kaydırılabilir Model kartı
eklendi. Açılış ve model kartı görsel olarak kontrol edildi. Menüye tıklama
sırasında kullanıcı girdisi algılandığı için o kontrol sürdürülemedi. Son
kaydırma değişikliği pencere kurulum testiyle doğrulandı; yeniden açınca görünür.

Eğitim işi arka planda bırakılmadı. Genel sohbet, ekran görme, ses ve bilgisayar
kontrolü bu büyütmeyle kazanılmış değildir.
