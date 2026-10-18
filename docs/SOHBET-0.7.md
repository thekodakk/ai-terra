# Terra 0.7 — sohbet hafızası ve eğitim denemeleri

21 Eylül 2026. Uygulama 0.7; etkin sinir ağı 0.6 ağırlıklarıyla korunuyor.
Hazır model veya harici AI servisi kullanılmadı.

## Kullanılabilir değişiklikler

- “Değişken nedir?” → “teşekkürler” → “örnek ver”: teşekkür ve onay mesajları
  son konuyu artık değiştirmiyor. Öğretilmiş eşdeğer ifadeler de aynı davranışı kullanır.
- İki konu konuştuktan sonra “önceki konuya dön” önceki konuyu seçer ve yanıtı
  yeniden yerel modele ürettirir. En fazla sekiz önceki konu oturum belleğinde tutulur.
- “Yanlış anladın”, “cevabın yanlış”, konu değiştirme ve bitirme mesajları eski
  konuya yanlışlıkla dönülmesini engeller. Sohbet temizlenince hafıza da temizlenir.
- `(8+4)/3 kaç eder` gibi açık ifadeler yerel dört işlem hesaplayıcısına gider.
  Ondalıklar noktayla yazılır; kesirli sonuçlar yuvarlanmadan gösterilir.
  Python eval kullanılmaz; sözdizimi ve işlem sınırları vardır.
  Bu sonuçlar açıkça **uygulama hesaplaması** olarak etiketlenir.

Bu özellikler modelin öğrenilmiş genel muhakemesi değildir. Konu hafızası ve araç
seçimi uygulama kodundadır. Öğretilmiş sohbet yanıtlarını sinir ağı üretmeye devam eder.
Uygulama açıksa kapatıp `Baslat.vbs` ile yeniden açarak yeni kodu yükleyebilirsin.

## Eğitim sonuçları

Toplam 20.000 deney adımı çalıştırıldı. Etkin modelin parametre sayısı **891.904**,
tarihsel eğitim adımı **41.600**, desteklediği soru biçimi **4.469** olarak kaldı.
Eğitimde yanıt gruplarını dengeleyen isteğe bağlı örnekleme eklendi. CLI kaynak
modelin üzerine eğitim çıktısı yazılmasını da artık reddeder.

177 yeni doğal soru biçimiyle `natural-training.jsonl` toplam 4.646 soruya çıktı.
Önceki soruların yanıtları korunur; değerlendirme soruları eğitimden hariçtir.

Sonuç sırası: eski 10 soru / diyalog 20 / genişleme 30 / önceki 18 anlama sorusu /
öğretilmiş soruların tamamı. Bunlar geliştirme setleridir, bağımsız genel zeka testi değildir.

- Etkin 0.6: **6/10, 18/20, 21/30, 4/18, 4469/4469**.
- Dengeli eğitim: **6/10, 18/20, 21/30, 4/18, 4469/4469**. Kazanç yok; etkinleştirilmedi.
- Yeni doğal ifadeler: **5/10, 18/20, 23/30, 9/18, 4646/4646**.
- Ek ince ayar: **4/10, 17/20, 23/30, 8/18, 4646/4646**.
- Önceki ağırlıklarla yarı yarıya birleştirme: **6/10, 18/20, 22/30, 5/18, 4608/4646**.
- Birleştirmeden sonra ince ayar: **5/10, 18/20, 23/30, 7/18, 4646/4646**.

Hiçbir aday bütün eski kalite kapılarını geçmedi; **etkin model değiştirilmedi**.
Özellikle doğal ifadeler adayında “modelin ağırlıkları nasıl öğreniyor” sorusu geriledi.
Yeni eğitim her ölçümde iyileşme anlamına gelmiyor.

Eğitimden önce yazılan ayrı 12 cümlede etkin model **2/12**, doğal ifadeler adayı
**4/12** doğru üretti. Bu cümleler aynı geliştiricinin yazdığı dar kapsamlı sorulardır.
Son testten sonra aday değiştirilmedi. Gelecek çalışmada bu set artık görülmüş
sayılmalı; yeniden bağımsız son test diye sunulmamalıdır.

## Doğrulama ve dosyalar

80 otomatik test geçti. Gerçek etkin ağırlıklarla, ağ bağlantısı engellenerek yapılan
12 sohbet hafızası kontrolü de geçti. Yeni dört işlem özelliği ayrı testlerle doğrulandı.
`QuestionIndex` artık liste dışında bir iterator verildiğinde de doğru indeks oluşturur.

- Etkin model: `models/terra-trained.pt` — bu çalışmada üzerine yazılmadı.
- Deneyler: `models/terra-balanced-candidate.pt`, `terra-natural-candidate.pt`,
  `terra-natural-refined.pt`, `terra-natural-blended.pt`, `terra-natural-repaired.pt`.
- Ölçümler: `data/balanced-evaluation.json`, `data/natural-evaluation.json`,
  `data/natural-refined-evaluation.json`, `data/natural-blended-evaluation.json`,
  `data/natural-repaired-evaluation.json`, `data/natural-final-probes.json`.
- Etkileşim denetimi: `data/topic-memory-active-audit.json`.
- Yeni veri: `training/natural-training.jsonl`; üretici: `training/build_natural_data.py`.

Test komutu: `.\.venv\Scripts\python.exe -m unittest discover -s tests -q`.
Gerçek hafıza testi: `.\.venv\Scripts\python.exe -m tests.audit_topic_memory`.

Bir sonraki eğitim çalışmasında tek tek test cümlelerini ezberletmek yerine veri
anlam çeşitliliği ve unutmayı azaltan eğitim araştırılmalı. Mevcut raporlar silinmemeli;
geliştirme setinde iyileşme, yeni ve ayrılmış sorular üzerinde ayrıca sınanmalıdır.
