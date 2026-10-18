"""Self-authored Turkish teaching data. No downloaded weights or personal data."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scratch.conversation import normalize
from scratch.routing import fold


def read(name):
    return [json.loads(s) for s in (ROOT/'training'/name).read_text('utf-8').splitlines() if s.strip()]


def write(name, rows):
    (ROOT/'training'/name).write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), 'utf-8')


# Freeze these before training. These are a small development set, not a general benchmark.
PROBES = [
    ('değişken', 'değişken dediğin şeyi anlatabilir misin'),
    ('fonksiyon', 'fonksiyon konusunda biraz bilgi istiyorum'),
    ('döngü', 'döngü tam olarak ne anlama geliyor'),
    ('liste', 'liste konusunu bana açıklayabilir misin acaba'),
    ('json', 'json hakkında kısa bilgi verir misin'),
    ('css', 'css denilen şey ne işe yarar'),
    ('html', 'html konusunda bir açıklama yapar mısın'),
    ('git', 'git tam olarak nedir acaba'),
    ('api', 'api kavramını anlatmanı istiyorum'),
    ('python', 'python ne demek biraz anlatsana'),
    ('değişken', 'degisken nedir acaba'),
    ('fonksiyon', 'fonksiyon ne ise yariyo'),
    ('döngü', 'donguyu bana anlat'),
    ('liste', 'listeyi aciklayabilir misin'),
    ('json', 'json tam olarak nasil bir sey'),
    ('css', 'bana css konusundan bahsetsene'),
    ('html', 'html ne ise yariyor acaba'),
    ('git', 'git hakkinda konusabilir miyiz'),
    ('api', 'apiyi bana anlatir misin'),
    ('python', 'python konusunu ogrenmek istiyorum'),
]

SIMPLE = {
    'değişken': 'Değişkeni, bir değere taktığın isim gibi düşün. Mesela puan = 10 yazınca puan adı 10 değerini gösterir. print(puan) ekrana 10 yazar. puan = 20 dersen aynı isim artık 20 değerini gösterir.',
    'fonksiyon': 'Fonksiyon, tekrar kullanabileceğin küçük bir kod parçasıdır. Mesela def iki_kati(sayi): satırının altına girintili olarak return sayi * 2 yazarsın. iki_kati(4) çağrısı 8 döndürür. Böylece aynı işlemi farklı sayılarla kullanırsın.',
    'döngü': 'Döngü aynı işi birkaç kez yapar. for i in range(3): satırının altına girintili print(i) yazarsan ekranda sırayla 0, 1 ve 2 görünür. print satırını üç kez yazmak yerine döngü kullanmış olursun.',
    'liste': 'Listeyi sıralı bir alışveriş listesi gibi düşün. urunler = ["ekmek", "sut"] iki öğe tutar. urunler[0] ilk öğeyi, yani "ekmek" değerini verir. Python listelerinde ilk sıra numarası 0 olur.',
    'json': 'JSON veriyi metin içinde düzenli tutar. {"ad": "Ada", "yas": 18} örneğinde ad ve yas anahtardır; Ada ve 18 onların değerleridir. JSON tek başına program çalıştırmaz, veri taşır.',
    'css': 'HTML sayfaya bir başlık koyar; CSS onun nasıl görüneceğini belirler. Örneğin h1 { color: green; } kuralı h1 başlıklarını yeşil yapar. CSS ile boşlukları ve sayfa yerleşimini de ayarlarsın.',
    'html': 'HTML sayfanın parçalarını belirtir. <h1>Merhaba</h1> bir başlık, <p>Bir paragraf.</p> bir paragraf oluşturur. Bunların rengini ve yerleşimini değiştirmek için CSS ekleyebilirsin.',
    'git': 'Git projendeki değişikliklerin geçmişini tutar. Bir aşamayı commit ile kaydedersin; sonra neyi değiştirdiğini karşılaştırabilirsin. Git yerelde çalışabilir. Başka bir yere yedek almak için ayrıca bir uzak depo gerekir.',
    'api': 'API iki programın konuşması için belirlenen kurallardır. Bir uygulama hava durumu servisine şehir adını gönderir, servis sıcaklık verisini döndürür. Hangi isteğin gönderileceğini ve yanıtın biçimini API belirler.',
    'python': 'Python bir programlama dilidir. print("Merhaba") kodu ekrana Merhaba yazar. Küçük betikler, veri işlemleri ve uygulamalar yazabilirsin. Kod blokları girintiyle ayrılır; bu yüzden satır başındaki boşluklar önemlidir.',
}


def main():
    base = read('augmented.jsonl')
    by_question = {normalize(r['question']):r for r in base}
    probes = [{'question':query, 'answer':by_question[topic+' nedir']['answer']} for topic,query in PROBES]
    frozen = read('heldout.jsonl') + probes
    forbidden = {normalize(r['question']) for r in frozen}
    rows = {}
    def add(q, answer):
        key = normalize(q)
        if key not in forbidden:
            if key in rows and rows[key]['answer'] != answer:
                raise ValueError('Conflicting training question: '+q)
            rows.setdefault(key, {'question':q, 'answer':answer})
    for row in base:
        add(row['question'], row['answer'])
    templates = ['{} nedir acaba', '{} ne işe yarıyor', '{} ne işe yarar',
                 '{} konusunu anlatır mısın', '{} hakkında bilgi verir misin',
                 '{} kavramını açıklar mısın', '{} tam olarak ne demek',
                 '{} konusunda konuşalım', '{} öğrenmek istiyorum',
                 '{} nedir basitçe anlat', 'bana {} anlatabilir misin',
                 '{} ne demek ya', '{} nedir kısaca açıkla', '{} hakkında konuşabilir miyiz']
    for row in base:
        q = normalize(row['question'])
        if not q.endswith(' nedir'):
            continue
        topic = q[:-6]
        for template in templates:
            query = template.format(topic)
            add(query, row['answer'])
            add(fold(query), row['answer'])
    links = {}
    for topic, answer in SIMPLE.items():
        target = topic+' için daha sade açıklama'
        add(target, answer)
        add(topic+' için örnek ver', answer)
        add(topic+' örnekle anlat', answer)
        add(fold(target), answer)
        base_answer = by_question[topic+' nedir']['answer']
        for row in list(rows.values()):
            if row['answer'] == base_answer:
                links[normalize(row['question'])] = target
    write('dialogue-heldout.jsonl', probes)
    write('dialogue-training.jsonl', list(rows.values()))
    (ROOT/'training/dialogue-links.json').write_text(json.dumps(links, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'training':len(rows), 'new_development':len(probes), 'followup_links':len(links)}))


if __name__ == '__main__':
    main()
