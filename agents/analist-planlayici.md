# Ajan: Analist + Planlayıcı

Görev: geçen haftanın sonuçlarını yorumla, önümüzdeki haftanın 4 Reels'ini planla ve **tek bir PR** aç.

## Girdiler
- `reports/` içindeki en yeni rapor (yoksa ilk hafta: analiz bölümünü "henüz veri yok" diye geç)
- `content/reels/*.json`: geçmiş reel'ler (`status`, `pillar`, `hook`, `insights`, `intro_text`)
- `content/plan/strateji.md`, `config/catalog.json`, `config/brand.json`

## Adımlar
1. Tarihleri hesapla (Europe/Istanbul). "Hafta" = gelecek pazartesiden başlayan 7 gün. Yayın günleri: **salı, perşembe, cumartesi, pazartesi (bir sonraki)** saat **20:30**. O tarihlerde zaten reel dosyası varsa onları sayıya dahil et, eksik olanları tamamla (toplam 4).
2. **Analiz** (veri varsa): reel başına izlenme, erişim, kayıt, paylaşım, ortalama izleme süresi. En iyi ve en zayıf sütunu/kancayı bul. 3–5 maddelik, somut öneri yaz (ör. "meydan okuma formatı 2 kat kayıt aldı → bu hafta 2 tane"). Bunu en yeni rapor dosyasının sonuna `## Analist yorumu` başlığıyla ekle.
3. **Plan**: 4 yeni `content/reels/<YYYY-AA-GG>-<seviye>-<hikâye-slug>.json` dosyası yaz. Şema için README'deki örneğe ve mevcut dosyalara bak. Kurallar:
   - `status: "planned"`, `publish_at` ISO biçiminde `+03:00` ile.
   - `record`: `catalog.json`'daki bir sekme + paket (premium hariç), `level: 1`. Son 4 haftada kullanılmış sekme/paket ikilisini tekrar etme; seviyeleri karıştır (her hafta en az bir A1/A2 ve bir B1+).
   - Sütun dağılımı stratejiye ve analize göre; varsayılan: tanıtım, meydan okuma, seviye, alışkanlık.
   - `hook.lines`: en fazla 3 satır, satır başına en fazla ~16 karakter, Türkçe, merak uyandıran.
   - `caption`: ilk satır kanca, sonra 1–2 cümle, son satır soru/çağrı. Uygulama hakkında doğrulanmamış iddia (indirme sayısı, ödül, "ücretsiz" vb.) yazma.
   - `hashtags`: en fazla 5.
   - **Meydan okuma** formatında boşluk doldurma cümlesi yalnızca `catalog.json → known_level1_sentences` ya da geçmiş reel'lerdeki `intro_text` içinde geçen **gerçek** bir cümleden alınır. Cümlesi bilinmeyen paket için meydan okuma yazma.
4. `python3 -c` ile her yeni JSON'un geçerli olduğunu ve hashtag ≤ 5 olduğunu doğrula.
5. Dal: `plan/<YYYY>-W<hafta>`. Commit mesajı ve PR başlığı: `Plan: <ilk yayın tarihi> haftası`. PR açıklamasında: analiz özeti, 4 reel'in tablosu (tarih, sütun, sekme/paket, kanca), ve "Pazartesi 08:00'den önce birleştirilirse o hafta üretilir" notu.

## Yapma
- PR'ı birleştirme, mevcut `approved`/`published` reel'leri değiştirme, iş akışı dosyalarına dokunma.
