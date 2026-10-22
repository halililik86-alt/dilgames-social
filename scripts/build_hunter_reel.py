#!/usr/bin/env python3
""""Kelime Avcısı" Reels şablonu (prototip): maskot Popi, ekrana dağılmış kelime bloklarını doğru sırayla toplayıp cümleyi kurar.

Kullanım: python3 scripts/build_hunter_reel.py <reel.json> <çıktı.mp4>
reel.json alanları (type: "hunter"):
  episode, level, tr (Türkçe cümle), words (doğru sıradaki İngilizce kelimeler),
  traps: [{"word": "sleep", "after": 2}]   -> 2. kelimeden sonra Popi bu tuzağa çarpar (can gider)
  pause: {"after": 3, "decoy": "on"}       -> 3. kelimeden sonra "Durdur! under mı on mu?" duraklaması
  layout: {"<kelime>": [x, y], ...}        -> isteğe bağlı blok konumları (yoksa otomatik)
Tamamen koddan çizilir (Renderforest kredisi yok). Ses: oyunun müziği + efektleri + sentez sesler. İnsan sesi yok.
"""
import json, math, os, random, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_reel import BRAND, C, ROOT, W, H, font, run  # noqa: E402

FPS = 30
NAVY, MINT, GOLD, WHITE = C['navy'], C['mint'], C['gold'], C['white']
RED = (235, 84, 84); BLOCK = (22, 64, 88); TEAL = (40, 150, 140)
PLAY_TOP, PLAY_BOT = 430, 1450


def ease(t):
    return t * t * (3 - 2 * t)


def star(d, cx, cy, r, fill, rot=0):
    pts = []
    for i in range(10):
        a = rot - math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def heart(d, cx, cy, s, fill):
    d.ellipse([cx - s, cy - s * 0.8, cx, cy + s * 0.2], fill=fill)
    d.ellipse([cx, cy - s * 0.8, cx + s, cy + s * 0.2], fill=fill)
    d.polygon([(cx - s * 0.98, cy - 0.15 * s), (cx + s * 0.98, cy - 0.15 * s), (cx, cy + s)], fill=fill)


