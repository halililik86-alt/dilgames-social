#!/usr/bin/env python3
""""Türk İngilizcesi Kazaları" Reels şablonu: Türklerin sık yaptığı bir İngilizce hatasının kısa sitcom'u.

Kullanım: python3 scripts/build_kaza_reel.py <reel.json> <çıktı.mp4>
reel.json alanları (type: "kaza"):
  episode, hook (kanca yazısı), voice_dir (ElevenLabs çıktısı, ör. tts/audio/kaza-001)
  scenes: [{clip, start, dur, sub, line, line_at}]   AI sahneler; sub = altyazı, line = ses dosyası adı
  wrong, right (ör. "I am agree" / "I agree"), why (kısa Türkçe açıklama), more (ek doğru örnekler listesi)
  narration: {why, right, cta}; sfx: {scratch, laugh, music} -> voice_dir içindeki ses adları
Akış: soğuk açılış (komik an hemen başlar, üstte kanca yazısı) → tepki sahnesi → donma + "KAZA!" + kahkaha
→ doğrusu kartı (anlatıcı) + yorum çağrısı. Görsel: 3B animasyon (Renderforest), ses: tamamı ElevenLabs
(karakterler, anlatıcı, efektler, sitcom müziği). Oyun müziği kullanılmaz.
"""
import json, os, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_reel import BRAND, C, ROOT, W, H, font, shadow_text, wrap, run  # noqa: E402
from build_duel_reel import chip, text_block, TR_RED  # noqa: E402

GREEN = (64, 190, 120)
UP = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1'


def dur(p):
    import subprocess
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p],
                                capture_output=True, text=True).stdout.strip())


def series_tag(im, ep):
    d = ImageDraw.Draw(im)
    chip(d, (W / 2, 150), f'TÜRK İNGİLİZCESİ KAZALARI #{ep}', font('ExtraBold', 32), C['navy'] + (220,), C['mint'])


def hook_band(im, text):
    band = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(band).rectangle([0, 200, W, 520], fill=(6, 18, 30, 150))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(40)))
    text_block(im, 240, text, font('ExtraBold', 80), C['white'], maxw=940, lh=94)


