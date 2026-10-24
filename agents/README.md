# Ajan iş akışı

OpenClaw ya da başka bir ajan çerçevesi kullanılmaz. Ajanlar **Claude zamanlanmış görevleridir**: her çalışmada bu repoyu açan yeni bir Claude oturumu başlar, buradaki talimat dosyasını okur, işini yapar ve sonucu **PR veya PR yorumu** olarak bırakır. Mekanik işleri (kayıt, kurgu, yayın, istatistik) GitHub Actions yapar.

```
Pazar 19:00  report.yml (Actions)          İstatistikleri çeker → reports/YYYY-Www.md
Pazar 19:45  Analist + Planlayıcı (Claude)  Raporu yorumlar, `100k.md` fazına göre haftanın reel'lerini yazar (Faz 1: 7) → "Plan" PR'ı
             ── sen Plan PR'ını birleştirirsin (pazartesi 08:00'den önce) ──
Pzt  08:00   build-reels.yml (Actions)      Planlı reel'leri oyundan kaydeder, kurgular → Release + "Onay" PR'ı
Pzt  10:51   Kalite Kontrol (Claude)        Onay PR'ındaki videoları izler (kare paftası, ses, süre) → PR yorumu
             ── sen Onay PR'ını birleştirirsin ──
Her 10 dk    publish.yml (Actions)          Saati gelen onaylı reel'i resmi Instagram API ile yayınlar
12:54 17:48 20:38  Yayın tetikleyici (Claude)  GitHub zamanlayıcısı saatlerce gecikebildiği için publish.yml'i elle tetikler (yalnızca tetikler)
```

## Kurallar (tüm ajanlar)
- Ajanlar **hiçbir şeyi yayınlamaz** (yayın tetikleyici yalnızca publish.yml'i başlatır; yayınlanan yine yalnızca main'de onaylı reel'lerdir), PR birleştirmez, secret okumaz/yazmaz, Instagram'a ya da Meta'ya bağlanmaz.
- Her çıktı insan onayından geçer: Plan PR'ı ve Onay PR'ı.
- Dil Türkçe. `content/plan/strateji.md`, `config/brand.json` ve `config/catalog.json` esas alınır.
- Takip/beğeni/yorum/DM otomasyonu önerilmez ve yazılmaz.

| Ajan | Talimat | Ne zaman |
|---|---|---|
| Analist + Planlayıcı | `agents/analist-planlayici.md` | Pazar 20:00 (TR) |
| Kalite Kontrol | `agents/kalite-kontrol.md` | Pazartesi 11:00 (TR) |
