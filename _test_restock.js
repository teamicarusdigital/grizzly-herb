/**
 * Restock test. Takes a real page, flips a sold-out product back to in stock
 * exactly the way sync_stock.py would (data-variants only, classes untouched),
 * and checks the card reappears clean with no leftover "Out of Stock" overlay.
 */
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const os = require('os');

const SLUG = 'premium-collection-rb';
const PID = '183859'; // Golden Oreoz: fully sold out, and carries a hardcoded --out-of-stock class

(async () => {
  const src = path.join(__dirname, 'pages', SLUG, 'index.html');
  let html = fs.readFileSync(src, 'utf8');

  // flip every variant of PID to inStock:true, leaving classes alone
  const re = new RegExp(`(data-product-id="${PID}"[^>]*data-variants=')([^']+)(')`);
  const m = html.match(re);
  if (!m) { console.log('  FAIL: could not find the product'); process.exit(1); }
  const before = JSON.parse(m[2]);
  const after = before.map(v => Object.assign({}, v, { inStock: true }));
  const restocked = html.replace(re, `$1${JSON.stringify(after)}$3`);

  const tmpDir = path.join(__dirname, 'pages', SLUG);
  const tmp = path.join(tmpDir, '_restock_tmp.html');
  fs.writeFileSync(tmp, restocked);

  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, m2) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${m2}`); };

  try {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    await ctx.route('**', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.goto('file:///' + tmp.replace(/\\/g, '/'));
    await page.waitForTimeout(700);

    const r = await page.evaluate((pid) => {
      const card = document.querySelector(`.gh-products__card[data-product-id="${pid}"]`);
      if (!card) return null;
      return {
        visible: !!(card.offsetWidth || card.offsetHeight),
        hasOosOverlay: card.classList.contains('gh-products__card--out-of-stock'),
        hasHiddenClass: card.classList.contains('gh-products__card--hidden-oos'),
        pills: card.querySelectorAll('.gh-products__card-variant').length,
        activePills: card.querySelectorAll('.gh-products__card-variant--active').length,
        addBtn: !!card.querySelector('.gh-products__card-btn'),
      };
    }, PID);

    console.log(`\n  restocking ${PID} on ${SLUG} (${before.length} variants, was all sold out)`);
    say(r !== null, 'card exists in the DOM');
    say(r && r.visible, 'card is visible again after restock');
    say(r && !r.hasOosOverlay, 'the hardcoded "Out of Stock" overlay class was cleared');
    say(r && !r.hasHiddenClass, 'the hidden class was not applied');
    say(r && r.pills === before.length, `all ${before.length} variant pills rendered (got ${r && r.pills})`);
    say(r && r.activePills === 1, 'exactly one variant pill is active');
    say(r && r.addBtn, 'add-to-cart button present');
    say(errs.length === 0, errs.length ? `JS errors: ${errs[0]}` : 'no JS errors');
    await ctx.close();
  } finally {
    fs.unlinkSync(tmp);
    await browser.close();
  }

  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
