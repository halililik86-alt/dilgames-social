// Oyundan 9:16 oynanış kaydı alır (görüntü + oyunun kendi sesi).
// Kullanım: node scripts/record.cjs <reel.json> <çıktı-klasörü>
// Ortam: GAME_URL (varsayılan http://127.0.0.1:5191), CHROMIUM_PATH (isteğe bağlı)
const fs = require('fs'), path = require('path');
const bot = require('./bot.cjs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const spec = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = process.argv[3]; fs.mkdirSync(out, { recursive: true });
const rec = Object.assign({ language: 'Türkçe', section: 0, tab: null, pack: 0, level: 1, stir: true }, spec.record || {});
const GAME_URL = process.env.GAME_URL || 'http://127.0.0.1:5191';

// Oyun motoruna (BubbleGame) kayıt için erişim: derlenmiş JS tarayıcıda yamalanır, dosyalar değişmez.
const HOOK = /([A-Za-z_$][\w$]*)=new ([A-Za-z_$][\w$]*)\(([A-Za-z_$][\w$]*)\("#physics"\),([\w$]+),([\w$]+),([\w$]+)\)/g;

async function take(attempt) {
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined, args: ['--autoplay-policy=no-user-gesture-required', '--hide-scrollbars'] });
  const c = await b.newContext({ viewport: { width: 405, height: 720 }, deviceScaleFactor: 2.6666667 });
  await c.route(/\/assets\/index-[^/]+\.js$/, async route => {
    const res = await route.fetch(); let body = await res.text(); let n = 0;
    body = body.replace(HOOK, (m, v, cls, q, a, b2, c2) => { n++; return `${v}=new ${cls}(${q}("#physics"),${a},${b2},${c2}),window.__dg=${v}`; });
    if (!n) console.warn('UYARI: oyun motoru kancası bulunamadı; oyunun derlemesi değişmiş olabilir.');
    await route.fulfill({ response: res, body, headers: { ...res.headers(), 'content-type': 'application/javascript' } });
  });
  await c.addInitScript({ path: path.join(__dirname, 'audiohook.js') });
  await c.addInitScript(() => { try { localStorage.setItem('dilgames-guidance-v2', 'off'); } catch (e) {} setInterval(() => { if (window.__dg) window.__dg.showAimTutorial = false; }, 50); });
  try { return await play(b, c, attempt); } finally { await b.close().catch(() => {}); }
}

