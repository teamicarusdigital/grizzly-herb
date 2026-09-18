/**
 * Verifies that out-of-stock items are absent from the rendered page, and that
 * every in-stock item is still present. Compares the page's own data against
 * what the DOM actually renders, so it stays true as stock sync changes.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const FLOWER = ['premium-collection-hsh', 'premium-collection-bb',
  'premium-collection-bc', 'premium-collection-rb'];
const VAPE = ['thca-vapes', 'd9-vapes-20pack', 'd9-vapes-bogo'];

const fileUrl = slug =>
  'file:///' + path.join(__dirname, 'pages', slug, 'index.html').replace(/\\/g, '/');

function cartridgeData(slug) {
  const html = fs.readFileSync(path.join(__dirname, 'pages', slug, 'index.html'), 'utf8');
  const re = /\{pid:'(\d+)'[^}]*?inStock:(true|false)/g;
  const out = [];
  let m;
  while ((m = re.exec(html)) !== null) out.push({ pid: m[1], inStock: m[2] === 'true' });
  // the vape pages declare CARTRIDGES once; dedupe defensively
  const seen = new Set();
  return out.filter(c => (seen.has(c.pid) ? false : seen.add(c.pid)));
}

function flowerData(slug) {
  const html = fs.readFileSync(path.join(__dirname, 'pages', slug, 'index.html'), 'utf8');
  const re = /data-product-id="(\d+)"[^>]*data-variants='([^']+)'/g;
  const out = [];
  let m;
  while ((m = re.exec(html)) !== null) {
    const vs = JSON.parse(m[2]);
    out.push({
      pid: m[1],
      variants: vs,
      oosCount: vs.filter(v => v.inStock === false).length,
      allOos: vs.every(v => v.inStock === false),
    });
  }
  return out;
}

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, m) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${m}`); };

  for (const slug of VAPE) {
    console.log(`\n  ${slug}`);
    const data = cartridgeData(slug);
    const oos = data.filter(c => !c.inStock);
    const inStock = data.filter(c => c.inStock);

    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    await ctx.route('**', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.goto(fileUrl(slug));
    await page.waitForTimeout(400);
    if (slug === 'thca-vapes') {
      await page.evaluate(() => {
        const o = document.querySelector('.gh-bundle-option');
        if (o) o.click();
      });
      await page.waitForTimeout(400);
    }

    const rendered = await page.evaluate(() =>
      Array.from(document.querySelectorAll('[data-pid], [data-ipid]'))
        .map(e => e.getAttribute('data-pid') || e.getAttribute('data-ipid'))
        .filter(Boolean));
    const set = new Set(rendered);

    console.log(`      data: ${inStock.length} in stock, ${oos.length} sold out`);
    say(oos.length > 0, `there is at least one sold-out item to test (${oos.map(c => c.pid).join(',')})`);
    const leaked = oos.filter(c => set.has(c.pid));
    say(leaked.length === 0, `no sold-out cartridge rendered (leaked: ${leaked.map(c => c.pid).join(',') || 'none'})`);
    const missing = inStock.filter(c => !set.has(c.pid));
    say(missing.length === 0, `every in-stock cartridge still rendered (missing: ${missing.map(c => c.pid).join(',') || 'none'})`);
    say(errs.length === 0, errs.length ? `JS errors: ${errs[0]}` : 'no JS errors');
    await ctx.close();
  }

  for (const slug of FLOWER) {
    console.log(`\n  ${slug}`);
    const data = flowerData(slug);
    const allOos = data.filter(p => p.allOos);
    const partial = data.filter(p => !p.allOos && p.oosCount > 0);

    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    await ctx.route('**', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.goto(fileUrl(slug));
    await page.waitForTimeout(600);

    const dom = await page.evaluate(() => {
      const out = {};
      document.querySelectorAll('.gh-products__card[data-product-id]').forEach(c => {
        const pid = c.getAttribute('data-product-id');
        const vis = !!(c.offsetWidth || c.offsetHeight);
        out[pid] = {
          visible: vis,
          pills: Array.from(c.querySelectorAll('.gh-products__card-variant'))
            .map(p => p.getAttribute('data-vid')),
          oosPills: c.querySelectorAll('.gh-products__card-variant--oos').length,
        };
      });
      return out;
    });

    console.log(`      data: ${data.length} products, ${allOos.length} fully sold out, ${partial.length} partly`);
    say(allOos.length > 0, `there is at least one fully sold-out product to test (${allOos.map(p => p.pid).join(',')})`);
    const shownAllOos = allOos.filter(p => dom[p.pid] && dom[p.pid].visible);
    say(shownAllOos.length === 0, `fully sold-out products hidden (still visible: ${shownAllOos.map(p => p.pid).join(',') || 'none'})`);

    let pillLeak = [], pillMissing = [];
    data.filter(p => !p.allOos).forEach(p => {
      const d = dom[p.pid];
      if (!d) return;
      const shown = new Set(d.pills);
      p.variants.forEach(v => {
        if (v.inStock === false && shown.has(String(v.vid))) pillLeak.push(`${p.pid}/${v.vid}`);
        if (v.inStock !== false && !shown.has(String(v.vid))) pillMissing.push(`${p.pid}/${v.vid}`);
      });
    });
    say(pillLeak.length === 0, `no sold-out variant pill rendered (leaked: ${pillLeak.join(',') || 'none'})`);
    say(pillMissing.length === 0, `every in-stock variant pill still rendered (missing: ${pillMissing.join(',') || 'none'})`);

    const anyActive = await page.evaluate(() =>
      Array.from(document.querySelectorAll('.gh-products__card[data-product-id]'))
        .filter(c => c.offsetWidth || c.offsetHeight)
        .every(c => c.querySelectorAll('.gh-products__card-variant').length === 0
          || c.querySelectorAll('.gh-products__card-variant--active').length === 1));
    say(anyActive, 'every visible card has exactly one active variant pill');
    say(errs.length === 0, errs.length ? `JS errors: ${errs[0]}` : 'no JS errors');
    await ctx.close();
  }

  await browser.close();
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
