#!/usr/bin/env python3
"""Resmi YouTube Data API v3 istemcisi (yalnızca kendi kanalımıza Shorts yükler, istatistik okur).

Ortam değişkenleri: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (GitHub secret'ları).
Komutlar:
  python3 scripts/yt.py whoami
  python3 scripts/yt.py upload <video.mp4> <başlık> <açıklama.txt> [--tags a,b] [--dry-run]
  python3 scripts/yt.py stats <video_id>[,<video_id>...]
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error

TOKEN_URL = 'https://oauth2.googleapis.com/token'
API = 'https://www.googleapis.com/youtube/v3'
UPLOAD = 'https://www.googleapis.com/upload/youtube/v3/videos'


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f'Eksik ortam değişkeni: {name}')
    return v


def configured():
    return all(os.environ.get(k) for k in ('YT_CLIENT_ID', 'YT_CLIENT_SECRET', 'YT_REFRESH_TOKEN'))


def _req(req):
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            body = r.read().decode() or '{}'
            return r, json.loads(body)
    except urllib.error.HTTPError as e:
        sys.exit(f'YouTube API hatası {e.code} {req.get_method()} {req.full_url.split("?")[0]}: {e.read().decode()[:600]}')


_tok = None


def access_token():
    global _tok
    if _tok: return _tok
    data = urllib.parse.urlencode({'client_id': env('YT_CLIENT_ID'), 'client_secret': env('YT_CLIENT_SECRET'),
                                   'refresh_token': env('YT_REFRESH_TOKEN'), 'grant_type': 'refresh_token'}).encode()
    _, j = _req(urllib.request.Request(TOKEN_URL, data=data, method='POST'))
    _tok = j['access_token']
    return _tok


def get(path, params):
    u = f'{API}/{path}?' + urllib.parse.urlencode(params)
    return _req(urllib.request.Request(u, headers={'Authorization': f'Bearer {access_token()}'}))[1]


def whoami():
    j = get('channels', {'part': 'snippet,statistics', 'mine': 'true'})
    c = (j.get('items') or [{}])[0]
    return {'kanal': c.get('snippet', {}).get('title'), 'id': c.get('id'),
            'abone': c.get('statistics', {}).get('subscriberCount'), 'video': c.get('statistics', {}).get('videoCount')}


def upload(video, title, description, tags=(), dry=False):
    meta = {'snippet': {'title': title[:100], 'description': description[:4900], 'tags': [t.lstrip('#') for t in tags][:15],
                        'categoryId': '27', 'defaultLanguage': 'tr', 'defaultAudioLanguage': 'tr'},
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False, 'embeddable': True}}
    if dry:
        return {'dry_run': True, 'video': video, 'bytes': os.path.getsize(video), 'meta': meta, 'kanal': whoami()}
    size = os.path.getsize(video)
    init = urllib.request.Request(f'{UPLOAD}?uploadType=resumable&part=snippet,status', data=json.dumps(meta).encode(), method='POST',
                                  headers={'Authorization': f'Bearer {access_token()}', 'Content-Type': 'application/json; charset=UTF-8',
                                           'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size)})
    r, _ = _req(init)
    loc = r.headers['Location']
    with open(video, 'rb') as f:
        put = urllib.request.Request(loc, data=f.read(), method='PUT', headers={'Content-Type': 'video/mp4', 'Content-Length': str(size)})
    _, j = _req(put)
    return {'video_id': j['id'], 'url': f'https://youtube.com/shorts/{j["id"]}', 'privacy': j.get('status', {}).get('privacyStatus'),
            'upload_status': j.get('status', {}).get('uploadStatus')}


def stats(ids):
    j = get('videos', {'part': 'statistics', 'id': ids})
    return {it['id']: it.get('statistics', {}) for it in j.get('items', [])}


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == 'whoami': print(json.dumps(whoami(), ensure_ascii=False))
    elif a[0] == 'upload':
        tags = a[a.index('--tags') + 1].split(',') if '--tags' in a else []
        print(json.dumps(upload(a[1], a[2], open(a[3], encoding='utf-8').read(), tags, '--dry-run' in a), ensure_ascii=False))
    elif a[0] == 'stats': print(json.dumps(stats(a[1]), ensure_ascii=False))
    else: sys.exit(__doc__)
