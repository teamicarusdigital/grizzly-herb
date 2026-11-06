/**
 * Drives each LP in Chromium and checks the ICtracking AddToCart behaviour:
 * fires once, carries the right payload, and a second add is suppressed.
 * The real loader is blocked; window.icTrack is pre-stubbed as a recorder, which
 * the snippet's `w.icTrack = w.icTrack || ...` leaves in place.
 */
const { chromium } = require('playwright');
const path = require('path');

const FLOWER = ['premium-collection-hsh', 'premium-collection-bb',
  'premium-collection-bc', 'premium-collection-rb'];
const D9 = ['d9-vapes-20pack', 'd9-vapes-bogo'];
const THCA = ['thca-vapes'];

const fileUrl = slug =>
  'file:///' + path.join(__dirname, 'pages', slug, 'index.html').replace(/\\/g, '/');

const STUB = () => {
  window.__ic = [];
  window.icTrack = function () { window.__ic.push(Array.prototype.slice.call(arguments)); };
};

async function open(browser, slug) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 1000 } });
  await ctx.route('**', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  await page.addInitScript(STUB);
  await page.goto(fileUrl(slug));
  await page.waitForTimeout(500);
  return { ctx, page, errs };
}

const events = page => page.evaluate(() => window.__ic.map(a => [a[0], a[1]]));

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, m) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${m}`); };

  for (const slug of [...FLOWER, ...THCA, ...D9]) {
    console.log(`\n  ${slug}`);
    const { ctx, page, errs } = await open(browser, slug);

    // nothing manual on load (PageView/ViewContent come from the library itself)
    const onLoad = await events(page);
    say(onLoad.length === 0, `no manual events on load (${onLoad.length})`);

    // add to cart, twice
    for (let i = 0; i < 2; i++) {
      if (FLOWER.includes(slug)) {
        await page.evaluate(() => {
          const b = document.querySelector('.gh-products__card-btn');
          if (b) b.click();
        });
      } else if (D9.includes(slug)) {
        await page.evaluate(() => {
          const b = document.querySelector('.qBtn[data-delta="1"]:not([disabled])');
          if (b) b.click();
        });
      } else {
        await page.evaluate(() => {
          const o = document.querySelector('.gh-bundle-option');
          if (o) o.click();
        });
        await page.waitForTimeout(300);
        await page.evaluate(() => {
          const b = document.querySelector('.gh-cart-plus:not([disabled])');
          if (b) b.click();
        });
      }
      await page.waitForTimeout(350);
    }

    const after = await events(page);
    const atc = after.filter(e => e[0] === 'AddToCart');
    say(atc.length === 1, `exactly ONE AddToCart after two adds (${atc.length})`);
    if (atc.length) {
      const p = atc[0][1] || {};
      say(p.currency === 'CAD', `currency CAD (${p.currency})`);
      say(p.content_type === 'product', `content_type product (${p.content_type})`);
      say(Array.isArray(p.content_ids) && p.content_ids.length > 0,
        `content_ids present (${JSON.stringify(p.content_ids)})`);
      say(typeof p.content_name === 'string' && p.content_name.length > 0,
        `content_name "${p.content_name}"`);
      say(typeof p.value === 'number' && p.value > 0,
        `value is a positive number (${p.value})`);
    }
    say(!after.some(e => e[0] === 'InitiateCheckout'), 'no InitiateCheckout fired');
    say(errs.length === 0, errs.length ? `JS errors: ${errs[0]}` : 'no JS errors');

    await ctx.close();
  }

  await browser.close();
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
