#!/usr/bin/env python3
"""Arama uyumlu (SEO) gönderi metinleri: Instagram açıklaması + hashtag, YouTube başlığı/açıklaması/etiketleri.

İlkeler (Instagram araması açıklamanın ilk satırını, YouTube başlığın başını ve açıklamanın ilk satırlarını tarar):
  - Her gönderinin bir ana anahtar kelimesi var ve ilk satırda/başlığın başında geçer ("İngilizce" + konu).
  - Hikâye kancası ikinci satırda, ders (❌/✅, kelime = anlam, okunuş, örnek) ortada, çağrı (kaydet/gönder/takip) sonda.
  - Instagram: en fazla 5 konuyla ilgili hashtag. YouTube: açıklamada 3 hashtag (başlığın üstünde görünür) + 10-15 etiket.
Kullanım:
  python3 scripts/seo.py content/reels/<id>.json [...]   spec'e caption/hashtags/yt_title/yt_description/yt_tags yazar
  (youtube_due.py bu alanları kullanır; publish_due.py caption + hashtags'i kullanır.)
"""
import json, re, sys

SCHEDULE = '11:48, 16:48 ve 21:48'
CTA_IG = "📌 Kaydet, sonra tekrar bak · 📩 Bilmeyen arkadaşına gönder\n🔔 Her gün 3 kısa İngilizce video için @dilgamesapp'i takip et"
CTA_YT = f'🔔 Her gün {SCHEDULE}\'de yeni İngilizce Shorts. Abone ol, bildirimleri aç!'
CORE_TAGS = ['ingilizce', 'ingilizce öğren', 'ingilizce shorts', 'kolay ingilizce', 'dilgames']


def tr_lower(t):
    return t.replace('I', 'ı').replace('İ', 'i').lower()


def tr_cap(t):
    t = tr_lower(t)
    return (t[:1].replace('i', 'İ').upper() + t[1:]) if t else t


def cut(t, n):
    return t if len(t) <= n else t[:n - 1].rstrip() + '…'


def _story(s):
    """Mevcut açıklamadaki hikâye satırı (yoksa kanca)."""
    lines = [l.strip() for l in (s.get('caption') or '').splitlines() if l.strip()]
    if s.get('type') == 'duel2' and len(lines) > 1:
        return lines[1]
    if s.get('seo_story'):
        return s['seo_story']
    return lines[0] if lines else s.get('hook', '')