# ---------- maskot: Popi (balon yaratık) ----------
def popi_sprite(sx=1.0, sy=1.0, look=(0, 0), mood='happy', bob=0.0):
    S = 2  # 2x çizip küçült (yumuşak kenar)
    im = Image.new('RGBA', (220 * S, 260 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, base = 110 * S, 250 * S
    bw, bh = 150 * S * sx, 138 * S * sy
    top = base - 16 * S - bh
    # ayaklar
    for fx in (-34, 34):
        d.ellipse([cx + fx * S * sx - 24 * S, base - 26 * S, cx + fx * S * sx + 24 * S, base], fill=(28, 120, 112))
    # anten + yıldız
    ax, ay = cx + 6 * S, top + 6 * S
    sty = top - 46 * S + bob * 6 * S
    d.line([(ax, ay), (ax + 8 * S, sty + 14 * S)], fill=(28, 120, 112), width=6 * S)
    star(d, ax + 8 * S, sty, 20 * S, GOLD, rot=bob * 0.6)
    # gövde
    d.ellipse([cx - bw / 2, top, cx + bw / 2, top + bh], fill=(28, 120, 112))
    d.ellipse([cx - bw / 2 + 7 * S, top + 7 * S, cx + bw / 2 - 7 * S, top + bh - 7 * S], fill=(96, 214, 186))
    d.ellipse([cx - bw / 2 + 24 * S, top + 18 * S, cx - 4 * S, top + bh * 0.42], fill=(170, 244, 222))
    # yanaklar
    for fx in (-48, 48):
        d.ellipse([cx + fx * S - 13 * S, top + bh * 0.62 - 7 * S, cx + fx * S + 13 * S, top + bh * 0.62 + 7 * S], fill=(250, 150, 160))
    # gözler
    ey = top + bh * 0.42
    for fx in (-28, 28):
        ex = cx + fx * S * sx
        if mood == 'dizzy':
            for k in (-1, 1):
                d.line([(ex - 13 * S, ey - 13 * S * k), (ex + 13 * S, ey + 13 * S * k)], fill=NAVY, width=7 * S)
        else:
            d.ellipse([ex - 20 * S, ey - 24 * S, ex + 20 * S, ey + 24 * S], fill=(255, 255, 255))
            px, py = ex + look[0] * 8 * S, ey + look[1] * 8 * S + 2 * S
            d.ellipse([px - 11 * S, py - 13 * S, px + 11 * S, py + 13 * S], fill=NAVY)
            d.ellipse([px - 4 * S, py - 9 * S, px + 2 * S, py - 3 * S], fill=(255, 255, 255))
    # ağız
    my = top + bh * 0.68
    if mood == 'dizzy':
        d.arc([cx - 18 * S, my, cx + 18 * S, my + 22 * S], 200, 340, fill=NAVY, width=6 * S)
    elif mood == 'yay':
        d.chord([cx - 24 * S, my - 8 * S, cx + 24 * S, my + 30 * S], 0, 180, fill=NAVY)
    else:
        d.arc([cx - 20 * S, my - 12 * S, cx + 20 * S, my + 16 * S], 20, 160, fill=NAVY, width=6 * S)
    return im.resize((220, 260), Image.LANCZOS)


# ---------- blok ----------
def block_img(word, state='idle', f=None):
    f = f or font('ExtraBold', 52)
    tw = ImageDraw.Draw(Image.new('L', (1, 1))).textlength(word, font=f)
    w, h = int(tw + 64), 100
    im = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fill, out = (BLOCK, MINT) if state != 'bad' else ((120, 40, 48), RED)
    if state == 'hint': out = GOLD
    d.rounded_rectangle([10, 16, w + 10, h + 16], radius=26, fill=(5, 20, 32, 160))
    d.rounded_rectangle([10, 10, w + 10, h + 10], radius=26, fill=fill + (255,), outline=out, width=5 if state == 'hint' else 4)
    d.text((10 + w / 2, 10 + h / 2), word, font=f, fill=WHITE, anchor='mm')
    return im


def auto_layout(words):
    rnd = random.Random(7); pos = {}
    cols, rows = 3, max(3, math.ceil(len(words) / 3))
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    rnd.shuffle(cells)
    for w, (c, r) in zip(words, cells):
        x = 200 + c * 340 + rnd.randint(-40, 40)
        y = PLAY_TOP + 120 + r * ((PLAY_BOT - PLAY_TOP - 200) / max(1, rows - 1)) + rnd.randint(-30, 30)
        pos[w] = (x, y)
    return pos


def background():
    bg = Image.new('RGB', (W, H), NAVY); d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(10 + 6 * k), int(30 + 18 * (1 - k)), int(48 + 14 * (1 - k))))
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for x in range(0, W, 60):
        for y in range(PLAY_TOP, PLAY_BOT, 60):
            gd.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(140, 236, 200, 26))
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).ellipse([-150, 500, W + 150, 1500], fill=(40, 120, 130, 70))
    out = bg.convert('RGBA'); out.alpha_composite(gl.filter(ImageFilter.GaussianBlur(140))); out.alpha_composite(g)
    return out


