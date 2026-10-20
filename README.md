# dilgames-social

DilGames'in Instagram içerik hattı. Oyundan gerçek oynanış kaydı alır, 9:16 Reels kurgular, haftalık onay PR'ı açar ve onaylanan videoları takvimdeki saatte **resmi Instagram Graph API** ile yayınlar. Pazar akşamları da haftalık istatistik raporu yazar.

Bu repo yalnızca **kendi hesabımıza içerik yayınlar ve kendi istatistiklerimizi okur**. Takip etme, beğenme, yorum/DM gönderme gibi etkileşim otomasyonu **bilerek yoktur**: Instagram kurallarına aykırıdır ve hesabı riske atar.

## Akış

```
content/reels/*.json  (planned)
        │  her pazartesi 08:00 — build-reels.yml
        ▼
oyun derlenir → bot bölümü oynar, ekran+ses kaydı → build_reel.py ile kurgu
        │
        ▼
GitHub Release (reels-YYYYMMDD-HHMM): mp4 + kapak + paylaşım metni
Onay PR'ı: reel dosyaları "approved"
        │  sen PR'ı inceleyip birleştirirsin (merge = onay)
        ▼
publish.yml (yarım saatte bir): saati gelen onaylı reel'i yayınlar → status "published"
        │
        ▼
report.yml (pazar 19:00): izlenme, erişim, kayıt, paylaşım… → reports/YYYY-Www.md
```

PR birleştirilmeden hiçbir şey yayınlanmaz. Bir reel'i yayından çıkarmak için PR'da dosyasındaki `status` değerini `planned` yap.

## Reel dosyası

```json
{
  "id": "2026-10-29-a2-sehirde-bir-gun",
  "publish_at": "2026-10-29T20:30:00+03:00",
  "pillar": "meydan okuma",
  "record": {"tab": "A2 Elementary", "pack": 0, "level": 1},
  "hook": {"lines": ["Bu cümleyi", "kurabilir", "misin?"]},
  "captions": {"complete": ["CEVAP", "Cümleyi tamamla, sesli dinle"]},
  "caption": "Paylaşım metni…",
  "hashtags": ["#ingilizce", "#ingilizceöğren"],
  "status": "planned"
}
```

- `record.tab`: Hikâyeler ekranındaki seviye sekmesi (A1…C2). `pack`: o sekmedeki kartın sırası (0'dan başlar). `level`: bölüm (yeni kullanıcıda yalnızca 1 açıktır).
- `captions`: sahne başlıklarını değiştirir (`intro`, `vocab`, `merge`, `stir`, `complete`, `win`). Varsayılanlar `config/brand.json` içinde.
- `hook.clip`: açılış klibi (varsayılan `assets/hook/bubbles-rise.mp4`, Renderforest'ta üretildi).
- Hashtag sayısı Instagram kuralı gereği en fazla 5'tir; fazlası kesilir.
- Sahneler kayıttaki olaylardan otomatik seçilir. Gerekirse `"segments": [{"kind":"vocab","start":17.6,"end":22.9}, …]` ile elle verilebilir.

## Ses ilkesi

İnsan seslendirmesi yok. Kullanılan sesler: oyunun kendi müziği, kayıttaki oyun sesleri (balon, birleşme, girdap, cümle okumaları, bölüm sonu), oyunun efekt dosyaları ve sentezlenmiş yumuşak bir geçiş sesi.

## Kurulum (bir kez)

### 1. GitHub ayarları
- **Settings → Actions → General → Workflow permissions:** "Read and write permissions" ve **"Allow GitHub Actions to create and approve pull requests"** açık olmalı.
- **Secrets → Actions → `GAME_REPO_TOKEN`:** oyunun reposunu (`halililik86-alt/dilgame`) okuyabilen ince ayarlı (fine-grained) PAT. İzin: yalnızca o repo, *Contents: Read-only*.

### 2. Instagram bağlantısı (önerilen: `facebook` modu)
Bu modda video doğrudan Meta'ya yüklenir, herkese açık bir barındırma gerekmez. Uzun ömürlü sayfa anahtarı süresiz olduğu için yenileme de gerekmez.

1. Instagram hesabı **İşletme/İçerik Üreticisi** olmalı ve bir **Facebook Sayfasına bağlı** olmalı (Instagram → Ayarlar → Hesap merkezi).
2. [developers.facebook.com](https://developers.facebook.com) → **Uygulama oluştur** → tür: *İşletme*. Ürün olarak **Instagram** (Facebook Login for Business ile) ekle.
3. İzinler: `instagram_basic`, `instagram_content_publish`, `instagram_manage_insights`, `pages_show_list`, `pages_read_engagement`. Uygulama *geliştirme* modunda kalabilir; hesap sahibi sen olduğun için uygulama incelemesi gerekmez.
4. **Graph API Explorer**'da kendi uygulamanı seç, bu izinlerle kullanıcı anahtarı al → uzun ömürlüye çevir → `/me/accounts` ile sayfanın **uzun ömürlü sayfa anahtarını** al. `/{sayfa-id}?fields=instagram_business_account` ile **Instagram kullanıcı kimliğini** al.
5. Repo → Settings → Secrets → Actions:
   - `IG_ACCESS_TOKEN` = sayfa anahtarı
   - `IG_USER_ID` = Instagram kullanıcı kimliği
6. Deneme: Actions → "Zamanı gelen Reels'i yayınla" → *Run workflow* → **dry_run** işaretli.

> Alternatif `instagram` modu (Facebook Sayfası olmadan): Variables'ta `IG_MODE=instagram`. Bu modda Meta videoyu herkese açık bir adresten çeker (`PUBLIC_MEDIA_BASE` gerekir) ve anahtar 60 günde bir yenilenmelidir (`refresh-token.yml`, `ADMIN_TOKEN` ister).

## Yerelde çalıştırma

```bash
# oyunun derlenmiş halini sun
(cd ../dilgame/dist && python3 -m http.server 5191 &)
npm install --no-save playwright && npx playwright install chromium
PLAYWRIGHT_MODULE=$PWD/node_modules/playwright GAME_DIST=../dilgame/dist \
  python3 scripts/produce.py --only 2026-10-29-a2-sehirde-bir-gun
# → out/<id>.mp4, out/<id>.jpg, out/<id>.txt

python3 scripts/ig.py whoami            # bağlantıyı dene
python3 scripts/ig.py limit             # 24 saatlik yayın kotası
python3 scripts/ig.py publish-reel out/x.mp4 out/x.txt --dry-run
```

## Dosyalar

| Yol | Ne yapar |
|---|---|
| `scripts/record.cjs`, `bot.cjs`, `audiohook.js` | Oyunu tarayıcıda açar, bölümü oynar, ekran + oyun sesini kaydeder. Oyunun dosyalarına dokunmaz. |
| `scripts/build_reel.py` | Kanca, sahne başlıkları, telefon çerçevesi, geçişler, kapanış kartı ve ses miksi |
| `scripts/produce.py` | Takvimdeki planlı reel'leri sırayla üretir |
| `scripts/ig.py` | Resmi Graph API: yayın, kota, istatistik, anahtar yenileme |
| `scripts/publish_due.py`, `report.py` | Zamanlanmış yayın ve haftalık rapor |
| `content/plan/strateji.md` | İçerik sütunları, ritim, elle yapılacak işler |
| `config/brand.json` | Renkler, yazılar, varsayılan sahne başlıkları |
