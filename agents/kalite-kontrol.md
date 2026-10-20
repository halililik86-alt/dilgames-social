# Ajan: Kalite Kontrol

Görev: haftalık üretimin açtığı **"Onay: reels-…"** PR'ındaki her videoyu kontrol edip PR'a tek bir yorum bırakmak.

## Adımlar
1. Açık PR'lar arasında başlığı `Onay: reels-` ile başlayanı bul (`gh pr list --state open`). Yoksa "kontrol edilecek üretim yok" diye bitir. PR'da zaten senin bıraktığın "Kalite kontrol" yorumu varsa tekrar yorum yapma.
2. PR açıklamasındaki Release etiketinden videoları indir: `gh release download <etiket> -p '*.mp4' -D /tmp/qa`.
3. Her video için `python3 scripts/qa_sheet.py /tmp/qa/<id>.mp4 /tmp/qa` çalıştır. JSON'daki `auto_issues`'u not et, ardından oluşan `_sheet.png` paftasını **görsel olarak incele**:
   - 0–4 sn: kanca yazısı okunuyor mu, kesik/taşma var mı?
   - Sırasıyla "Hikâyeyi dinle", "Kelimeyi eşleştir", "Balonları birleştir", "Çalkala", "Cümleyi tamamla", "Bölüm tamam" sahneleri ve kapanış kartı var mı?
   - Oyun ekranında hata mesajı, boş havuz, yanlış seviye, rehber balonunun sahneyi kapatması var mı?
   - Paylaşım metni (`content/reels/<id>.json → caption`) videodaki hikâyeyle uyumlu mu? Meydan okumadaki cümle videoda gerçekten geçiyor mu (`intro_text`)?
4. PR'a yorum yaz (`gh pr comment`): başlık `## Kalite kontrol`, her reel için ✅ / ⚠️ / ❌ ve kısa gerekçe. ❌ olan için öneri: dosyada `status` → `planned` yap (yayından çıkar) ya da `record.pack` değiştirip `build-reels.yml`'i `only=<id>` ile yeniden çalıştır.

## Yapma
- PR'ı birleştirme veya kapatma, dosya değiştirme, yeniden üretim tetikleme. Sadece yorum.
