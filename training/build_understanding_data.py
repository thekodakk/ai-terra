"""Broader self-authored phrasings; all previous evaluation files stay frozen."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scratch.conversation import normalize
from scratch.routing import fold

ALIASES = {
 'çok yoruldum': ['enerjim kalmadı','kendimi yorgun hissediyorum','bugün hiç halim yok','çok yorgun hissediyorum','bu akşam yorgunum','yoruldum biraz','bütün gün yoruldum','yorgunluktan bir şey yapasım yok'],
 'ne yapacağımı bilmiyorum': ['neyle uğraşacağımı seçemiyorum','bir şey yapasım var ama ne bilmiyorum','karar veremiyorum ne yapsam','ne yapayım şimdi','hangi işle uğraşsam','kendime bir uğraş bulamıyorum','yapacak iş seçemedim','bir fikir bulmakta zorlanıyorum'],
 'bir şey öğrenmek istiyorum': ['yeni şeyler öğrenesim var','öğrenmek istiyorum','bir konu öğrenelim','yeni bir şey öğrenmek isterim','bugün öğrenmeye zaman ayırmak istiyorum','bir şeyler öğrenesim geldi','öğrenebileceğim bir şey seçelim','bilmediğim bir konuya bakalım'],
 'dinlenmek istiyorum': ['dinlenesim var','mola vermek istiyorum','şimdi ara veriyorum','biraz dinlenmeye ihtiyacım var','ekrandan uzaklaşacağım','bir süre dinleneyim','bugün mola vermek istiyorum','kendime kısa bir ara vereceğim'],
 'küçük bir şey üretmek istiyorum': ['ufak bir proje geliştirelim','küçük bir uygulama yapmak istiyorum','bir şey geliştirmek istiyorum','basit bir proje seçelim','ufak bir şey yapalım','üretebileceğim küçük bir iş arıyorum','mini proje fikri ver','bir uygulamanın ilk sürümünü yapalım'],
 'başlamak zor geliyor': ['başlamayı erteliyorum','ilk adımı atamıyorum','başlamak istesem de zorlanıyorum','yapacağım iş gözümde büyüyor','işe başlama konusunda takıldım','başlamak istiyorum ama zor geliyor','nereden başlayacağımı düşünürken duruyorum','bir türlü ilk adımı atamadım'],
 'ders çalışma planı yap': ['derslerimi planlamak istiyorum','ders çalışmayı nasıl planlayayım','konuları hangi sırayla çalışayım','okul dersleri için program yap','çalışma düzeni kurmak istiyorum','dersler için zamanımı nasıl ayırayım','derslerimi nasıl düzenleyeyim','çalışacağım konuları planlayalım'],
 'projemi nasıl böleyim': ['projeyi nereden başlatayım','büyük projeyi küçük işlere böl','projeyi nasıl parçalara ayırırım','büyük bir projede ilk adım ne olmalı','projeye nereden girişeyim','projenin başlangıcını planla','uygulamayı küçük adımlarla yapmak istiyorum','kapsamlı bir projeye nasıl girişilir'],
 'kod çalışmıyor': ['yazdığım kod çalışmıyor','programım çalışmayı reddediyor','kodum bir türlü çalışmadı','programı başlatınca hata oluyor','uygulamam hata veriyor','programı çalıştıramadım','kodda hata alıyorum','programın çalışmasında sorun var'],
 'hata mesajını nasıl okuyayım': ['hata çıktısını nasıl inceleyeyim','traceback çıktısında nereye bakılır','hata yazısında önemli kısım neresi','hata mesajındaki hangi satır önemli','hata raporunu okumayı anlat','kodun hata çıktısını anlamıyorum','traceback satırları ne anlatıyor','hata çıktısını nereden okumalıyım'],
 'kod çalıştı': ['programı çalıştırmayı başardım','artık kodum çalışıyor','sorunu giderdim','kodun hatası düzeldi','program artık açılıyor','nihayet kod çalışıyor','uygulamadaki hatayı çözdüm','çalışmayan kodu düzelttim'],
 'yanlış anladın': ['beni doğru anlamadın','demek istediğim farklıydı','bunu kastetmiyordum','anlatmak istediğim bu değil','söylediğim şeyi başka anladın','öyle demek istemedim','sorumu farklı yorumladın','beni anlamakta yanıldın'],
 'cevabın yanlış': ['yanıtında hata var','söylediğin bilgi doğru değil','cevabın doğru görünmüyor','verdiğin bilgide yanlışlık var','bu yanıtı yanlış buluyorum','cevapta bir hata olduğunu düşünüyorum','söylediğin doğru değil','yanıtın hatalı'],
 'başka konuya geçelim': ['bu konuyu bırakalım','farklı bir konu konuşalım','başka bir konudan bahsedelim','konuştuğumuz konuyu değiştirelim','bu konu yerine başka şey konuşalım','şimdi farklı bir şey soracağım','konu değiştirmek istiyorum','başka bir başlığa geçelim'],
 'yarın devam edelim': ['bugünlük bırakalım','şimdilik burada duralım','yarın kaldığımız yerden sürdürürüz','sonra devam etmek istiyorum','bugün bitirelim yarın bakalım','çalışmaya daha sonra devam ederiz','bu işi sonraya bırakalım','bugün ara verip sonra sürdürürüz'],
 'yeni bilgi öğreniyor musun': ['ben yazınca öğreniyor musun','sohbetten kendini eğitir misin','mesajlaşırken model değişiyor mu','her mesajım seni eğitir mi','yazdığım şeyler ağırlıklarına işlenir mi','benimle konuşarak kendini geliştiriyor musun','sohbette söylediklerim eğitim sayılır mı','konuşma sırasında öğrenme oluyor mu'],
 'kaç parametren var': ['toplam parametren kaç','modelindeki parametre sayısı ne','sen kaç parametresin','parametre adedini söyle','kaç tane ağırlığın var','modelin kaç parametreden oluşuyor','ne kadar parametren bulunuyor','modelinin boyutu kaç parametre'],
 'cevaplarını nereden alıyorsun': ['cevapları nasıl üretiyorsun','yanıtların nasıl oluşuyor','bu cevapları hangi yöntemle yazıyorsun','cevabı model mi üretiyor','yazdıklarını nereden getiriyorsun','hazır yanıtı mı kopyalıyorsun','bu uygulama nasıl yanıt oluşturuyor','cevap verme yöntemin ne'],
}

# New probes are written before training and are not used as augmentation inputs.
PROBES = [
 ('çok yoruldum','kendimi bugün epey bitkin hissediyorum'),
 ('ne yapacağımı bilmiyorum','yapacak bir uğraş seçmekte kararsız kaldım'),
 ('bir şey öğrenmek istiyorum','bugün yeni bir konu öğrenmeyi düşünüyorum'),
 ('dinlenmek istiyorum','bir müddet ara verip dinleneyim diyorum'),
 ('küçük bir şey üretmek istiyorum','ufacık bir uygulama geliştirmeye ne dersin'),
 ('başlamak zor geliyor','işin ilk adımını sürekli erteliyorum'),
 ('ders çalışma planı yap','derslere çalışacağım zamanı düzenlememe yardım et'),
 ('projemi nasıl böleyim','yapacağım uygulamayı ufak adımlara ayırmak istiyorum'),
 ('kod çalışmıyor','bu yazdığım kodda çalıştırma sorunu yaşıyorum'),
 ('hata mesajını nasıl okuyayım','traceback çıktısını incelemeye nereden başlayayım'),
 ('kod çalıştı','programdaki sorunu sonunda düzelttim'),
 ('yanlış anladın','kastettiğim şeyi başka yorumlamışsın'),
 ('cevabın yanlış','yazdığın yanıtta bir yanlışlık görüyorum'),
 ('başka konuya geçelim','şimdi konuştuğumuz başlığı değiştirmek istiyorum'),
 ('yarın devam edelim','bugün ara verelim kalanına yarın bakalım'),
 ('yeni bilgi öğreniyor musun','sana gönderdiğim mesajlardan ağırlıkların öğrenir mi'),
 ('kaç parametren var','içindeki toplam ağırlık sayısı ne kadar'),
 ('cevaplarını nereden alıyorsun','bu yanıtları ortaya çıkarma yöntemin nasıl'),
]


def main():
    def read(name):
        return [json.loads(s) for s in (ROOT/'training'/name).read_text('utf-8').splitlines() if s.strip()]
    old = read('growth-training.jsonl')
    known = {normalize(p['question']):p for p in old}
    probes = [{'question':q,'answer':known[normalize(key)]['answer']} for key,q in PROBES]
    frozen = probes + sum([read(f) for f in ['heldout.jsonl','dialogue-heldout.jsonl','growth-heldout.jsonl']],[])
    forbidden = {normalize(p['question']) for p in frozen}
    rows = dict(known)
    def add(q,answer):
        key=normalize(q)
        if key in forbidden:
            return
        if key in rows and rows[key]['answer']!=answer:
            raise ValueError('Conflicting question: '+q)
        rows.setdefault(key,{'question':q,'answer':answer})
    for key,aliases in ALIASES.items():
        answer=known[normalize(key)]['answer']
        for query in aliases:
            for text in [query,'terra '+query,query+' ya']:
                add(text,answer)
                add(fold(text),answer)
    # Explain concepts with additional natural question constructions shared
    # across topics. Excluded questions are never taught verbatim.
    for pair in old:
        question=normalize(pair['question'])
        if question.endswith(' nedir'):
            topic=question[:-6]
            for template in ['{} konusu ne anlatıyor','{} kavramından bahseder misin','{} konusunda biraz konuşalım','{} hakkında biraz açıklama yap','{} kavramını anlamak istiyorum']:
                add(template.format(topic),pair['answer'])
                add(fold(template.format(topic)),pair['answer'])
    assert not (set(rows)&forbidden)
    for name,data in [('understanding-training.jsonl',list(rows.values())),('understanding-probes.jsonl',probes)]:
        path=ROOT/'training'/name
        text=''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in data)
        if name.endswith('probes.jsonl') and path.exists() and path.read_text('utf-8')!=text:
            raise ValueError('Frozen probes must not change')
        path.write_text(text,'utf-8')
    print(json.dumps({'training':len(rows),'distinct_answers':len({p['answer'] for p in rows.values()}),'fresh_probes':len(probes)}))


if __name__=='__main__':
    main()
