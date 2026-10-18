"""Self-authored conversational expressions; development questions excluded."""
import json
from pathlib import Path
from scratch.conversation import normalize
from scratch.routing import fold

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
 'çok yoruldum': ['bugün pilim bitti', 'çok bitkinim', 'kendimi tükenmiş hissediyorum', 'yorgunum biraz soluklanayım', 'gün boyunca koşturdum halim kalmadı'],
 'ne yapacağımı bilmiyorum': ['yapabileceğim bir şey arıyorum', 'boş kaldım neyle uğraşayım', 'seçenekler arasında karar veremedim', 'canım bir şey yapmak istiyor aklıma gelmiyor', 'uğraşacak bir şey seçelim mi'],
 'bir şey öğrenmek istiyorum': ['bana bilmediğim bir şey öğret', 'yeni bir konuyu öğrenmek için hazırım', 'bugün kendime bir şey katayım', 'öğrenmeye başlayalım mı', 'beraber yeni bir konu çalışalım'],
 'dinlenmek istiyorum': ['biraz nefes alacağım', 'bir müddet mola vereyim', 'şimdi çalışmayı bırakıp dinleneceğim', 'kısa bir dinlenme arası lazım', 'biraz ara vermeye karar verdim'],
 'küçük bir şey üretmek istiyorum': ['ufacık bir proje yapalım', 'kendime küçük bir uygulama yazayım', 'kolay bir şey geliştirerek başlayalım', 'bir şeyler üretmeye niyetim var', 'basit bir uygulama geliştirmeyi düşünüyorum'],
 'başlamak zor geliyor': ['işi sürekli erteliyorum', 'ilk adımda tıkanıp kalıyorum', 'bir işe girişmekte zorlanıyorum', 'nasıl başlayacağım gözüm korkuyor', 'başlayacak cesareti bulamıyorum'],
 'ders çalışma planı yap': ['okul için çalışma takvimi hazırlayalım', 'derslere ayırdığım vakti düzenle', 'çalışma saatlerimi planlamama yardım et', 'ders programımı nasıl kurayım', 'hangi derse önce çalışacağımı seçelim'],
 'projemi nasıl böleyim': ['uygulamayı aşamalara ayıralım', 'projenin parçalarını sıraya koy', 'yapılacak işleri küçük görevlere böl', 'projede önce hangi parçayı yapayım', 'uygulama için adım adım bir yol çiz'],
 'kod çalışmıyor': ['kodumu çalıştırırken sorun yaşıyorum', 'program hata yüzünden açılmıyor', 'çalıştırdığım uygulama patlıyor', 'yazdığım programı başlatamıyorum', 'kodun yürütülmesi başarısız oluyor'],
 'hata mesajını nasıl okuyayım': ['traceback nasıl yorumlanır', 'hata dökümünü anlayamadım', 'hata metninde nereye dikkat edeyim', 'çıkan hata satırları neyi gösteriyor', 'hata açıklamasını okumama yardım et'],
 'kod çalıştı': ['sonunda programı düzelttim', 'hata gitti program çalışıyor', 'bozuk kodu onardım', 'uygulamayı sorunsuz başlattım', 'artık hata almıyorum'],
 'yanlış anladın': ['benim kastım o değildi', 'sözümü yanlış yorumladın', 'demek istediğimi anlamamışsın', 'sorunun anlamını kaçırdın', 'başka bir şey söylemek istemiştim'],
 'cevabın yanlış': ['verdiğin cevap hatalı', 'bilgide yanlışlık görüyorum', 'yanıtın gerçeği yansıtmıyor', 'bence söylediğin yanlış', 'bu açıklaman doğru değil'],
 'başka konuya geçelim': ['başlığı değiştirelim', 'artık başka şeyden konuşalım', 'bu konudan sıkıldım başka konu açalım', 'konuşmaya farklı konudan devam et', 'şimdiki konuyu kapatalım'],
 'yarın devam edelim': ['kalanını yarına bırakalım', 'bugünkü işi burada bitirelim', 'bir sonraki gün sürdürürüz', 'yarın tekrar çalışmaya başlarız', 'bugün duralım sonra bakarız'],
 'yeni bilgi öğreniyor musun': ['konuşmalarımızla modelin eğitiliyor mu', 'mesajlarımı öğrenmek için kullanıyor musun', 'yazışırken ağırlıkların güncelleniyor mu', 'seninle sohbet etmek eğitim oluyor mu', 'yeni söylediğim şeyleri kendine öğretiyor musun'],
 'kaç parametren var': ['ağırlıklarının toplam sayısı kaç', 'modelinin kaç ağırlığı bulunuyor', 'parametrelerinin adedi nedir', 'sende toplam kaç parametre var', 'sinir ağındaki parametre sayısını söyle'],
 'cevaplarını nereden alıyorsun': ['yazdığın yanıt nasıl ortaya çıkıyor', 'cevabı oluştururken ne yapıyorsun', 'yanıt üretirken nasıl çalışıyorsun', 'cevap vermenin arkasındaki yöntem nedir', 'bu cümleleri nasıl oluşturuyorsun'],
}
# Frozen before candidate training. Same-author narrow probes, not an external benchmark.
PROBES = [
 ('çok yoruldum', 'bugünkü işlerden sonra iyice bitap düştüm'),
 ('ne yapacağımı bilmiyorum', 'boş vaktimde yapacak bir iş bulamadım'),
 ('bir şey öğrenmek istiyorum', 'bugün daha önce bilmediğim bir konuyu çalışmak isterim'),
 ('dinlenmek istiyorum', 'işe bir süre ara versem iyi olacak'),
 ('küçük bir şey üretmek istiyorum', 'kendim ufak bir uygulama geliştirmek istedim'),
 ('başlamak zor geliyor', 'yapılacak işe bir türlü girişemiyorum'),
 ('ders çalışma planı yap', 'okul konularını çalışmak için zamanımı planlayalım'),
 ('projemi nasıl böleyim', 'bu uygulamanın işlerini ufak görevlere ayıralım'),
 ('kod çalışmıyor', 'yazdığım uygulamayı çalıştırmayı başaramadım'),
 ('hata mesajını nasıl okuyayım', 'traceback içindeki satırları nasıl yorumlayacağım'),
 ('kod çalıştı', 'nihayet uygulamadaki sorunu giderdim'),
 ('yanlış anladın', 'söylemeye çalıştığım şeyi farklı anlamışsın'),
]


