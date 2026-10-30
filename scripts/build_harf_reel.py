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
from build_reel import C, ROOT, W, H, font, run  # noqa: E402

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
    w = b.get('word')
    if w:
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
        if t: shadowed(im, (W / 2, 245), t[0], f, (255, 255, 255))
        if len(t) > 1: shadowed(im, (W / 2, 245 + size + 14), t[1], f, tuple(b.get('accent', ACCENT)))
    if b.get('sub'):
        pill(im, W / 2, 1585, b['sub'], font('Bold', 42), (12, 20, 30, 200), (255, 255, 255))
    pill(im, 120, 1760, 'DilGames', font('Bold', 30), (12, 20, 30, 190), (255, 255, 255), padx=22, pady=10)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, 1820, W - 60, 1828], 4, fill=(255, 255, 255, 70))
    d.rounded_rectangle([60, 1820, 60 + (W - 120) * progress, 1828], 4, fill=MINT + (230,))
    im.save(path)


def build(spec_path, out):
    s = json.load(open(spec_path, encoding='utf-8'))
    vd = os.path.join(ROOT, s['voice_dir'])
    t = tempfile.mkdtemp(prefix='harf-')

    def V(n):  # baştaki/sondaki sessizliği kırpılmış kopya (tempo için)
        src, dst = os.path.join(vd, n + '.mp3'), os.path.join(t, n + '.wav')
        if not os.path.exists(dst):
            run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-af',
                 'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse,apad=pad_dur=0.05', dst])
        return dst
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
              "[1:v]format=rgba,fade=in:st=0:d=0.12:alpha=1[a];[v][a]overlay,format=yuv420p[o]")
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
