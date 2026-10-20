#!/usr/bin/env python3
"""Kayıttan 1080x1920 Reels videosu kurgular.

Kullanım: python3 scripts/build_reel.py <reel.json> <kayıt-klasörü> <çıktı.mp4>
Ortam:   GAME_DIST  oyunun derlenmiş klasörü (müzik ve efektler için), varsayılan ../dilgame/dist

Ses: yalnızca oyunun kendi sesleri (kayıttaki müzik/efekt/cümle okumaları + oyunun efekt dosyaları)
ve sentezlenmiş yumuşak geçiş sesi. İnsan seslendirmesi yok.
"""
import json, math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = json.load(open(os.path.join(ROOT, 'config/brand.json'), encoding='utf-8'))
C = {k: tuple(v) for k, v in BRAND['colors'].items()}
W, H = 1080, 1920
XF = 0.3  # geçiş süresi
FW, FH, FY = 800, 1422, 440  # oyun çerçevesi


def run(args):
    subprocess.run(args, check=True)


def font(weight, size):
    return ImageFont.truetype(os.path.join(BRAND['font_dir'], f'Inter-{weight}.otf'), size)


def shadow_text(im, xy, text, f, fill, anchor='ma', blur=6, offset=4):
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0], xy[1] + offset), text, font=f, fill=(0, 0, 0, 180), anchor=anchor)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(im).text(xy, text, font=f, fill=fill, anchor=anchor)


def wrap(d, text, f, maxw):
    lines, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    return lines + [cur]


def caption_png(path, step, text, accent):
    im = Image.new('RGBA', (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f, fs = font('ExtraBold', 62), font('ExtraBold', 44)
    y = 40
    if step:
        sw = d.textlength(step, font=fs) + 56; x0 = (W - sw) / 2
        d.rounded_rectangle([x0, y, x0 + sw, y + 70], radius=35, fill=accent + (255,))
        d.text((W / 2, y + 35), step, font=fs, fill=C['navy'], anchor='mm'); y += 96
    for ln in wrap(d, text, f, 900)[:2]:
        shadow_text(im, (W / 2, y), ln, f, C['white']); y += 76
    im.save(path)


def hook_png(path, lines):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    y = 300
    for i, ln in enumerate(lines):
        f = font('ExtraBold', 104 if i == 0 else 92)
        shadow_text(im, (W / 2, y), ln, f, C['white'] if i == 0 else C['mint'], blur=10, offset=6)
        y += 140 if i == 0 else 105
    im.save(path)


def endcard_png(path, cta):
    bg = Image.new('RGB', (W, H), C['navy']); px = bg.load()
    for yy in range(H):
        for xx in range(W):
            k = max(0, 1 - math.hypot(xx - W / 2, yy - H * 0.42) / 1100)
            px[xx, yy] = (int(10 + 18 * k), int(30 + 60 * k), int(48 + 60 * k))
    im = bg.convert('RGBA'); d = ImageDraw.Draw(im)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([W / 2 - 190, 510, W / 2 + 190, 890], radius=90, fill=C['mint'] + (90,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40)))
    icon = Image.open(os.path.join(ROOT, BRAND['icon'])).convert('RGBA').resize((360, 360), Image.LANCZOS)
    mask = Image.new('L', (360, 360), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, 359, 359], radius=80, fill=255)
    im.paste(icon, (int(W / 2 - 180), 520), mask); d = ImageDraw.Draw(im)
    d.text((W / 2, 950), BRAND['name'], font=font('ExtraBold', 128), fill=C['white'], anchor='ma')
    d.text((W / 2, 1100), BRAND['tagline'], font=font('SemiBold', 50), fill=C['mint'], anchor='ma')
    d.text((W / 2, 1260), BRAND['subline'], font=font('Medium', 44), fill=(190, 215, 220), anchor='ma')
    f = font('ExtraBold', 52); tw = d.textlength(cta, font=f)
    d.rounded_rectangle([W / 2 - tw / 2 - 60, 1400, W / 2 + tw / 2 + 60, 1520], radius=60, fill=C['mint'])
    d.text((W / 2, 1460), cta, font=f, fill=C['navy'], anchor='mm')
    im.convert('RGB').save(path)


def frame_assets(tmp):
    m = Image.new('L', (FW, FH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, FW - 1, FH - 1], radius=48, fill=255)
    m.save(f'{tmp}/mask.png')
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([(W - FW) / 2 - 6, FY + 14, (W + FW) / 2 + 6, FY + FH + 20], radius=56, fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(24))
    ImageDraw.Draw(sh).rounded_rectangle([(W - FW) / 2 - 3, FY - 3, (W + FW) / 2 + 3, FY + FH + 3], radius=51, outline=C['mint'] + (150,), width=3)
    sh.save(f'{tmp}/shadow.png')


