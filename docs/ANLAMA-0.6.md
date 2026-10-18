# Terra 0.6 — anlama ve netleştirme

Parametre sayısı değiştirilmedi: **891.904**. Aynı kendi modelinin ağırlıkları
6.000 ek adım eğitildi; eğitim geçmişi toplam 41.600 adım oldu. Hazır model,
harici model servisi, indirilen veri veya kişisel dosya taraması kullanılmadı.

## Öğrenme değişikliği

132 ayrı yanıtın farklı yazımlarını çeşitlendirdik. Eğitim kümesi 2.801'den
4.469 soru biçimine çıktı. Günlük konuşma, bir işe başlama, dersleri planlama,
hata mesajını okuma, konu değiştirme ve modelin nasıl çalıştığını sorma için
doğal ifadeler ve Türkçe karaktersiz karşılıkları eklendi. Önceki öğretilmiş
yanıtlar değiştirilmedi. Mevcut geliştirme soruları ve yeni 18 son kontrol
sorusu eğitim verisine katılmadı; ayrıklık kod testiyle denetlendi.

Ham modelin yönlendirme olmadan, açgözlü üretimle ölçülen tam metin eşleşmeleri:

- Önceki 10 geliştirme sorusu: 5/10 → 6/10.
- Önceki 20 geliştirme sorusu: 18/20 → 18/20.
- Önceki 30 geliştirme sorusu: 5/30 → 21/30.
- Bu tur eğitimden önce yazılan 18 ayrı son kontrol sorusu: 0/18 → 4/18.
- Öğretilmiş örnekler: 4.469/4.469.

İlk üç küme geliştirme içindir; daha önce sonuçları incelenmiştir. Yeni 18
soru aday seçildikten sonra son kontrol için kullanıldı, sonrasında yeniden
eğitim yapılmadı. Bunların hepsi küçük, elle hazırlanmış kümelerdir; genel zekâ
veya geniş kapsamlı Türkçe yeterliliği ölçmez. Özellikle 4/18 sonucu, daha uzak
ifadeleri anlamanın hâlâ zayıf olduğunu gösterir. Tam metin ölçümü, başka bir
biçimde doğru yazılmış yanıtı da başarısız sayabilir.

## Sohbet akışı

Uygulama bir soruyu kesin eşleştiremediğinde, yeterince yakın öğretilmiş sorular
bulursa en fazla üç seçenek gösterir. Bir numara, “ikincisi” gibi bir seçim
veya tek seçenek varsa “evet” ile yanıt istenebilir. Seçim yapılana kadar model
yanıt üretmez. Birden fazla seçenek varken sadece “evet” demek seçimi yapmaz.
“Hiçbiri”, “hayır” veya “iptal” seçenekleri temizler. Yeni bir soru eski
seçenekleri onaylamak yerine yeni bir konuşma adımı başlatır.

Örnek: “python listelerini anlatır mısın” → sunulan liste sorusunun numarasını
yaz → “peki bunun örneği var mı”. Ayrıca “kodum hata veriiyor” gibi bazı
yazım hatalarında doğru soruyu seçmek mümkün olur.

“Bunun örneğini ver”, “buna örnek ver” ve “peki bunun örneği var mı” gibi takip
ifadeleri desteklenir. Aynı yanıtı öğrenmiş yeni soru biçimleri de varsa mevcut
örnekli açıklamayı kullanır. Seçenekler, bu bağlantılar ve kısa konu takibi
uygulama kodudur; sinir ağının öğrendiği genel bir hafıza değildir. Yanıtın
metnini yine yerel model üretir; bozuk üretim yerine beklenen yanıt yapıştırılmaz.

## Doğrulama

- 66 birim/regresyon testi geçti.
- Gerçek modelle 5 netleştirme, 1 yeni soru biçiminden takip açıklaması ve
  1 iptal senaryosu: 7/7. Bu ölçüm simüle edilmiş açık kullanıcı seçimini içerir.
- Etkin modelde örnekli takip açıklamaları: 10/10.
- Önceki uygulama kontrolü: 7/8 doğrudan benzer soru, 15/15 kapsam dışı istekte
  model yanıtından kaçınma, 5/5 temel yanıt, 2/2 konu takibi. Sekizinci benzer
  soru artık seçim sunar; bunu doğrudan doğru yanıt saymadık.
- Masaüstü açılışı, 0.6 sürüm başlığı ve etkin model kartı görsel kontrol edildi.
  Netleştirme akışı gerçek ağırlıklarla kod üzerinden uçtan uca sınandı.

Öğretilmiş örneklerdeki hızlı değerlendirme, tüm yanıt baytları ve bitiş
işareti için nedensel açgözlü üretimi kontrol eder. Belirsiz eşitlikler ve
başarısızlıklar normal otoregresif yöntemle üretilir. Bu yalnızca test
hızlandırmasıdır; sohbet yanıtları bu yolla kopyalanmaz.

## Dosyalar

- Etkin model: `models/terra-trained.pt`.
- Geri dönüş: `models/terra-before-0.6.pt` ve aynı adlı JSON özeti.
- Aday: `models/terra-understanding-candidate.pt`.
- Eğitim: `training/understanding-training.jsonl`.
- Son kontrol soruları: `training/understanding-probes.jsonl`.
- Önce/sonra: `data/understanding-baseline.json`, `data/understanding-candidate-evaluation.json`.
- Etkileşim: `data/understanding-interaction-audit.json`.
- Takipler: `data/understanding-active-followups.json`.

Raporlarda ağırlık ve veri SHA-256 özetleri bulunur. Etkinleştirme öncesinde
eski yanıtların korunması, bütün ölçümlerin gerilememesi ve raporun doğru
model dosyasına ait olması denetlendi. Arka planda eğitim işi bırakılmadı.

Yeniden test: `.\.venv\Scripts\python.exe -m unittest discover -s tests -q`.
