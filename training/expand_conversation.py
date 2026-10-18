"""Locally authored curriculum. No downloads, private files or pretrained model."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scratch.conversation import normalize

GROUPS = [
    (['iyiyim', 'iyi', 'ben iyiyim', 'gayet iyiyim'], 'İyi olmana sevindim. İstersen küçük bir konu seçip birlikte üzerinde çalışabiliriz.'),
    (['idare eder', 'fena değil', 'eh işte'], 'Anladım. İstersen nasıl geçtiğini anlatabilir veya başka bir konuyla devam edebilirsin.'),
    (['sıkıldım', 'canım sıkılıyor', 'yapacak bir şey yok'], 'Küçük bir mola veya kısa bir uğraş iyi gelebilir. Bir çizim, kısa yürüyüş ya da küçük bir kod denemesi seçebilirsin. Hangisi ilgini çekiyor?'),
    (['bugün yoruldum', 'yorgunum', 'çok yoruldum'], 'Biraz dinlenmek isteyebilirsin. Bugünkü işleri küçük parçalara ayırıp yalnızca en gerekli olanı bırakmak da bir seçenek.'),
    (['günaydın', 'iyi sabahlar'], 'Günaydın! Yeni bir güne merhaba. Bugün ne üzerinde çalışmak istersin?'),
    (['iyi geceler', 'yatıyorum', 'uyuyacağım'], 'İyi geceler. İyi dinlenmeler; tekrar konuşmak istediğinde buradayım.'),
    (['tamam', 'olur', 'anladım', 'ok'], 'Tamam. Hazır olduğunda sonraki sorunla devam edebiliriz.'),
    (['özür dilerim', 'pardon', 'kusura bakma'], 'Sorun değil. Konuşmaya devam edebiliriz.'),
    (['adın ne', 'ismin ne', 'kendini tanıt'], 'Adım Terra. Bu bilgisayarda sıfırdan eğitilen küçük bir metin modeliyim. Şimdilik sınırlı örnekleri destekliyorum; genel amaçlı bir asistan değilim.'),
    (['ne yapabilirsin', 'neler yapabiliyorsun', 'özelliklerin neler'], 'Şimdilik öğretilmiş temel sohbet ve kısa açıklama örneklerine yanıt verebilirim. Ekran görme, ses tanıma ve bilgisayarı yönetme yeteneğim yok. Öğrenmediğim sorularda uygulama kapsam bildirimi gösterir.'),
    (['kendi modelim misin', 'başka bir model kullanıyor musun', 'hazır model misin'], 'Bu modelin ağırlıkları burada rastgele başlatılıp eğitildi. Hazır bir model servisine bağlanmıyorum. Python ve PyTorch ise çalışmak için kullanılan yazılım kütüphaneleri.'),
    (['beni duyuyor musun', 'sesimi duyabilir misin', 'mikrofonu kullanıyor musun'], 'Bu sürüm yalnızca yazılı mesajları işler. Mikrofonu dinlemiyorum ve ses tanıma yapmıyorum.'),
    (['ekranıma bak', 'ekranımı görüyor musun', 'ne yaptığımı görebiliyor musun'], 'Hayır, bu metin modelinin ekran erişimi yok. Yazdığın mesaj dışında bilgisayarındaki görüntüleri görmüyorum.'),
    (['fareyi hareket ettir', 'bilgisayarımı kontrol et', 'tarayıcıyı aç'], 'Bu sürüm bilgisayar komutu çalıştırmaz ve fareyi hareket ettirmez. Yazdığım metinler otomatik işlem olarak uygulanmaz.'),
    (['bilmediğin sorularda ne yapıyorsun', 'her şeyi biliyor musun', 'yanlış cevap verir misin'], 'Her şeyi bilmiyorum ve hata yapabilirim. Bu sürüm yalnızca desteklenen örnekleri yanıtlar; diğer sorularda uygulama sınırımı belirtir. Örnekleri doğru üretmek genel doğruluk garantisi değildir.'),
    (['konuşmalarımı hatırlıyor musun', 'önceki mesajımı hatırlıyor musun', 'hafızan var mı'], 'Bu sürüm yanıt üretirken yalnızca o anki soruyu kullanır. Sohbet ekranda görünse de önceki mesajları anlamlı bir konuşma belleği olarak kullanmıyorum.'),
    (['verilerim internete gidiyor mu', 'mesajlarımı gönderiyor musun', 'çevrimdışı çalışır mısın'], 'Bu masaüstü sürümünde sohbet ve eğitim yerelde çalışır; yanıt üretmek için dış model servisine mesaj gönderilmez.'),
    (['nasıl öğreniyorsun', 'nasıl eğitiliyorsun', 'model eğitimi nasıl çalışır'], 'Örnek soruların yanıtlarını tahmin ederim. Eğitim yazılımı tahmin hatasını hesaplayıp ağırlıkları değiştirir. Daha önce görmediğim soruları ayrıca test etmek gerekir; ezberlemek ile genellemek aynı değildir.'),
    (['parametre nedir', 'parametre ne demek', 'model parametreleri nedir'], 'Parametre, modelin eğitim sırasında ayarlanan sayısal değeridir. Bu değerler girdilerle çıktılar arasındaki ilişkiyi belirler. Parametre sayısı tek başına modelin ne kadar iyi olduğunu göstermez.'),
    (['token nedir', 'token ne demek', 'bayt token nedir'], 'Token, modelin işlediği metin parçasıdır. Bu küçük model UTF-8 baytlarını kullanır. Türkçe bir harf birden fazla bayt olabilir; bu yüzden token sayısı kelime sayısıyla aynı değildir.'),
    (['eğitim kaybı nedir', 'loss nedir', 'kayıp değeri nedir'], 'Eğitim kaybı, model tahminlerinin hedef metinden ne kadar saptığını ölçen sayıdır. Düşmesi eğitim örneklerine uyumu gösterir; modelin bütün soruları doğru yanıtladığını kanıtlamaz.'),
    (['doğrulama verisi nedir', 'test verisi ne işe yarar', 'neden ayrı test yapılır'], 'Eğitimde kullanılmayan örnekler modelin yeni sorularda nasıl davrandığını ölçmeye yarar. Aynı örnekleri hem öğretmek hem test etmek, genelleme yeteneğini olduğundan iyi gösterebilir.'),
    (['ezberleme nedir', 'overfitting nedir', 'aşırı öğrenme nedir'], 'Modelin eğitim örneklerini çok iyi öğrenip yeni örneklerde başarısız kalmasına aşırı uyum denir. Bunu görmek için eğitimden ayrı değerlendirme verisi kullanılır.'),
    (['neden uzun cevap vermiyorsun', 'cevapların neden kısa', 'uzun yanıt ayarı ne yapar'], 'Yanıt uzunluğu ayarı en fazla ne kadar metin üretilebileceğini belirler. Öğretilen yanıt kısa ise ayarı artırmak yeni bilgi eklemez. Daha kapsamlı yanıtlar için uygun eğitim örnekleri gerekir.'),
    (['yazılım nedir', 'program nedir', 'yazılım ne demek'], 'Yazılım, bilgisayara ne yapacağını söyleyen talimatların ve ilgili verilerin bütünüdür. Bir hesap makinesi, oyun veya metin düzenleyici buna örnek olabilir.'),
    (['değişken nedir', 'variable nedir', 'değişken ne işe yarar'], 'Değişken, bir değere program içinde isim vermeyi sağlar. Python örneği: puan = 10. Sonra print(puan) ile bu değeri kullanabilirsin.'),
    (['fonksiyon nedir', 'function nedir', 'fonksiyon ne işe yarar'], 'Fonksiyon, belirli bir işi yapan ve tekrar çağrılabilen kod bölümüdür. Girdi alabilir ve sonuç döndürebilir. Böylece aynı kodu her yerde yeniden yazmak gerekmez.'),
    (['döngü nedir', 'loop nedir', 'döngü ne işe yarar'], 'Döngü, bir işlemi tekrar etmeyi sağlar. Python içinde for i in range(3): ifadesiyle aynı işlem üç kez yürütülebilir. Döngü gövdesi girintili yazılır.'),
    (['koşul nedir', 'if ne işe yarar', 'if else nedir'], 'Koşullar, programa duruma göre farklı davranış kazandırır. Python içinde if puan >= 50: ile bir durum kontrol edilir; else: bölümü koşul yanlışsa çalışır.'),
    (['liste nedir', 'python listesi nedir', 'list ne işe yarar'], 'Python listesi birden fazla değeri sırayla tutar. Örnek: renkler = ["yeşil", "mavi"]. İlk elemana renkler[0] ile erişilir; sıralama sıfırdan başlar.'),
    (['sözlük nedir', 'python sözlüğü nedir', 'dict nedir'], 'Python sözlüğü anahtar-değer çiftlerini tutar. Örnek: kisi = {"ad": "Deniz"}. kisi["ad"] ifadesi "Deniz" değerini verir.'),
    (['string nedir', 'metin türü nedir', 'str nedir'], 'String, metin tutan veri türüdür. Python içinde "merhaba" bir string örneğidir. Sayı gibi görünse de "12" bir metindir; 12 ise tam sayıdır.'),
    (['boolean nedir', 'bool nedir', 'true false nedir'], 'Boolean, doğru veya yanlış değerini temsil eder. Python içinde bunlar True ve False olarak yazılır. Koşul kontrollerinde sık kullanılır.'),
    (['hata ayıklama nedir', 'debug nedir', 'debugging nedir'], 'Hata ayıklama, beklenmeyen davranışın nedenini bulma sürecidir. Önce hatayı tekrar üret, beklenen sonuçla karşılaştır, ilgili kodu incele ve düzeltmeden sonra yeniden test et.'),
    (['birim testi nedir', 'unit test nedir', 'test yazmak ne işe yarar'], 'Birim testi, küçük bir kod parçasının belirli girdilerde beklenen sonucu verip vermediğini kontrol eder. Testin geçmesi yalnızca sınanan durumlar için kanıt sağlar.'),
    (['algoritma nedir', 'algoritma ne demek', 'algoritma örneği ver'], 'Algoritma, bir problemi çözmek için izlenen adımlar dizisidir. Örneğin listedeki en büyük sayıyı bulmak için her elemanı sırayla mevcut en büyük değerle karşılaştırabilirsin.'),
    (['api nedir', 'api ne demek', 'api ne işe yarar'], 'API, programların birbirleriyle belirlenmiş kurallar üzerinden iletişim kurmasını sağlar. Örneğin bir uygulama hava durumu verisini bir servisin API arayüzünden isteyebilir.'),
    (['json nedir', 'json ne demek', 'json örneği ver'], 'JSON, veriyi metin olarak temsil eden bir biçimdir. Örnek: {"ad": "Deniz", "puan": 10}. Nesneler, listeler, metinler, sayılar, boolean değerler ve null içerebilir.'),
    (['html nedir', 'html ne işe yarar', 'web sayfasının yapısı nedir'], 'HTML, web sayfasının yapısını tanımlar. Başlık, paragraf, bağlantı ve form gibi öğeler etiketlerle belirtilir. Görünüm için genellikle CSS kullanılır.'),
    (['css nedir', 'css ne işe yarar', 'web sayfası nasıl biçimlenir'], 'CSS, web sayfasındaki öğelerin görünümünü düzenler. Renkler, yazı boyutları, boşluklar ve yerleşim kuralları CSS ile tanımlanabilir.'),
    (['javascript nedir', 'javascript ne işe yarar'], 'JavaScript bir programlama dilidir. Web sayfalarına etkileşim eklemek için kullanılır; tarayıcı dışında da uygun çalışma ortamlarıyla çalıştırılabilir.'),
    (['python nedir', 'python ne işe yarar'], 'Python bir programlama dilidir. Otomasyon, veri işleme, web uygulamaları ve yapay zekâ çalışmaları gibi birçok alanda kullanılabilir.'),
    (['git nedir', 'sürüm kontrolü nedir', 'git ne işe yarar'], 'Git, dosyalardaki değişiklik geçmişini izleyen bir sürüm kontrol sistemidir. Değişiklikleri karşılaştırmayı, farklı geliştirme dallarıyla çalışmayı ve eski sürümlere dönmeyi kolaylaştırır.'),
    (['veritabanı nedir', 'database nedir', 'veritabanı ne işe yarar'], 'Veritabanı, verileri düzenli saklamak ve sorgulamak için kullanılan sistemdir. Örneğin bir uygulamanın ürün ve sipariş kayıtları veritabanında tutulabilir.'),
    (['sql nedir', 'sql ne işe yarar'], 'SQL, ilişkisel veritabanlarıyla çalışmak için kullanılan bir dildir. Veriyi sorgulama, ekleme ve güncelleme gibi işlemler için komutlar içerir.'),
    (['yorum satırı nedir', 'python yorum satırı nasıl yazılır'], 'Yorum satırı kodu açıklamak içindir ve normal program talimatı olarak çalıştırılmaz. Python içinde # işaretiyle başlar. Örnek: # Bu satır açıklamadır.'),
    (['python merhaba dünya yaz', 'python hello world yaz'], 'Python örneği:\n\nprint("Merhaba dünya!")\n\nBu kod çalıştırıldığında ekrana Merhaba dünya! yazar. Burada kodu göstermiş oldum; bilgisayarında çalıştırmadım.'),
    (['python toplama fonksiyonu yaz', 'iki sayıyı toplayan fonksiyon yaz'], 'Python örneği:\n\ndef topla(a, b):\n    return a + b\n\nprint(topla(2, 3))\n\nBeklenen çıktı 5. Bu mesaj kod örneğidir; burada test çalıştırmadım.'),
    (['python liste uzunluğu nasıl bulunur', 'len ne işe yarar'], 'len, bir dizinin veya koleksiyonun eleman sayısını verir. Örneğin len([10, 20, 30]) sonucu 3 olur. Boş listenin uzunluğu sıfırdır.'),
    (['sıfıra bölme nedir', 'python sıfıra bölme hatası'], 'Python içinde bir sayıyı sıfıra bölmeye çalışmak ZeroDivisionError hatasına yol açar. Bölme işleminden önce paydanın sıfır olup olmadığını kontrol edebilirsin.'),
    (['int ve float farkı nedir', 'tam sayı ve ondalıklı sayı farkı nedir'], 'Python içinde int tam sayıları, float ise kayan noktalı sayıları temsil eder. Örneğin 5 bir int, 5.5 bir float değeridir. Float ile bazı ondalık işlemler tam temsil edilemeyebilir.'),
    (['eşittir ve çift eşittir farkı nedir', 'python = ve == farkı'], 'Python içinde = bir değişkene değer atamak için kullanılır. == ise iki değerin eşit olup olmadığını karşılaştırır. Örneğin x = 5 atamadır; x == 5 karşılaştırmadır.'),
    (['proje fikri ver', 'küçük bir proje öner', 'ne kodlayabilirim'], 'Basit bir görev takip uygulaması yapabilirsin. Önce görev ekleme ve listelemeyi kur, sonra tamamlandı işareti ekle. Son aşamada veriyi dosyaya kaydet ve yeniden açılışta yükle.'),
    (['nereden başlamalıyım', 'kodlamaya nasıl başlayayım'], 'Küçük bir hedef seç: örneğin iki sayıyı toplayan program. Çalıştır, girdileri değiştir ve ne olduğunu gözle. Sonra koşul, döngü ve fonksiyon ekleyerek adım adım ilerle.'),
    (['kodum çalışmıyor', 'hata aldım', 'bir hata var'], 'Hata mesajını, ilgili kısa kod bölümünü ve beklediğin sonucu paylaş. Önce sorunu tekrar üretmek ve hangi satırda ortaya çıktığını görmek gerekir. Bu sürüm kodu kendisi çalıştırmaz.'),
]


def main():
    directory = Path(__file__).parent
    base = [json.loads(line) for line in (directory / 'conversation.jsonl').read_text('utf-8').splitlines()]
    # Resolve the older contradictory Merhaba/Merhaba. entries by the same
    # normalization used in the application; the latest supported answer wins.
    pairs = {normalize(row['question']): row for row in base}
    for questions, answer in GROUPS:
        for question in questions:
            pairs[normalize(question)] = {'question': question, 'answer': answer}
    for a in range(1, 6):
        for b in range(1, 6):
            question = f'{a} + {b} kaç eder'
            pairs[normalize(question)] = {'question': question, 'answer': f'{a} + {b} = {a+b}. İki sayının toplamı {a+b} eder.'}
    rows = list(pairs.values())
    (directory / 'expanded.jsonl').write_text('\n'.join(json.dumps(p, ensure_ascii=False) for p in rows)+'\n', encoding='utf-8')
    def answer_for(question):
        return pairs[normalize(question)]['answer']
    heldout = [
        ('kendinden bahseder misin', answer_for('adın ne')),
        ('modelin ağırlıkları nasıl öğreniyor', answer_for('nasıl öğreniyorsun')),
        ('bir değişkeni anlatır mısın', answer_for('değişken nedir')),
        ('fonksiyonları açıklar mısın', answer_for('fonksiyon nedir')),
        ('python içinde bir döngü ne yapar', answer_for('döngü nedir')),
        ('veriyi json olarak tutmak ne demek', answer_for('json nedir')),
        ('css ile ne yapılabilir', answer_for('css nedir')),
        ('git kullanmak ne işe yarıyor', answer_for('git nedir')),
        ('dört artı üç kaç eder', '4 + 3 = 7. İki sayının toplamı 7 eder.'),
        ('6 + 2 kaç eder', '6 + 2 = 8. İki sayının toplamı 8 eder.'),
    ]
    assert not set(map(normalize, (q for q,_ in heldout))) & set(pairs)
    (directory / 'heldout.jsonl').write_text('\n'.join(json.dumps({'question':q,'answer':a},ensure_ascii=False) for q,a in heldout)+'\n',encoding='utf-8')
    print(f'{len(rows)} training examples; {len(heldout)} separate held-out questions')


if __name__ == '__main__':
    main()
