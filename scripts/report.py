#!/usr/bin/env python3
"""Yayınlanmış Reels'lerin istatistiklerini çekip haftalık rapor yazar: reports/<yıl>-W<hafta>.md"""
import datetime as dt, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import ig  # noqa: E402


def main():
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'content/reels/*.json'))):
        s = json.load(open(path, encoding='utf-8'))
        if s.get('status') != 'published' or not s.get('media_id'): continue
        m = ig.insights(s['media_id']); s['insights'] = m; s['insights_at'] = dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
        json.dump(s, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(path, 'a').write('\n')
        rows.append((s, m))
    acct = ig.whoami()
    y, w, _ = dt.date.today().isocalendar()
    out = os.path.join(ROOT, 'reports', f'{y}-W{w:02d}.md'); os.makedirs(os.path.dirname(out), exist_ok=True)
    f = lambda v: '–' if v is None else str(v)
    lines = [f'# Haftalık Instagram raporu — {y} hafta {w}', '',
             f"Hesap: @{acct.get('username')} · takipçi: {acct.get('followers_count')} · gönderi: {acct.get('media_count')}", '',
             '| Reel | Sütun | İzlenme | Erişim | Beğeni | Yorum | Paylaşım | Kayıt | Ort. izleme (ms) |',
             '|---|---|---|---|---|---|---|---|---|']
    for s, m in sorted(rows, key=lambda r: -(r[1].get('views') or 0)):
        link = f"[{s['id']}]({s.get('permalink')})" if s.get('permalink') else s['id']
        lines.append(f"| {link} | {s.get('pillar','')} | {f(m.get('views'))} | {f(m.get('reach'))} | {f(m.get('likes'))} | {f(m.get('comments'))} | {f(m.get('shares'))} | {f(m.get('saved'))} | {f(m.get('ig_reels_avg_watch_time'))} |")
    open(out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(out)


if __name__ == '__main__':
    main()
