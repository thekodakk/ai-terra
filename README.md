> **Kaynak kod dağıtımı:** Bu depoda hazır model ağırlıkları, kişisel ayarlar, çalışma kayıtları ve önceden üretilmiş eğitim/değerlendirme veri dosyaları bulunmaz. Aşağıdaki sürüm raporları geliştirme geçmişini belgeler; yeni kurulum için önce aşağıdaki adımları uygulayın.

## Yeni kurulum

Python ile bir sanal ortam oluşturun ve yerel masaüstü bağımlılıklarını kurun. PyTorch sürümünü donanımınıza göre seçebilirsiniz; Windows CUDA kurulumu için mevcut `Kurulum.cmd` kullanılabilir.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-native.txt
.\.venv\Scripts\python.exe training/make_demo.py
.\.venv\Scripts\python.exe -m scratch.training training/demo.jsonl --output models/terra-trained.pt --steps 200
.\.venv\Scripts\python.exe launcher.py
```

`make_demo.py`, kaynakta bulunan yapay örneklerden deneme verisi üretir; gerçek kullanıcı konuşması içermez. Oluşan model yalnızca küçük bir eğitim denemesidir, tarihsel raporlardaki modelin aynısı değildir. Daha kapsamlı eğitim için kullanma hakkınız olan verileri yerel olarak seçin. Ağırlıklar, veriler ve yerel kayıtlar `.gitignore` ile depodan dışlanır. Ana masaüstü uygulaması API anahtarı gerektirmez. Eski web prototipi için `docs/WEB-LEGACY.md` belgesini okuyun; anahtarları kaynak dosyalarına eklemeyin.

---

> **0.7 uygulama güncellemesi:** Teşekkür/onay sonrası konu hafızası, “önceki konuya dön” ve açıkça etiketlenen yerel dört işlem hesaplayıcısı eklendi. 80 test geçti. Yeni eğitim adayları bazı ölçümlerde ilerleyip bazılarında gerilediği için etkin 0.6 ağırlıkları korundu. Sonuçlar: [docs/SOHBET-0.7.md](docs/SOHBET-0.7.md). Önceki model raporu: [docs/ANLAMA-0.6.md](docs/ANLAMA-0.6.md).

# Terra — kendi modelin

## Açmak

`Baslat.vbs` dosyasına çift tıkla. Artık tarayıcı yerine **Windows masaüstü uygulaması** açılır.
Alternatif: `Baslat.cmd`. Bu bilgisayarda gerekli sanal ortam ve CUDA destekli PyTorch kuruldu.

## Bu sürümün yaptığı

- Hazır model veya API kullanmadan çalışan yerel metin modeli.
- Kendi Transformer kodu, UTF-8 bayt sözlüğü, rastgele başlatılmış ağırlıklar.
- Açıkça seçtiğin TXT / JSONL verileriyle eğitim; otomatik kişisel dosya taraması yok.
- Eğitim/doğrulama kaybı, GPU kullanımı, kayıt, aynı veriyle eğitime devam etme.
- Durdur düğmesi / Escape; eğitim kapanırken tamamlanan son adım kaydedilir.
- Kısa, Ayrıntılı (varsayılan), Uzun yanıt bütçeleri.
- Sohbet ve eğitim sırasında dış servise bağlantı yok. Sohbetler yalnızca oturum belleğinde.

**Bu, henüz güçlü ve güvenilir bir asistan değildir.** İlk model sadece 12 yapay örnekle
200 adım eğitimden geçirilmiş bir eğitim hattı denemesidir. Bozuk sözcükler, anlamsız ve
çelişkili yanıtlar üretebilir. GPT düzeyinde değildir. Ekran görme, ses tanıma, kodu güvenilir
biçimde düzeltme veya otonom bilgisayar kontrolü bu kendi modelinde henüz yoktur.
Uzun yanıt seçeneği üretim sınırını yükseltir; kalite veya minimum uzunluk garantisi değildir.

## Kendi verinle eğitim

1. Eğitim atölyesi → Metin dosyalarını seç.
2. Kullanma hakkına sahip olduğun UTF-8 `.txt` veya `.jsonl` dosyalarını seç.
3. Adım sayısını belirle ve Yeni model eğit ile farklı bir `.pt` dosyasına kaydet.
4. Eğitime devam et, seçili modelin ağırlıklarını ve optimizasyon durumunu yükler.
   Devam ederken verinin aynı olması gerekir; değişen veri için yeni bir model başlat.
5. Sohbet sekmesinde modeli dene. Model kartından farklı kendi model dosyanı seçebilirsin.

Deneme verisini kullan düğmesi yalnızca `training/demo.jsonl` dosyasını seçer.
Bu dosya bu proje için yapay olarak yazılmıştır; gerçek bilgi külliyatı değildir.

JSONL satır örnekleri:

```json
{"question":"Sorun burada","answer":"Ayrıntılı yanıtın burada"}
{"text":"Serbest metin belgen burada"}
```

Toplam sınır: 32 MB; en az 2048 bayt. Dosyalar seçildikleri sırayla birleştirilir.
İlk %90 eğitim, son %10 doğrulama için ayrılır. Bu basit bölme yönteminde benzer/tekrarlı
belgeler ölçümü iyimser gösterebilir; sonuçlar genel zekâ ölçümü değildir.

## Modelin boyutu ve bağımsızlık

İlk deneme: 859.136 parametre, 4 katman, 128 genişlik, 4 attention head,
256 bayt-token bağlamı. Her sinir ağı modelinin parametreleri vardır; bunlar başka bir
şirketin modelini kullanmak anlamına gelmez. Mimari `scratch/model.py` içinde değiştirilebilir.
Model kodu, örnek veri ve üretilen ağırlıklar proje klasöründedir.
Python, PyTorch ve diğer kütüphaneler kendi lisansları olan yazılım bağımlılıklarıdır.

256 baytlık bağlam çok kısadır: uzun soruların ve sohbet geçmişinin eski kısımları
kesilir. Bağlamı büyütmek yeniden eğitim gerektirir; ayarı büyütmek tek başına zekâ kazandırmaz.
Daha iyi bir model için kapsamlı, izinli veri, daha büyük deneyler ve bağımsız değerlendirme gerekir.

## Komut satırı

```powershell
.\.venv\Scripts\python.exe -m scratch.training training/demo.jsonl --output models/benim-modelim.pt --steps 200
.\.venv\Scripts\python.exe -m scratch.training training/demo.jsonl --output models/benim-modelim.pt --steps 200 --resume
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Ağırlıklar ve optimizer `.pt`, okunabilir eğitim özeti aynı adlı `.json` dosyasındadır.
Kayıtlar geçici dosya üzerinden atomik olarak değiştirilir. Özet en son başarılı kaydı gösterir.
Bilinmeyen kaynaklardan model dosyası alma; bu uygulama Terra biçimini ve `weights_only`
yüklemeyi kullanır ancak kötü niyetli dosyaların bütün kaynak tüketimi risklerini engellemez.

## Önceki sürüm

Eski web prototipinin kodları korundu. Açıkça `python launcher_web_legacy.py` çalıştırılırsa
önceki sağlayıcı ayarlarıyla açılır; ana masaüstü uygulaması buna otomatik geçmez.
Eski özellikler ve dış model gereksinimi `docs/WEB-LEGACY.md` içinde açıklanır.
Eski kısa yanıt talimatı da daha açıklayıcı yanıt verecek şekilde düzeltildi.

## Kurulum / sorun giderme

Bu PC'de `Kurulum.cmd` tekrar gerekmez. Başka bir Windows PC'de Python 3.14 ve uyumlu
sürücü gerekir; `Kurulum.cmd` matematik kütüphanelerini indirir, model indirmez.
GPU yoksa çalışma CPU'ya geçer. Model dosyası yoksa uygulama başka modele geçmez.
Başlatma hatalarının kaydı `data/native-error.log` dosyasındadır.

Teknik referans: https://docs.pytorch.org/docs/2.11/generated/torch.nn.functional.scaled_dot_product_attention.html

