#!/usr/bin/env python3
""""Yanlış Arkadaşlar" Reels şablonu: Türkçede bilinen bir kelimeye benzeyen ama başka anlama gelen İngilizce kelime.

Kullanım: python3 scripts/build_ff_reel.py <reel.json> <çıktı.mp4>
reel.json alanları (type: "ff"):
  episode, en_word, tr_word, en_meaning (Türkçe), tr_in_en (Türkçe kelimenin İngilizcesi),
  example_en, example_tr, clip (repo içindeki AI klip yolu; gerçek anlamı gösterir)
Akış (~14 sn): kanca (oyun balonları) → 3-2-1 tahmin → AI sahne + gerçek anlam → kart + takip çağrısı.
Ses: oyunun müziği + oyunun efektleri + sentez geçiş sesi. İnsan sesi yok.
"""
import json, os, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_reel import BRAND, C, ROOT, W, H, font, shadow_text, wrap, run  # noqa: E402
from build_duel_reel import chip, text_block, TR_RED, EN_BLUE  # noqa: E402
from tr import soru_eki  # noqa: E402

GREEN = (64, 190, 120)


def tr_upper(t):
    return t.replace('i', 'İ').replace('ı', 'I').upper()


def series_tag(im, ep):
    d = ImageDraw.Draw(im)
    chip(d, (W / 2, 150), f'YANLIŞ ARKADAŞLAR #{ep}' if ep else 'YANLIŞ ARKADAŞLAR', font('ExtraBold', 34), C['navy'] + (220,), C['mint'])


def overlay_hook(path, s):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    im.alpha_composite(Image.new('RGBA', (W, H), (4, 14, 24, 90)))
    series_tag(im, s.get('episode'))
    y = text_block(im, 520, s['en_word'], font('ExtraBold', 124), C['white'], lh=140)
    y = text_block(im, y + 10, '=', font('ExtraBold', 90), C['mint'])
    y = text_block(im, y + 10, s['tr_word'] + ' ' + soru_eki(s['tr_word']) + '?', font('ExtraBold', 112), C['gold'], lh=128)
    shadow_text(im, (W / 2, y + 60), 'Çoğu kişi yanlış biliyor', font('SemiBold', 50), C['mint'])
    im.save(path)


def overlay_question(path, n):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    im.alpha_composite(Image.new('RGBA', (W, H), (4, 14, 24, 150)))
    y = text_block(im, 620, 'Sence ne demek?', font('ExtraBold', 96), C['white'])
    shadow_text(im, (W / 2, y + 30), 'Cevabını yoruma yaz', font('SemiBold', 50), C['mint'])
    d = ImageDraw.Draw(im); cx, cy, r = W / 2, y + 260, 110
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=C['mint'] + (235,), outline=(255, 255, 255, 220), width=6)
    d.text((cx, cy), str(n), font=font('ExtraBold', 120), fill=C['navy'], anchor='mm')
    im.save(path)


def overlay_reveal(path, s):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); series_tag(im, s.get('episode'))
    d = ImageDraw.Draw(im)
    y = chip(d, (W / 2, 260), tr_upper(s['tr_word']) + ' DEĞİL', font('ExtraBold', 38), TR_RED + (255,), (255, 255, 255)) + 24
    text_block(im, y, s['en_word'], font('ExtraBold', 100), C['white'], lh=112)
    band = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(band).rectangle([0, 1180, W, 1480], fill=(6, 18, 30, 175))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(30)))
    shadow_text(im, (W / 2, 1220), 'Gerçek anlamı:', font('SemiBold', 46), C['mint'])
    text_block(im, 1295, s['en_meaning'], font('ExtraBold', 70), C['white'], maxw=900, lh=82)
    im.save(path)


