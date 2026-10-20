#!/usr/bin/env python3
""""Deyim Düellosu" Reels şablonu: Türkçe deyimin kelimesi kelimesine canlandırması ↔ İngilizce karşılığının canlandırması.

Kullanım: python3 scripts/build_duel_reel.py <reel.json> <çıktı.mp4>
reel.json alanları (type: "duel"):
  tr: {idiom, literal_en, clip}     clip: repo içindeki AI klip yolu (ör. assets/ai/<id>-tr.mp4)
  en: {idiom, literal_tr, clip}
  meaning, example_en, example_tr, episode (sayı)
Ses: oyunun müziği + oyunun efektleri + sentez geçiş sesi. İnsan sesi yok.
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_reel import BRAND, C, ROOT, W, H, font, shadow_text, wrap, run  # noqa: E402

TR_RED = (227, 66, 66); EN_BLUE = (76, 132, 232)


def chip(d, xy, text, f, fill, fg):
    tw = d.textlength(text, font=f); x, y = xy; h = f.size + 30
    d.rounded_rectangle([x - tw / 2 - 26, y, x + tw / 2 + 26, y + h], radius=h / 2, fill=fill)
    d.text((x, y + h / 2), text, font=f, fill=fg, anchor='mm')
    return y + h


def text_block(im, y, text, f, fill, maxw=940, lh=None, blur=10):
    d = ImageDraw.Draw(im); lh = lh or int(f.size * 1.18)
    for ln in wrap(d, text, f, maxw):
        shadow_text(im, (W / 2, y), ln, f, fill, blur=blur, offset=5); y += lh
    return y


def series_tag(im, ep):
    d = ImageDraw.Draw(im)
    f = font('ExtraBold', 34)
    label = f'DEYİM DÜELLOSU #{ep}' if ep else 'DEYİM DÜELLOSU'
    chip(d, (W / 2, 150), label, f, C['navy'] + (220,), C['mint'])


def overlay_tr(path, s):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); series_tag(im, s.get('episode'))
    d = ImageDraw.Draw(im)
    y = chip(d, (W / 2, 260), 'TÜRKÇE', font('ExtraBold', 36), TR_RED + (255,), (255, 255, 255)) + 24
    text_block(im, y, s['tr']['idiom'], font('ExtraBold', 86), C['white'])
    im.save(path)


def overlay_tr_literal(path, s):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    band = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(band).rectangle([0, 1180, W, 1470], fill=(6, 18, 30, 170))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(30)))
    shadow_text(im, (W / 2, 1220), 'Kelimesi kelimesine çevirirsek:', font('SemiBold', 44), C['mint'])
    text_block(im, 1290, '“' + s['tr']['literal_en'] + '”', font('ExtraBold', 62), C['white'], maxw=880, lh=74)
    im.save(path)


def overlay_question(path, n=None):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shade = Image.new('RGBA', (W, H), (4, 14, 24, 150)); im.alpha_composite(shade)
    y = text_block(im, 640, 'Peki İngilizler', font('ExtraBold', 96), C['white'])
    y = text_block(im, y, 'ne der?', font('ExtraBold', 96), C['gold'])
    shadow_text(im, (W / 2, y + 40), 'Tahminini yoruma yaz', font('SemiBold', 48), C['mint'])
    if n:
        d = ImageDraw.Draw(im); cx, cy, r = W / 2, y + 260, 110
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=C['mint'] + (235,), outline=(255, 255, 255, 220), width=6)
        d.text((cx, cy), str(n), font=font('ExtraBold', 120), fill=C['navy'], anchor='mm')
    im.save(path)


def overlay_en(path, s):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); series_tag(im, s.get('episode'))
    d = ImageDraw.Draw(im)
    y = chip(d, (W / 2, 260), 'İNGİLİZCE', font('ExtraBold', 36), EN_BLUE + (255,), (255, 255, 255)) + 24
    text_block(im, y, s['en']['idiom'], font('ExtraBold', 80), C['white'], lh=92)
    band = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(band).rectangle([0, 1200, W, 1460], fill=(6, 18, 30, 160))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(30)))
    shadow_text(im, (W / 2, 1240), 'Kelimesi kelimesine:', font('SemiBold', 42), C['mint'])
    text_block(im, 1300, '“' + s['en']['literal_tr'] + '”', font('ExtraBold', 54), C['white'], maxw=880, lh=64)
    im.save(path)


def meaning_card(path, s):
    bg = Image.new('RGB', (W, H), C['navy']); im = bg.convert('RGBA')
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([-200, 300, W + 200, 1500], fill=(40, 110, 120, 120))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(120))); series_tag(im, s.get('episode'))
    d = ImageDraw.Draw(im)
    y = 250
    y = chip(d, (W / 2, y), 'İKİSİ DE AYNI ANLAMDA', font('ExtraBold', 36), C['gold'] + (255,), C['navy']) + 40
    y = text_block(im, y, s['tr']['idiom'], font('ExtraBold', 64), C['white'], lh=74, blur=6)
    y = text_block(im, y + 6, '=', font('ExtraBold', 60), C['mint'], blur=6)
    y = text_block(im, y + 6, s['en']['idiom'], font('ExtraBold', 64), C['white'], lh=74, blur=6) + 30
    y = text_block(im, y, 'Anlamı: ' + s['meaning'], font('Medium', 46), (200, 225, 228), lh=58, blur=4) + 50
    box_top = y
    dm = ImageDraw.Draw(im)
    n_en = len(wrap(dm, s['example_en'], font('SemiBold', 46), 820)); n_tr = len(wrap(dm, s['example_tr'], font('Medium', 38), 820))
    box_h = 34 + n_en * 58 + 12 + n_tr * 48 + 30
    box = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([90, box_top, W - 90, box_top + box_h], radius=36, fill=(255, 255, 255, 26), outline=C['mint'] + (140,), width=3)
    im.alpha_composite(box)
    yy = text_block(im, box_top + 34, s['example_en'], font('SemiBold', 46), C['white'], maxw=820, lh=58, blur=2)
    text_block(im, yy + 12, s['example_tr'], font('Medium', 38), (170, 200, 205), maxw=820, lh=48, blur=2)
    d = ImageDraw.Draw(im)
    f = font('ExtraBold', 50); t = 'Bilmeyen arkadaşına gönder'; tw = d.textlength(t, font=f)
    d.rounded_rectangle([W / 2 - tw / 2 - 56, 1360, W / 2 + tw / 2 + 56, 1470], radius=55, fill=C['mint'])
    d.text((W / 2, 1415), t, font=f, fill=C['navy'], anchor='mm')
    icon = Image.open(os.path.join(ROOT, BRAND['icon'])).convert('RGBA').resize((84, 84), Image.LANCZOS)
    m = Image.new('L', (84, 84), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 83, 83], radius=20, fill=255)
    im.paste(icon, (int(W / 2 - 210), 1500), m); d = ImageDraw.Draw(im)
    d.text((W / 2 - 110, 1542), 'DilGames · oyunla İngilizce', font=font('SemiBold', 38), fill=(200, 225, 228), anchor='lm')
    im.convert('RGB').save(path)


def build(spec_path, out):
    s = json.load(open(spec_path, encoding='utf-8'))
    dist = os.environ.get('GAME_DIST', os.path.join(ROOT, '..', 'dilgame', 'dist'))
    eff = os.path.join(dist, BRAND['game_audio']['effects_dir']); music = os.path.join(dist, BRAND['game_audio']['music'])
    t = tempfile.mkdtemp(prefix='duel-')
    clip_tr = os.path.join(ROOT, s['tr']['clip']); clip_en = os.path.join(ROOT, s['en']['clip'])
    overlay_tr(f'{t}/tr.png', s); overlay_tr_literal(f'{t}/trl.png', s); overlay_en(f'{t}/en.png', s); meaning_card(f'{t}/m.png', s)
    for n in (3, 2, 1): overlay_question(f'{t}/q{n}.png', n)
    D_TR, D_Q, D_EN, D_M = 5.0, 2.4, 5.0, 4.4
    up = 'scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920,fps=30,setsar=1'
    # 1) Türkçe sahne
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', clip_tr, '-loop', '1', '-t', str(D_TR), '-i', f'{t}/tr.png', '-loop', '1', '-t', str(D_TR), '-i', f'{t}/trl.png',
         '-filter_complex', f"[0:v]trim=0:{D_TR},setpts=PTS-STARTPTS,{up}[v];[1:v]format=rgba,fade=in:st=0.15:d=0.35:alpha=1[a];[2:v]format=rgba,fade=in:st=1.9:d=0.4:alpha=1[b];[v][a]overlay[v1];[v1][b]overlay,format=yuv420p[o]",
         '-map', '[o]', '-an', '-t', str(D_TR), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s1.mp4'])
    # 2) Soru + geri sayım (Türkçe klibin son karesi donuk + bulanık)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-sseof', '-0.1', '-i', clip_tr, '-frames:v', '1', f'{t}/last.png'])
    qn = D_Q / 3
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', str(D_Q), '-i', f'{t}/last.png', '-loop', '1', '-t', str(qn), '-i', f'{t}/q3.png',
         '-loop', '1', '-t', str(qn), '-i', f'{t}/q2.png', '-loop', '1', '-t', str(qn), '-i', f'{t}/q1.png', '-filter_complex',
         f"[0:v]{up},gblur=sigma=18[bg];[1:v][2:v][3:v]concat=n=3:v=1:a=0,format=rgba[q];[bg][q]overlay,format=yuv420p[o]",
         '-map', '[o]', '-t', str(D_Q), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s2.mp4'])
    # 3) İngilizce sahne
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', clip_en, '-loop', '1', '-t', str(D_EN), '-i', f'{t}/en.png',
         '-filter_complex', f"[0:v]trim=0:{D_EN},setpts=PTS-STARTPTS,{up}[v];[1:v]format=rgba,fade=in:st=0.1:d=0.35:alpha=1[a];[v][a]overlay,format=yuv420p[o]",
         '-map', '[o]', '-an', '-t', str(D_EN), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s3.mp4'])
    # 4) Anlam kartı
    run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', str(D_M), '-i', f'{t}/m.png', '-filter_complex',
         f"[0:v]scale=1134:2016,zoompan=z='1.05-0.05*on/{int(D_M * 30)}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,format=yuv420p[o]",
         '-map', '[o]', '-t', str(D_M), '-c:v', 'libx264', '-crf', '16', '-r', '30', f'{t}/s4.mp4'])
    X = 0.25
    o2 = D_TR - X; o3 = o2 + D_Q - X; o4 = o3 + D_EN - X; total = o4 + D_M
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{t}/s1.mp4', '-i', f'{t}/s2.mp4', '-i', f'{t}/s3.mp4', '-i', f'{t}/s4.mp4', '-filter_complex',
         f"[0:v][1:v]xfade=transition=fade:duration={X}:offset={o2:.3f}[a];[a][2:v]xfade=transition=circleopen:duration={X}:offset={o3:.3f}[b];[b][3:v]xfade=transition=slideup:duration={X}:offset={o4:.3f},format=yuv420p[o]",
         '-map', '[o]', '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-r', '30', f'{t}/video.mp4'])
    # Ses: oyun müziği + efektler + geri sayım tıkları
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=pink:duration=0.6:amplitude=0.9', '-af',
         'bandpass=f=900:width_type=o:w=2.2,highpass=f=250,afade=t=in:d=0.32:curve=exp,afade=t=out:st=0.32:d=0.28',
         '-ar', '48000', '-ac', '2', f'{t}/whoosh.wav'])
    inp, fc, labs = [], [], []
    def add(p, flt, at=None):
        if not os.path.exists(p): return
        k = len(labs); inp.extend(['-i', p]); dl = f',adelay={int(at * 1000)}|{int(at * 1000)}' if at is not None else ''
        fc.append(f'[{k}:a]{flt}{dl}[a{k}]'); labs.append(f'[a{k}]')
    add(music, f'atrim=0:{total:.2f},asetpts=PTS-STARTPTS,volume=0.55,afade=t=in:d=0.4,afade=t=out:st={total - 1.2:.2f}:d=1.2')
    add(f'{eff}/app-launch.mp3', 'volume=0.8', 0.05)
    add(f'{eff}/bubble-connection.mp3', 'volume=0.9', 1.9)
    add(f'{t}/whoosh.wav', 'volume=0.6', o2 - 0.1)
    for i in range(3): add(f'{eff}/bubble-connection.mp3', 'volume=0.7,atempo=1.0', o2 + 0.1 + i * qn)
    add(f'{t}/whoosh.wav', 'volume=0.7', o3 - 0.1)
    add(f'{eff}/vortex.mp3', 'volume=0.5,atrim=0:2,afade=t=out:st=1.5:d=0.5', o3)
    add(f'{t}/whoosh.wav', 'volume=0.6', o4 - 0.1)
    add(f'{eff}/level-complete.mp3', 'volume=0.8', o4 + 0.1)
    fc.append(''.join(labs) + f'amix=inputs={len(labs)}:normalize=0:duration=longest,atrim=0:{total:.2f},alimiter=limit=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[out]')
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '48000', '-ac', '2', f'{t}/mix.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{t}/video.mp4', '-i', f'{t}/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-shortest', '-movflags', '+faststart', out])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '2.6', '-i', out, '-frames:v', '1', '-q:v', '3', out[:-4] + '.jpg'])
    print(json.dumps({'out': out, 'duration': round(total, 2)}, ensure_ascii=False))


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