def build():
    def read(name):
        return [json.loads(s) for s in (ROOT/'training'/name).read_text('utf-8').splitlines() if s.strip()]
    rows = {normalize(p['question']):p for p in read('understanding-training.jsonl')}
    probes = [{'question':q, 'answer':rows[normalize(key)]['answer']} for key,q in PROBES]
    frozen = probes + sum([read(n) for n in ('heldout.jsonl','dialogue-heldout.jsonl','growth-heldout.jsonl','understanding-probes.jsonl')], [])
    forbidden = {normalize(p['question']) for p in frozen}
    for canonical, aliases in ALIASES.items():
        answer = rows[normalize(canonical)]['answer']
        for text in aliases:
            for q in (text, fold(text)):
                key = normalize(q)
                if key in forbidden:
                    raise ValueError('Training/evaluation overlap')
                if key in rows and rows[key]['answer'] != answer:
                    raise ValueError('Conflicting answer')
                rows[key] = {'question':q,'answer':answer}
    for name, data in [('natural-training.jsonl',list(rows.values())),('natural-probes.jsonl',probes)]:
        path = ROOT/'training'/name
        content = ''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in data)
        if 'probes' in name and path.exists() and path.read_text('utf-8') != content:
            raise ValueError('Refusing to replace frozen probes')
        path.write_text(content,'utf-8')
    print(json.dumps({'questions':len(rows),'probes':len(probes)}))


if __name__ == '__main__':
    build()
