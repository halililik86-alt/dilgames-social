# dilgames-social — Claude için notlar

- Dil: Türkçe. Kullanıcı DilGames'in geliştiricisi.
- Bu repo yalnızca kendi Instagram hesabına içerik üretir/yayınlar ve istatistik okur. Takip/beğeni/yorum/DM otomasyonu ekleme; resmi olmayan Instagram kütüphaneleri (instagrapi vb.) kullanma.
- Ses ilkesi: gerçek insan kaydı yok. Oyun kayıtlarında oyunun kendi sesleri + efektleri + sentez geçiş sesi. AI seslendirme yalnızca ElevenLabs resmi API'siyle (`scripts/tts.py`, `tts/**` dalına itilen `tts/requests/*.json` → `.github/workflows/tts.yml`, anahtar yalnızca `ELEVENLABS_API_KEY` secret'ında). Kazalar serisinde oyun müziği kullanılmaz; müzik/efekt ElevenLabs'ten üretilir.
- Türk İngilizcesi Kazaları (`type: kaza`, `scripts/build_kaza_reel.py`): 3B animasyon (Renderforest ücretsiz model, Elif için referans görsel https://halililik86-alt.github.io/media/elif.jpg), sesler ElevenLabs `eleven_v3`.
- Yeni reel = `content/reels/<YYYY-AA-GG>-<seviye>-<hikâye>.json`, `status: planned`. Hashtag ≤ 5.
- Yayın yalnızca onay PR'ı main'e birleştirildikten sonra olur; bu güvenceyi zayıflatma.
- Oyun kaydı oyunun dosyalarını değiştirmez; motor erişimi `record.cjs` içinde tarayıcıda yapılan yamayla sağlanır. Oyunun derlemesi değişip kanca bulunamazsa `HOOK` regex'ini güncelle.
- Kayıt botu ipucu hakkı harcamamak için `world.hint()` kullanmaz; eşleşmeyi `world.match()` ile bulur.
- Zamanlanmış bir ajan olarak çalışıyorsan önce `agents/README.md`, sonra sana verilen talimat dosyasını oku; secret'lara ve Instagram'a erişmeye çalışma.
