#!/usr/bin/env python3
"""Instagram için onaylanmış (approved/published) ve saati gelmiş reel'leri YouTube Shorts'a da yükler.

Onay aynıdır: yalnızca main'de 'approved' ya da 'published' durumundaki reel'ler yüklenir.
Her reel bir kez yüklenir; sonuç spec'e 'youtube' alanı olarak yazılır. Instagram yayınından bağımsızdır.
Kullanım: python3 scripts/youtube_due.py [--dry-run] [--max 1]
"""
import datetime as dt, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import yt  # noqa: E402
from tr import soru_eki  # noqa: E402
from produce import post_text  # noqa: E402

START = os.environ.get('YT_START', '2026-10-21')  # bundan eski reel'ler geriye dönük yüklenmez


def title(s):
    t = s.get('type')
    if s.get('yt_title'):
        return s['yt_title']
    if t == 'duel':
        return f"{s['tr']['idiom']} İngilizcede ne demek? | Deyim Düellosu #{s.get('episode', '')}"
    if t == 'ff':
        return f"{s['en_word']} = {s['tr_word']} {soru_eki(s['tr_word'])}? | Yanlış Arkadaşlar #{s.get('episode', '')}"
    if t == 'kaza':
        return f"{s['wrong']} değil! Doğrusu: {s['right']} | Türk İngilizcesi Kazaları #{s.get('episode', '')}"
    if s.get('format') == 'F1':
        lv = s['id'].split('-')[3].upper() if s['id'][:4].isdigit() else ''
        return f"Bu cümleyi kurabilir misin? {lv} İngilizce meydan okuma".strip()
    first = s['caption'].strip().splitlines()[0]
    return first[:90]


def video_path(s):
    if s.get('video') and os.path.exists(os.path.join(ROOT, s['video'])):
        return os.path.join(ROOT, s['video'])
    v = os.path.join(ROOT, 'out', s['id'] + '.mp4')
    if not os.path.exists(v) and s.get('release'):
        os.makedirs(os.path.dirname(v), exist_ok=True)
        subprocess.run(['gh', 'release', 'download', s['release'], '-p', s['id'] + '.mp4', '-D', os.path.dirname(v), '--clobber'], check=True)
    return v


def main():
    dry = '--dry-run' in sys.argv
    mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 1
    if not yt.configured():
        print('YouTube henüz bağlı değil (YT_* secret yok).'); return
    now = dt.datetime.now(dt.timezone.utc)
    due = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'content/reels/*.json'))):
        s = json.load(open(p, encoding='utf-8'))
        if s.get('status') not in ('approved', 'published') or s.get('youtube'):
            continue
        at = dt.datetime.fromisoformat(s['publish_at'])
        if at <= now and s['publish_at'][:10] >= START:
            due.append((s['publish_at'], p, s))
    due.sort()
    if dry:
        print(json.dumps({'kanal': yt.whoami(), 'sirada': [d[2]['id'] for d in due]}, ensure_ascii=False))
    for _, p, s in due[:mx]:
        desc = post_text(s) + '\n\n#shorts'
        res = yt.upload(video_path(s), title(s), desc, s.get('hashtags', []), dry, synthetic=s.get('type') in ('duel', 'ff', 'kaza', 'harf', 'duel2'))
        print(json.dumps({s['id']: res}, ensure_ascii=False))
        if dry: continue
        s['youtube'] = {'video_id': res['video_id'], 'url': res['url'], 'privacy': res.get('privacy'),
                        'uploaded_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}
        json.dump(s, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(p, 'a').write('\n')
    if not due:
        print('YouTube için sırada reel yok.')


if __name__ == '__main__':
    main()
