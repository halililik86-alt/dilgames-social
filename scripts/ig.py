#!/usr/bin/env python3
"""Resmi Instagram Graph API istemcisi (yalnızca kendi hesabımız için yayın ve istatistik).

İki mod desteklenir (IG_MODE):
  facebook  (önerilen)  graph.facebook.com + rupload.facebook.com — video dosyası doğrudan yüklenir,
                        herkese açık barındırma gerekmez. Facebook Sayfası erişim anahtarı kullanılır
                        (uzun ömürlü sayfa anahtarı süresiz olduğundan yenileme gerekmez).
  instagram             graph.instagram.com — Meta videoyu herkese açık bir adresten çeker
                        (PUBLIC_MEDIA_BASE gerekir); anahtar 60 günde bir yenilenmelidir.

Ortam değişkenleri: IG_MODE, IG_USER_ID, IG_ACCESS_TOKEN, IG_API_VERSION (varsayılan v23.0),
                    PUBLIC_MEDIA_BASE (yalnızca instagram modu).

Komutlar:
  python3 scripts/ig.py whoami
  python3 scripts/ig.py limit
  python3 scripts/ig.py publish-reel <video.mp4> <caption.txt> [--cover-offset-ms 1500] [--no-feed] [--dry-run]
  python3 scripts/ig.py publish-story <video.mp4> [--dry-run]
  python3 scripts/ig.py insights <media_id>
  python3 scripts/ig.py refresh-token          (yalnızca instagram modu; yeni anahtarı stdout'a yazar)
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

MODE = os.environ.get('IG_MODE', 'facebook')
VER = os.environ.get('IG_API_VERSION', 'v23.0')
HOST = 'https://graph.facebook.com' if MODE == 'facebook' else 'https://graph.instagram.com'


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f'Eksik ortam değişkeni: {name}')
    return v


def call(method, path, params=None, data=None, headers=None, url=None):
    params = dict(params or {})
    h = {'Authorization': f'OAuth {env("IG_ACCESS_TOKEN")}'}
    h.update(headers or {})
    u = url or f'{HOST}/{VER}/{path.lstrip("/")}'
    if params:
        u += ('&' if '?' in u else '?') + urllib.parse.urlencode(params)
    req = urllib.request.Request(u, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')
        raise SystemExit(f'API hatası {e.code} {method} {path}: {body}')


def whoami():
    uid = env('IG_USER_ID')
    return call('GET', uid, {'fields': 'id,username,followers_count,media_count'})


def publishing_limit():
    return call('GET', f'{env("IG_USER_ID")}/content_publishing_limit', {'fields': 'quota_usage,config'})


def wait_container(cid, tries=30, every=10):
    for _ in range(tries):
        st = call('GET', cid, {'fields': 'id,status,status_code'})
        code = st.get('status_code')
        if code == 'FINISHED':
            return st
        if code in ('ERROR', 'EXPIRED'):
            raise SystemExit(f'Kapsayıcı başarısız: {json.dumps(st, ensure_ascii=False)}')
        time.sleep(every)
    raise SystemExit('Kapsayıcı zamanında hazır olmadı')


def publish_reel(video, caption, cover_offset_ms=None, share_to_feed=True, dry_run=False, trial=False, cover_url=None):
    params = {'media_type': 'REELS', 'caption': caption, 'share_to_feed': 'true' if share_to_feed else 'false'}
    if trial:
        # Trial Reels: önce yalnızca takipçi olmayanlara gösterilir; iyi giderse Meta otomatik olarak takipçilere açar.
        # Hesabın uygun olması gerekir (1.000+ takipçi). Trial reel'ler akışa paylaşılmaz.
        params['trial_params'] = json.dumps({'graduation_strategy': 'SS_PERFORMANCE'})
        params.pop('share_to_feed', None)
    if cover_url:  # özel kapak (herkese açık adres, ör. GitHub Pages); verilince thumb_offset yok sayılır
        params['cover_url'] = cover_url
    elif cover_offset_ms is not None:
        params['thumb_offset'] = str(int(cover_offset_ms))
    if dry_run:
        return {'dry_run': True, 'mode': MODE, 'video': video, 'bytes': os.path.getsize(video), 'params': params}
    uid = env('IG_USER_ID')
    if MODE == 'facebook':
        params['upload_type'] = 'resumable'
        c = call('POST', f'{uid}/media', params)
        size = os.path.getsize(video)
        with open(video, 'rb') as f:
            up = call('POST', '', data=f.read(), url=c['uri'], headers={'offset': '0', 'file_size': str(size), 'Content-Type': 'application/octet-stream'})
        if not up.get('success'):
            raise SystemExit(f'Yükleme başarısız: {up}')
    else:
        base = env('PUBLIC_MEDIA_BASE').rstrip('/')
        params['video_url'] = f'{base}/{os.path.basename(video)}'
        c = call('POST', f'{uid}/media', params)
    wait_container(c['id'])
    pub = call('POST', f'{uid}/media_publish', {'creation_id': c['id']})
    media = call('GET', pub['id'], {'fields': 'id,permalink,timestamp'})
    return {'container_id': c['id'], 'media_id': pub['id'], 'permalink': media.get('permalink'), 'timestamp': media.get('timestamp')}


def publish_image(image_url, caption, dry_run=False):
    """Tek görsellik akış gönderisi (JPEG, herkese açık adres; en-boy 4:5 ile 1,91:1 arası)."""
    params = {'image_url': image_url, 'caption': caption}
    if dry_run:
        return {'dry_run': True, 'mode': MODE, 'params': params}
    uid = env('IG_USER_ID')
    c = call('POST', f'{uid}/media', params)
    wait_container(c['id'], tries=12, every=5)
    pub = call('POST', f'{uid}/media_publish', {'creation_id': c['id']})
    media = call('GET', pub['id'], {'fields': 'id,permalink,timestamp'})
    return {'container_id': c['id'], 'media_id': pub['id'], 'permalink': media.get('permalink'), 'timestamp': media.get('timestamp')}


def publish_story(video, dry_run=False):
    """Aynı videoyu hikâye olarak paylaşır (resmi API; çıkartma/link eklenemez). Yalnızca onaylı reel'in ardından çağrılır."""
    params = {'media_type': 'STORIES'}
    if dry_run:
        return {'dry_run': True, 'mode': MODE, 'video': video, 'params': params}
    uid = env('IG_USER_ID')
    if MODE == 'facebook':
        params['upload_type'] = 'resumable'
        c = call('POST', f'{uid}/media', params)
        size = os.path.getsize(video)
        with open(video, 'rb') as f:
            up = call('POST', '', data=f.read(), url=c['uri'], headers={'offset': '0', 'file_size': str(size), 'Content-Type': 'application/octet-stream'})
        if not up.get('success'):
            raise SystemExit(f'Hikâye yüklemesi başarısız: {up}')
    else:
        base = env('PUBLIC_MEDIA_BASE').rstrip('/')
        params['video_url'] = f'{base}/{os.path.basename(video)}'
        c = call('POST', f'{uid}/media', params)
    wait_container(c['id'])
    pub = call('POST', f'{uid}/media_publish', {'creation_id': c['id']})
    return {'story_id': pub['id']}


