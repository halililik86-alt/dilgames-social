#!/usr/bin/env python3
""""Bugünün İfadesi" (Elif + Tom) Reels şablonu: bir İngilizce kalıbın kelimesi kelimesine yanlış anlaşıldığı
mini skeç + "Bugünün ifadesi" bitiş kartı.

Kullanım: python3 scripts/build_ifade_reel.py <reel.json> <çıktı.mp4> [--nomusic]
reel.json alanları (type: "ifade"):
  episode, series, voice_dir, hook: [satır1, satır2?], music, ambience
  scenes: [{clip, start, dur, speed?, subs: [{at, end, speaker, en, tr}], say: [[ses, an]], sfx: [[efekt, an]]}]
  card: {phrase, tr, use, cta, dur, say: [[ses, an]], sfx: [[efekt, an]]}
  Zamanlar sahnenin kendi başlangıcına göredir (saniye).
Görsel: 3B animasyon (Renderforest forest-1.0, referanslar elif.jpg + tom.jpg), ses: ElevenLabs. Oyun müziği yok.
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_reel import C, ROOT, W, H, font, run, wrap  # noqa: E402

FPS = 30
ENC = ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', str(FPS)]
TEAL = (16, 48, 56)
GOLD = C['gold']
SPEAKER = {'Elif': (255, 196, 92), 'Tom': (140, 236, 200), 'Ellie': (255, 196, 92), 'Kerem': (140, 200, 255), 'Anne': (255, 150, 170)}


def label(d, cx, y, text, f, bg, fg, padx=22, pady=10):
    w = d.textlength(text, font=f)
    d.rounded_rectangle([cx - w / 2 - padx, y, cx + w / 2 + padx, y + f.size + 2 * pady], 14, fill=bg)
    d.text((cx, y + pady + f.size / 2), text, font=f, fill=fg, anchor='mm')


def strip(im, r):
    d = ImageDraw.Draw(im); f = font('SemiBold', 26)
    t = f"DilGames  •  {r['series'].title().replace('İ', 'İ')}  /  {r['episode']:02d}"
    w = d.textlength(t, font=f)
    d.rounded_rectangle([50, H - 112, 50 + w + 44, H - 62], 12, fill=(12, 34, 40, 200))
    d.text((72, H - 87), t, font=f, fill=(225, 238, 236), anchor='lm')


def hook_png(path, r):
    """Üstte tek satırlık merak bandı (yüzlerin üstünde kalsın diye ince)."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    text = ' '.join(r['hook']); size = 84
    while size > 56 and d.textlength(text, font=font('Black', size)) > 900: size -= 4
    fh, fc = font('Black', size), font('ExtraBold', 26)
    x0, y0, bh = 50, 46, 86 + size + 26
    d.rounded_rectangle([x0, y0, W - x0, y0 + bh], 30, fill=(14, 40, 46, 228))
    d.rounded_rectangle([x0 + 30, y0 + 24, x0 + 30 + d.textlength(r['series'], font=fc) + 36, y0 + 70], 14, fill=(140, 236, 200, 255))
    d.text((x0 + 48, y0 + 47), r['series'], font=fc, fill=TEAL, anchor='lm')
    d.text((W - x0 - 30, y0 + 47), f"BÖLÜM {r['episode']:02d}", font=fc, fill=(220, 232, 230), anchor='rm')
    d.text((W / 2, y0 + 86), text, font=fh, fill=GOLD, anchor='ma')
    im.save(path)


def sub_png(path, s, r):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fe, ft, fl = font('ExtraBold', 58), font('SemiBold', 42), font('ExtraBold', 28)
    le, lt = wrap(d, s['en'], fe, 940), wrap(d, s.get('tr', ''), ft, 920) if s.get('tr') else []
    bh = 70 + len(le) * 72 + (14 + len(lt) * 54 if lt else 0) + 36
    y0 = H - 150 - bh
    box = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([50, y0, W - 50, y0 + bh], 30, fill=(14, 40, 46, 225))
    im.alpha_composite(box); d = ImageDraw.Draw(im)
    col = SPEAKER.get(s['speaker'], (255, 255, 255))
    d.text((W / 2, y0 + 40), s['speaker'].upper(), font=fl, fill=col, anchor='mm')
    y = y0 + 70
    for ln in le: d.text((W / 2, y), ln, font=fe, fill=(255, 255, 255), anchor='ma'); y += 72
    if lt:
        y += 14
        for ln in lt: d.text((W / 2, y), ln, font=ft, fill=(190, 215, 212), anchor='ma'); y += 54
    strip(im, r)
    im.save(path)