async function play(b, c, attempt) {
  const p = await c.newPage(); const errors = [];
  p.on('pageerror', e => errors.push(e.message));
  await p.goto(GAME_URL, { waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
  await p.getByText(rec.language, { exact: true }).click(); await p.waitForTimeout(600);

  const dir = path.join(out, `frames${attempt}`); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir);
  const cdp = await c.newCDPSession(p); const frames = []; let fi = 0;
  cdp.on('Page.screencastFrame', ev => {
    const f = path.join(dir, String(fi++).padStart(6, '0') + '.jpg');
    fs.writeFileSync(f, Buffer.from(ev.data, 'base64')); frames.push({ f, t: Date.now() });
    cdp.send('Page.screencastFrameAck', { sessionId: ev.sessionId }).catch(() => {});
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 90, maxWidth: 1080, maxHeight: 1920, everyNthFrame: 1 });
  await p.waitForTimeout(400);
  const recStart = await p.evaluate(() => window.__startRec());
  const t0 = Date.now(), marks = [];
  const mark = n => { marks.push({ n, t: Date.now() }); console.log('MARK', n, ((Date.now() - t0) / 1000).toFixed(2)); };

  mark('welcome'); await p.waitForTimeout(2200);
  await p.click('#welcome-start'); mark('home'); await p.waitForTimeout(2300);
  await p.locator('.platform-section').nth(rec.section).click(); mark('packs'); await p.waitForTimeout(1600);
  if (rec.tab) { await p.locator('[role=tab]').filter({ has: p.locator('b').getByText(rec.tab.split(' ')[0], { exact: true }) }).first().click({ timeout: 8000 }); await p.waitForTimeout(1200); }
  await p.locator('.pack-card').nth(rec.pack).click(); mark('levels'); await p.waitForTimeout(1600);
  const start = p.getByText('Başla', { exact: true });
  if (rec.level > 1 || !(await start.count())) await p.getByText(String(rec.level).padStart(2, '0'), { exact: false }).first().click();
  else await start.first().click();
  mark('intro');
  let introText = null;
  for (let i = 0; i < 60; i++) {
    await p.waitForTimeout(500);
    if (!introText && await p.locator('#intro-listen').isVisible().catch(() => false))
      introText = await p.locator('#intro-listen').evaluate(el => (el.closest('.modal, [role=dialog]') || el.parentElement.parentElement).innerText).catch(() => null);
    if (!(await p.locator('#intro-listen').isVisible().catch(() => false))) { const s = await bot.state(p); if (s && s.ready && s.hand.length) break; }
  }
  mark('vocab');
  let phase = 'vocab', stirred = !rec.stir, result = 'timeout';
  for (let k = 0; k < 70; k++) {
    const s = await bot.state(p); if (!s) { result = 'no-game'; break; }
    if (s.finished) { mark('finished'); result = 'finished'; break; }
    if (phase === 'vocab' && !s.vocab) { phase = 'sentence'; mark('sentence'); await p.waitForTimeout(1500); }
    if (!s.ready) { await p.waitForTimeout(500); continue; }
    if (!s.hand.length) {
      // Kelime turunda boşa giden balonlar kısa bir beklemeden sonra ele geri döner.
      let back = false;
      for (let w = 0; w < 10 && !back; w++) { await p.waitForTimeout(500); const t = await bot.state(p); back = !t || t.finished || t.hand.length > 0; }
      if (back) continue;
      if (!(await bot.grabTop(p))) { mark('stuck'); result = 'stuck'; break; }
    } else await bot.shoot(p, 950);
    await p.waitForTimeout(400);
    mark('shot:' + await p.$eval('#physics', e => e.dataset.lastFeedback));
    if (!stirred && !s.vocab && s.bubbles.length >= 4) { stirred = true; await p.waitForTimeout(800); await p.click('#stir').catch(() => {}); mark('stir'); await p.waitForTimeout(5500); }
    await p.waitForTimeout(1400);
    if (await p.locator('#finish-session').isVisible().catch(() => false)) { mark('options'); result = 'stuck'; break; }
    if (await p.locator('#win-notebook').isVisible().catch(() => false)) { mark('finished'); result = 'finished'; break; }
  }
  await p.waitForTimeout(7000); mark('end');
  const b64 = await p.evaluate(() => window.__stopRec());
  await cdp.send('Page.stopScreencast');
  return { result, recStart, marks, frames, errors, introText, audio: Buffer.from(b64, 'base64'), dir };
}

(async () => {
  const tries = Number(process.env.RECORD_TRIES || 4);
  for (let attempt = 1; attempt <= tries; attempt++) {
    let r;
    try { r = await take(attempt); } catch (e) { console.error('Deneme', attempt, 'hata:', e.message.split('\n')[0]); if (attempt === tries) throw e; continue; }
    console.log('SONUÇ', attempt, r.result, r.errors.length ? r.errors : '');
    if (r.result === 'finished' || attempt === tries) {
      fs.writeFileSync(path.join(out, 'take.webm'), r.audio);
      fs.writeFileSync(path.join(out, 'take.json'), JSON.stringify({ result: r.result, recStart: r.recStart, marks: r.marks, frames: r.frames, introText: r.introText }));
      for (let a = 1; a <= tries; a++) if (a !== attempt) fs.rmSync(path.join(out, `frames${a}`), { recursive: true, force: true });
      if (r.result !== 'finished') { console.error('Bölüm bitirilemedi; kayıt yine de kaydedildi.'); process.exitCode = 2; }
      return;
    }
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