def build(s):
    t = s.get('type')
    story = s.get('seo_story') or _story(s)
    if t == 'kaza':
        w, r = s['wrong'], s['right']
        first = f'İngilizcede en sık yapılan hatalardan biri: “{w}” 😅'
        lesson = f'❌ {w}\n✅ {r}\n💡 {tr_cap(s["why"])}'
        if s.get('more'): lesson += '\nÖrnek: ' + ' · '.join(s['more'])
        ig_tags = ['#ingilizce', '#ingilizceöğren', '#ingilizcehatalar', '#ingilizcekonuşma', '#englishlearning']
        title = cut(f'“{w}” deme! Doğrusu “{r}” 😅 İngilizce hatalar', 95)
        lead = f'İngilizcede “{w}” demek yanlış, doğrusu “{r}”. Türklerin en sık yaptığı İngilizce hatalardan biri.'
        yt3 = '#ingilizce #ingilizcehatalar #shorts'
        tags = CORE_TAGS + ['ingilizce hatalar', 'türk ingilizcesi', 'ingilizce konuşma', w.lower(), r.lower(), f'{w.lower()} yanlış mı', 'türk ingilizcesi kazaları']
    elif t == 'harf':
        words = [b['word'] for b in s['beats'] if b.get('word')]
        subs = [b.get('sub', '') for b in s['beats'] if b.get('word')]
        a, b = words[0]['en'].title(), words[1]['en'].title()
        first = f'İngilizcede {a} ve {b} farkı: küçük bir fark, bambaşka anlam! 😅'
        lesson = '\n'.join(f'🔤 {w["en"].title()} = {tr_cap(w["tr"])}' + (f' ({tr_lower(sb)})' if sb else '') for w, sb in zip(words, subs))
        ig_tags = ['#ingilizce', '#ingilizceöğren', '#ingilizcekelimeler', '#ingilizcetelaffuz', '#englishlearning']
        unit = 'küçük bir ses' if any('KÜÇÜK' in (x.get('chip') or '') for x in s['beats']) else ('iki harf' if any('İKİ HARF' in (x.get('chip') or '') for x in s['beats']) else 'tek harf')
        title = cut(f'{a} / {b} farkı 😅 İngilizcede {unit}, iki anlam', 95)
        lead = f'İngilizcede {a} ile {b} karıştırılıyor: {tr_lower(words[0]["tr"])} ve {tr_lower(words[1]["tr"])}. Okunuşu ve farkı bu videoda.'
        yt3 = '#ingilizce #ingilizcekelimeler #shorts'
        tags = CORE_TAGS + ['ingilizce kelimeler', 'ingilizce telaffuz', 'karıştırılan ingilizce kelimeler', a.lower(), b.lower(), f'{a.lower()} {b.lower()} farkı', 'bir harfin hikayesi']
    elif t == 'duel2':
        c = next(b['card'] for b in s['beats'] if b.get('card'))
        first = f'“{c["a"]}” İngilizcede nasıl denir? 🇬🇧'
        lesson = f'🇹🇷 {c["a"]}\n🇬🇧 {c["b"]}\nAnlamı: {c["meaning"]}\n\n“{c["ex_en"]}”\n{c["ex_tr"]}'
        ig_tags = ['#ingilizce', '#ingilizceöğren', '#ingilizcedeyimler', '#deyimler', '#englishidioms']
        title = f'{c["a"]} İngilizcede nasıl denir? “{c["b"]}”'
        if len(title) > 95: title = cut(f'{c["a"]} İngilizcesi: {c["b"]}', 95)
        lead = f'“{c["a"]}” deyiminin İngilizcesi: “{c["b"]}”. Anlamı: {tr_lower(c["meaning"])} Telaffuzu ve örnek cümlesi bu videoda.'
        yt3 = '#ingilizce #ingilizcedeyimler #shorts'
        tags = CORE_TAGS + ['ingilizce deyimler', 'türkçe deyimlerin ingilizcesi', tr_lower(c['a']), c['b'].lower(), f'{tr_lower(c["a"])} ingilizcesi', 'deyim düellosu', 'english idioms']
    elif t == 'ifade':
        x = s['seo']; ph = x['phrase']
        first = f'İngilizcede “{ph}” ne demek? “{x["literal"]}” değil! 😅'
        lesson = (f'🇬🇧 {ph}!\n❌ {x["literal"]} (kelimesi kelimesine)\n✅ {x["meaning"]}\n💡 {x["use"]}'
                  f'\n\n“{x["ex_en"]}”\n{x["ex_tr"]}')
        ig_tags = ['#ingilizce', '#ingilizceöğren', '#ingilizcekalıplar', '#ingilizcedeyimler', '#englishidioms']
        title = cut(f'“{ph}” ne demek? {x["literal"]} değil! 😅 İngilizce kalıplar', 95)
        lead = f'İngilizcede “{ph}” ne demek? Kelimesi kelimesine “{tr_lower(x["literal"])}” ama anlamı: {tr_lower(x["meaning"])} Ne zaman söylendiği ve örnek cümlesi bu videoda.'
        yt3 = '#ingilizce #ingilizcekalıplar #shorts'
        tags = CORE_TAGS + ['ingilizce kalıplar', 'ingilizce deyimler', ph.lower(), f'{ph.lower()} ne demek', f'{ph.lower()} anlamı',
                            f'{tr_lower(x["meaning"])} ingilizce', 'english idioms', 'bugünün ifadesi', 'elif ve tom']
    else:
        return s
    s['caption'] = f'{first}\n\n{story}\n\n{lesson}\n\n{s.get("seo_question") or "Sen bunu biliyor muydun? Yorumlara yaz 👇"}\n\n{CTA_IG}'
    s['hashtags'] = ig_tags[:5]
    s['yt_title'] = title
    s['yt_description'] = f'{lead}\n\n{story}\n\n{lesson}\n\n{CTA_YT}\n\n{yt3}'
    seen, out = set(), []
    for x in tags:
        x = re.sub(r'[“”"?!.,]', '', x).strip()
        if x and x not in seen and len(','.join(out + [x])) < 480: seen.add(x); out.append(x)
    s['yt_tags'] = out
    s['seo_story'] = story
    return s


if __name__ == '__main__':
    for p in sys.argv[1:]:
        s = json.load(open(p, encoding='utf-8'))
        if s.get('status') == 'published':
            print('atlandı (yayınlanmış):', p); continue
        build(s)
        json.dump(s, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(p, 'a').write('\n')
        print(s['id'], '|', s.get('yt_title'))
