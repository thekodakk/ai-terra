# AI Terra

Windows üzerinde çalışan kişisel yardımcı prototipi. Sıfırdan eğitilmiş bir model değildir.
Seçtiğin modeli ekran, dosya, komut ve masaüstü araçlarıyla birleştirir.

## Başlat

`Baslat.vbs` dosyasına çift tıkla. Konsol görünmeden tarayıcında açılır.
Alternatif: `Baslat.cmd`. Adres: **http://127.0.0.1:8844**.

Bu bilgisayarda Python ve Pillow mevcut. Ollama üzerinden **qwen3.5:4b** indirildi.
Ayarlar yerel modeli kullanacak şekilde hazırlandı. Model GPT-5.6 Terra ile aynı değildir;
özellikle karmaşık görevlerde ve Türkçe ifadelerde hata yapabilir.

Başka bilgisayara taşırken Python 3.11+ ve `Kurulum.cmd` gerekir. Yerel model
ayrıca kurulmalıdır; model ağırlıkları bu proje klasöründe değildir.

## Neler var?

- Türkçe sohbet ve tarayıcı üzerinden sesli yazdırma / sesli yanıt.
- İzin verdiğinde ana monitörün görüntüsünü modele gönderme.
- İki dakikada bir kısa öneri veren, oturum başına 10 gözlemle sınırlı isteğe bağlı fikir modu.
- Seçilen klasörde dosya listeleme/okuma, farkını gösterip onay alarak dosya yazma.
- Komutu gösterip onay aldıktan sonra PowerShell ile test/build çalıştırma.
- Ekrana bakıp onaylı fare ve klavye işlemleri. Her eylem sonrası yeniden ekran alınması gerekir.
- Gerçek işlem kayıtları: okunan/yazılan dosya sayısı ve komutların gerçek çıkış kodu.
- F8 ve **Durdur** düğmesi. Ekran ve kontrol izinleri iptal edilir; yeni adımlar engellenir.
- Kullanıcı tarafından düzenlenen kalıcı tercih notları; API anahtarı için Windows DPAPI.

## İlk deneme

Terra'ya `ornek-proje dosyalarını oku, testleri çalıştır ve hatayı düzelt` de.
Bu klasör yapay bir test projesidir. Örnek hata daha önce test sırasında düzeltilmiş olabilir.
Dosya değişikliğini ve terminal komutunu uygulamadan önce onay penceresinde incele.
İşlem akışındaki sonuçlar modelin yorumundan bağımsızdır; sıfır çıkış kodu yalnızca
çalıştırılan komutun başarılı bittiğini gösterir, bütün programın hatasız olduğunu kanıtlamaz.

## Ekran ve ses

Ekranı ekleyip mesajı gönderdiğinde üç saniyelik hazırlık süresi vardır; hedef pencereye geç.
Yalnızca ana monitör desteklenir. Modelin gördüğü görüntü küçültülmüş bir ekran görüntüsüdür.
Kontrol onayında dayanak ekran gösterilir, ardından hedef pencereye dönülür. Ekran belirgin
biçimde değişmişse işlem reddedilir. Bu basit görüntü kontrolü kusursuz bir güvence değildir.
Yönetici/güvenlik ekranları desteklenmez. Onay beklerken pencereyi taşımamaya dikkat et.

Sesli giriş tarayıcının `SpeechRecognition` desteğine bağlıdır; Chrome/Edge gerekebilir.
Tarayıcı ses kaydını kendi konuşma tanıma hizmetine gönderebilir; ilk kullanımda bildirim vardır.
Varsayılan olarak konuşma metne dökülür ve sen gönderirsin. **Sesli komutu gönder**
seçeneğini açarsan konuşma bitince otomatik gönderilir. Sürekli dinleme yoktur.
Sesli yanıt için Türkçe ses bulunamazsa tarayıcının varsayılan sesi kullanılır.
Gerçek mikrofon ve hoparlör deneyimi kullanıcı tarafından denenmelidir.