def assemble_take(recdir, tmp):
    """Ekran yayını karelerini + sesi zaman damgalarına göre 30 fps videoya çevirir."""
    d = json.load(open(f'{recdir}/take.json')); fr = d['frames']; t0 = fr[0]['t']
    with open(f'{tmp}/frames.ffconcat', 'w') as o:
        o.write('ffconcat version 1.0\n')
        for a, b in zip(fr, fr[1:]):
            o.write(f"file '{os.path.abspath(a['f'])}'\nduration {max(b['t'] - a['t'], 1) / 1000:.4f}\n")
        o.write(f"file '{os.path.abspath(fr[-1]['f'])}'\nduration 0.1\nfile '{os.path.abspath(fr[-1]['f'])}'\n")
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{tmp}/frames.ffconcat',
         '-itsoffset', str((d['recStart'] - t0) / 1000), '-i', f'{recdir}/take.webm',
         '-vf', 'fps=30,scale=1080:1920:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '16', '-preset', 'medium',
         '-c:a', 'aac', '-b:a', '192k', '-map', '0:v', '-map', '1:a', f'{tmp}/take.mp4'])
    marks = [(m['n'], (m['t'] - t0) / 1000) for m in d['marks']]
    return marks, d['result']


def auto_segments(marks, spec):
    """Kayıttaki olay işaretlerinden sahneleri seçer. spec['segments'] ile elle de verilebilir."""
    if spec.get('segments'):
        return [(s['kind'], s['start'], s['end']) for s in spec['segments']]
    first = lambda pred: next((t for n, t in marks if pred(n)), None)
    seg = []
    t = first(lambda n: n == 'intro')
    if t is not None: seg.append(('intro', t + 0.1, t + 2.9))
    t = first(lambda n: n == 'shot:vocabulary')
    if t is not None: seg.append(('vocab', max(0, t - 0.6), t + 4.6))
    t = first(lambda n: n == 'shot:merge')
    if t is not None: seg.append(('merge', t - 2.0, t + 1.1))
    t = first(lambda n: n == 'stir')
    if t is not None:
        if seg and seg[-1][0] == 'merge' and seg[-1][2] > t: seg[-1] = ('merge', seg[-1][1], t)
        seg.append(('stir', t, t + 3.8))
    t = first(lambda n: n == 'finished')
    if t is not None:
        lo = max(seg[-1][2] if seg else 0, t - 7.2)
        seg.append(('complete', lo, t + 1.3))
        seg.append(('win', t + 1.85, t + 4.65))
    return seg


