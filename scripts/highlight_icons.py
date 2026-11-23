#!/usr/bin/env python3
"""Instagram öne çıkan kapak ikonları (content/series.json anahtarlarıyla): python3 scripts/highlight_icons.py → media/highlights/<key>.jpg"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD='/usr/share/fonts/opentype/inter/'
def F(w,s): return ImageFont.truetype(f'{FD}Inter-{w}.otf', s)
W,H=1080,1920; C=(540,960)
NAVY=(14,24,38); CREAM=(244,228,190); GOLD=(255,196,92); MINT=(140,236,200); CORAL=(255,128,112); SKY=(140,200,255); LIL=(200,170,255)
def base(col):
    im=Image.new('RGB',(W,H),NAVY); d=ImageDraw.Draw(im)
    g=Image.new('RGB',(W,H),col); m=Image.new('L',(W,H),0); ImageDraw.Draw(m).ellipse([C[0]-520,C[1]-520,C[0]+520,C[1]+520],fill=70)
    im=Image.composite(g,im,m.filter(ImageFilter.GaussianBlur(120)))
    d=ImageDraw.Draw(im); d.ellipse([C[0]-400,C[1]-400,C[0]+400,C[1]+400],outline=col,width=18)
    return im,d
def save(im,name): im.save(f'media/highlights/{name}.jpg',quality=92)
# kagit: iki kâğıt yaprağı + arada kıvrık not
im,d=base(CREAM)
d.rounded_rectangle([355,700,665,1110],18,fill=(200,184,150)); 
d.polygon([(415,660),(705,660),(705,1000),(645,1060),(415,1060)],fill=CREAM); d.polygon([(705,1000),(645,1060),(645,1000)],fill=(210,190,150))
for y in (740,790,840,890,940): d.line([(450,y),(670,y)],fill=(150,130,100),width=10)
save(im,'kagit')
# komedi: konuşma balonu + Ha!
im,d=base(GOLD)
d.rounded_rectangle([300,720,780,1080],80,fill=GOLD); d.polygon([(400,1060),(370,1190),(500,1075)],fill=GOLD)
d.text((540,900),'Ha!',font=F('Black',190),fill=NAVY,anchor='mm'); save(im,'komedi')
# kelime: Aa
im,d=base(MINT); d.text((540,955),'Aa',font=F('Black',330),fill=MINT,anchor='mm'); save(im,'kelime')
# deyim: tırnak
im,d=base(SKY); d.text((540,1050),'“ ”',font=F('Black',420),fill=SKY,anchor='mm'); save(im,'deyim')
# hata: ✗ ve ✓
im,d=base(CORAL)
d.line([(330,820),(490,980)],fill=CORAL,width=48); d.line([(490,820),(330,980)],fill=CORAL,width=48)
d.line([(590,920),(660,1000)],fill=MINT,width=48); d.line([(650,1000),(780,820)],fill=MINT,width=48)
d.text((540,1110),'hata → doğru',font=F('ExtraBold',54),fill=(235,235,235),anchor='mm'); save(im,'hata')
# oyun: oyun kolu (sade)
im,d=base(LIL)
d.rounded_rectangle([290,820,790,1100],140,fill=LIL)
d.rectangle([380,935,480,975],fill=NAVY); d.rectangle([410,905,450,1005],fill=NAVY)
d.ellipse([640,890,690,940],fill=NAVY); d.ellipse([690,950,740,1000],fill=NAVY)
save(im,'oyun')


# Seri tanıtım hikâyeleri: ortadaki ikon öne çıkan kapağı olur; üstte seri adı, altta kısa tanıtım
import json, glob, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from playlists import series_of
INFO = {'komedi': 'İngilizce kalıplar harfiyen çevrilirse ne olur?\nEllie & Tom ve arkadaşlarıyla güldüren skeçler',
        'kelime': 'Bir harf değişir, anlam bambaşka olur\nKarıştırılan İngilizce kelimeler',
        'deyim': 'Türkçe deyimler İngilizcede nasıl söylenir?\nDeyim Düellosu',
        'hata': 'Türklerin en sık yaptığı İngilizce hatalar\nve doğruları',
        'oyun': 'Oynayarak İngilizce cümle kur\nDilGames oyunundan hikâyeler',
        'kagit': 'Kayıp bir dayı, bir not, son vapur…\n20 bölümlük İngilizce gizem dizisi'}
cfg = json.load(open('content/series.json', encoding='utf-8'))
cnt = {}
for p in glob.glob('content/reels/*.json'):
    sp = json.load(open(p, encoding='utf-8'))
    if sp.get('media') in ('story', 'image') or sp.get('status') != 'published': continue
    k = series_of(sp, cfg); cnt[k] = cnt.get(k, 0) + 1
for x in cfg['series']:
    k = x['key']; im = Image.open(f'media/highlights/{k}.jpg').convert('RGB'); d = ImageDraw.Draw(im)
    d.text((540, 330), 'DilGames serisi', font=F('ExtraBold', 44), fill=(200, 215, 225), anchor='mm')
    t = x['ig']; size = 120
    while d.textlength(t, font=F('Black', size)) > 960: size -= 6
    d.text((540, 450), t, font=F('Black', size), fill=(255, 255, 255), anchor='mm')
    for i, line in enumerate(INFO[k].split('\n')):
        d.text((540, 1460 + i * 70), line, font=F('Bold', 48 if i == 0 else 42), fill=(255, 255, 255) if i == 0 else (200, 215, 225), anchor='mm')
    n = cnt.get(k, 0)
    d.text((540, 1650), (f'{n} kısa video yayında · ' if n else '') + 'Profilde öne çıkanlarda', font=F('ExtraBold', 40), fill=(255, 196, 92), anchor='mm')
    d.text((540, 1760), '@dilgamesapp', font=F('ExtraBold', 44), fill=(200, 222, 220), anchor='mm')
    im.save(f'media/highlights/story-{k}.jpg', quality=92)
