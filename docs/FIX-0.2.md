# Terra 0.2 düzeltmesi

Varsayılan model artık `models/terra-chat.pt`: 30 küçük soru-cevap örneğiyle,
rastgele ağırlıklardan 1600 adım eğitim. Eğitim yöntemi tam örnekler üzerinde,
sadece yanıt kısmında hesaplanan kayıptır. Bağlam 512 bayt-token.

`merhaba`, `hello`, `selam`, `nasılsın`, `sen kimsin`, `eğitim nedir` gibi
öğretilmiş soruları destekler. Büyük/küçük harf, boşluk ve noktalama normalize edilir.
Sohbet geçmişi modele eklenmez; bu aşama tek mesajlık örnekleri destekler.

Yanıt gerçekten modelden üretilir (deterministik çözümleme). Ardından öğretilen
metinle eşleşmesi kontrol edilir. Eşleşmeyen çıktı yerine model yanıtı uydurulmaz;
Uygulama etiketiyle başarısızlık bildirimi gösterilir. Öğretilmemiş sorulara yine
Uygulama etiketiyle kapsam bildirimi verilir. Bu yaklaşım genel bir sohbet çözümü
veya olgusal doğruluk denetimi değildir; bozuk çıktıyı kullanıcıya cevap diye sunmaz.

Gerçek ağırlıklarla test: 30/30 eğitim örneği tam eşleşti. Bu sonuç ezberlenen
örnekleri yeniden üretme ölçümüdür, görülmemiş sorularda genelleme kanıtı değildir.
Tam çıktılar `data/chat-evaluation.json`; 36 birim/lifecycle testi geçti.

Yeniden eğitim ve ölçüm (geliştirici):

```powershell
.\.venv\Scripts\python.exe training/make_conversation.py
.\.venv\Scripts\python.exe -m scratch.train_chat --steps 1600
.\.venv\Scripts\python.exe -m tests.evaluate_chat
```

Atölyedeki eski serbest metin deneyi ayrı bir eğitim yöntemidir; bu sohbet
modelinin tam soru-cevap eğitimini sürdürmez. Eski ağırlıklar silinmedi.
API, Ollama veya başka hazır model eklenmedi. Gönder düğmeleri küçük pencerede
görünür kalacak şekilde yerleşim düzeltildi. Varsayılan modele geçiş için uygulamayı
kapatıp Baslat.vbs ile yeniden aç. Yeni pencere başlığında 0.2 yazar.
