/** Live check: popup heading no longer overlaps, at every viewport. */
const { chromium } = require('playwright');

const VIEWPORTS = [
  { name: 'mobile-360', width: 360, height: 740 },
  { name: 'mobile-390', width: 390, height: 844 },
  { name: 'tablet-768', width: 768, height: 1024 },
  { name: 'desktop-1280', width: 1280, height: 900 },
];
const PAGES = ['d9-vapes-bogo', 'd9-vapes-20pack', 'thca-vapes', 'premium-collection-rb'];

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, m) => { ok ? pass++ : fail++; console.log(`      ${ok ? 'PASS' : 'FAIL'}  ${m}`); };

  for (const slug of PAGES) {
    console.log(`\n  ${slug}`);
    for (const vp of VIEWPORTS) {
      const ctx = await browser.newContext({
        viewport: { width: vp.width, height: vp.height },
        isMobile: vp.width < 768, hasTouch: vp.width < 768,
      });
      const page = await ctx.newPage();
      await page.goto(`https://app.grizzlyherb.us/pages/${slug}?cb=${Date.now()}`,
        { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
      let shown = false;
      for (let t = 0; t < 14; t++) {
        await page.waitForTimeout(1000);
        shown = await page.evaluate(() => !!document.querySelector('[class*="kl-private-reset-css"]'));
        if (shown) break;
      }
      if (!shown) { say(false, `${vp.name}: popup never appeared`); await ctx.close(); continue; }
      await page.waitForTimeout(700);

      const r = await page.evaluate(() => {
        const modal = document.querySelector('[class*="kl-private-reset-css"]');
        const h1 = modal.querySelector('h1');
        const cs = h1 ? getComputedStyle(h1) : null;
        const leaves = Array.from(modal.querySelectorAll('*'))
          .filter(e => (e.textContent || '').trim() && !e.children.length)
          .map(e => { const b = e.getBoundingClientRect();
            return { t: e.textContent.trim().slice(0, 20), top: b.top, bottom: b.bottom, left: b.left, right: b.right }; })
          .filter(i => i.bottom - i.top > 1);
        let worst = 0, pair = '';
        for (let i = 0; i < leaves.length; i++)
          for (let j = i + 1; j < leaves.length; j++) {
            const a = leaves[i], b = leaves[j];
            const v = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            const h = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            if (v > 2 && h > 2 && v > worst) { worst = v; pair = `"${a.t}" x "${b.t}"`; }
          }
        return { lh: cs ? cs.lineHeight : 'n/a', ls: cs ? cs.letterSpacing : 'n/a', worst: Math.round(worst), pair };
      });
      say(r.worst === 0, `${vp.name.padEnd(13)} lh=${String(r.lh).padEnd(8)} ls=${String(r.ls).padEnd(8)} overlap=${r.worst}px ${r.pair}`);
      await ctx.close();
    }
  }
  await browser.close();
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
