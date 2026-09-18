/**
 * Proves the real checkout URL carries gh_offer=carts3 after a popup submit,
 * and carries nothing when the popup was never submitted.
 *
 * Captures the outgoing request to grizzlyherb.co/cart|checkout rather than
 * letting it leave, so it works offline and sees the exact URL the customer
 * would be sent to, whether the page navigates or POSTs a form.
 */
const { chromium } = require('playwright');
const path = require('path');

const fileUrl = slug =>
  'file:///' + path.join(__dirname, 'pages', slug, 'index.html').replace(/\\/g, '/');

async function open(browser, slug, submitPopup) {
  const ctx = await browser.newContext();
  const captured = [];
  await ctx.route('**', route => {
    const u = route.request().url();
    if (u.startsWith('file:')) return route.continue();
    if (/grizzlyherb\.co\/(cart|checkout)/.test(u)) {
      captured.push(u);
      return route.fulfill({ status: 200, contentType: 'text/html', body: 'stub' });
    }
    return route.abort();
  });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.log('      JS ERROR: ' + e.message));
  await page.goto(fileUrl(slug) + '?utm_source=fbtest&gh_offer=carts3');
  await page.waitForTimeout(300);
  if (submitPopup) {
    await page.evaluate(() => window.dispatchEvent(
      new CustomEvent('klaviyoForms', { detail: { formId: 'Sn3i8w', type: 'submit' } })));
    await page.waitForTimeout(150);
  }
  return { ctx, page, captured };
}

async function vape(browser, slug, submitPopup) {
  const { ctx, page, captured } = await open(browser, slug, submitPopup);
  await page.evaluate(() => {
    for (let i = 0; i < 40; i++) {
      const b = document.querySelector('.qBtn[data-delta="1"]:not([disabled])');
      if (!b) break;
      b.click();
    }
  });
  await page.waitForTimeout(150);
  await page.evaluate(() => window.submitBundle && window.submitBundle());
  await page.waitForTimeout(500);
  await ctx.close();
  return captured[0] || null;
}

async function thca(browser, slug, submitPopup) {
  const { ctx, page, captured } = await open(browser, slug, submitPopup);
  const opt = page.locator('.gh-bundle-option').first();
  if (await opt.count()) { await opt.click({ force: true }); await page.waitForTimeout(400); }
  await page.evaluate(() => {
    for (let i = 0; i < 80; i++) {
      const b = document.querySelector('.gh-cart-plus:not([disabled])');
      if (!b) break;
      b.click();
    }
  });
  await page.waitForTimeout(300);
  const clicked = await page.evaluate(() => {
    const b = document.querySelector('#gh-checkout-btn');
    if (!b || b.disabled) return false;
    b.scrollIntoView();
    b.click();
    return true;
  });
  if (clicked) await page.waitForTimeout(700);
  else console.log('      (could not complete a bundle, checkout stayed disabled)');
  await ctx.close();
  return captured[0] || null;
}

async function flower(browser, slug, submitPopup) {
  const { ctx, page, captured } = await open(browser, slug, submitPopup);
  const add = page.locator('.gh-products__card-btn').first();
  if (await add.count()) { await add.click({ force: true }); await page.waitForTimeout(500); }
  const co = page.locator('.gh-cart-panel__checkout-btn').first();
  if (await co.count()) { await co.click({ force: true }); await page.waitForTimeout(800); }
  await ctx.close();
  return captured[0] || null;
}

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, m) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${m}`); };

  const suites = [
    ['d9-vapes-bogo', vape], ['d9-vapes-20pack', vape], ['thca-vapes', thca],
    ['premium-collection-rb', flower], ['premium-collection-hsh', flower],
    ['premium-collection-bb', flower], ['premium-collection-bc', flower],
  ];

  for (const [slug, drive] of suites) {
    console.log(`\n  ${slug}`);
    const before = await drive(browser, slug, false);
    const after = await drive(browser, slug, true);
    console.log(`      no submit : ${before}`);
    console.log(`      submitted : ${after}`);
    if (!before || !after) { say(false, 'could not drive this page to checkout'); continue; }
    say(before.indexOf('gh_offer') === -1, 'no popup submit -> checkout has NO gh_offer');
    say(after.indexOf('gh_offer=carts3') !== -1, 'after submit -> checkout carries gh_offer=carts3');
    say(after.indexOf('utm_source=fbtest') !== -1, 'utm attribution still intact');
  }

  await browser.close();
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
