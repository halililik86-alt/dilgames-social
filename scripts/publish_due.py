#!/usr/bin/env python3
"""Zamanı gelmiş ve onaylanmış ('approved') Reels'leri Instagram'a yayınlar.

Onay: haftalık üretim PR'ı main'e birleştirildiğinde reel'ler 'approved' olur.
Video dosyası, PR'daki GitHub Release'ten (reels-<tarih>) indirilir.
Kullanım: python3 scripts/publish_due.py [--dry-run] [--max 1]
"""
import datetime as dt, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ig  # noqa: E402
from produce import post_text  # noqa: E402


def main():
    dry = '--dry-run' in sys.argv
    mx = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 1
    now = dt.datetime.now(dt.timezone.utc)
    if dry:
        # Deneme: yayın yapmadan bağlantıyı ve 24 saatlik yayın kotasını doğrula (yalnızca okuma).
        acct = ig.whoami()
        print(json.dumps({'hesap': acct.get('username'), 'takipci': acct.get('followers_count'), 'gonderi': acct.get('media_count'),
                          'kota': ig.publishing_limit().get('data')}, ensure_ascii=False))
    due = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'content/reels/*.json'))):
        s = json.load(open(path, encoding='utf-8'))
        if s.get('status') == 'approved' and dt.datetime.fromisoformat(s['publish_at']) <= now:
            due.append((s['publish_at'], path, s))
    due.sort()
    for _, path, s in due[:mx]:
        rid = s['id']; video = os.path.join(ROOT, 'out', rid + '.mp4')
        if s.get('video') and os.path.exists(os.path.join(ROOT, s['video'])):
            video = os.path.join(ROOT, s['video'])  # repoda duran (elle ya da yerelde üretilmiş) video
        elif not os.path.exists(video):
            os.makedirs(os.path.dirname(video), exist_ok=True)
            subprocess.run(['gh', 'release', 'download', s['release'], '-p', rid + '.mp4', '-D', os.path.dirname(video), '--clobber'], check=True)
        res = ig.publish_reel(video, post_text(s), s.get('cover_offset_ms', 1500), True, dry, bool(s.get('trial')), s.get('cover_url'))
        print(json.dumps({rid: res}, ensure_ascii=False))
        if dry: continue
        s.update({'status': 'published', 'media_id': res['media_id'], 'permalink': res.get('permalink'), 'published_at': res.get('timestamp')})
        if s.get('story', True):  # aynı videoyu hikâyeye de ekle; hata olursa reel yayını etkilenmez
            try:
                st = ig.publish_story(video)
                s['story_id'] = st['story_id']; print(json.dumps({rid: st}, ensure_ascii=False))
            except SystemExit as e:
                s['story_error'] = str(e)[:300]; print(f'Hikâye paylaşılamadı: {e}')
        json.dump(s, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(path, 'a').write('\n')
    if not due:
        print('Zamanı gelmiş onaylı reel yok.')


if __name__ == '__main__':
    main()