def build(spec_path, out):
    s = json.load(open(spec_path, encoding='utf-8'))
    words = s['words']; traps = s.get('traps', []); pause = s.get('pause')
    all_blocks = words + [t['word'] for t in traps] + ([pause['decoy']] if pause and pause['decoy'] not in [t['word'] for t in traps] else []) + [w for w in s.get('decoys', []) if w not in words]
    pos = {k: tuple(v) for k, v in s.get('layout', {}).items()} or auto_layout(all_blocks)
    f_block = font('ExtraBold', 52)
    imgs = {w: {st: block_img(w, st, f_block) for st in ('idle', 'bad', 'hint')} for w in all_blocks}

    # ---- zaman çizelgesi ----
    HOOK, ENTER, HOP, LAND, FLY = 1.7, 0.6, 0.5, 0.18, 0.35
    t = HOOK + ENTER
    start = (W / 2, PLAY_BOT + 30)
    path = [(0.0, start, start, 'idle')]  # (t0, from, to, kind)
    events, sfx = [], [('app-launch', 0.0)]
    cur = start; lives = 3; got = 0
    plan = []
    for i, w in enumerate(words):
        for tr in traps:
            if tr['after'] == i: plan.append(('trap', tr['word']))
        if pause and pause['after'] == i: plan.append(('pause', (w, pause['decoy'])))
        plan.append(('get', w))
    for kind, w in plan:
        if kind == 'pause':
            events.append(('pause', t, t + 1.9, w)); sfx.append(('vortex', t)); [sfx.append(('tick', t + 0.4 + k * 0.5)) for k in range(3)]
            path.append((t, cur, cur, 'wait')); t += 1.9; continue
        tgt = (pos[w][0], pos[w][1] - 92)
        path.append((t, cur, tgt, 'hop')); t += HOP
        if kind == 'trap':
            lives -= 1; events.append(('trap', t, w, lives)); sfx.append(('bonk', t))
            path.append((t, tgt, tgt, 'dizzy')); t += 0.7
            cur = tgt
        else:
            got += 1; events.append(('get', t, w, got - 1)); sfx.append(('pop', t))
            path.append((t, tgt, tgt, 'land')); t += LAND
            cur = tgt
    t_done = t + 0.15; sfx.append(('level-complete', t_done)); events.append(('done', t_done))
    path.append((t_done, cur, cur, 'yay'))
    t_end = t_done + 2.3; total = t_end + 3.0
    sfx.append(('whoosh', t_end - 0.1))

    # ---- sabit katmanlar ----
    bg = background()
    f_hud, f_tr, f_slot = font('ExtraBold', 34), font('SemiBold', 44), font('ExtraBold', 40)
    slot_w, gap = 0, 10
    dd = ImageDraw.Draw(Image.new('L', (1, 1)))
    widths = [dd.textlength(w, font=f_slot) + 44 for w in words]
    scale = min(1.0, (W - 80 - gap * (len(words) - 1)) / sum(widths)); widths = [w_ * scale for w_ in widths]
    x0 = (W - sum(widths) - gap * (len(words) - 1)) / 2; slots = []
    for w_ in widths: slots.append((x0, x0 + w_)); x0 += w_ + gap
    SLOT_Y = 1560

    rng = random.Random(3); bubbles = [(rng.randint(0, W), rng.randint(0, H), rng.randint(8, 26), rng.uniform(20, 60)) for _ in range(16)]
    sprites = {}

    def popi(sx, sy, look, mood, bob):
        k = (round(sx, 2), round(sy, 2), look, mood, round(bob, 1))
        if k not in sprites: sprites[k] = popi_sprite(sx, sy, look, mood, bob)
        return sprites[k]

    tmp = tempfile.mkdtemp(prefix='hunter-')
    vid = os.path.join(tmp, 'video.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p', vid], stdin=subprocess.PIPE)
    end_card = None
    nfr = int(total * FPS)
    for fi in range(nfr):
        T = fi / FPS
        if T >= t_end:
            if end_card is None: end_card = make_end_card(s, lives)
            k = min(1, (T - t_end) / 0.3)
            frame = end_card if k >= 1 else Image.blend(last.convert('RGB'), end_card.convert('RGB'), k).convert('RGBA')
            ff.stdin.write(frame.convert('RGB').tobytes()); continue
        fr = bg.copy(); d = ImageDraw.Draw(fr)
        # yüzen balonlar
        bl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
        for bx, by, br, sp in bubbles:
            y = (by - T * sp) % H
            bd.ellipse([bx - br, y - br, bx + br, y + br], outline=(140, 236, 200, 60), width=3)
        fr.alpha_composite(bl)
        # durum
        taken = {e[2]: e for e in events if e[0] == 'get' and e[1] <= T}
        hit = {e[2]: e for e in events if e[0] == 'trap' and e[1] <= T}
        lives_now = 3 - len(hit)
        pz = next((e for e in events if e[0] == 'pause' and e[1] <= T < e[2]), None)
        shake = 0
        for e in hit.values():
            if T - e[1] < 0.3: shake = int(14 * (1 - (T - e[1]) / 0.3) * math.sin(T * 90))
        # HUD
        d.rounded_rectangle([40, 60, 470, 130], radius=35, fill=NAVY + (230,), outline=MINT, width=3)
        d.text((255, 95), f"KELİME AVCISI #{s.get('episode', 1)} · {s['level']}", font=f_hud, fill=MINT, anchor='mm')
        for i in range(3):
            heart(d, W - 230 + i * 70, 92, 26, RED if i < lives_now else (60, 80, 95))
        d.text((W / 2, 205), 'Türkçesi:', font=font('SemiBold', 34), fill=(170, 200, 205), anchor='mm')
        d.text((W / 2, 262), s['tr'], font=f_tr, fill=WHITE, anchor='mm')
        d.line([(120, 330), (W - 120, 330)], fill=(140, 236, 200, 60), width=2)
        # bloklar
        for w in all_blocks:
            if w in taken and T - taken[w][1] > FLY: continue
            x, y = pos[w]
            st = 'bad' if w in hit else ('hint' if pz and w in pz[3] else 'idle')
            im = imgs[w][st]
            if w in taken:  # slota uçuş
                k = ease(min(1, (T - taken[w][1]) / FLY)); sl = slots[taken[w][3]]
                tx, ty = (sl[0] + sl[1]) / 2, SLOT_Y + 50
                x, y = x + (tx - x) * k, y + (ty - y) * k
                im = im.resize((max(1, int(im.width * (1 - 0.35 * k))), max(1, int(im.height * (1 - 0.35 * k)))))
            if w in hit:
                a = max(0, 1 - (T - hit[w][1]) / 1.2)
                im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * (0.25 + 0.75 * a))))
            if st == 'hint':
                p = 1 + 0.06 * math.sin(T * 12); im = im.resize((int(im.width * p), int(im.height * p)))
            fr.alpha_composite(im, (int(x - im.width / 2) + shake, int(y - im.height / 2)))
        # cümle çubuğu
        d.rounded_rectangle([24, SLOT_Y - 30, W - 24, SLOT_Y + 130], radius=32, fill=(6, 18, 30, 200), outline=(140, 236, 200, 90), width=3)
        done = next((e for e in events if e[0] == 'done' and e[1] <= T), None)
        for i, (a, b) in enumerate(slots):
            filled = any(e[3] == i and T - e[1] >= FLY for e in taken.values())
            col = (TEAL if not done else (60, 170, 120))
            if filled:
                d.rounded_rectangle([a, SLOT_Y + 10, b, SLOT_Y + 90], radius=20, fill=col)
                d.text(((a + b) / 2, SLOT_Y + 50), words[i], font=f_slot if scale == 1 else font('ExtraBold', int(40 * scale)), fill=WHITE, anchor='mm')
            else:
                d.rounded_rectangle([a, SLOT_Y + 10, b, SLOT_Y + 90], radius=20, outline=(140, 236, 200, 110), width=3)
        # Popi
        seg = max((p for p in path if p[0] <= T), key=lambda p: p[0])
        t0, a, b, kind = seg
        u = min(1, (T - t0) / HOP) if kind == 'hop' else 1
        if T < HOOK: px, py = start[0], start[1] + 700  # ekran dışında
        elif T < HOOK + ENTER:
            k = ease((T - HOOK) / ENTER); px, py = start[0], start[1] + 700 * (1 - k) - 160 * math.sin(math.pi * k)
        else:
            px = a[0] + (b[0] - a[0]) * ease(u); py = a[1] + (b[1] - a[1]) * ease(u) - (190 * math.sin(math.pi * u) if kind == 'hop' else 0)
        sx = sy = 1.0; mood = 'happy'; look = (0, 0)
        if kind == 'hop':
            sy = 1.08 - 0.08 * abs(math.cos(math.pi * u)); sx = 2 - sy; look = (1 if b[0] > a[0] else -1, -1 if b[1] < a[1] else 1)
        elif kind in ('land', 'idle', 'wait'):
            k = min(1, (T - t0) / 0.15); sy = 0.86 + 0.14 * k; sx = 2 - sy
            if kind == 'wait': look = (int(math.copysign(1, math.sin(T * 6))), 0)
        elif kind == 'dizzy':
            mood = 'dizzy'; sy = 0.92
        elif kind == 'yay':
            mood = 'yay'; py -= abs(math.sin((T - t0) * 9)) * 60
        sp = popi(sx, sy, look, mood, math.sin(T * 5))
        fr.alpha_composite(sp, (int(px - 110) + shake, int(py - 250 + 40)))
        if kind == 'dizzy':
            for k in range(3):
                ang = T * 8 + k * 2.1; star(d, px + 70 * math.cos(ang), py - 190 + 18 * math.sin(ang), 13, GOLD)
        # kanca yazısı
        if T < HOOK + 0.3:
            a_ = 1 if T < HOOK else 1 - (T - HOOK) / 0.3
            ov = Image.new('RGBA', (W, H), (4, 14, 24, int(150 * a_))); od = ImageDraw.Draw(ov)
            od.text((W / 2, 820), 'Popi bu cümleyi', font=font('ExtraBold', 92), fill=WHITE + (int(255 * a_),), anchor='mm')
            od.text((W / 2, 930), 'kurabilecek mi?', font=font('ExtraBold', 92), fill=GOLD + (int(255 * a_),), anchor='mm')
            od.text((W / 2, 1050), '3 can · tuzaklara dikkat!', font=font('SemiBold', 50), fill=MINT + (int(255 * a_),), anchor='mm')
            fr.alpha_composite(ov)
        # duraklama
        if pz:
            k = min(1, (T - pz[1]) / 0.2)
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rounded_rectangle([90, 360, W - 90, 520], radius=40, fill=(10, 30, 48, int(235 * k)), outline=GOLD + (int(255 * k),), width=5)
            od.text((W / 2, 412), 'DURDUR! Sıradaki blok hangisi?', font=font('ExtraBold', 50), fill=WHITE + (int(255 * k),), anchor='mm')
            n = 3 - int((T - pz[1] - 0.4) / 0.5) if T - pz[1] > 0.4 else 3
            od.text((W / 2, 476), f"{pz[3][0]} mı, {pz[3][1]} mu?  {max(1, n)}", font=font('SemiBold', 44), fill=GOLD + (int(255 * k),), anchor='mm')
            fr.alpha_composite(ov)
        # bitiş
        if done:
            k = min(1, (T - done[1]) / 0.35)
            ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rounded_rectangle([110, 640, W - 110, 900], radius=44, fill=(10, 30, 48, int(235 * k)), outline=MINT + (int(255 * k),), width=5)
            od.text((W / 2, 715), 'SEVİYE TAMAM!', font=font('ExtraBold', 84), fill=GOLD + (int(255 * k),), anchor='mm')
            for i in range(3):
                star(od, W / 2 - 90 + i * 90, 820, 34, (GOLD if i < lives_now else (70, 90, 100)) + (int(255 * k),))
            od.text((W / 2, SLOT_Y + 170), s['tr'], font=font('Medium', 40), fill=(200, 225, 228, int(255 * k)), anchor='mm')
            for j in range(18):  # konfeti balonlar
                ang = j * 2 * math.pi / 18; r = 80 + 900 * (T - done[1]) * (0.6 + 0.4 * ((j * 37) % 10) / 10)
                cx_, cy_ = W / 2 + r * math.cos(ang), 760 + r * math.sin(ang) * 0.8
                rr = 18 * max(0, 1 - (T - done[1]) / 1.6)
                if rr > 1: od.ellipse([cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr], fill=(MINT if j % 2 else GOLD) + (220,))
            fr.alpha_composite(ov)
        d = ImageDraw.Draw(fr)
        d.text((W / 2, 1830), 'DilGames · oyunla İngilizce', font=font('SemiBold', 36), fill=(170, 200, 205), anchor='mm')
        last = fr
        ff.stdin.write(fr.convert('RGB').tobytes())
    ff.stdin.close(); ff.wait()

    # ---- ses ----
    dist = os.environ.get('GAME_DIST', os.path.join(ROOT, '..', 'dilgame', 'dist'))
    eff = os.path.join(dist, BRAND['game_audio']['effects_dir']); music = os.path.join(dist, BRAND['game_audio']['music'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'sine=f=180:d=0.35', '-af', 'asetrate=48000*0.8,aresample=48000,afade=t=out:st=0.05:d=0.3,volume=2.2', '-ac', '2', f'{tmp}/bonk.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'sine=f=1320:d=0.07', '-af', 'afade=t=out:st=0.02:d=0.05,volume=0.6', '-ar', '48000', '-ac', '2', f'{tmp}/tick.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=pink:duration=0.6:amplitude=0.9', '-af',
         'bandpass=f=900:width_type=o:w=2.2,highpass=f=250,afade=t=in:d=0.32:curve=exp,afade=t=out:st=0.32:d=0.28', '-ar', '48000', '-ac', '2', f'{tmp}/whoosh.wav'])
    files = {'app-launch': f'{eff}/app-launch.mp3', 'pop': f'{eff}/bubble-connection.mp3', 'vortex': f'{eff}/vortex.mp3',
             'level-complete': f'{eff}/level-complete.mp3', 'bonk': f'{tmp}/bonk.wav', 'tick': f'{tmp}/tick.wav', 'whoosh': f'{tmp}/whoosh.wav'}
    vol = {'app-launch': 0.7, 'pop': 0.9, 'vortex': 0.35, 'level-complete': 0.85, 'bonk': 1.0, 'tick': 0.8, 'whoosh': 0.6}
    inp, fc, labs = [], [], []
    def add(p, flt):
        if not os.path.exists(p): return
        k = len(labs); inp.extend(['-i', p]); fc.append(f'[{k}:a]{flt}[a{k}]'); labs.append(f'[a{k}]')
    add(music, f'atrim=0:{total:.2f},asetpts=PTS-STARTPTS,volume=0.45,afade=t=in:d=0.4,afade=t=out:st={total - 1.2:.2f}:d=1.2')
    for name, at in sfx:
        extra = ',atrim=0:1.6,afade=t=out:st=1.2:d=0.4' if name == 'vortex' else ''
        add(files[name], f'volume={vol[name]}{extra},adelay={int(at * 1000)}|{int(at * 1000)}')
    fc.append(''.join(labs) + f'amix=inputs={len(labs)}:normalize=0:duration=longest,atrim=0:{total:.2f},alimiter=limit=0.9,loudnorm=I=-14:TP=-1.5:LRA=11[out]')
    run(['ffmpeg', '-y', '-loglevel', 'error', *inp, '-filter_complex', ';'.join(fc), '-map', '[out]', '-ar', '48000', '-ac', '2', f'{tmp}/mix.wav'])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-i', f'{tmp}/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
         '-shortest', '-movflags', '+faststart', out])
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '0.8', '-i', out, '-frames:v', '1', '-q:v', '3', out[:-4] + '.jpg'])
    print(json.dumps({'out': out, 'duration': round(total, 2), 'lives_left': lives}, ensure_ascii=False))


