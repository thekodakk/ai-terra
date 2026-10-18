# Terra 0.4 — sohbet ve eğitim

## Neler değişti?

Kendi yerel Transformer modelinin ağırlıkları 16.000 ek adım eğitildi.
Varsayılan model toplam 29.600 adım ve 891.904 parametre içerir.
Hazır model, harici model servisi veya indirilen eğitim metni kullanılmadı.
Eğitim metinleri proje için yazılmış sınırlı Türkçe soru-cevap örnekleridir.

Soru biçimleri 881'den 2.336'ya çıktı. Türkçe karakter kullanmadan yazılan
ifadeler ve farklı soru kalıpları eklendi. Değişken, fonksiyon, döngü, liste,
JSON, CSS, HTML, Git, API ve Python için ayrıca örnekli, daha sade yanıtlar var.

Örnek sohbet: “değişken nedir” → “anlamadım” → “peki fonksiyon” → “örnek ver”.
Konuyu ve takip isteğini uygulama eşleştirir. Seçilen yanıtın metnini model
üretir; beklenen metin yanıt olarak doğrudan yapıştırılmaz. Öğretilmiş metni
doğru üretemezse uygulama başarısızlığı belirtir. Bu, genel sohbet belleği değildir.

## Ölçüm

- Öğretilmiş örneklerin doğrudan, açgözlü üretimi: 2.336/2.336 tam metin eşleşmesi.
- Önceden ayrılmış 10 geliştirme sorusu: eski model 2/10, yeni model 4/10.
- Bu eğitimden önce ayrılmış 20 yeni yazım sorusu: eski model 3/20, yeni model 18/20.
- Uygulama eşleştirmesiyle ayrı sohbet kontrolü: 7/8 farklı ifade, 15/15 desteklenmeyen
  istekte kapsam bildirimi, 5/5 temel regresyon, 2/2 konu takibi.

Bu küçük kümeler genel zekâ, gerçek dünya doğruluğu veya serbest sohbet ölçümü değildir.
18/20 sonucu, yönlendirme kullanmadan modelin ham üretimini ölçer. 7/8 sonucu ise
uygulamanın soru eşleştirmesini de içerir. Bu iki ölçüm birbirine karıştırılmamalı.
“python listelerini anlatır mısın” uygulama kontrolünde henüz eşleştirilemedi.
Geliştirme soruları eğitim dosyasına eklenmedi; raporlarda veri ve ağırlık SHA-256
özetleri kaydedildi. Test sonuçlarının sonradan değiştirilmiş ağırlıklara aitmiş
gibi kullanılması etkinleştirme aşamasında reddedilir.

## Eğitim atölyesi

“Sohbet verisini kullan” ve “Soru-cevap” türü, JSONL içindeki question/answer
çiftleriyle yalnızca yanıtı tahmin ederek eğitim yapar. “Eğitime devam et”
kendi seçili modelinin ağırlıklarından yeni bir ince ayar aşaması başlatır;
optimizasyon durumu sıfırlanır, önceki zamanlayıcı kaldığı yerden sürdürülmez.
Yeni model ayrı bir aday dosyasına kaydedilir. Çalışan modelin üzerine yazılmaz
ve aday otomatik etkinleştirilmez. Denemek için Model kartından dosya seçilebilir.

Her 100 adımda ve durdurulunca kayıt alınır. İlk adım öncesinde durdurulursa
boş model oluşturulmaz. Eğitim kaybı gösterilir; bu modda bağımsız doğrulama
kaybı ölçülmediği açıkça yazılır. Genel metin modu, TXT veya text alanlı JSONL
ile önceki eğitim yöntemini sunmaya devam eder.

## Dosyalar ve tekrar çalıştırma

- Etkin: `models/terra-trained.pt`
- Önceki çalışan model: `models/terra-before-0.4.pt`
- Yeni aday: `models/terra-balanced-candidate.pt`
- Eğitim: `training/dialogue-training.jsonl`
- Ham ölçümler: `data/dialogue-baseline.json`, `data/balanced-candidate-evaluation.json`
- Uygulama kontrolü: `data/balanced-candidate-audit.json`

Proje klasöründe:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -q
.\.venv\Scripts\python.exe -m scratch.batch_evaluate models/terra-trained.pt --trained --output data/recheck-0.4.json
```

Arayüz 0.4 açılışı görsel olarak kontrol edildi. Sonraki masaüstü etkileşiminden
önce pencere kapandığı için düğmeler üzerinden uçtan uca kontrol tamamlanamadı.
Model üretimi ve sohbet takibi ayrı kod testleriyle çalıştırıldı.

Ekran görme, mikrofon, bilgisayar kontrolü ve genel amaçlı kod yazma bu sürümde yok.

## Deney kayıtları

İlk 8.000 adımlık aday: 3/10, 17/20, 2336/2336. Sonraki 4.000 adımda metin konumları 0–16 arasında kaydırıldı: 5/10, 17/20, 2331/2336. Beş eski örnek bozulduğu için bu aday etkinleştirilmedi. Son 4.000 adımda adımların yarısı normal konumlarda tutuldu: 4/10, 18/20, 2336/2336. Bu son aday etkinleştirildi. Küçük geliştirme kümeleri aday seçiminde kullanıldı; bağımsız bir son değerlendirme değiller.

53 birim/regresyon testi geçti. Kayıt, durdurma, kaynak modelin korunması, yanıt maskesi, nedensellik ve toplu üretimin tekli üretimle eşdeğerliği sınandı.