Fikir modu yalnızca uygulama sekmesi görünürken çalışır. Her gözlem model işlemi gerektirir;
OpenAI seçildiğinde ayrı API maliyeti oluşur. Fikir modu dosya/masaüstü işlemi yapamaz.

## Model bağlantısı

**Yerel:** Ollama servisinin açık olması gerekir. Başlatıcı varsayılan kurulum konumundaki
Ollama'yı gerektiğinde başlatır. `qwen3.5:4b` görüntü ve araç çağrısı destekler.
Başka bir model seçersen bu özelliklere sahip olduğunu kontrol et.

**OpenAI:** Ayarlardan sağlayıcıyı seç, model adını ve kendi API anahtarını gir.
ChatGPT Plus kullanım hakkı API kredisi değildir. API ayrıca ücretlendirilir.
Anahtar bu bilgisayarda Windows kullanıcı hesabına bağlı şifrelenir. Sohbete yazma.
API bağlantısı gerçek bir anahtar olmadan uçtan uca test edilmiş sayılmaz.
Web kaynaklarıyla doğrulama OpenAI sağlayıcısında isteğe bağlıdır.
Sağlayıcı/ayar değişince ekran ve kontrol izinleri kapatılır; tekrar açıkça izin vermen gerekir.

## Veriler ve sınırlar

- Sunucu yalnızca `127.0.0.1` üzerinde dinler; internetten yayınlama.
- Yerel HTTP arayüzünde oturum anahtarı, Host/Origin kontrolü ve CSP vardır.
- Ekranlar diske kaydedilmez. Sohbet RAM'de kalır; servis kapanınca gider.
- `data/settings.json`: ayarlar ve senin yazdığın tercihler.
- `data/key.bin`: varsa Windows tarafından şifrelenmiş API anahtarı.
- `data/backups/`: üzerine yazılan dosyaların yedekleri ve asıl yol eşlemesi.
- `data/server.log`: başlatıcı servis hataları; istek/sohbet içerikleri loglanmaz.
- OpenAI seçiliyken mesaj, kullanılan dosya içeriği ve izinli ekranlar OpenAI'a gider.
- Yerel modelde bu içerikler yapılandırılan yerel Ollama servisine gider.
- Dosya araçları seçilen klasörü aşamaz; hassas ve üretilmiş bazı yollar engellenir.
- **Onaylı PowerShell komutları bir sandbox içinde değildir.** Kullanıcı hesabının eriştiği
  dosyaları değiştirebilir, ağ kullanabilir ve program başlatabilir. Komutu incelemeden onaylama.
- Komutlar 60 saniye ve 2 MB çıktı sınırına sahiptir. Görevler 1–30 adım sınırıyla çalışır.
- Durdurma devam eden model ağ isteğini hemen sonlandırmayabilir; yanıt geldiğinde atılır.
- Yapılmış dosya değişiklikleri Durdur ile otomatik geri alınmaz; yedekten döndürülebilir.
- Model yanlış bilgi/yanlış işlem önerebilir. Bu prototip hatasızlık veya tam özerklik garantisi vermez.

## Geliştirme

```powershell
python app.py --no-browser
python -m unittest discover -s tests -v
node --check web/main.js
python -m tests.vision_smoke
```

`vision_smoke` yalnızca yapay bir test resmi kullanır; masaüstünü yakalamaz.
`terra/providers.py` model bağlantıları, `terra/agent.py` görev döngüsü,
`terra/tools.py` onaylı araçlar, `terra/desktop.py` Windows girdileri,
`app.py` HTTP sunucusu, `web/` kullanıcı arayüzüdür.

Resmî kaynaklar:
- https://developers.openai.com/api/docs/guides/function-calling
- https://developers.openai.com/api/docs/guides/images-vision
- https://docs.ollama.com/api/chat
- https://ollama.com/library/qwen3.5:4b
