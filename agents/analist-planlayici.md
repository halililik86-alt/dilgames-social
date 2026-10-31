# Ajan: Analist + Planlayıcı

Görev: geçen haftanın sonuçlarını yorumla, önümüzdeki haftanın Reels'lerini **`content/plan/100k.md`'deki faza göre** planla ve **tek bir PR** aç.

## Girdiler
- `reports/` içindeki en yeni rapor (yoksa ilk hafta: analiz bölümünü "henüz veri yok" diye geç)
- `content/reels/*.json`: geçmiş reel'ler (`status`, `pillar`, `hook`, `insights`, `intro_text`)
- `content/plan/100k.md` (ana plan: fazlar, formatlar, eşikler), `content/plan/strateji.md`, `config/catalog.json`, `config/brand.json`

## Adımlar
1. **Fazı belirle**: en yeni rapordaki takipçi sayısına ve `100k.md`'deki fazlara bak. Rapor yoksa Faz 1.
2. Tarihleri hesapla (Europe/Istanbul). "Hafta" = gelecek pazartesiden başlayan 7 gün. **Faz 1'de her gün 1 Reel** (7 adet). Saat: **11:48 / 16:48 / 21:48** (öğle Bir Harfin Hikâyesi, akşamüstü Deyim Düellosu, akşam Kazalar). **Tam saat ve buçuk kullanma** (ör. 13:00, 20:30): dakikayı 7–23 veya 37–53 arasından seç. O tarihlerde zaten reel dosyası varsa onları sayıya dahil et, eksikleri tamamla.
3. **Analiz** (veri varsa): reel başına paylaşım/erişim, kayıt/erişim, izleme oranı, izlenme; format ve saat bazında ortalamalar. `100k.md`'deki eşiklerle karşılaştır. En iyi ve en zayıf formatı/kancayı/saati bul. 3–5 maddelik **somut** öneri yaz ve bu haftanın planına uygula. Bunu en yeni rapor dosyasının sonuna `## Analist yorumu` başlığıyla ekle.
4. **Plan**: eksik günler için `content/reels/<YYYY-AA-GG>-<seviye>-<hikâye-slug>.json` yaz. Şema için README'deki örneğe ve mevcut dosyalara bak. Kurallar:
   - `status: "planned"`, `publish_at` ISO biçiminde `+03:00` ile, `format`: `100k.md`'deki kod (F1, F2, F4, F5, F6…), `pillar`: kısa Türkçe ad.
   - D1 (Deyim Düellosu) bölümleri AI kredisi gerektirir; **sen D1 planlama**, yalnızca mevcut D1 dosyalarını ve sonuçlarını analizde kullan. Yeni D1 fikirlerini PR açıklamasına öneri olarak yaz.
   - Yalnızca **durumu "Var" olan** formatları planla; "Yapılacak" formatlar için şablon hazır olana kadar en yakın mevcut formatı kullan ve PR'da not düş.
   - Faz 1 dağılımı: F1 ×2, F2, F6, ve kalan günler veriye göre. Kazanan format varsa (eşiği geçen) payını artır; seri numarası ver ("Meydan okuma #N", `hook.lines` ve `caption` içinde).
   - **Trial**: rapordaki takipçi ≥ 1.000 ise günde en fazla 1 ek reel'e `"trial": true` ver (aynı formatın farklı kancası, farklı saat).
   - `record`: `catalog.json`'daki bir sekme + paket (premium hariç), `level: 1`. Son 3 haftada kullanılmış ikiliyi mümkünse tekrar etme; tekrarlanırsa kanca ve format farklı olsun. Her hafta en az bir A1/A2 ve bir B1+.
   - `hook.lines`: en fazla 3 satır, satır başına en fazla ~16 karakter, Türkçe, merak uyandıran.
   - `caption`: ilk satır kanca, sonra 1–2 cümle, son satır **paylaşım çağrısı** ("Bilemeyen arkadaşına gönder", "Seviyeni yorumla"). Uygulama hakkında doğrulanmamış iddia (indirme sayısı, ödül, yüzde, "ücretsiz" vb.) yazma.
   - `hashtags`: en fazla 5.
   - **F1 meydan okuma** cümlesi yalnızca `catalog.json → known_level1_sentences` ya da geçmiş reel'lerdeki `intro_text` içinde geçen **gerçek** bir cümleden alınır. Cümlesi bilinmeyen paket için F1 yazma.
5. `python3 -c` ile her yeni JSON'un geçerli olduğunu ve hashtag ≤ 5 olduğunu doğrula.
6. Dal: `plan/<YYYY>-W<hafta>`. Commit mesajı ve PR başlığı: `Plan: <ilk yayın tarihi> haftası`. PR açıklamasında: analiz özeti, reel tablosu (tarih, saat, format, sekme/paket, kanca, trial), ve "Pazartesi 08:00'den önce birleştirilirse o hafta üretilir" notu.

## Yapma
- PR'ı birleştirme, mevcut `approved`/`published` reel'leri değiştirme, iş akışı dosyalarına dokunma.
