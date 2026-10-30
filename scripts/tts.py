#!/usr/bin/env python3
"""ElevenLabs resmi API ile seslendirme (yalnızca kendi içeriklerimiz).

tts/requests/<ad>.json:
  {"voices": true}                               -> tts/voices.json (hesaptaki sesler)
  {"model": "eleven_multilingual_v2",
   "lines": [{"id": "l1", "voice": "<voice_id>", "text": "...", "settings": {...}}],
   "sfx":   [{"id": "s1", "text": "whoosh", "seconds": 0.8}]}
Çıktı: tts/out/<ad>/<id>.mp3 ; aynı id ve metin bir kez üretilir (kredi tasarrufu).
"""
import glob, hashlib, json, os, sys, urllib.request, urllib.error

API = 'https://api.elevenlabs.io/v1'
KEY = os.environ.get('ELEVENLABS_API_KEY')


def req(method, path, body=None, accept='application/json'):
    r = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                               headers={'xi-api-key': KEY, 'Content-Type': 'application/json', 'Accept': accept})
    try:
        with urllib.request.urlopen(r, timeout=120) as f:
            return f.read()
    except urllib.error.HTTPError as e:
        sys.exit(f'ElevenLabs API hatası {e.code} {path}: {e.read().decode()[:400]}')


def main():
    if not KEY:
        sys.exit('ELEVENLABS_API_KEY yok.')
    for rp in sorted(glob.glob('tts/requests/*.json')):
        name = os.path.splitext(os.path.basename(rp))[0]
        r = json.load(open(rp, encoding='utf-8'))
        if r.get('voices'):
            data = json.loads(req('GET', '/voices'))
            slim = [{'voice_id': v['voice_id'], 'name': v['name'], 'category': v.get('category'),
                     'labels': v.get('labels'), 'preview_url': v.get('preview_url')} for v in data.get('voices', [])]
            json.dump(slim, open('tts/voices.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f'{len(slim)} ses listelendi')
        out = os.path.join('tts', 'out', name); os.makedirs(out, exist_ok=True)
        model = r.get('model', 'eleven_multilingual_v2')
        for ln in r.get('lines', []):
            sig = hashlib.sha1(json.dumps([ln, model], sort_keys=True).encode()).hexdigest()[:10]
            path = os.path.join(out, f"{ln['id']}.mp3"); meta = path + '.sig'
            if os.path.exists(path) and os.path.exists(meta) and open(meta).read() == sig:
                continue
            body = {'text': ln['text'], 'model_id': ln.get('model', model)}
            if ln.get('settings'): body['voice_settings'] = ln['settings']
            if ln.get('language'): body['language_code'] = ln['language']
            audio = req('POST', f"/text-to-speech/{ln['voice']}?output_format=mp3_44100_128", body, accept='audio/mpeg')
            open(path, 'wb').write(audio); open(meta, 'w').write(sig)
            print(f"{name}/{ln['id']}: {len(ln['text'])} karakter")
        for sx in r.get('sfx', []):
            path = os.path.join(out, f"{sx['id']}.mp3")
            if os.path.exists(path): continue
            body = {'text': sx['text']}
            if sx.get('seconds'): body['duration_seconds'] = sx['seconds']
            open(path, 'wb').write(req('POST', '/sound-generation', body, accept='audio/mpeg'))
            print(f"{name}/{sx['id']}: efekt")


if __name__ == '__main__':
    main()
