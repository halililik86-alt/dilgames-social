#!/usr/bin/env python3
"""Öne çıkanlar için seri özet kartları (9:16 hikâye görseli): serideki bütün kalıp/kelime/deyimlerin listesi.
python3 scripts/series_cards.py  →  media/highlights/card-<seri>-<n>.jpg
"""
import json, glob, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from playlists import series_of

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = '/usr/share/fonts/opentype/inter/'
W, H = 1080, 1920
NAVY = (14, 24, 38)
COL = {'komedi': (255, 196, 92), 'kelime': (140, 236, 200), 'deyim': (140, 200, 255), 'hata': (255, 128, 112), 'oyun': (200, 170, 255)}


def F(w, s): return ImageFont.truetype(f'{FD}Inter-{w}.otf', s)


def fit(d, t, w, size, maxw, mn=24):
    while size > mn and d.textlength(t, font=F(w, size)) > maxw: size -= 2
    return F(w, size)


def items():
    cfg = json.load(open(os.path.join(ROOT, 'content/series.json'), encoding='utf-8'))
    out = {}
    for p in sorted(glob.glob(os.path.join(ROOT, 'content/reels/*.json')), key=lambda p: json.load(open(p)).get('publish_at', '')):
        s = json.load(open(p, encoding='utf-8'))
        if s.get('status') != 'published' or s.get('media') in ('image', 'story'): continue
        k = series_of(s, cfg); t = s.get('type')
        if t in ('ifade', 'ellietom'): it = (s['seo']['phrase'], s['seo']['meaning'])
        elif t in ('sitkom', 'gelin'): it = (s['seo']['tr_phrase'], s['seo']['right'])
        elif t == 'kaza': it = (s['wrong'], s['right'])
        elif t == 'harf':
            w = [b['word'] for b in s['beats'] if b.get('word')]
            it = (' / '.join(x['en'].lower() for x in w), ' / '.join(x['tr'].lower() for x in w))
        elif t == 'ff': it = (f'{s["en_word"]} ≠ {s["tr_word"]}', s['en_meaning'])
        elif t == 'duel': it = (s['tr']['idiom'], s['en']['idiom'])
        elif t == 'duel2':
            c = next(b['card'] for b in s['beats'] if b.get('card')); it = (c['a'], c['b'])
        else: continue
        out.setdefault(k, []).append(it)
    return out


def card(key, title, sub, rows, n, of):
    col = COL[key]
    im = Image.new('RGB', (W, H), NAVY)
    g = Image.new('RGB', (W, H), col); m = Image.new('L', (W, H), 0)
    ImageDraw.Draw(m).ellipse([-300, -500, W + 300, 700], fill=60); im = Image.composite(g, im, m.filter(ImageFilter.GaussianBlur(140)))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 230), 'DilGames · öne çıkan', font=F('ExtraBold', 40), fill=(200, 215, 225), anchor='mm')
    d.text((W / 2, 330), title, font=fit(d, title, 'Black', 104, 960), fill=(255, 255, 255), anchor='mm')
    d.text((W / 2, 420), sub + (f'  ({n}/{of})' if of > 1 else ''), font=fit(d, sub, 'Bold', 44, 960), fill=col, anchor='mm')
    top, bottom = 500, 1700
    step = min(170, (bottom - top) // max(1, len(rows)))
    for i, (a, b) in enumerate(rows):
        y = top + i * step
        d.rounded_rectangle([70, y, W - 70, y + step - 18], 22, fill=(255, 255, 255, 18) if False else (28, 40, 58))
        fa = fit(d, a, 'ExtraBold', 46, 870, 26); ya = y + (step - 18) * 0.32
        d.text((105, ya), a, font=fa, fill=(255, 255, 255) if key != 'hata' else (200, 200, 205), anchor='lm')
        if key == 'hata':  # yanlış cümlenin üstünü çiz
            d.line([(100, ya + 2), (110 + d.textlength(a, font=fa), ya + 2)], fill=col, width=6)
        if b: d.text((105, y + (step - 18) * 0.72), '→ ' + b, font=fit(d, '→ ' + b, 'SemiBold', 38, 870, 22), fill=col, anchor='lm')
    d.text((W / 2, 1780), 'Videolar profilde · @dilgamesapp', font=F('ExtraBold', 42), fill=(200, 222, 220), anchor='mm')
    return im


META = {'komedi': ('Komik Kalıplar', 'Bu seride öğrendiğin kalıplar'),
        'kelime': ('Kelimeler', 'Karıştırılan kelimeler'),
        'deyim': ('Deyimler', 'Türkçe deyim → İngilizcesi'),
        'hata': ('Hatalar', 'Yanlışı ve doğrusu'),
        'oyun': ('Oyun', 'DilGames oyununda neler var?')}
OYUN = [('Akşam Vapuru', 'kısa bir hikâyeyi cümle cümle kur'), ('Pazarda Bir Masa', 'pazar alışverişi cümleleri'),
        ('Şehirde Bir Gün', 'günlük hayat İngilizcesi'), ('Son Kartpostal', 'A2 hikâye: kartpostal yaz'),
        ('Mahalle Konseri', 'A2 hikâye: etkinlik anlat'), ('Kelime Avı', 'harflerden kelime bul'), ('Balon modu', 'balonları birleştir, cümleyi kur'),
        ('Ücretsiz dene', 'dilgames.app · App Store · Google Play')]

if __name__ == '__main__':
    it = items(); it['oyun'] = OYUN
    made = []
    for k, (title, sub) in META.items():
        rows = it.get(k, [])
        chunks = [rows] if len(rows) <= 8 else [rows[:(len(rows) + 1) // 2], rows[(len(rows) + 1) // 2:]]
        for i, ch in enumerate(chunks, 1):
            p = os.path.join(ROOT, f'media/highlights/card-{k}-{i}.jpg')
            card(k, title, sub, ch, i, len(chunks)).save(p, quality=92); made.append(p)
    print('\n'.join(made))