REEL_METRICS = ['views', 'reach', 'likes', 'comments', 'shares', 'saved', 'total_interactions', 'ig_reels_avg_watch_time', 'ig_reels_video_view_total_time']


def insights(media_id):
    out = {}
    # Meta zaman zaman metrik adlarını değiştiriyor; desteklenmeyenleri tek tek atlıyoruz.
    for m in REEL_METRICS:
        try:
            r = call('GET', f'{media_id}/insights', {'metric': m})
            vals = r.get('data', [{}])[0].get('values', [{}])
            out[m] = vals[0].get('value') if vals else None
        except SystemExit as e:
            out[m] = None
    return out


def refresh_token():
    if MODE != 'instagram':
        sys.exit('facebook modunda uzun ömürlü sayfa anahtarı süresizdir; yenileme gerekmez.')
    r = call('GET', '', {'grant_type': 'ig_refresh_token', 'access_token': env('IG_ACCESS_TOKEN')}, url='https://graph.instagram.com/refresh_access_token')
    print(r['access_token'])
    return {'expires_in': r.get('expires_in')}


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd = a[0]
    if cmd == 'whoami':
        print(json.dumps(whoami(), ensure_ascii=False, indent=1))
    elif cmd == 'limit':
        print(json.dumps(publishing_limit(), ensure_ascii=False, indent=1))
    elif cmd == 'publish-reel':
        cover = None
        if '--cover-offset-ms' in a:
            cover = a[a.index('--cover-offset-ms') + 1]
        cap = open(a[2], encoding='utf-8').read().strip()
        print(json.dumps(publish_reel(a[1], cap, cover, '--no-feed' not in a, '--dry-run' in a), ensure_ascii=False, indent=1))
    elif cmd == 'publish-story':
        print(json.dumps(publish_story(a[1], '--dry-run' in a), ensure_ascii=False, indent=1))
    elif cmd == 'insights':
        print(json.dumps(insights(a[1]), ensure_ascii=False, indent=1))
    elif cmd == 'refresh-token':
        info = refresh_token()
        print(json.dumps(info), file=sys.stderr)
    else:
        sys.exit(__doc__)
