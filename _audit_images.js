/**
 * Loads every LP in a real browser and records every image request that fails,
 * so we catch what the customer actually sees, including images injected by JS.
 */
const { chromium } = require('playwright');

const PAGES = ['premium-collection-hsh', 'premium-collection-bb', 'premium-collection-bc',
  'premium-collection-rb', 'thca-vapes', 'd9-vapes-20pack', 'd9-vapes-bogo'];

(async () => {
  const browser = await chromium.launch();
  const failures = new Map();   // url -> {status, pages:Set}
  const okCount = new Map();

  for (const slug of PAGES) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 1200 } });
    const page = await ctx.newPage();

    page.on('response', async res => {
      const req = res.request();
      if (req.resourceType() !== 'image') return;
      const u = res.url();
      if (res.status() >= 400) {
        if (!failures.has(u)) failures.set(u, { status: res.status(), pages: new Set() });
        failures.get(u).pages.add(slug);
      } else {
        okCount.set(slug, (okCount.get(slug) || 0) + 1);
      }
    });
    page.on('requestfailed', req => {
      if (req.resourceType() !== 'image') return;
      const u = req.url();
      if (!failures.has(u)) failures.set(u, { status: 'FAILED: ' + (req.failure() || {}).errorText, pages: new Set() });
      failures.get(u).pages.add(slug);
    });

    await page.goto(`https://app.grizzlyherb.us/pages/${slug}?cb=${Date.now()}`,
      { waitUntil: 'domcontentloaded', timeout: 90000 }).catch(() => {});
    // scroll the whole page so lazy images load
    await page.evaluate(async () => {
      await new Promise(r => {
        let y = 0;
        const t = setInterval(() => {
          window.scrollBy(0, 900); y += 900;
          if (y >= document.body.scrollHeight + 2000) { clearInterval(t); r(); }
        }, 120);
      });
    });
    await page.waitForTimeout(2500);
    // open any interactive grids that render images lazily
    await page.evaluate(() => {
      const o = document.querySelector('.gh-bundle-option'); if (o) o.click();
    });
    await page.waitForTimeout(1500);
    console.log(`  ${slug.padEnd(24)} ok=${okCount.get(slug) || 0}`);
    await ctx.close();
  }

  await browser.close();

  console.log(`\n  ===== BROKEN IMAGES: ${failures.size} unique =====`);
  if (!failures.size) { console.log('    none'); return; }
  const byHost = new Map();
  for (const [u, info] of failures) {
    const host = new URL(u).host;
    if (!byHost.has(host)) byHost.set(host, []);
    byHost.get(host).push({ u, ...info });
  }
  for (const [host, list] of byHost) {
    console.log(`\n  ${host}  (${list.length})`);
    list.forEach(f => {
      console.log(`    [${f.status}] ${f.u.replace('https://' + host, '')}`);
      console.log(`         on: ${[...f.pages].join(', ')}`);
    });
  }
})();