def sitcom_card(im, d, c, path):
    """Sitkom bitişi: ❌ harfiyen çeviri / ✅ doğrusu + sıradaki bölüm (takip sebebi)."""
    RED = (240, 110, 110)
    d.text((W / 2, 455), c.get('kicker', 'BUGÜNÜN DERSİ'), font=font('ExtraBold', 34), fill=(140, 236, 200), anchor='mm')
    fw = font('Black', 64)
    while fw.size > 44 and d.textlength('✗  ' + c['wrong'], font=fw) > 960: fw = font('Black', fw.size - 4)
    y = 520; tw = d.textlength(c['wrong'], font=fw)
    d.text((W / 2, y), c['wrong'], font=fw, fill=RED, anchor='ma')
    d.line([W / 2 - tw / 2 - 10, y + fw.size * 0.62, W / 2 + tw / 2 + 10, y + fw.size * 0.62], fill=RED, width=6)
    y += fw.size + 18
    d.text((W / 2, y), c.get('wrong_note', ''), font=font('Medium', 38), fill=(200, 222, 220), anchor='ma'); y += 90
    size = 104
    while size > 64 and d.textlength(c['right'], font=font('Black', size)) > 960: size -= 4
    d.text((W / 2, y), c['right'], font=font('Black', size), fill=GOLD, anchor='ma'); y += size + 24
    if c.get('alt'):
        d.text((W / 2, y), c['alt'], font=font('SemiBold', 42), fill=(235, 245, 243), anchor='ma'); y += 70
    if c.get('use'):
        for ln in wrap(d, c['use'], font('Medium', 38), 880):
            d.text((W / 2, y), ln, font=font('Medium', 38), fill=(200, 222, 220), anchor='ma'); y += 50
    # sıradaki bölüm kutusu
    by = 1150; box = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([90, by, W - 90, by + 300], 34, fill=(8, 26, 30, 235), outline=GOLD, width=4)
    im.alpha_composite(box); d = ImageDraw.Draw(im)
    label(d, W / 2, by - 28, 'SIRADAKİ BÖLÜM', font('ExtraBold', 30), GOLD + (255,), TEAL)
    fn = font('Black', 72)
    while fn.size > 44 and d.textlength(c['next'], font=fn) > 820: fn = font('Black', fn.size - 4)
    d.text((W / 2, by + 110), c['next'], font=fn, fill=(255, 255, 255), anchor='mm')
    d.text((W / 2, by + 210), c['cta'], font=font('SemiBold', 40), fill=(140, 236, 200), anchor='mm')
    d.text((W / 2, 1650), '@dilgamesapp', font=font('ExtraBold', 60), fill=(140, 236, 200), anchor='mm')
    d.line([W / 2 - 300, 1740, W / 2 + 300, 1740], fill=(70, 110, 116), width=3)
    d.text((W / 2, 1790), 'GÜL  •  ÖĞREN  •  TAKİP ET', font=font('ExtraBold', 26), fill=(200, 222, 220), anchor='mm')
    im.save(path)


def card_png(path, r):
    c = r['card']; im = Image.new('RGBA', (W, H), TEAL + (255,)); d = ImageDraw.Draw(im)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([W - 520, H - 760, W + 380, H + 140], fill=(40, 92, 100, 120))
    ImageDraw.Draw(glow).ellipse([-420, -260, 420, 580], fill=(40, 92, 100, 90))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(80))); d = ImageDraw.Draw(im)
    d.text((80, 150), 'DilGames', font=font('ExtraBold', 44), fill=(235, 245, 243), anchor='lm')
    fb = font('Bold', 32); t = f"{r['episode']:02d}"
    d.rounded_rectangle([W - 190, 122, W - 80, 178], 16, outline=(220, 232, 230), width=3)
    d.text((W - 135, 150), t, font=fb, fill=(220, 232, 230), anchor='mm')
    d.text((W / 2, 300), r['series'], font=font('ExtraBold', 34), fill=(220, 232, 230), anchor='mm')
    d.line([W / 2 - 300, 360, W / 2 + 300, 360], fill=(70, 110, 116), width=3)
    d.line([W / 2 - 300, 360, W / 2 - 140, 360], fill=GOLD, width=5)
    if c.get('wrong'):
        return sitcom_card(im, d, c, path)
    d.text((W / 2, 470), 'BUGÜNÜN İFADESİ', font=font('ExtraBold', 34), fill=(140, 236, 200), anchor='mm')
    size = 150; lines = c['phrase']
    while size > 80 and max(d.textlength(s, font=font('Black', size)) for s in lines) > 940: size -= 6
    y = 540
    for s in lines:
        d.text((W / 2, y), s, font=font('Black', size), fill=GOLD, anchor='ma'); y += size + 16
    y += 30; d.line([W / 2 - 110, y, W / 2 + 110, y], fill=(220, 232, 230), width=4); y += 50
    d.text((W / 2, y), c['tr'], font=font('ExtraBold', 76), fill=(255, 255, 255), anchor='ma'); y += 120
    for ln in wrap(d, c['use'], font('Medium', 42), 860):
        d.text((W / 2, y), ln, font=font('Medium', 42), fill=(200, 222, 220), anchor='ma'); y += 56
    y += 50; label(d, W / 2, y, 'İNGİLİZCE  •  KISA MACERALAR', font('ExtraBold', 28), (8, 26, 30), (230, 240, 238))
    d.text((W / 2, 1560), c['cta'], font=font('SemiBold', 42), fill=(235, 245, 243), anchor='mm')
    d.text((W / 2, 1640), '@dilgamesapp', font=font('ExtraBold', 60), fill=(140, 236, 200), anchor='mm')
    d.line([W / 2 - 300, 1740, W / 2 + 300, 1740], fill=(70, 110, 116), width=3)
    d.text((W / 2, 1790), 'BİR İFADE  •  BİR MACERA', font=font('ExtraBold', 26), fill=(200, 222, 220), anchor='mm')
    im.save(path)