def card(path, s):
    im = Image.new('RGB', (W, H), C['navy']).convert('RGBA')
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([-200, 300, W + 200, 1500], fill=(40, 110, 120, 120))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120))); series_tag(im, s.get('episode'))
    d = ImageDraw.Draw(im)
    y = 260
    y = chip(d, (W / 2, y), 'DOĞRUSU', font('ExtraBold', 34), GREEN + (255,), (255, 255, 255)) + 20
    y = text_block(im, y, s['en_word'], font('ExtraBold', 76), C['white'], lh=86, blur=6)
    y = text_block(im, y, '= ' + s['en_meaning'], font('SemiBold', 54), (200, 225, 228), lh=64, blur=4) + 50
    d = ImageDraw.Draw(im)
    y = chip(d, (W / 2, y), '“' + tr_upper(s['tr_word']) + '” DEMEK İSTERSEN', font('ExtraBold', 34), TR_RED + (255,), (255, 255, 255)) + 20
    y = text_block(im, y, s['tr_in_en'], font('ExtraBold', 76), C['gold'], lh=86, blur=6) + 40
    d = ImageDraw.Draw(im)
    dm = ImageDraw.Draw(im); box_top = y + 6
    n_en = len(wrap(dm, s['example_en'], font('SemiBold', 46), 820)); n_tr = len(wrap(dm, s['example_tr'], font('Medium', 38), 820))
    box_h = 34 + n_en * 58 + 12 + n_tr * 48 + 30
    box = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([90, box_top, W - 90, box_top + box_h], radius=36, fill=(255, 255, 255, 26), outline=C['mint'] + (140,), width=3)
    im.alpha_composite(box)
    yy = text_block(im, box_top + 34, s['example_en'], font('SemiBold', 46), C['white'], maxw=820, lh=58, blur=2)
    text_block(im, yy + 12, s['example_tr'], font('Medium', 38), (170, 200, 205), maxw=820, lh=48, blur=2)
    d = ImageDraw.Draw(im)
    cy = max(1380, box_top + box_h + 110)
    f = font('ExtraBold', 48); t = 'Takip et: her gün 1 yanlış arkadaş'; tw = d.textlength(t, font=f)
    d.rounded_rectangle([W / 2 - tw / 2 - 48, cy - 55, W / 2 + tw / 2 + 48, cy + 55], radius=55, fill=C['mint'])
    d.text((W / 2, cy), t, font=f, fill=C['navy'], anchor='mm')
    shadow_text(im, (W / 2, cy + 90), 'Bilmeyen arkadaşına gönder', font('SemiBold', 42), C['gold'], blur=3)
    icon = Image.open(os.path.join(ROOT, BRAND['icon'])).convert('RGBA').resize((76, 76), Image.LANCZOS)
    m = Image.new('L', (76, 76), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 75, 75], radius=18, fill=255)
    ly = cy + 175; im.paste(icon, (int(W / 2 - 205), ly), m); d = ImageDraw.Draw(im)
    d.text((W / 2 - 112, ly + 38), 'DilGames · oyunla İngilizce', font=font('SemiBold', 36), fill=(200, 225, 228), anchor='lm')
    im.convert('RGB').save(path)


