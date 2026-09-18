/**
 * Smoke test against the LIVE site with the real Klaviyo script loading, to
 * catch any conflict between Klaviyo's onsite JS and the offer logic.
 * Dispatches the klaviyoForms event directly, so no real subscriber is created.
 */
const { chromium } = require('playwright');

const PAGES = ['premium-collection-hsh', 'premium-collection-bb', 'premium-collection-bc',
  'premium-collection-rb', 'thca-vapes', 'd9-vapes-20pack', 'd9-vapes-bogo'];

const offerLinks = p => p.evaluate(() =>
  Array.from(document.querySelectorAll('a[href*="grizzlyherb.co"]'))
    .filter(a => a.getAttribute('href').includes('gh_offer=carts3')).length);
const storeLinks = p => p.evaluate(() =>
  document.querySelectorAll('a[href*="grizzlyherb.co"]').length);

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, m) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${m}`); };

  for (const slug of PAGES) {
    console.log(`\n  ${slug}`);
    const ctx = await browser.newContext();
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));

    // arrive with gh_offer in the URL: must grant nothing
    await page.goto(`https://app.grizzlyherb.us/pages/${slug}?utm_source=live&gh_offer=carts3`,
      { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(1200);

    const klaviyoLoaded = await page.evaluate(() =>
      !!document.querySelector('script[src*="klaviyo.js"]'));
    say(klaviyoLoaded, 'Klaviyo onsite script present');

    const total = await storeLinks(page);
    say((await offerLinks(page)) === 0, `inbound ?gh_offer granted nothing (${total} store links)`);

    await page.evaluate(() => window.dispatchEvent(
      new CustomEvent('klaviyoForms', { detail: { formId: 'Sn3i8w', type: 'submit' } })));
    await page.waitForTimeout(400);
    const after = await offerLinks(page);
    say(after === total && total > 0, `all ${total} store links carry gh_offer after submit (${after})`);

    say(errs.length === 0, errs.length ? `JS errors: ${errs.slice(0, 2).join(' | ')}` : 'no JS errors with Klaviyo live');
    await ctx.close();
  }

  await browser.close();
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
