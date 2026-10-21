#!/usr/bin/env python3
"""Takvimdeki 'planned' Reels'leri kaydedip kurgular.

Kullanım: python3 scripts/produce.py [--until 2026-11-03] [--only <id>]
Çıktılar: out/<id>.mp4, out/<id>.jpg ve out/<id>.txt (paylaşım metni)
Her başarılı reel'in durumu 'rendered' olur. RELEASE_TAG verilirse (GitHub Actions) 'approved' yazılır:
bu değişiklik ayrı bir PR'da gelir ve PR main'e birleştirilmeden hiçbir şey yayınlanmaz.
"""
import datetime as dt, glob, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'out'); os.makedirs(OUT, exist_ok=True)
BRAND = json.load(open(os.path.join(ROOT, 'config/brand.json'), encoding='utf-8'))


def post_text(spec):
    tags = spec.get('hashtags', [])[:BRAND['max_hashtags']]
    return (spec['caption'].strip() + ('\n\n' + ' '.join(tags) if tags else '')).strip()


def main():
    a = sys.argv[1:]
    until = a[a.index('--until') + 1] if '--until' in a else None
    only = a[a.index('--only') + 1] if '--only' in a else None
    done, failed = [], []
    for path in sorted(glob.glob(os.path.join(ROOT, 'content/reels/*.json'))):
        spec = json.load(open(path, encoding='utf-8'))
        if only and spec['id'] != only: continue
        if not only and spec.get('status', 'planned') != 'planned': continue
        if until and spec.get('publish_at', '9999')[:10] > until: continue
        rid = spec['id']; rec = os.path.join(OUT, 'rec-' + rid)
        print(f'==> {rid}', flush=True)
        if spec.get('type') in ('duel', 'ff'):
            # Deyim Düellosu / Yanlış Arkadaşlar: oyun kaydı yok; hazır AI klipleri (assets/ai) şablonla kurgulanır.
            builder = 'build_duel_reel.py' if spec['type'] == 'duel' else 'build_ff_reel.py'
            b = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', builder), path, os.path.join(OUT, rid + '.mp4')], capture_output=True, text=True)
            print(b.stdout[-2000:], b.stderr[-2000:], flush=True)
            if b.returncode != 0:
                failed.append(rid); continue
            try: spec['duration'] = json.loads(b.stdout.strip().splitlines()[-1])['duration']
            except Exception: pass
            open(os.path.join(OUT, rid + '.txt'), 'w', encoding='utf-8').write(post_text(spec))
            tag = os.environ.get('RELEASE_TAG')
            spec['status'] = 'approved' if tag else 'rendered'
            if tag: spec['release'] = tag
            spec['rendered_at'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
            json.dump(spec, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(path, 'a').write('\n')
            done.append(rid); continue
        r = subprocess.run(['node', os.path.join(ROOT, 'scripts/record.cjs'), path, rec])
        if r.returncode not in (0, 2):
            failed.append(rid); continue
        b = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts/build_reel.py'), path, rec, os.path.join(OUT, rid + '.mp4')], capture_output=True, text=True)
        print(b.stdout[-2000:], b.stderr[-2000:], flush=True)
        try:
            spec['duration'] = json.loads(b.stdout.strip().splitlines()[-1])['duration']
        except Exception:
            pass
        if b.returncode != 0:
            failed.append(rid); continue
        open(os.path.join(OUT, rid + '.txt'), 'w', encoding='utf-8').write(post_text(spec))
        try:
            intro = json.load(open(os.path.join(rec, 'take.json'))).get('introText')
            if intro: spec['intro_text'] = intro  # bölümün gerçek cümleleri (planlayıcı ajan bunu kullanır)
        except Exception:
            pass
        tag = os.environ.get('RELEASE_TAG')
        spec['status'] = 'approved' if tag else 'rendered'
        if tag: spec['release'] = tag  # PR main'e birleşince yayın kuyruğuna girer
        spec['rendered_at'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
        if r.returncode == 2: spec['note'] = 'Bot bölümü bitiremedi; kurguyu kontrol et.'
        json.dump(spec, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(path, 'a').write('\n')
        done.append(rid)
    print(json.dumps({'rendered': done, 'failed': failed}, ensure_ascii=False))
    if failed and not done: sys.exit(1)


if __name__ == '__main__':
    main()
