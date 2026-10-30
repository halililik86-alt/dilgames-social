#!/usr/bin/env python3
"""Hesabın tüm gönderilerini (elle paylaşılanlar dahil) istatistikleriyle listeler; en çok izlenen,
repoda olmayan gönderinin videosunu indirir. Yalnızca kendi hesabımızı okur (resmi Graph API).
Çıktı: analysis/media.json, analysis/top/<media_id>.mp4
"""
import json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ig  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
uid = ig.env('IG_USER_ID')
items, after = [], None
while True:
    p = {'fields': 'id,caption,media_type,media_product_type,timestamp,permalink,media_url,like_count,comments_count', 'limit': 50}
    if after: p['after'] = after
    r = ig.call('GET', f'{uid}/media', p)
    items += r.get('data', [])
    after = r.get('paging', {}).get('cursors', {}).get('after')
    if not r.get('paging', {}).get('next'): break
known = set()
for f in os.listdir(os.path.join(ROOT, 'content/reels')):
    s = json.load(open(os.path.join(ROOT, 'content/reels', f), encoding='utf-8'))
    if s.get('media_id'): known.add(s['media_id'])
for it in items:
    it['insights'] = ig.insights(it['id']) if it.get('media_type') == 'VIDEO' else {}
    it['from_repo'] = it['id'] in known
os.makedirs(os.path.join(ROOT, 'analysis/top'), exist_ok=True)
items.sort(key=lambda x: -((x['insights'] or {}).get('views') or 0))
manual = [i for i in items if not i['from_repo'] and i.get('media_type') == 'VIDEO'][:3]
for it in manual:
    if it.get('media_url'):
        urllib.request.urlretrieve(it['media_url'], os.path.join(ROOT, 'analysis/top', it['id'] + '.mp4'))
for it in items: it.pop('media_url', None)
json.dump(items, open(os.path.join(ROOT, 'analysis/media.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for it in items[:15]:
    print((it['insights'] or {}).get('views'), it['from_repo'], it['timestamp'][:10], (it.get('caption') or '')[:60].replace('\n', ' '))
