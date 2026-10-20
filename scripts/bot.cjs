// Oynanış botu: oyunun kendi durumunu (window.__dg) okuyup hedefe nişan alır.
// Yalnızca kayıt içindir; oyunun kaynak koduna dokunmaz.

exports.state = (p) => p.evaluate(() => {
  const g = window.__dg; if (!g) return null;
  const w = g.world;
  return {
    ready: w.ready, vocab: !!w.state.vocabularyMode, finished: !!w.state.finished,
    hand: w.state.hand.map(f => ({ s: f.sentence, a: f.start, e: f.end })),
    deck: w.state.deck.length,
    bubbles: [...w.bubbles.values()].map(b => ({ id: b.id, x: b.body.position.x, y: b.body.position.y, s: b.sentence, wet: b.wet })),
  };
});

// Eldeki parçalardan, üstü en açık hedefi olanı seçip atar.
exports.shoot = async (p, holdMs = 950) => {
  const info = await p.evaluate(() => {
    const g = window.__dg, w = g.world;
    if (!w.ready || !w.state.hand.length) return null;
    const all = [...w.bubbles.values()];
    let best = null;
    for (let i = 0; i < w.state.hand.length; i++) {
      // hint() ipucu hakkı harcadığı için kullanılmaz; eşleşmeyi doğrudan oyunun kuralıyla bulur.
      const f = w.state.hand[i];
      const targets = all.filter(b => b.wet && !(w.state.vocabularyMode && b.vocabularyShot) && w.match(f, b));
      for (const t of targets) {
        const bx = t.body.position.x, width = t.body.bounds.max.x - t.body.bounds.min.x;
        const xs = [];
        for (let dx = -0.35; dx <= 0.351; dx += 0.07) {
          const x = bx + dx * width;
          const blockers = all.filter(o => o !== t && o.wet && !(w.state.vocabularyMode && o.vocabularyShot) && o.body.bounds.min.y < t.body.bounds.min.y && o.body.bounds.min.x < x + 6 && o.body.bounds.max.x > x - 6).length;
          xs.push({ x, blockers, d: Math.abs(dx) });
        }
        xs.sort((a, b) => a.blockers - b.blockers || a.d - b.d);
        const score = xs[0].blockers * 10 + i * 0.1;
        if (!best || score < best.score) best = { i, x: xs[0].x, score };
      }
    }
    return best || { i: 0, x: null };
  });
  if (!info) return false;
  const choices = p.locator('.word-choice');
  if (info.i > 0 && await choices.count() > info.i) { await choices.nth(info.i).click(); await p.waitForTimeout(350); }
  const r = await p.evaluate(() => { const c = window.__dg.canvas.getBoundingClientRect(); return { x: c.x, y: c.y, w: c.width, h: c.height, W: window.__dg.world.pixelScale * c.width }; });
  const wx = info.x ?? r.W / 2;
  const sx = r.x + wx / r.W * r.w, sy = r.y + r.h * 0.25;
  await p.mouse.move(r.x + r.w / 2, sy); await p.waitForTimeout(150);
  await p.mouse.move(sx, sy, { steps: 14 }); await p.waitForTimeout(250);
  await p.mouse.down(); await p.waitForTimeout(holdMs); await p.mouse.up();
  return true;
};

// Kelime eşleştirmede geri dönen balonu tutup eşinin üstüne sürükler.
exports.grabTop = async (p, holdMs = 800) => {
  const info = await p.evaluate(() => {
    const g = window.__dg, w = g.world, c = g.canvas.getBoundingClientRect(), W = w.pixelScale * c.width;
    const list = [...w.bubbles.values()];
    const top = list.filter(b => !b.wet).sort((a, b) => a.body.position.y - b.body.position.y)[0];
    if (!top) return null;
    const pair = list.find(b => b !== top && b.wet && b.sentence === top.sentence);
    const m = (x, y) => ({ x: c.x + x / W * c.width, y: c.y + y / W * c.width });
    return { from: m(top.body.position.x, top.body.position.y), to: pair ? m(pair.body.position.x, top.body.position.y) : null };
  });
  if (!info) return false;
  await p.mouse.move(info.from.x, info.from.y); await p.mouse.down(); await p.waitForTimeout(200);
  if (info.to) await p.mouse.move(info.to.x, info.to.y, { steps: 16 });
  await p.waitForTimeout(holdMs); await p.mouse.up();
  return true;
};
