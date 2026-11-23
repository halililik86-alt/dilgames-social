#!/usr/bin/env python3
"""YouTube oynatma listeleri + kanal ana sayfası rafları, content/series.json sınıflandırmasına göre (resmi YouTube Data API v3).

  python3 scripts/playlists.py scopes            erişim belirtecinin izinlerini yazar
  python3 scripts/playlists.py plan              hangi video hangi listeye, API'ye yazmadan
  python3 scripts/playlists.py sync [--dry-run]  eksik listeleri açar, eksik videoları ekler, açıklamaları günceller
  python3 scripts/playlists.py sections [--dry-run]  kanal ana sayfasına her liste için bir raf ekler (yoksa)

Liste kimlikleri content/playlists_state.json'da tutulur (iş akışı commit'ler). Liste yazmak için belirtecin
youtube veya youtube.force-ssl izni olmalı; yalnızca youtube.upload varsa ne yapılacağını söyleyip çıkar.
Kota: liste açma ve video ekleme 50'şer birim; günlük 10.000 birimin yükleme payını yememek için --max ile sınırlanır.
"""
import json, os, sys, glob, urllib.parse, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__))
import yt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERIES = os.path.join(ROOT, 'content/series.json')
STATE = os.path.join(ROOT, 'content/playlists_state.json')
WRITE_SCOPES = ('https://www.googleapis.com/auth/youtube', 'https://www.googleapis.com/auth/youtube.force-ssl')


def call(method, path, params, body=None):
    u = f'{yt.API}/{path}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(u, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': f'Bearer {yt.access_token()}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{e.code} {method} {path}: {e.read().decode()[:400]}')


def scopes():
    with urllib.request.urlopen('https://oauth2.googleapis.com/tokeninfo?' + urllib.parse.urlencode({'access_token': yt.access_token()}), timeout=30) as r:
        return json.loads(r.read().decode()).get('scope', '').split()


def can_write():
    return any(s in WRITE_SCOPES for s in scopes())


def series_of(s, cfg):
    k = s.get('type') or s.get('format')
    for x in cfg['series']:
        if k in x['types']:
            return x['key']
    return None


def load():
    cfg = json.load(open(SERIES, encoding='utf-8'))
    state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
    vids = {x['key']: [] for x in cfg['series']}
    for p in glob.glob(os.path.join(ROOT, 'content/reels/*.json')):
        s = json.load(open(p, encoding='utf-8'))
        vid = (s.get('youtube') or {}).get('video_id')
        key = series_of(s, cfg)
        if vid and key:
            vids[key].append((s.get('episode') or 0, s.get('publish_at', ''), vid, s['id']))
    for x in cfg['series']:
        vids[x['key']].sort(key=(lambda v: (v[0], v[1])) if x.get('order') == 'episode' else (lambda v: v[1]))
    return cfg, state, vids


def save(state):
    json.dump(state, open(STATE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(STATE, 'a').write('\n')


def items(pid):
    out, tok = [], None
    while True:
        p = {'part': 'contentDetails', 'playlistId': pid, 'maxResults': 50}
        if tok: p['pageToken'] = tok
        j = call('GET', 'playlistItems', p)
        out += [i['contentDetails']['videoId'] for i in j.get('items', [])]
        tok = j.get('nextPageToken')
        if not tok: return out


def sync(dry, mx):
    cfg, state, vids = load()
    if not dry and not can_write():
        sys.exit('YouTube belirtecinde liste yazma izni yok (yalnızca youtube.upload). YT_REFRESH_TOKEN youtube.force-ssl izniyle yeniden alınmalı.')
    budget = mx
    for x in cfg['series']:
        k = x['key']; snip = {'title': x['yt_title'][:150], 'description': x['yt_description'][:5000], 'defaultLanguage': 'tr'}
        pid = state.get(k, {}).get('playlist_id')
        if not pid:
            print(f'[{k}] liste açılacak: {snip["title"]}')
            if dry or budget <= 0: continue
            j = call('POST', 'playlists', {'part': 'snippet,status'}, {'snippet': snip, 'status': {'privacyStatus': 'public'}})
            pid = j['id']; state[k] = {'playlist_id': pid}; save(state); budget -= 1
        elif not dry:
            call('PUT', 'playlists', {'part': 'snippet'}, {'id': pid, 'snippet': snip})  # başlık/açıklama series.json ile aynı kalsın
        have = set(items(pid)) if pid and not dry else set()
        for ep, at, vid, sid in vids[k]:
            if vid in have: continue
            print(f'[{k}] + {sid} ({vid})')
            if dry or budget <= 0: continue
            call('POST', 'playlistItems', {'part': 'snippet'}, {'snippet': {'playlistId': pid, 'resourceId': {'kind': 'youtube#video', 'videoId': vid}}})
            have.add(vid); budget -= 1
    if budget <= 0: print('Kota sınırına gelindi (--max); kalanlar sonraki çalışmada eklenir.')


def add_one(spec):
    """youtube_due'den: yeni yüklenen videoyu serisinin listesine ekler. Hata yüklemeyi etkilemez."""
    try:
        cfg = json.load(open(SERIES, encoding='utf-8'))
        state = json.load(open(STATE, encoding='utf-8')) if os.path.exists(STATE) else {}
        k = series_of(spec, cfg); pid = state.get(k, {}).get('playlist_id')
        vid = (spec.get('youtube') or {}).get('video_id')
        if not (pid and vid): return None
        call('POST', 'playlistItems', {'part': 'snippet'}, {'snippet': {'playlistId': pid, 'resourceId': {'kind': 'youtube#video', 'videoId': vid}}})
        return pid
    except Exception as e:
        print(f'Oynatma listesine eklenemedi: {e}'); return None


def sections(dry):
    cfg, state, _ = load()
    if not dry and not can_write():
        sys.exit('YouTube belirtecinde kanal düzenleme izni yok.')
    have = set()
    if not dry:
        for s in call('GET', 'channelSections', {'part': 'contentDetails', 'mine': 'true'}).get('items', []):
            have.update((s.get('contentDetails') or {}).get('playlists') or [])
    for i, x in enumerate(cfg['series']):
        pid = state.get(x['key'], {}).get('playlist_id')
        if not pid: print(f'[{x["key"]}] önce sync çalışmalı'); continue
        if pid in have: continue
        print(f'[{x["key"]}] ana sayfa rafı: {x["yt_title"][:60]}')
        if not dry:
            try:
                call('POST', 'channelSections', {'part': 'snippet,contentDetails'},
                     {'snippet': {'type': 'singlePlaylist', 'position': i + 1}, 'contentDetails': {'playlists': [pid]}})
            except RuntimeError as e:
                print(f'   raf eklenemedi (YouTube Studio > Özelleştirme > Düzen\'den elle eklenebilir): {e}')


if __name__ == '__main__':
    a = sys.argv[1:]
    dry = '--dry-run' in a
    mx = int(a[a.index('--max') + 1]) if '--max' in a else 80
    if not a: sys.exit(__doc__)
    if a[0] == 'plan':
        cfg, state, vids = load()
        for x in cfg['series']:
            print(f'{x["key"]:7} {len(vids[x["key"]]):3} video  IG: {x["ig"]:18} YT: {x["yt_title"]}')
    elif not yt.configured():
        print('YouTube henüz bağlı değil (YT_* secret yok).')
    elif a[0] == 'scopes': print(scopes())
    elif a[0] == 'sync': sync(dry, mx)
    elif a[0] == 'sections': sections(dry)
    else: sys.exit(__doc__)
