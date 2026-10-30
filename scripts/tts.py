#!/usr/bin/env python3
"""ElevenLabs resmi API ile seslendirme (yalnızca kendi içeriklerimiz).

tts/requests/<ad>.json:
  {"voices": true}                               -> tts/voices.json (hesaptaki sesler)
  {"model": "eleven_multilingual_v2",
   "lines": [{"id": "l1", "voice": "<voice_id>", "text": "...", "settings": {...}}],
   "sfx":   [{"id": "s1", "text": "whoosh", "seconds": 0.8}]}
Çıktı: tts/audio/<ad>/<id>.mp3 ; aynı id ve metin bir kez üretilir (kredi tasarrufu).
"""
import base64, glob, hashlib, json, os, sys, urllib.request, urllib.error

API = 'https://api.elevenlabs.io/v1'
KEY = os.environ.get('ELEVENLABS_API_KEY')


class ApiError(Exception):
    pass


def req(method, path, body=None, accept='application/json', soft=False):
    r = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                               headers={'xi-api-key': KEY, 'Content-Type': 'application/json', 'Accept': accept})
    try:
        with urllib.request.urlopen(r, timeout=120) as f:
            return f.read()
    except urllib.error.HTTPError as e:
        msg = f'ElevenLabs API hatası {e.code} {path}: {e.read().decode()[:400]}'
        if soft: raise ApiError(msg)
        sys.exit(msg)


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
        out = os.path.join('tts', 'audio', name); os.makedirs(out, exist_ok=True)
        model = r.get('model', 'eleven_multilingual_v2')
        for ln in r.get('lines', []):
            sig = hashlib.sha1(json.dumps([ln, model], sort_keys=True).encode()).hexdigest()[:10]
            path = os.path.join(out, f"{ln['id']}.mp3"); meta = path + '.sig'
            if os.path.exists(path) and os.path.exists(meta) and open(meta).read() == sig:
                continue
            models = ln.get('model', model); models = models if isinstance(models, list) else [models]
            for k, mid in enumerate(models):  # ilk model desteklenmiyorsa sıradakine geç (ör. eleven_v4 → eleven_v3)
                body = {'text': ln['text'], 'model_id': mid}
                if ln.get('settings'): body['voice_settings'] = ln['settings']
                if ln.get('language'): body['language_code'] = ln['language']
                try:
                    if ln.get('timestamps'):  # tek parça anlatım + karakter zamanları (sahnelere bölmek için)
                        j = json.loads(req('POST', f"/text-to-speech/{ln['voice']}/with-timestamps?output_format=mp3_44100_128", body, soft=True))
                        audio = base64.b64decode(j['audio_base64'])
                        json.dump({'model': mid, 'text': ln['text'], 'alignment': j.get('alignment'), 'normalized_alignment': j.get('normalized_alignment')},
                                  open(path[:-4] + '.align.json', 'w', encoding='utf-8'), ensure_ascii=False)
                    else:
                        audio = req('POST', f"/text-to-speech/{ln['voice']}?output_format=mp3_44100_128", body, accept='audio/mpeg', soft=True)
                    break
                except ApiError as e:
                    print(f"{name}/{ln['id']}: {mid} olmadı ({e})")
                    if k == len(models) - 1: sys.exit(str(e))
            open(path, 'wb').write(audio); open(meta, 'w').write(sig)
            print(f"{name}/{ln['id']}: {len(ln['text'])} karakter, {mid}")
        for sx in r.get('sfx', []):
            path = os.path.join(out, f"{sx['id']}.mp3")
            if os.path.exists(path): continue
            body = {'text': sx['text']}
            if sx.get('seconds'): body['duration_seconds'] = sx['seconds']
            open(path, 'wb').write(req('POST', '/sound-generation', body, accept='audio/mpeg'))
            print(f"{name}/{sx['id']}: efekt")


if __name__ == '__main__':
    main()
