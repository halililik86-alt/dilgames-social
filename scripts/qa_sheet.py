#!/usr/bin/env python3
"""Bir Reels videosu için kalite kontrol çıktısı üretir: süre, çözünürlük, ses seviyesi ve kare paftası.

Kullanım: python3 scripts/qa_sheet.py <video.mp4> [çıktı-klasörü]
Çıktı: <klasör>/<ad>_sheet.png (saniyede 1 kare, zaman damgalı) ve stdout'a JSON özet.
"""
import json, os, re, subprocess, sys


def main(video, outdir=None):
    outdir = outdir or os.path.dirname(os.path.abspath(video))
    os.makedirs(outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(video))[0]
    probe = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height,r_frame_rate',
                                       '-of', 'json', video], capture_output=True, text=True, check=True).stdout)
    v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    has_audio = any(s['codec_type'] == 'audio' for s in probe['streams'])
    dur = float(probe['format']['duration'])
    loud = {}
    if has_audio:
        log = subprocess.run(['ffmpeg', '-i', video, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
        m = re.findall(r'I:\s+(-?[\d.]+) LUFS', log); loud['integrated_lufs'] = float(m[-1]) if m else None
        vd = subprocess.run(['ffmpeg', '-i', video, '-af', 'volumedetect', '-f', 'null', '-'], capture_output=True, text=True).stderr
        mx = re.search(r'max_volume: (-?[\d.]+) dB', vd); loud['max_db'] = float(mx.group(1)) if mx else None
    # siyah/donuk kare kontrolü
    bl = subprocess.run(['ffmpeg', '-i', video, '-vf', 'blackdetect=d=0.5:pix_th=0.08', '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
    blacks = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', bl)
    sheet = os.path.join(outdir, name + '_sheet.png')
    cols = 8; rows = max(1, -(-int(dur) // cols))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-vf',
                    f"fps=1,scale=216:-1,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=16:fontcolor=yellow:box=1:boxcolor=black,tile={cols}x{rows}",
                    '-frames:v', '1', sheet], check=True)
    issues = []
    if (int(v['width']), int(v['height'])) != (1080, 1920): issues.append(f"çözünürlük {v['width']}x{v['height']} (1080x1920 olmalı)")
    if not 10 <= dur <= 60: issues.append(f'süre {dur:.1f} sn (10–60 olmalı)')
    if not has_audio: issues.append('ses yok')
    elif loud.get('integrated_lufs') is not None and not -17 <= loud['integrated_lufs'] <= -11: issues.append(f"ses seviyesi {loud['integrated_lufs']} LUFS (-14 civarı olmalı)")
    for a, b in blacks:
        if float(a) > 0.5: issues.append(f'siyah ekran {float(a):.1f}–{float(b):.1f} sn')
    print(json.dumps({'video': video, 'duration': round(dur, 2), 'size': f"{v['width']}x{v['height']}", 'audio': has_audio, **loud,
                      'black_segments': blacks, 'sheet': sheet, 'auto_issues': issues}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:3])
