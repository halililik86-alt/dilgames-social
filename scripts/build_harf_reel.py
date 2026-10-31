#!/usr/bin/env python3
""""Bir Harfin Hikâyesi" Reels şablonu: tek harfle (ya da aynı sesle) anlamı değişen iki İngilizce kelimenin mini hikâyesi.

Kullanım: python3 scripts/build_harf_reel.py <reel.json> <çıktı.mp4>
Akış (~15 sn): görsel şaka sonucu ("X istedi. Y geldi!") → "3 saniye önce" yanlış sipariş → "tek bir harf" →
iki kelime kartı (farklı harf vurgulu) → "şimdi oldu" → mutlu son → "Bir kelime daha?".
reel.json alanları (type: "harf"):
  episode, voice_dir, music
  beats: [{clip, start, dur?, chip, title: [satır1, satır2?], sub?, word?: {en, hi: [i,j], tr}, say: [[ses, gecikme], ...], sfx: [[efekt, gecikme]]}]
  Bir beat'in süresi verilmezse içindeki seslerin bitişine göre hesaplanır.
Görsel: 3B animasyon (Renderforest), ses: ElevenLabs (anlatıcı, karakter, efekt, müzik). Oyun müziği kullanılmaz.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_reel import C, ROOT, W, H, font, run, wrap  # noqa: E402

UP = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,setsar=1'
ACCENT = (255, 196, 92)
MINT = (120, 230, 190)


def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout.strip())


def shadowed(im, xy, text, f, fill, anchor='ma', blur=10):
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text(xy, text, font=f, fill=(0, 0, 0, 200), anchor=anchor)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor=anchor)


def pill(im, cx, cy, text, f, bg, fg, padx=26, pady=14):
    d = ImageDraw.Draw(im); w = d.textlength(text, font=f); h = f.size
    d.rounded_rectangle([cx - w / 2 - padx, cy - h / 2 - pady, cx + w / 2 + padx, cy + h / 2 + pady], (h + 2 * pady) / 2, fill=bg)
    d.text((cx, cy), text, font=f, fill=fg, anchor='mm')


def overlay(path, b, progress):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    top = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(top).rectangle([0, 0, W, 560], fill=(10, 12, 20, 120))
    im.alpha_composite(top.filter(ImageFilter.GaussianBlur(60)))
    if b.get('chip'):
        pill(im, W / 2, 170, b['chip'], font('ExtraBold', 30), (12, 20, 30, 215), (235, 240, 245))
    if b.get('label'):  # ör. TÜRKÇE (kırmızı) / İNGİLİZCE (mavi)
        pill(im, W / 2, 232, b['label'], font('ExtraBold', 30), tuple(b.get('label_color', [227, 66, 66])) + (240,), (255, 255, 255))
    w = b.get('word'); c = b.get('card')
    if c:  # deyim kartı: iki deyim, anlam ve örnek cümle (kutu içeriğe göre boyutlanır)
        d = ImageDraw.Draw(im); rows = []
        for txt, col in ((c['a'], (255, 255, 255)), (c.get('sep', '='), MINT), (c['b'], ACCENT)):
            size = 80
            while size > 44 and d.textlength(txt, font=font('ExtraBold', size)) > 880: size -= 4
            rows.append((txt, col, size))
        fm = font('SemiBold', 48); lm = wrap(d, 'Anlamı: ' + c['meaning'], fm, 860)
        fe, ft = font('Bold', 48), font('Medium', 40)
        le, lt = wrap(d, c['ex_en'], fe, 800), wrap(d, c['ex_tr'], ft, 800)
        ex_h = 40 + len(le) * 60 + 16 + len(lt) * 50 + 36
        body = 90 + sum(sz + 24 for _, _, sz in rows) + 10 + len(lm) * 60 + 44 + ex_h + 60
        top = max(300, (H - body) // 2 - 60)
        box = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(box).rounded_rectangle([60, top, W - 60, top + body], 48, fill=(10, 16, 26, 225))
        im.alpha_composite(box)
        pill(im, W / 2, top + 70, c.get('chip', 'İKİSİ DE AYNI ANLAMDA'), font('ExtraBold', 32), (255, 196, 92, 255), (20, 24, 32))
        y = top + 130
        for txt, col, sz in rows:
            shadowed(im, (W / 2, y), txt, font('ExtraBold', sz), col, blur=6); y += sz + 24
        y += 10
        for ln in lm: shadowed(im, (W / 2, y), ln, fm, (210, 230, 232), blur=4); y += 60
        y += 44
        exl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); de = ImageDraw.Draw(exl)
        de.rounded_rectangle([110, y, W - 110, y + ex_h], 32, fill=(0, 0, 0, 150), outline=(120, 230, 190, 140), width=3)
        im.alpha_composite(exl); d = ImageDraw.Draw(im); yy = y + 38
        for ln in le: d.text((W / 2, yy), ln, font=fe, fill=(255, 255, 255), anchor='ma'); yy += 60
        yy += 16
        for ln in lt: d.text((W / 2, yy), ln, font=ft, fill=(200, 215, 220), anchor='ma'); yy += 50
    elif w:
        f = font('ExtraBold', 150); d = ImageDraw.Draw(im); en = w['en']
        x = W / 2 - d.textlength(en, font=f) / 2; y = 250
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x, y), en, font=f, fill=(0, 0, 0, 200))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12))); d = ImageDraw.Draw(im)
        for i, ch in enumerate(en):
            col = MINT if w.get('hi') and w['hi'][0] <= i < w['hi'][1] else (w.get('color') and tuple(w['color']) or (255, 255, 255))
            d.text((x, y), ch, font=f, fill=col); x += d.textlength(ch, font=f)
        shadowed(im, (W / 2, 425), w['tr'], font('ExtraBold', 66), (255, 255, 255))
    else:
        t = b.get('title') or []
        d = ImageDraw.Draw(im); size = 92
        while size > 50 and max(d.textlength(x, font=font('ExtraBold', size)) for x in t or ['']) > 980: size -= 4
        f = font('ExtraBold', size)
        y0 = 300 if b.get('label') else 245
        if t: shadowed(im, (W / 2, y0), t[0], f, (255, 255, 255))
        if len(t) > 1: shadowed(im, (W / 2, y0 + size + 14), t[1], f, tuple(b.get('accent', ACCENT)))
    if b.get('sub'):
        d = ImageDraw.Draw(im); size = 42
        while size > 30 and d.textlength(b['sub'], font=font('Bold', size)) > 940: size -= 2
        pill(im, W / 2, 1585, b['sub'], font('Bold', size), (12, 20, 30, 200), (255, 255, 255))
    pill(im, 120, 1760, 'DilGames', font('Bold', 30), (12, 20, 30, 190), (255, 255, 255), padx=22, pady=10)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, 1820, W - 60, 1828], 4, fill=(255, 255, 255, 70))
    d.rounded_rectangle([60, 1820, 60 + (W - 120) * progress, 1828], 4, fill=MINT + (230,))
    im.save(path)


def _in_tag(text, k):
    return text.rfind('[', 0, k + 1) > text.rfind(']', 0, k)


def voice(vd, t, n):  # "take#metin": tek parça anlatımdan o cümleyi zaman damgasıyla keser; düz ad: dosyanın kendisi
    key = n.replace('/', '_').replace('.', '_') if '#' not in n else n.split('#')[0] + '_' + str(abs(hash(n)) % 10 ** 8)
    dst = os.path.join(t, key + '.wav')
    if os.path.exists(dst): return dst
    if '#' in n:
        take, sub = n.split('#', 1)
        al = json.load(open(os.path.join(vd, take + '.align.json'), encoding='utf-8'))['alignment']
        text = ''.join(al['characters']); i = text.index(sub); j = i + len(sub) - 1
        while i < j and (not text[i].strip() or text[i] in '[]' or _in_tag(text, i)): i += 1  # etiketi değil ilk gerçek harfi esas al
        st, en = al['character_start_times_seconds'], al['character_end_times_seconds']
        prv = [en[k] for k in range(0, i) if text[k].strip() and text[k] not in '[]' and not _in_tag(text, k)]
        a = max(prv[-1] + 0.02 if prv else 0.0, st[i] - 0.3)  # biraz erken başla, önceki kelimeye taşma
        nxt = [st[k] for k in range(j + 1, len(text)) if text[k].strip() and text[k] not in '[]' and not _in_tag(text, k)]
        b = min(en[j] + 0.25, nxt[0] - 0.02) if nxt else en[j] + 0.3
        # atrim + asetpts: kesilen parçanın zamanı 0'dan başlar, kısma efekti parçanın kendi sonuna uygulanır
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(vd, take + '.mp3'), '-af',
             f'atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,afade=t=out:st={max(0, b - a - 0.05):.3f}:d=0.05,apad=pad_dur=0.05', dst])
    else:
        src = os.path.join(vd, n + '.mp3')
        if not os.path.exists(src): return src  # dosya yoksa (ör. müziksiz kontrol) çağıran atlar
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-af',
             'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.05', dst])
    return dst


def build(spec_path, out):
    s = json.load(open(spec_path, encoding='utf-8'))
    vd = os.path.join(ROOT, s['voice_dir'])
    t = tempfile.mkdtemp(prefix='harf-')

    V = lambda n: voice(vd, t, n)  # noqa: E731
    beats = s['beats']
    for b in beats:
        if not b.get('dur'):
            end = max([g + dur(V(n)) for n, g in b.get('say', [])] or [1.2])
            b['dur'] = round(end + b.get('tail', 0.25), 2)
    total = sum(b['dur'] for b in beats)
    segs, audio, at = [], [], 0.0
    for i, b in enumerate(beats):
        overlay(f'{t}/o{i}.png', b, (at + b['dur']) / total)
        z = b.get('zoom', 0.04); n = int(b['dur'] * 30)
        vf = (f"[0:v]trim={b.get('start', 0)}:{b.get('start', 0) + b['dur']},setpts=PTS-STARTPTS,{UP},fps=30,tpad=stop_mode=clone:stop_duration={b['dur']},"
              f"scale=1134:2016,zoompan=z='1+{z}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
              + (",gblur=sigma=14,eq=brightness=-0.08" if b.get('blur') else '') + "[v];"
              "[1:v]format=rgba" + (",fade=in:st=0:d=0.12:alpha=1" if i == 0 or beats[i - 1]['clip'] != b['clip'] or beats[i - 1].get('blur') != b.get('blur') else '') + "[a];[v][a]overlay,format=yuv420p[o]")
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(ROOT, b['clip']), '-loop', '1', '-t', str(b['dur']), '-i', f'{t}/o{i}.png',
             '-filter_complex', vf, '-map', '[o]', '-an', '-t', str(b['dur']), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s{i}.mp4'])
        segs.append(f'{t}/s{i}.mp4')
        for n_, g in b.get('say', []): audio.append((V(n_), at + g, 1.0))
        for n_, g in b.get('sfx', []): audio.append((V(n_), at + g, 0.55))
        at += b['dur']
    inp = []
    for p in segs: inp += ['-i', p]
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ''.join(f'[{i}:v]' for i in range(len(segs))) + f'concat=n={len(segs)}:v=1:a=0,format=yuv420p[o]',
         '-map', '[o]', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-r', '30', f'{t}/video.mp4'])
    inp, fc, labs = [], [], []

    def add(p, flt, at=None):
        if not os.path.exists(p): return
        k = len(labs); inp.extend(['-i', p]); dl = f',adelay={int(at * 1000)}|{int(at * 1000)}' if at is not None else ''
        fc.append(f'[{k}:a]{flt}{dl}[a{k}]'); labs.append(f'[a{k}]')
    add(os.path.join(ROOT, s['music']), f'aloop=loop=2:size=3e6,atrim=0:{total:.2f},volume=0.18,afade=t=in:d=0.3,afade=t=out:st={total - 1.0:.2f}:d=1.0', 0)
    for p, a, v in audio: add(p, f'volume={v}', max(0, a))
    fc.append(''.join(labs) + f'amix=inputs={len(labs)}:normalize=0:duration=longest,atrim=0:{total:.2f},alimiter=limit=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[out]')
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '48000', '-ac', '2', f'{t}/mix.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{t}/video.mp4', '-i', f'{t}/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-shortest', '-movflags', '+faststart', out])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '0.8', '-i', out, '-frames:v', '1', '-q:v', '3', out[:-4] + '.jpg'])
    print(json.dumps({'out': out, 'duration': round(total, 2)}, ensure_ascii=False))


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