def build(spec_path, out):
    s = json.load(open(spec_path, encoding='utf-8'))
    dist = os.environ.get('GAME_DIST', os.path.join(ROOT, '..', 'dilgame', 'dist'))
    eff = os.path.join(dist, BRAND['game_audio']['effects_dir']); music = os.path.join(dist, BRAND['game_audio']['music'])
    t = tempfile.mkdtemp(prefix='ff-')
    hook = os.path.join(ROOT, 'assets/hook/bubbles-rise.mp4'); clip = os.path.join(ROOT, s['clip'])
    overlay_hook(f'{t}/h.png', s); overlay_reveal(f'{t}/r.png', s); card(f'{t}/c.png', s)
    for n in (3, 2, 1): overlay_question(f'{t}/q{n}.png', n)
    D_H, D_Q, D_R, D_C = 3.0, 2.4, 5.0, 4.6
    up = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1'
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', hook, '-loop', '1', '-t', str(D_H), '-i', f'{t}/h.png', '-filter_complex',
         f"[0:v]trim=0:{D_H},setpts=PTS-STARTPTS,{up}[v];[1:v]format=rgba,fade=in:st=0:d=0.25:alpha=1[a];[v][a]overlay,format=yuv420p[o]",
         '-map', '[o]', '-an', '-t', str(D_H), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s1.mp4'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-sseof', '-0.1', '-i', f'{t}/s1.mp4', '-frames:v', '1', f'{t}/last.png'])
    qn = D_Q / 3
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', str(D_Q), '-i', f'{t}/last.png', '-loop', '1', '-t', str(qn), '-i', f'{t}/q3.png',
         '-loop', '1', '-t', str(qn), '-i', f'{t}/q2.png', '-loop', '1', '-t', str(qn), '-i', f'{t}/q1.png', '-filter_complex',
         f"[0:v]{up},gblur=sigma=18[bg];[1:v][2:v][3:v]concat=n=3:v=1:a=0,format=rgba[q];[bg][q]overlay,format=yuv420p[o]",
         '-map', '[o]', '-t', str(D_Q), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s2.mp4'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', clip, '-loop', '1', '-t', str(D_R), '-i', f'{t}/r.png', '-filter_complex',
         f"[0:v]trim=0:{D_R},setpts=PTS-STARTPTS,{up},tpad=stop_mode=clone:stop_duration={D_R}[v];[1:v]format=rgba,fade=in:st=0.1:d=0.35:alpha=1[a];[v][a]overlay,format=yuv420p[o]",
         '-map', '[o]', '-an', '-t', str(D_R), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s3.mp4'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', str(D_C), '-i', f'{t}/c.png', '-filter_complex',
         f"[0:v]scale=1134:2016,zoompan=z='1.05-0.05*on/{int(D_C * 30)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p[o]",
         '-map', '[o]', '-t', str(D_C), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s4.mp4'])
    X = 0.25
    o2 = D_H - X; o3 = o2 + D_Q - X; o4 = o3 + D_R - X; total = o4 + D_C
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{t}/s1.mp4', '-i', f'{t}/s2.mp4', '-i', f'{t}/s3.mp4', '-i', f'{t}/s4.mp4', '-filter_complex',
         f"[0:v][1:v]xfade=transition=fade:duration={X}:offset={o2:.3f}[a];[a][2:v]xfade=transition=circleopen:duration={X}:offset={o3:.3f}[b];[b][3:v]xfade=transition=slideup:duration={X}:offset={o4:.3f},format=yuv420p[o]",
         '-map', '[o]', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-r', '30', f'{t}/video.mp4'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=pink:duration=0.6:amplitude=0.9', '-af',
         'bandpass=f=900:width_type=o:w=2.2,highpass=f=250,afade=t=in:d=0.32:curve=exp,afade=t=out:st=0.32:d=0.28',
         '-ar', '48000', '-ac', '2', f'{t}/whoosh.wav'])
    inp, fc, labs = [], [], []

    def add(p, flt, at=None):
        if not os.path.exists(p): return
        k = len(labs); inp.extend(['-i', p]); dl = f',adelay={int(at * 1000)}|{int(at * 1000)}' if at is not None else ''
        fc.append(f'[{k}:a]{flt}{dl}[a{k}]'); labs.append(f'[a{k}]')
    add(music, f'atrim=0:{total:.2f},asetpts=PTS-STARTPTS,volume=0.55,afade=t=in:d=0.3,afade=t=out:st={total - 1.2:.2f}:d=1.2')
    add(f'{eff}/app-launch.mp3', 'volume=0.8', 0.0)
    add(f'{t}/whoosh.wav', 'volume=0.6', o2 - 0.1)
    for i in range(3): add(f'{eff}/bubble-connection.mp3', 'volume=0.7', o2 + 0.1 + i * qn)
    add(f'{t}/whoosh.wav', 'volume=0.7', o3 - 0.1)
    add(f'{eff}/vortex.mp3', 'volume=0.5,atrim=0:2,afade=t=out:st=1.5:d=0.5', o3)
    add(f'{t}/whoosh.wav', 'volume=0.6', o4 - 0.1)
    add(f'{eff}/level-complete.mp3', 'volume=0.8', o4 + 0.1)
    fc.append(''.join(labs) + f'amix=inputs={len(labs)}:normalize=0:duration=longest,atrim=0:{total:.2f},alimiter=limit=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[out]')
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '48000', '-ac', '2', f'{t}/mix.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{t}/video.mp4', '-i', f'{t}/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-shortest', '-movflags', '+faststart', out])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '1.5', '-i', out, '-frames:v', '1', '-q:v', '3', out[:-4] + '.jpg'])
    print(json.dumps({'out': out, 'duration': round(total, 2)}, ensure_ascii=False))


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
