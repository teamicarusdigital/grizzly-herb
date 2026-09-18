/**
 * End-to-end check of the Klaviyo free-cartridge flag in a real browser.
 * Runs offline: all external requests are aborted, and the Klaviyo event is
 * dispatched directly, which is the same event Klaviyo itself fires.
 */
const { chromium } = require('playwright');
const path = require('path');

const PAGES = ['premium-collection-hsh', 'premium-collection-bb', 'premium-collection-bc',
  'premium-collection-rb', 'thca-vapes', 'd9-vapes-20pack', 'd9-vapes-bogo'];

const fileUrl = slug =>
  'file:///' + path.join(__dirname, 'pages', slug, 'index.html').replace(/\\/g, '/');

const countOfferLinks = page => page.evaluate(() =>
  Array.from(document.querySelectorAll('a[href*="grizzlyherb.co"]'))
    .filter(a => a.getAttribute('href').indexOf('gh_offer=carts3') !== -1).length);

const countStoreLinks = page => page.evaluate(() =>
  document.querySelectorAll('a[href*="grizzlyherb.co"]').length);

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, msg) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${msg}`); };

  for (const slug of PAGES) {
    console.log(`\n  ${slug}`);
    const ctx = await browser.newContext();
    // stay offline: no Klaviyo, no Tracklution, no fonts, no remote images
    await ctx.route('**', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
    const page = await ctx.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));

    // 1. LEAK TEST: arrive with gh_offer in the URL, popup never submitted
    await page.goto(fileUrl(slug) + '?utm_source=test&gh_offer=carts3');
    await page.waitForTimeout(250);
    const storeLinks = await countStoreLinks(page);
    say(storeLinks > 0, `found ${storeLinks} grizzlyherb.co links to inspect`);
    say((await countOfferLinks(page)) === 0, 'inbound ?gh_offer granted nothing');

    // 2. popup submitted -> links back-filled
    await page.evaluate(() => window.dispatchEvent(
      new CustomEvent('klaviyoForms', { detail: { formId: 'Sn3i8w', type: 'submit' } })));
    await page.waitForTimeout(150);
    const after = await countOfferLinks(page);
    say(after === storeLinks, `all ${storeLinks} store links carry gh_offer after submit (got ${after})`);

    // 3. wrong form id must not unlock
    const ctx2 = await browser.newContext();
    await ctx2.route('**', r => r.request().url().startsWith('file:') ? r.continue() : r.abort());
    const p2 = await ctx2.newPage();
    await p2.goto(fileUrl(slug));
    await p2.waitForTimeout(200);
    await p2.evaluate(() => window.dispatchEvent(
      new CustomEvent('klaviyoForms', { detail: { formId: 'WRONG1', type: 'submit' } })));
    await p2.waitForTimeout(150);
    say((await countOfferLinks(p2)) === 0, 'a different Klaviyo form does not unlock it');
    await ctx2.close();

    // 4. persistence: same context, fresh load, flag must survive via localStorage
    await page.goto(fileUrl(slug));
    await page.waitForTimeout(250);
    const onReload = await countOfferLinks(page);
    say(onReload === (await countStoreLinks(page)) && onReload > 0,
      `flag survives reload, links decorated at load (${onReload})`);

    say(errors.length === 0, errors.length ? `JS errors: ${errors.join(' | ')}` : 'no JS errors');
    await ctx.close();
  }

  await browser.close();
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