def scene_mp4(tmp, i, sc, r):
    """Bir sahne: klip (hız/kırpma) + altyazı katmanları, tek dosya."""
    src = os.path.join(ROOT, sc['clip']); sp = sc.get('speed', 1.0)
    ins, chain = ['-ss', str(sc.get('start', 0)), '-t', str(sc['dur'] / sp + 0.2), '-i', src], []
    chain.append(f"[0:v]setpts=PTS*{1 / sp:.4f},fps={FPS},scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,"
                 f"crop=1080:1920,setsar=1,trim=duration={sc['dur']}[v0]")
    layers = []
    if i == 0 and r.get('hook'):
        p = os.path.join(tmp, 'hook.png'); hook_png(p, r); layers.append((p, 0, sc.get('hook_until', sc['dur'])))
    for k, s in enumerate(sc.get('subs', [])):
        p = os.path.join(tmp, f's{i}_{k}.png'); sub_png(p, s, r); layers.append((p, s['at'], s.get('end', sc['dur'])))
    if not sc.get('subs'):
        p = os.path.join(tmp, f'strip{i}.png'); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); strip(im, r); im.save(p)
        layers.append((p, 0, sc['dur']))
    last = 'v0'
    for k, (p, a, b) in enumerate(layers):
        ins += ['-i', p]
        chain.append(f"[{last}][{k + 1}:v]overlay=0:0:enable='between(t,{a},{b})'[v{k + 1}]"); last = f'v{k + 1}'
    out = os.path.join(tmp, f'scene{i}.mp4'); part = out[:-4] + '.part.mp4'
    run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(chain), '-map', f'[{last}]', '-an', *ENC, part])
    os.replace(part, out); return out


def card_mp4(tmp, r):
    p = os.path.join(tmp, 'card.png'); card_png(p, r); d = r['card']['dur']
    out = os.path.join(tmp, 'card.mp4'); part = out[:-4] + '.part.mp4'
    run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', p, '-vf',
         f'format=yuv420p,loop=-1:1,trim=duration={d},fade=in:st=0:d=0.25', *ENC, part])
    os.replace(part, out); return out


def speech_segments(path, start=0.0, length=None, noise=-35, gap=0.25):
    """Konuşma (sessiz olmayan) aralıkları, start'a göre göreli: [[s, e], ...]."""
    cmd = ['ffmpeg', '-hide_banner', '-nostats', '-ss', str(start)] + (['-t', str(length)] if length else []) + \
          ['-i', path, '-af', f'silencedetect=n={noise}dB:d={gap}', '-f', 'null', '-']
    out = subprocess.run(cmd, capture_output=True, text=True).stderr
    dur = length or float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                                         capture_output=True, text=True).stdout)
    segs, cur = [], 0.0
    for kind, v in re.findall(r'silence_(start|end): ([0-9.]+)', out):
        v = float(v)
        if kind == 'start':
            if v - cur > 0.08: segs.append([cur, v])
        else:
            cur = v
    if dur - cur > 0.08 and (not segs or segs[-1][1] < cur): segs.append([cur, dur])
    return segs


def merge_to(segs, n):
    segs = [list(x) for x in segs]
    while len(segs) > n:
        k = min(range(len(segs) - 1), key=lambda i: segs[i + 1][0] - segs[i][1])
        segs[k][1] = segs[k + 1][1]; del segs[k + 1]
    return segs


