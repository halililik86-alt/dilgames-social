#!/usr/bin/env python3
"""Reels kapağı (1080x1920): profil ızgarasında (orta 3:4 kırpım) ve keşfette tıklatan kapak.

Kurallar: büyük ifadeli kare + 2-4 kelimelik dev merak cümlesi + seri rozeti/rengi; bütün yazılar 3:4 güvenli
alanda (y 300-1560, Reels arayüzünün altında kalmaz). Seri tipine göre şablon:
  (spec'te isteğe bağlı cover_t = kare zamanı, cover_shift = sahneyi aşağı kaydırma pikseli)
  kaza  : "BUNU DEME!" + “yanlış cümle” + "Doğrusu ne?"            (Elif sahnesi)
  harf  : KELİME1 / KELİME2 (farklı harf vurgulu) + hikâye kancası  (şaka sahnesi)
  duel2 : "TÜRKÇE DEYİM" + deyim + "İngilizcesi ne?"         (deyimin harfiyen sahnesi)
  ifade : "BUGÜNÜN İFADESİ" + “ifade” + harfiyen yanlış anlam   (yanlış anlama sahnesi; cover_scene)
Kullanım: python3 scripts/cover.py <spec.json> <çıktı.jpg>
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1080, 1920
FD = '/usr/share/fonts/opentype/inter/'
RED, MINT, GOLD, NAVY, BLUE = (233, 64, 64), (120, 230, 190), (255, 200, 90), (12, 20, 32), (76, 132, 232)
SERIES = {'kaza': ('TÜRK İNGİLİZCESİ KAZALARI', RED), 'harf': ('BİR HARFİN HİKÂYESİ', MINT), 'duel2': ('DEYİM DÜELLOSU', GOLD), 'ifade': ('ELİF + TOM', MINT), 'sitkom': ('ELLIE & KEREM', GOLD), 'ellietom': ('ELLIE & TOM', GOLD)}


def font(w, s):
    return ImageFont.truetype(f'{FD}Inter-{w}.otf', s)


def frame(clip, t):
    out = tempfile.mktemp(suffix='.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', os.path.join(ROOT, clip), '-frames:v', '1',
                    '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920', out], check=True)
    return Image.open(out).convert('RGBA')


def shift_down(im, dy):
    """Sahneyi aşağı kaydır (yüz yazının altına insin); üst boşluk bulanık uzatmayla dolar."""
    if dy <= 0: return im
    bg = im.resize((W, H)).filter(ImageFilter.GaussianBlur(40)); top = im.crop((0, 0, W, H - dy))
    m = Image.new('L', top.size, 255); dm = ImageDraw.Draw(m); fe = min(160, dy)
    for y in range(fe): dm.line([(0, y), (W, y)], fill=int(255 * y / fe))  # yumuşak geçiş, sert dikiş yok
    top.putalpha(m); bg.alpha_composite(top, (0, dy))
    return bg


def fit(d, text, weight, size, maxw, minsize=48):
    while size > minsize and d.textlength(text, font=font(weight, size)) > maxw: size -= 4
    return font(weight, size)


def stroke_text(im, xy, text, f, fill, stroke=10, anchor='mm', shadow=True):
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 6, xy[1] + 8), text, font=f, fill=(0, 0, 0, 170), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(10, 14, 22))


def chip(im, cx, cy, text, f, bg, fg, padx=34, pady=18, rot=0):
    d = ImageDraw.Draw(im); w = d.textlength(text, font=f); h = f.size
    layer = Image.new('RGBA', (int(w + 2 * padx + 20), int(h + 2 * pady + 20)), (0, 0, 0, 0)); dl = ImageDraw.Draw(layer)
    dl.rounded_rectangle([10, 10, 10 + w + 2 * padx, 10 + h + 2 * pady], (h + 2 * pady) / 2, fill=bg)
    dl.text((10 + padx + w / 2, 10 + pady + h / 2), text, font=f, fill=fg, anchor='mm')
    if rot: layer = layer.rotate(rot, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def vignette(im, top=0.55, bottom=0.6):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    for y in range(H):
        a = 0
        if y < 760: a = int(255 * top * (1 - y / 760))
        if y > 1150: a = int(255 * bottom * ((y - 1150) / (H - 1150)))
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    im.alpha_composite(g)


def badge(im, s, color):
    name = SERIES.get(s['type'], ('DilGames', MINT))[0]
    chip(im, W / 2, 352, f"{name} #{s.get('episode', '')}", font('ExtraBold', 34), color + (255,), NAVY if color != RED else (255, 255, 255))


def cover_kaza(s):
    sc = s['scenes'][0]; im = frame(sc['clip'], s.get('cover_t', sc.get('start', 0) + 2.4))
    im = im.resize((int(W * 1.08), int(H * 1.08)), Image.LANCZOS).crop((int(W * .04), int(H * .02), int(W * .04) + W, int(H * .02) + H))
    im = shift_down(im, s.get('cover_shift', 120))
    vignette(im, 0.7, 0.75); badge(im, s, RED)
    chip(im, W / 2, 470, 'BUNU DEME!', font('Black', 64), RED + (255,), (255, 255, 255), rot=-4)
    d = ImageDraw.Draw(im); f = fit(d, f'“{s["wrong"]}”', 'Black', 118, 980)
    stroke_text(im, (W / 2, 610), f'“{s["wrong"]}”', f, (255, 255, 255))
    stroke_text(im, (W / 2, 1420), 'Doğrusu ne?', font('Black', 96), GOLD)
    return im


def cover_harf(s):
    b0 = s['beats'][0]; im = shift_down(frame(b0['clip'], s.get('cover_t', b0.get('start', 0) + 2.6)), s.get('cover_shift', 200))
    vignette(im, 0.75, 0.75); badge(im, s, MINT)
    words = [b['word'] for b in s['beats'] if b.get('word')]
    d = ImageDraw.Draw(im); y = 520
    for i, w in enumerate(words[:2]):
        txt = w['en']; f = fit(d, txt, 'Black', 170, 900); x = W / 2 - d.textlength(txt, font=f) / 2
        for k, ch in enumerate(txt):
            col = MINT if w.get('hi') and w['hi'][0] <= k < w['hi'][1] else (255, 255, 255)
            stroke_text(im, (x, y), ch, f, col, anchor='lm', shadow=(k == 0)); x += d.textlength(ch, font=f)
        if i == 0:
            stroke_text(im, (W / 2, y + 135), 'mi?', font('Black', 70), GOLD); y += 270
    hook = re.sub(r'[^\w\s,.!?’\'-]', '', s.get('seo_story') or (s.get('caption') or '').split('\n')[0]).strip()
    if hook:
        f = fit(d, hook, 'ExtraBold', 70, 980, 44); stroke_text(im, (W / 2, 1490), hook, f, (255, 255, 255), stroke=8)
    return im


def cover_duel2(s):
    a = next(b for b in s['beats'] if b.get('label') == 'TÜRKÇE')
    im = shift_down(frame(a['clip'], s.get('cover_t', a.get('start', 0) + 1.5)), s.get('cover_shift', 200))
    vignette(im, 0.75, 0.75); badge(im, s, GOLD)
    chip(im, W / 2, 470, 'TÜRKÇE DEYİM', font('Black', 50), RED + (255,), (255, 255, 255), rot=-3)
    d = ImageDraw.Draw(im); idiom = ' '.join(a['title']).rstrip('!')
    words = idiom.split(); lines = [idiom]
    if d.textlength(idiom, font=font('Black', 110)) > 980 and len(words) > 1:  # iki satıra böl
        k = min(range(1, len(words)), key=lambda k: abs(len(' '.join(words[:k])) - len(' '.join(words[k:]))))
        lines = [' '.join(words[:k]), ' '.join(words[k:])]
    f = min((fit(d, l, 'Black', 120, 980, 64) for l in lines), key=lambda f: f.size)
    for n, l in enumerate(lines):
        stroke_text(im, (W / 2, 610 + n * (f.size + 14)), l, f, (255, 255, 255))
    stroke_text(im, (W / 2, 1460), 'İngilizcesi ne?', font('Black', 104), GOLD, stroke=8)
    return im


def cover_ifade(s):
    sc = s['scenes'][s.get('cover_scene', 1)]
    im = frame(sc['clip'], s.get('cover_t', sc.get('start', 0) + 1.2))
    if s.get('cover_crop'):  # [y0, y1, cx]: gömülü altyazı bantlarını dışarıda bırakan yakın çekim (1920 ölçeğinde)
        y0, y1, cx = (list(s['cover_crop']) + [W / 2])[:3]; h = y1 - y0; w = h * W / H
        x0 = max(0, min(W - w, cx - w / 2)); im = im.crop((int(x0), int(y0), int(x0 + w), int(y1))).resize((W, H), Image.LANCZOS)
    im = shift_down(im, s.get('cover_shift', 200))
    vignette(im, 0.75, 0.75); badge(im, s, SERIES.get(s['type'], ('', MINT))[1])
    chip(im, W / 2, 470, 'BUGÜNÜN İFADESİ', font('Black', 50), GOLD + (255,), NAVY, rot=-3)
    d = ImageDraw.Draw(im); ph = f'“{s["seo"]["phrase"]}!”'
    stroke_text(im, (W / 2, 620), ph, fit(d, ph, 'Black', 140, 980, 64), (255, 255, 255))
    lit = f'{s["seo"]["literal"]} mı?!'
    stroke_text(im, (W / 2, 1460), lit, fit(d, lit, 'Black', 100, 980, 56), GOLD, stroke=8)
    return im


def cover_sitkom(s):
    sc = s['scenes'][s.get('cover_scene', 1)]
    im = shift_down(frame(sc['clip'], s.get('cover_t', sc.get('start', 0) + 1.5)), s.get('cover_shift', 260))
    vignette(im, 0.75, 0.75); badge(im, s, GOLD)
    chip(im, W / 2, 470, s['seo'].get('cover_chip', 'TÜRKÇE DÜŞÜNDÜ'), font('Black', 50), RED + (255,), (255, 255, 255), rot=-3)
    d = ImageDraw.Draw(im); ph = f'“{s["seo"]["wrong"]}”'
    stroke_text(im, (W / 2, 620), ph, fit(d, ph, 'Black', 120, 980, 60), (255, 255, 255))
    q = s['seo'].get('cover_q', 'Ne oldu?!')
    stroke_text(im, (W / 2, 1460), q, fit(d, q, 'Black', 96, 980, 56), GOLD, stroke=8)
    return im


def cover_card(s):
    """Kart düzeni: videoda gömülü altyazı olan bölümler için. Sahne ortada çerçeveli kartta (altyazı sahnenin parçası),
    seri rozeti + ifade üstte, merak sorusu altta; hepsi 3:4 ızgara alanında."""
    sc = s['scenes'][s.get('cover_scene', 0)]
    src = frame(sc['clip'], s.get('cover_t', 1.2)).convert('RGB')
    ya = s.get('cover_y', 280); src = src.crop((0, ya, W, ya + 1350))          # 4:5 bölge
    cw, chh, cx0, cy0 = 760, 950, (W - 760) // 2, 600
    card = src.resize((cw, chh), Image.LANCZOS)
    bg = Image.new('RGBA', (W, H), (12, 34, 42, 255))
    glow = src.resize((W, H)).filter(ImageFilter.GaussianBlur(60)).convert('RGBA'); glow.putalpha(70); bg.alpha_composite(glow)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([cx0 + 6, cy0 + 14, cx0 + cw + 6, cy0 + chh + 14], 40, fill=(0, 0, 0, 150))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    m = Image.new('L', (cw, chh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, chh - 1], 40, fill=255)
    bg.paste(card, (cx0, cy0), m)
    ImageDraw.Draw(bg).rounded_rectangle([cx0, cy0, cx0 + cw, cy0 + chh], 40, outline=GOLD, width=5)
    name, col = SERIES.get(s['type'], ('DilGames', MINT))
    chip(bg, W / 2, 300, f"{name} #{s.get('episode', '')}", font('ExtraBold', 32), col + (255,), NAVY)
    d = ImageDraw.Draw(bg); d.text((W / 2, 380), s.get('cover_kicker', 'BUGÜNÜN İFADESİ'), font=font('ExtraBold', 34), fill=MINT, anchor='mm')
    ph = f'“{s["seo"]["phrase"]}!”'
    stroke_text(bg, (W / 2, 490), ph, fit(d, ph, 'Black', 112, 1000, 60), (255, 255, 255), stroke=8)
    q = s['seo'].get('cover_q') or f'{s["seo"]["literal"]} mı?!'
    stroke_text(bg, (W / 2, 1625), q, fit(d, q, 'Black', 92, 1000, 52), GOLD, stroke=8)
    d.text((W / 2, 1800), '@dilgamesapp', font=font('ExtraBold', 40), fill=(200, 222, 220), anchor='mm')
    return bg


def build(spec_path, out):
    s = json.load(open(spec_path, encoding='utf-8'))
    im = {'kaza': cover_kaza, 'harf': cover_harf, 'duel2': cover_duel2, 'ifade': cover_ifade, 'sitkom': cover_sitkom, 'ellietom': cover_card}[s['type']](s)
    im.convert('RGB').save(out, quality=92)
    return out


if __name__ == '__main__':
    print(build(sys.argv[1], sys.argv[2]))
