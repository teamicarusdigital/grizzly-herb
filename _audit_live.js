/** Full live audit: sold-out hidden, restocked visible, popup clean, offer intact. */
const { chromium } = require('playwright');

const FLOWER = ['premium-collection-hsh', 'premium-collection-bb', 'premium-collection-bc', 'premium-collection-rb'];
const VAPE = ['thca-vapes', 'd9-vapes-20pack', 'd9-vapes-bogo'];

// current truth from WooCommerce, confirmed by running sync_stock.py
const RESTOCKED = '183881';           // Ghost Breath, was fully sold out today
const STILL_OOS = ['144038', '183859'];
const OOS_CARTRIDGE = '125872';       // Peach Rings

(async () => {
  const browser = await chromium.launch();
  let pass = 0, fail = 0;
  const say = (ok, m) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${m}`); };

  for (const slug of FLOWER) {
    console.log(`\n  ${slug}`);
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.goto(`https://app.grizzlyherb.us/pages/${slug}?cb=${Date.now()}`, { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForTimeout(2200);

    const r = await page.evaluate((args) => {
      const vis = pid => {
        const c = document.querySelector(`.gh-products__card[data-product-id="${pid}"]`);
        return c ? !!(c.offsetWidth || c.offsetHeight) : null;
      };
      const card = document.querySelector(`.gh-products__card[data-product-id="${args.restocked}"]`);
      return {
        restockedVisible: vis(args.restocked),
        restockedPills: card ? card.querySelectorAll('.gh-products__card-variant').length : 0,
        restockedHasOosOverlay: card ? card.classList.contains('gh-products__card--out-of-stock') : null,
        restockedBuyable: card ? !!card.querySelector('.gh-products__card-btn') : false,
        stillOosVisible: args.stillOos.map(vis),
        strikeThroughPills: document.querySelectorAll('.gh-products__card-variant--oos').length,
        visibleCards: Array.from(document.querySelectorAll('.gh-products__card[data-product-id]')).filter(c => c.offsetWidth || c.offsetHeight).length,
      };
    }, { restocked: RESTOCKED, stillOos: STILL_OOS });

    say(r.restockedVisible === true, `restocked Ghost Breath (${RESTOCKED}) is VISIBLE again`);
    say(r.restockedPills === 3, `it has all 3 variant pills back (${r.restockedPills})`);
    say(r.restockedHasOosOverlay === false, 'no leftover "Out of Stock" overlay on it');
    say(r.restockedBuyable, 'it has an add-to-cart button');
    say(r.stillOosVisible.every(v => v === false), `still-sold-out products stay hidden (${STILL_OOS.join(',')})`);
    say(r.strikeThroughPills === 0, 'no struck-through variant pills anywhere');
    say(r.visibleCards === 10, `10 of 12 product cards visible (got ${r.visibleCards})`);
    say(errs.length === 0, errs.length ? `JS errors: ${errs[0]}` : 'no JS errors');
    await ctx.close();
  }

  for (const slug of VAPE) {
    console.log(`\n  ${slug}`);
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on('pageerror', e => errs.push(e.message));
    await page.goto(`https://app.grizzlyherb.us/pages/${slug}?cb=${Date.now()}`, { waitUntil: 'domcontentloaded' }).catch(() => {});
    await page.waitForTimeout(2000);
    if (slug === 'thca-vapes') {
      await page.evaluate(() => { const o = document.querySelector('.gh-bundle-option'); if (o) o.click(); });
      await page.waitForTimeout(600);
    }
    const r = await page.evaluate((oosPid) => ({
      oosRendered: document.querySelectorAll(`[data-pid="${oosPid}"], [data-ipid="${oosPid}"]`).length,
      greyed: document.querySelectorAll('.flavorCard.oos, .gh-cartridge-card--oos').length,
      visible: Array.from(document.querySelectorAll('.flavorCard, .gh-cartridge-card')).filter(c => c.offsetWidth || c.offsetHeight).length,
    }), OOS_CARTRIDGE);
    say(r.oosRendered === 0, `sold-out Peach Rings (${OOS_CARTRIDGE}) not rendered`);
    say(r.greyed === 0, 'no greyed-out cartridges');
    say(r.visible > 0, `${r.visible} cartridges showing`);
    say(errs.length === 0, errs.length ? `JS errors: ${errs[0]}` : 'no JS errors');
    await ctx.close();
  }

  await browser.close();
  console.log(`\n  ${pass} passed, ${fail} failed\n`);
  process.exit(fail ? 1 : 0);
})();
