# Terra 0.3 — soru eşleştirme ve kısa sohbet takibi

Bu sürüm mevcut kendi model ağırlıklarını kullanır; yeniden eğitim veya başka bir modele geçiş yapılmadı.

- Soru tam eşleşmiyorsa yerel TF-IDF karakter/kelime benzerliği denenir.
- Eşik ve farklı yanıt grupları arasında fark kontrolü uygulanır. Sayılar, operatörler,
  bileşik ve bazı olumsuz sorular yaklaşık eşleştirmeden hariç tutulur.
- Eşleştirilen öğretilmiş soru ekranda gösterilir. Yanıt yine sinir ağı tarafından
  üretilir ve beklenen eğitim yanıtıyla doğrulanır; hazır yanıtın kopyası döndürülmez.
- Bu yöntem anlamsal anlama veya genel doğruluk garantisi değildir. Benzerlik
  yanlış yorumlanabilir; örnek eşleştirmesi kullanıcının incelemesi için görünür tutulur.
- Uygulama son başarıyla yanıtlanan konuyu oturum belleğinde tutar. Tekrar anlat,
  bir daha açıkla ve anlamadım ifadeleri aynı yanıtı yeniden ürettirir.
- Peki fonksiyon? gibi kısa takip ifadelerinde açıklama sorusu tamamlanır.
  Bu özellik uygulama kurallarıdır; modelin serbest sohbet belleği değildir.
- Desteklenmeyen konu ve Sohbeti temizle, eski konuya yanlış dönüşü önlemek için
  takip bağlamını temizler. Geçmiş diske veya dış servise gönderilmez.
- Model oturumda bir kez yüklenir; dosya, boyut veya değiştirilme zamanı değişince
  yeniden yüklenir. Bu sırada eski modelin takip bağlamı kullanılmaz.

Kontrol: 45 birim/lifecycle testi geçti. Gerçek model ağırlıklarıyla 8 farklı
soru biçiminin 6'sı doğru yanıtlandı, 15 kapsam dışı soru reddedildi, 5 eski soru
ve 2 bağlam kontrolü geçti. Ham sonuç: data/dialogue-audit.json.
Bu küçük geliştirme örneklemi bir genel zekâ ölçümü değildir. Önceki ham modelin
2/10 sonucu ile yeni uygulamanın eşleştirme puanı aynı ölçüm değildir.

Deneme:
1. Bir değişkeni anlatır mısın
2. Tekrar anlat
3. Peki fonksiyon?

Baslat.vbs ile açılır; pencere başlığında 0.3 yazar.