def build(spec_path, recdir, out):
    spec = json.load(open(spec_path, encoding='utf-8'))
    dist = os.environ.get('GAME_DIST', os.path.join(ROOT, '..', 'dilgame', 'dist'))
    eff = os.path.join(dist, BRAND['game_audio']['effects_dir']); music = os.path.join(dist, BRAND['game_audio']['music'])
    tmp = tempfile.mkdtemp(prefix='reel-')
    frame_assets(tmp)
    marks, result = assemble_take(recdir, tmp)
    segs = auto_segments(marks, spec)
    if spec.get('format') == 'F1':
        # Meydan okuma: giriş kartı cümleyi baştan gösterip cevabı bozar; bu formatta atlanır.
        segs = [x for x in segs if x[0] != 'intro']
    caps = dict(BRAND['default_captions']); caps.update(spec.get('captions', {}))

    hook = spec.get('hook', {})
    hook_clip = os.path.join(ROOT, hook.get('clip', 'assets/hook/bubbles-rise.mp4'))
    hook_png(f'{tmp}/hook.png', hook.get('lines', ['Ezber yok.', 'İngilizceyi', 'oynayarak öğren']))
    endcard_png(f'{tmp}/end.png', spec.get('cta', BRAND['cta']))

    parts = [('hook', None, 0.4, 0.4 + hook.get('duration', 3.7))] + [(k, 'take', a, b) for k, a, b in segs] + [('end', None, 0, 3.4)]
    files = []
    for i, (kind, src, a, b) in enumerate(parts):
        d = b - a; o = f'{tmp}/seg{i:02d}.mp4'; files.append(o)
        if kind == 'hook':
            run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(a), '-t', str(d), '-i', hook_clip, '-loop', '1', '-t', str(d), '-i', f'{tmp}/hook.png',
                 '-filter_complex', '[0:v]scale=1080:1920:flags=lanczos,fps=30,eq=brightness=-0.04[v];[1:v]format=rgba,fade=in:st=0.35:d=0.45:alpha=1[c];[v][c]overlay=0:0,format=yuv420p[o]',
                 '-map', '[o]', '-an', '-c:v', 'libx264', '-crf', '16', '-r', '30', o])
        elif kind == 'end':
            n = int(d * 30)
            run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', str(d), '-i', f'{tmp}/end.png', '-filter_complex',
                 f"[0:v]scale=1188:2112,zoompan=z='1.10-0.10*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p[o]",
                 '-map', '[o]', '-c:v', 'libx264', '-crf', '16', '-r', '30', '-t', str(d), o])
        else:
            step, text = caps.get(kind, [None, ''])
            accent = C['gold'] if kind in ('stir', 'win') else C['mint']
            caption_png(f'{tmp}/cap{i}.png', step, text, accent)
            run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(a), '-t', str(d), '-i', f'{tmp}/take.mp4',
                 '-loop', '1', '-t', str(d), '-i', f'{tmp}/mask.png', '-loop', '1', '-t', str(d), '-i', f'{tmp}/shadow.png', '-loop', '1', '-t', str(d), '-i', f'{tmp}/cap{i}.png',
                 '-filter_complex',
                 '[0:v]fps=30,split[a][b];[a]scale=1080:1920,gblur=sigma=40,eq=brightness=-0.18:saturation=0.85[bg];'
                 f'[b]scale={FW}:{FH}:flags=lanczos,format=rgba[fg0];[1:v]format=gray,scale={FW}:{FH}[m];[fg0][m]alphamerge[fg];'
                 '[2:v]format=rgba[sh];[3:v]format=rgba,fade=in:st=0.1:d=0.35:alpha=1[c];'
                 f'[bg][sh]overlay=0:0[t1];[t1][fg]overlay={(W - FW) // 2}:{FY}[t2];[t2][c]overlay=0:120,format=yuv420p[o]',
                 '-map', '[o]', '-an', '-c:v', 'libx264', '-crf', '16', '-r', '30', o])

    starts, t = [], 0.0
    for kind, src, a, b in parts:
        starts.append(t); t += (b - a) - XF
    total = t + XF
    trans = ['circleopen'] + ['slideleft', 'slideleft', 'smoothup'] * 4
    inputs, fc, prev = [], [], '0:v'
    for f in files: inputs += ['-i', f]
    for i in range(1, len(files)):
        tr = 'fade' if i == len(files) - 1 else trans[i - 1]
        fc.append(f'[{prev}][{i}:v]xfade=transition={tr}:duration={XF}:offset={starts[i]:.3f}[x{i}]'); prev = f'x{i}'
    run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(fc), '-map', f'[{prev}]',
         '-c:v', 'libx264', '-crf', '17', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-r', '30', f'{tmp}/video.mp4'])

    # Ses
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=pink:duration=0.6:amplitude=0.9', '-af',
         'bandpass=f=900:width_type=o:w=2.2,highpass=f=250,afade=t=in:d=0.32:curve=exp,afade=t=out:st=0.32:d=0.28,volume=0.9',
         '-ar', '48000', '-ac', '2', f'{tmp}/whoosh.wav'])
    inp, fc, labs, k = [], [], [], 0
    def add(path, flt, at=None):
        nonlocal k
        inp.extend(['-i', path]); lab = f'a{k}'
        delay = f',adelay={int(at * 1000)}|{int(at * 1000)}' if at is not None else ''
        fc.append(f'[{k}:a]{flt}{delay}[{lab}]'); labs.append(f'[{lab}]'); k += 1
    if os.path.exists(music):
        add(music, f'atrim=0:{total:.2f},asetpts=PTS-STARTPTS,volume=0.32,afade=t=in:d=0.6,afade=t=out:st={total - 1.8:.2f}:d=1.8')
    for i, (kind, src, a, b) in enumerate(parts):
        if src == 'take':
            d = b - a
            add(f'{tmp}/take.mp4', f'atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,volume=3.2,afade=t=in:d=0.12,afade=t=out:st={d - 0.3:.2f}:d=0.3', starts[i])
    for i in range(1, len(parts)):
        add(f'{tmp}/whoosh.wav', 'volume=0.55', max(0, starts[i] - 0.15))
        if parts[i][0] in ('vocab', 'merge', 'complete', 'win') and os.path.exists(f'{eff}/bubble-connection.mp3'):
            add(f'{eff}/bubble-connection.mp3', 'volume=0.7', starts[i] + 0.05)
    if os.path.exists(f'{eff}/app-launch.mp3'): add(f'{eff}/app-launch.mp3', 'volume=0.9', starts[1] - 0.1)
    if os.path.exists(f'{eff}/level-complete.mp3'): add(f'{eff}/level-complete.mp3', 'volume=0.6', starts[-1] + 0.2)
    fc.append(''.join(labs) + f'amix=inputs={len(labs)}:normalize=0:duration=longest,atrim=0:{total:.2f},alimiter=limit=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[out]')
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '48000', '-ac', '2', f'{tmp}/mix.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{tmp}/video.mp4', '-i', f'{tmp}/mix.wav', '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out])
    # kapak karesi (önizleme ve Instagram kapağı için)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(starts[2] + 1.0 if len(starts) > 2 else 1.0), '-i', out, '-frames:v', '1', '-q:v', '3', out[:-4] + '.jpg'])
    print(json.dumps({'out': out, 'record_result': result, 'segments': [(p[0], round(p[2], 2), round(p[3], 2)) for p in parts], 'duration': round(total, 2)}, ensure_ascii=False))


if __name__ == '__main__':
    build(*sys.argv[1:4])