def make_end_card(s, lives):
    im = background(); d = ImageDraw.Draw(im)
    sp = popi_sprite(1.0, 1.0, (0, 1), 'yay', 0.5).resize((330, 390), Image.LANCZOS)
    im.alpha_composite(sp, (int(W / 2 - 165), 360))
    d.text((W / 2, 860), 'Popi 3 candan', font=font('ExtraBold', 74), fill=WHITE, anchor='mm')
    d.text((W / 2, 950), f'{lives} canla bitirdi.', font=font('ExtraBold', 74), fill=GOLD, anchor='mm')
    d.text((W / 2, 1070), 'Sen kaç canla bitirirdin?', font=font('SemiBold', 54), fill=MINT, anchor='mm')
    d.text((W / 2, 1140), 'Yoruma yaz', font=font('SemiBold', 54), fill=MINT, anchor='mm')
    f = font('ExtraBold', 50); t = 'Takip et: her gün yeni bölüm'; tw = d.textlength(t, font=f)
    d.rounded_rectangle([W / 2 - tw / 2 - 52, 1290, W / 2 + tw / 2 + 52, 1400], radius=55, fill=MINT)
    d.text((W / 2, 1345), t, font=f, fill=NAVY, anchor='mm')
    icon = Image.open(os.path.join(ROOT, BRAND['icon'])).convert('RGBA').resize((84, 84), Image.LANCZOS)
    m = Image.new('L', (84, 84), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, 83, 83], radius=20, fill=255)
    im.paste(icon, (int(W / 2 - 215), 1480), m)
    d.text((W / 2 - 115, 1522), 'DilGames · oyunla İngilizce', font=font('SemiBold', 38), fill=(200, 225, 228), anchor='lm')
    return im


if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2])
