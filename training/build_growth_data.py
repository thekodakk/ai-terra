"""Self-authored additional conversation intents; frozen unseen phrasings."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scratch.conversation import normalize
from scratch.routing import fold

# Each entry: taught phrasings, an excluded development phrasing, answer.
ENTRIES = [
    (['çok yoruldum','bugün yorgunum','yorgun hissediyorum'], 'bugün çok yorgun hissediyorum',
     'Yorulmuşsun. Şimdi büyük bir iş seçmek yerine kısa bir mola verebilirsin. Devam edeceksen sadece küçük bir adım belirleyelim; her şeyi bugün bitirmek zorunda değilsin.'),
    (['ne yapacağımı bilmiyorum','aklıma bir şey gelmiyor','yapacak bir şey bulamadım'], 'şimdi neyle uğraşsam karar veremedim',
     'Önce ne istediğini daraltalım: dinlenmek mi, bir şey öğrenmek mi, küçük bir şey üretmek mi? Birini seçersen ona uygun kısa bir başlangıç önerebilirim.'),
    (['bir şey öğrenmek istiyorum','öğrenmeyi seçiyorum','yeni bir şey öğrenelim'], 'bugün yeni bir şey öğrenesim var',
     'Küçük bir Python denemesiyle başlayabiliriz: iki sayıyı toplayan bir fonksiyon yaz, sonra farklı sayılarla çağır. Çalışınca neden o sonucu verdiğini açıklamaya çalış. Tek bir örneği anlamak iyi bir başlangıçtır.'),
    (['dinlenmek istiyorum','dinlenmeyi seçiyorum','biraz mola vereceğim'], 'şu an biraz dinlenesim var',
     'Tamam, ara verebilirsin. Ekrandan uzaklaşıp rahat edeceğin kısa bir uğraş seç. Geri döneceksen kaldığın yeri bir cümleyle not etmek yeniden başlamanı kolaylaştırabilir.'),
    (['küçük bir şey üretmek istiyorum','üretmeyi seçiyorum','küçük proje yapalım'], 'ufak bir şey geliştirmek istiyorum',
     'Bir not uygulamasının tek özelliğini yapabilirsin: yazılan metni listeye eklemek. Sonra silme, kaydetme ve arama eklenebilir. İlk hedefi küçük tutarsan çalışan bir sonuç görmen kolaylaşır.'),
    (['başlamak zor geliyor','bir türlü başlayamıyorum','işe başlayamadım'], 'başlamak istiyorum ama başlayamıyorum',
     'İşi tek bir küçük adıma indirelim. Kod yazacaksan önce proje klasörünü açıp yapılacak ilk davranışı bir cümleyle yaz. Sonraki hedef sadece o davranışı çalıştırmak olsun.'),
    (['ders çalışma planı yap','nasıl ders çalışayım','ders çalışmam gerekiyor'], 'derslerimi nasıl planlayabilirim',
     'Önce çalışacağın konuları ve teslim tarihlerini yaz. En yakın ya da en zor konudan küçük bir bölüm seç; kısa bir çalışma ve mola süresi belirle. Sonunda sadece okuyup okumadığını değil, bir soruyu kendin çözebilip çözemediğini kontrol et.'),
    (['projemi nasıl böleyim','projeyi küçük parçalara ayır','büyük projeye nasıl başlanır'], 'büyük bir projeyi nereden tutmalıyım',
     'Önce uygulamanın yapacağı tek temel işi yaz. Onu giriş, işlem ve sonuç olarak üçe ayır. Her parçayı ayrı çalıştır, sonra birleştir. Arayüzü süslemekten önce bu küçük akışın düzgün çalışmasını hedefle.'),
    (['kod çalışmıyor','kodum hata veriyor','program açılmıyor'], 'yazdığım program bir türlü çalışmıyor',
     'Hata mesajının tamamı, ilgili kısa kod parçası ve beklediğin davranış sorunu ayırmaya yardımcı olur. Bu sürüm kodunu çalıştırmaz; dosyalarını görmez. Önce hatanın hangi satırı ve hangi işlemi gösterdiğine bakabilirsin.'),
    (['hata mesajını nasıl okuyayım','hata mesajı nereden okunur','traceback nasıl okunur'], 'hata çıktısında hangi kısma bakmalıyım',
     'Python traceback çıktısında son satır hata türünü ve açıklamasını verir. Üstteki dosya ve satır bilgileri hataya giden çağrıları gösterir. Kendi kodundaki ilgili satırı bulup değişkenlerin beklediğin değerleri taşıyıp taşımadığını kontrol edebilirsin.'),
    (['kod çalıştı','sonunda çalışıyor','hatayı çözdüm'], 'sonunda programı çalıştırabildim',
     'Güzel, şimdi sonucu birkaç farklı girdiyle kontrol et. Özellikle boş değer, sıfır veya beklenmedik giriş gibi sınır durumlarını dene. Değişikliği ve neden işe yaradığını kısa bir notla kaydetmek de yararlı olur.'),
    (['yanlış anladın','onu demek istemedim','beni yanlış anladın'], 'benim demek istediğim bu değildi',
     'Tamam, önceki yorumum uygun olmamış. Ne demek istediğini biraz farklı yazabilir veya tek bir örnek verebilirsin. Bu küçük modelin desteklediği konular sınırlı olduğu için her ifadeyi doğru eşleştiremeyebilirim.'),
    (['cevabın yanlış','bu bilgi yanlış','yanlış cevap verdin'], 'verdiğin yanıt doğru görünmüyor',
     'Yanıtımı kesin doğru kabul etme. Hangi bölümün yanlış olduğunu gösterebilirsin. Bu sürüm düzeltmeyi otomatik olarak ağırlıklarına işlemez; eğitim örneğinin düzenlenmesi ve yeniden test edilmesi gerekir.'),
    (['başka konuya geçelim','konuyu değiştirelim','başka bir şey konuşalım'], 'bu konuyu bırakıp başka şey konuşsak',
     'Olur. Yeni konuyu doğrudan yazabilirsin. Temel programlama kavramları, küçük proje adımları ve bazı günlük sohbet örnekleri bu sürümde öğretilmiş durumda.'),
    (['yarın devam edelim','sonra devam ederiz','bugünlük yeter'], 'bugün bırakıp yarın sürdürsek',
     'Tamam, burada bırakabiliriz. Yeniden başlarken son yaptığın işi ve sıradaki küçük adımı yazman yeterli. Uygulama kapandığında bu sürüm konuşmayı kalıcı bir kişisel hafıza olarak saklamaz.'),
    (['yeni bilgi öğreniyor musun','sohbet ederken öğrenir misin','konuşunca ağırlıkların değişir mi'], 'ben yazdıkça kendini eğitiyor musun',
     'Sohbet ederken ağırlıklarım değişmez. Yeni örneklerin eğitim dosyasına eklenip eğitim çalıştırılması gerekir. Ekranda konuşmayı göstermek veya son konuyu uygulamada tutmak, model eğitimiyle aynı işlem değildir.'),
    (['kaç parametren var','model boyutun ne','parametre sayın kaç'], 'senin toplam parametre sayın nedir',
     'Parametre sayısı seçilen model dosyasına bağlıdır. Güncel sayıyı Model kartı sekmesinden kontrol edebilirsin. Daha fazla parametre tek başına daha doğru yanıt anlamına gelmez; eğitim verisi ve test sonuçları da önemlidir.'),
    (['cevaplarını nereden alıyorsun','hazır cevap mı gösteriyorsun','yanıtı gerçekten model mi yazıyor'], 'yanıtları hangi yolla üretiyorsun',
     'Uygulama soruyu desteklenen bir örnekle eşleştirir, ardından yerel model yanıtı bayt bayt üretir. Üretilen metin öğretilmiş yanıtla uyuşmazsa gösterilmez. Bu sınırlı düzen, serbestçe her soruyu anlayabildiğim anlamına gelmez.'),
]

TOPICS = {
    'klasör': 'Klasör, dosyaları ve başka klasörleri düzenlemek için kullanılır. Örneğin bir projede kod, görseller ve testler ayrı klasörlerde tutulabilir. Klasör adı ile dosyanın uzantısı farklı şeylerdir.',
    'dosya yolu': 'Dosya yolu, bir dosyanın bulunduğu yeri belirtir. Mutlak yol başlangıçtan itibaren konumu gösterir; göreli yol bulunduğun klasöre göre yorumlanır. Dosya bulunamadığında yolun hangi klasöre göre çözüldüğünü kontrol etmek gerekir.',
    'terminal': 'Terminal, metin komutlarıyla bir kabuk veya programa ulaşmanı sağlayan arayüzdür. Bir komutun ne yaptığını ve hangi klasörde çalıştığını anlamak önemlidir. Bu Terra sürümü terminal komutlarını senin yerine çalıştırmaz.',
    'sözdizimi hatası': 'Sözdizimi hatası, kodun dilin yazım kurallarına uymamasıdır. Eksik parantez veya Python içinde eksik iki nokta buna neden olabilir. Hatanın gösterdiği satırın yanında önceki satırı da kontrol etmek yararlı olur.',
    'mantık hatası': 'Mantık hatasında program çalışabilir ama istenen sonucu vermez. Örneğin ortalama için toplamı eleman sayısına bölmek gerekirken yanlış sayıya bölmek böyle bir hatadır. Küçük ve sonucu bilinen örneklerle test etmek yardımcı olur.',
    'birim testi': 'Birim testi, kodun küçük bir bölümünün belirli girdilerde beklenen sonucu verip vermediğini kontrol eder. Toplama fonksiyonu için 2 ve 3 girdisinin 5 üretmesi bir örnektir. Tek testin geçmesi bütün programın doğru olduğunu kanıtlamaz.',
    'sınır durumu': 'Sınır durumu, işlemin uç koşullarından biridir. Boş liste, tek eleman, sıfır veya izin verilen en büyük değer örnek olabilir. Normal girdiler çalışsa bile sınır durumlarını ayrıca test etmek gerekir.',
    'yedekleme': 'Yedekleme, dosyaların kaybolması veya bozulmasına karşı ayrı bir kopyasını tutmaktır. Aynı diskteki kopya disk arızasına karşı yeterli değildir. Bir yedeğin işe yarayıp yaramadığını anlamak için geri yüklemeyi de denemek gerekir.',
    'sürüm kontrolü': 'Sürüm kontrolü, dosyalardaki değişikliklerin geçmişini izler. Hangi değişikliğin ne zaman yapıldığını karşılaştırmayı ve önceki bir sürüme dönmeyi sağlar. Git buna bir örnektir; ayrıca yedekleme planı yapmak yine önemlidir.',
    'arayüz': 'Arayüz, kullanıcının bir uygulamayla etkileştiği bölümdür. Düğmeler, metin alanları ve menüler buna örnektir. İyi bir arayüz yapılan işlemi ve sonucunu anlaşılır gösterir; görünüm kadar kullanılabilirlik de önemlidir.',
    'veri tipi': 'Veri tipi, bir değerin nasıl yorumlandığını ve hangi işlemleri desteklediğini belirler. Python içinde 5 bir tam sayı, "5" ise metindir. Aynı görünseler bile toplama gibi işlemlerde farklı davranabilirler.',
    'girinti': 'Girinti, satır başındaki boşluklardır. Python kod bloklarını girintiyle ayırır. Bir fonksiyon veya döngü gövdesindeki satırlar uygun biçimde içeri kaydırılır. Tutarsız girinti hataya veya yanlış davranışa yol açabilir.',
}


def main():
    def read(name):
        return [json.loads(s) for s in (ROOT/'training'/name).read_text('utf-8').splitlines() if s.strip()]
    old = read('dialogue-training.jsonl')
    old_map = {normalize(p['question']):p for p in old}
    entries = []
    for questions, query, answer in ENTRIES:
        existing = {old_map[normalize(q)]['answer'] for q in questions if normalize(q) in old_map}
        if len(existing)>1:
            raise ValueError('Intent merges different existing answers: '+query)
        entries.append((questions,query,next(iter(existing)) if existing else answer))
    topics = {topic:old_map.get(normalize(topic+' nedir'),{'answer':answer})['answer'] for topic,answer in TOPICS.items()}
    new_dev = [{'question':q,'answer':a} for _,q,a in entries]
    new_dev += [{'question':topic+' konusundan biraz bahsedebilir misin','answer':answer} for topic,answer in topics.items()]
    frozen = read('heldout.jsonl')+read('dialogue-heldout.jsonl')+new_dev
    forbidden = {normalize(p['question']) for p in frozen}
    rows = {normalize(p['question']):p for p in old}
    def add(q,a):
        key = normalize(q)
        if key in forbidden:
            return
        if key in rows and rows[key]['answer'] != a:
            raise ValueError('Conflicting question: '+q)
        rows.setdefault(key,{'question':q,'answer':a})
    for questions,_,answer in entries:
        for question in questions:
            for query in [question,question+' ya','terra '+question]:
                add(query,answer)
                add(fold(query),answer)
    for topic,answer in topics.items():
        for template in ['{} nedir','{} ne demek','{} anlatır mısın','{} konusunu açıkla','{} hakkında bilgi ver','bana {} anlat','{} tam olarak nedir','{} hakkında konuşalım']:
            query = template.format(topic)
            add(query,answer)
            add(fold(query),answer)
    # Assert old data stays intact and all frozen questions stay out of training.
    assert all(rows[normalize(p['question'])]==p for p in old)
    assert not (set(rows) & forbidden)
    for name, data in [('growth-training.jsonl',list(rows.values())),('growth-heldout.jsonl',new_dev)]:
        path = ROOT/'training'/name
        text = ''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in data)
        if name.endswith('heldout.jsonl') and path.exists() and path.read_text('utf-8')!=text:
            raise ValueError('Frozen development set cannot be overwritten')
        path.write_text(text,'utf-8')
    print(json.dumps({'training':len(rows),'distinct_answers':len({p['answer'] for p in rows.values()}),'new_development':len(new_dev)}))


if __name__ == '__main__':
    main()