def freeze_overlay(path, s):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); im.alpha_composite(Image.new('RGBA', (W, H), (10, 10, 20, 70)))
    series_tag(im, s['episode'])
    st = Image.new('RGBA', (760, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(st)
    d.rounded_rectangle([10, 10, 750, 250], 40, outline=TR_RED, width=14, fill=(255, 255, 255, 230))
    d.text((380, 130), 'KAZA!', font=font('ExtraBold', 150), fill=TR_RED, anchor='mm')
    st = st.rotate(-8, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(st, ((W - st.width) // 2, 760))
    im.save(path)


def subtitle(path, s, text, speaker=None, hook=None):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); series_tag(im, s['episode'])
    if hook: hook_band(im, hook)
    d = ImageDraw.Draw(im); f = font('ExtraBold', 76)
    lines = wrap(d, text, f, 900); lh = 92
    top = 1300; h = len(lines) * lh + 60 + (56 if speaker else 0)
    box = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([60, top, W - 60, top + h], 36, fill=(255, 255, 255, 238))
    im.alpha_composite(box.filter(ImageFilter.GaussianBlur(0.6)))
    d = ImageDraw.Draw(im); y = top + 30
    if speaker:
        d.text((W / 2, y), speaker, font=font('Bold', 40), fill=(90, 110, 120), anchor='ma'); y += 56
    for ln in lines:
        d.text((W / 2, y), ln, font=f, fill=C['navy'], anchor='ma'); y += lh
    im.save(path)


def card(path, s, cta, bg=None):
    im = Image.new('RGB', (W, H), C['navy']).convert('RGBA')
    if bg:
        b = Image.open(bg).convert('RGBA').resize((W, H)).filter(ImageFilter.GaussianBlur(28))
        im = Image.alpha_composite(b, Image.new('RGBA', (W, H), C['navy'] + (200,)))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([-200, 300, W + 200, 1500], fill=(40, 110, 120, 120))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120))); series_tag(im, s['episode'])
    d = ImageDraw.Draw(im)
    y = chip(d, (W / 2, 430), 'YANLIŞ', font('ExtraBold', 40), TR_RED + (255,), (255, 255, 255)) + 18
    f = font('ExtraBold', 104)
    y2 = text_block(im, y, s['wrong'], f, (215, 160, 160), lh=118, blur=4)
    d = ImageDraw.Draw(im); tw = d.textlength(s['wrong'], font=f)
    d.line([W / 2 - tw / 2 - 10, y + 62, W / 2 + tw / 2 + 10, y + 62], fill=TR_RED, width=10)
    y = chip(d, (W / 2, y2 + 60), 'DOĞRUSU', font('ExtraBold', 40), GREEN + (255,), (255, 255, 255)) + 18
    y = text_block(im, y, s['right'], font('ExtraBold', 150), C['gold'], lh=166, blur=8) + 40
    y = text_block(im, y, s['why'], font('SemiBold', 56), (210, 230, 232), maxw=900, lh=70, blur=4) + 70
    for m in s.get('more', []):
        y = text_block(im, y, m, font('Bold', 62), C['white'], lh=80, blur=4)
    if cta:
        d = ImageDraw.Draw(im)
        bx = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(bx).rounded_rectangle([90, 1590, W - 90, 1760], 40, fill=C['mint'] + (255,))
        im.alpha_composite(bx)
        d = ImageDraw.Draw(im)
        d.text((W / 2, 1640), 'Sen de böyle diyor muydun?', font=font('ExtraBold', 46), fill=C['navy'], anchor='mm')
        d.text((W / 2, 1712), 'Yorumlara itiraf et · Takip et', font=font('SemiBold', 40), fill=C['navy'], anchor='mm')
    im.save(path)


def build(spec_path, out):
    s = json.load(open(spec_path, encoding='utf-8'))
    vd = os.path.join(ROOT, s['voice_dir']); nar = s['narration']; fx = s['sfx']
    V = lambda n: os.path.join(vd, n + '.mp3')  # noqa: E731
    t = tempfile.mkdtemp(prefix='kaza-')
    segs, audio, at = [], [], 0.0

    # 1) Sahneler (soğuk açılış: ilk sahnede kanca yazısı üstte)
    for i, sc in enumerate(s['scenes']):
        la = sc.get('line_at', 0.2)
        d = sc.get('dur') or round(la + dur(V(sc['line'])) + sc.get('tail', 0.25), 2)
        subtitle(f'{t}/sub{i}.png', s, sc['sub'], sc.get('speaker'), s['hook'] if i == 0 else None)
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(ROOT, sc['clip']), '-loop', '1', '-t', str(d), '-i', f'{t}/sub{i}.png', '-filter_complex',
             f"[0:v]trim={sc.get('start', 0)}:{sc.get('start', 0) + d},setpts=PTS-STARTPTS,{UP},tpad=stop_mode=clone:stop_duration={d}[v];"
             f"[1:v]format=rgba[a];[v][a]overlay,format=yuv420p[o]",
             '-map', '[o]', '-an', '-t', str(d), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s{i}.mp4'])
        segs.append((f'{t}/s{i}.mp4', d)); audio.append((V(sc['line']), at + la, 1.0)); at += d

    # 2) Donma + KAZA! + kahkaha
    D_F = 1.6
    lc = s['scenes'][-1]
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(lc.get('start', 0) + segs[-1][1] - 0.1), '-i', os.path.join(ROOT, lc['clip']), '-frames:v', '1',
         '-vf', UP.replace(',fps=30', ''), f'{t}/last.png'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '2.5', '-i', os.path.join(ROOT, s['scenes'][0]['clip']), '-frames:v', '1',
         '-vf', UP.replace(',fps=30', ''), f'{t}/bg.png'])
    freeze_overlay(f'{t}/fz.png', s)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', str(D_F), '-i', f'{t}/last.png', '-loop', '1', '-t', str(D_F), '-i', f'{t}/fz.png', '-filter_complex',
         "[0:v]scale=1080:1920,zoompan=z='1.03':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,hue=s=0.5[v];"
         "[1:v]format=rgba,fade=in:st=0:d=0.08:alpha=1[a];[v][a]overlay,format=yuv420p[o]",
         '-map', '[o]', '-t', str(D_F), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/fz.mp4'])
    segs.append((f'{t}/fz.mp4', D_F))
    audio += [(V(fx['scratch']), at - 0.05, 0.8), (V(fx['laugh']), at + 0.15, 0.7)]
    at += D_F

    # 3) Kart: açıklama + doğrusu, sonra yorum/takip çağrısı
    t_why = dur(V(nar['why'])); t_right = dur(V(nar['right'])); t_cta = dur(V(nar['cta']))
    D_C1 = 0.2 + t_why + 0.1 + t_right + 0.3; D_C2 = t_cta + 0.8
    card(f'{t}/c1.png', s, False, f'{t}/bg.png'); card(f'{t}/c2.png', s, True, f'{t}/bg.png')
    for k, (img, d) in enumerate(((f'{t}/c1.png', D_C1), (f'{t}/c2.png', D_C2))):
        run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', str(d), '-i', img, '-filter_complex',
             f"[0:v]scale=1134:2016,zoompan=z='1.04-0.04*on/{int(d * 30)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p[o]",
             '-map', '[o]', '-t', str(d), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/c{k}.mp4'])
    segs += [(f'{t}/c0.mp4', D_C1), (f'{t}/c1.mp4', D_C2)]
    audio += [(V(nar['why']), at + 0.2, 1.0), (V(nar['right']), at + 0.2 + t_why + 0.1, 1.0), (V(nar['cta']), at + D_C1 + 0.1, 1.0)]
    total = sum(d for _, d in segs)

    inp = []
    for p, _ in segs: inp += ['-i', p]
    n = len(segs)
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ''.join(f'[{i}:v]' for i in range(n)) + f'concat=n={n}:v=1:a=0,format=yuv420p[o]',
         '-map', '[o]', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-r', '30', f'{t}/video.mp4'])

    inp, fc, labs = [], [], []

    def add(p, flt, at=None):
        if not os.path.exists(p): return
        k = len(labs); inp.extend(['-i', p]); dl = f',adelay={int(at * 1000)}|{int(at * 1000)}' if at is not None else ''
        fc.append(f'[{k}:a]{flt}{dl}[a{k}]'); labs.append(f'[a{k}]')
    add(V(fx['music']), f'aloop=loop=2:size=3e6,atrim=0:{total:.2f},volume=0.16,afade=t=in:d=0.3,afade=t=out:st={total - 1.0:.2f}:d=1.0', 0)
    for p, a, v in audio:
        add(p, f'volume={v}', max(0, a))
    fc.append(''.join(labs) + f'amix=inputs={len(labs)}:normalize=0:duration=longest,atrim=0:{total:.2f},alimiter=limit=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[out]')
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '48000', '-ac', '2', f'{t}/mix.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{t}/video.mp4', '-i', f'{t}/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-shortest', '-movflags', '+faststart', out])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '1.0', '-i', out, '-frames:v', '1', '-q:v', '3', out[:-4] + '.jpg'])
    print(json.dumps({'out': out, 'duration': round(total, 2)}, ensure_ascii=False))


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
