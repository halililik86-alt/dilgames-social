# dilgames-social — Claude için notlar

- Dil: Türkçe. Kullanıcı DilGames'in geliştiricisi.
- Bu repo yalnızca kendi Instagram hesabına içerik üretir/yayınlar ve istatistik okur. Takip/beğeni/yorum/DM otomasyonu ekleme; resmi olmayan Instagram kütüphaneleri (instagrapi vb.) kullanma.
- Ses ilkesi: insan seslendirmesi yok. Oyunun kendi sesleri + oyunun efekt dosyaları + sentez geçiş sesi.
- Yeni reel = `content/reels/<YYYY-AA-GG>-<seviye>-<hikâye>.json`, `status: planned`. Hashtag ≤ 5.
- Yayın yalnızca onay PR'ı main'e birleştirildikten sonra olur; bu güvenceyi zayıflatma.
- Oyun kaydı oyunun dosyalarını değiştirmez; motor erişimi `record.cjs` içinde tarayıcıda yapılan yamayla sağlanır. Oyunun derlemesi değişip kanca bulunamazsa `HOOK` regex'ini güncelle.
- Kayıt botu ipucu hakkı harcamamak için `world.hint()` kullanmaz; eşleşmeyi `world.match()` ile bulur.