def lipsync_pieces(line, clip, clip_start, win, clip_speed=1.0):
    """ElevenLabs repliğini klibin kendi konuşmasının (dudak hareketinin) üstüne oturt.
    Döner: [(satır_başı, satır_sonu, sahne_içi_an, tempo), ...]"""
    w0, w1 = win
    cs = [[a + w0, b + w0] for a, b in speech_segments(clip, clip_start + w0 * clip_speed, (w1 - w0) * clip_speed)]
    ls = speech_segments(line, gap=0.12)
    if not cs or not ls: return [(0, None, w0, 1.0)]
    n = min(len(cs), len(ls)); cs, ls = merge_to(cs, n), merge_to(ls, n)
    out, end = [], -1.0
    for (la, lb), (ca, cb) in zip(ls, cs):
        tempo = max(0.75, min(1.35, (lb - la) / max(0.2, cb - ca)))
        at = max(ca, end + 0.04)  # parçalar üst üste binmesin
        out.append((la, lb, at, tempo)); end = at + (lb - la) / tempo
    return out


def audio(tmp, r, total, music=True):
    vd = os.path.join(ROOT, r['voice_dir']); ev, t0 = [], 0.0
    sync = []
    for sc in r['scenes']:
        for item in sc.get('say', []):
            name, at = item[0], item[1]
            if at == 'auto':  # dudak senkronu: [id, "auto", pencere_başı, pencere_sonu]
                win = (item[2] if len(item) > 2 else 0.0, item[3] if len(item) > 3 else sc['dur'])
                for la, lb, ca, tempo in lipsync_pieces(os.path.join(vd, name + '.mp3'), os.path.join(ROOT, sc['clip']),
                                                        sc.get('start', 0), win):
                    sync.append((name, t0 + ca, la, lb, tempo))
            else:
                ev.append((name, t0 + at, 1.0))
        for name, at in sc.get('sfx', []): ev.append((name, t0 + at, 0.55))
        t0 += sc['dur']
    scenes_end = t0
    for name, at in r['card'].get('say', []): ev.append((name, t0 + at, 1.0))
    for name, at in r['card'].get('sfx', []): ev.append((name, t0 + at, 0.55))
    ins, parts = [], []
    for k, (name, at, vol) in enumerate(ev):
        ins += ['-i', os.path.join(vd, name + '.mp3')]
        ms = int(at * 1000); parts.append(f'[{k}:a]aresample=44100,volume={vol},adelay={ms}|{ms}[e{k}]')
    for j, (name, at, la, lb, tempo) in enumerate(sync):
        k = len(ev) + j; ins += ['-i', os.path.join(vd, name + '.mp3')]; ms = int(at * 1000)
        cut = f'atrim={la}:{lb},' if lb else f'atrim={la},'
        parts.append(f'[{k}:a]aresample=44100,{cut}asetpts=PTS-STARTPTS,atempo={tempo:.3f},adelay={ms}|{ms}[e{k}]')
    labels = [f'[e{k}]' for k in range(len(ev) + len(sync))]; n = len(ev) + len(sync)
    if r.get('ambience'):
        ins += ['-i', os.path.join(vd, r['ambience'] + '.mp3')]
        parts.append(f'[{n}:a]aresample=44100,volume=0.32,atrim=0:{scenes_end},afade=t=out:st={scenes_end - 0.6}:d=0.6[amb]')
        labels.append('[amb]'); n += 1
    if music and r.get('music'):
        ins += ['-stream_loop', '-1', '-i', os.path.join(vd, r['music'] + '.mp3')]
        parts.append(f'[{n}:a]aresample=44100,volume=0.16,atrim=0:{total},afade=t=out:st={total - 1.2}:d=1.2[mus]')
        labels.append('[mus]'); n += 1
    parts.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{total},'
                 'alimiter=limit=0.95,aformat=channel_layouts=stereo[a]')
    out = os.path.join(tmp, 'mix.m4a')
    run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', ';'.join(parts), '-map', '[a]', '-c:a', 'aac', '-b:a', '192k', out])
    return out


def main():
    spec, out = sys.argv[1], sys.argv[2]; music = '--nomusic' not in sys.argv
    r = json.load(open(spec, encoding='utf-8'))
    with tempfile.TemporaryDirectory() as tmp:
        files = [scene_mp4(tmp, i, sc, r) for i, sc in enumerate(r['scenes'])] + [card_mp4(tmp, r)]
        lst = os.path.join(tmp, 'list.txt'); open(lst, 'w').write(''.join(f"file '{f}'\n" for f in files))
        vid = os.path.join(tmp, 'v.mp4'); run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', vid])
        total = sum(sc['dur'] for sc in r['scenes']) + r['card']['dur']
        a = audio(tmp, r, total, music)
        part = out[:-4] + '.part.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', a, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy',
             '-shortest', '-movflags', '+faststart', part])
        os.replace(part, out)
    print(out, f'{total:.2f} sn')


if __name__ == '__main__':
    main()
