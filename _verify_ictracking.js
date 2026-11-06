/** Verify the ICtracking install across all 7 Grizzly Herb LPs. */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.join(__dirname, 'pages');
const PAGES = ['premium-collection-hsh', 'premium-collection-bb', 'premium-collection-bc',
  'premium-collection-rb', 'thca-vapes', 'd9-vapes-20pack', 'd9-vapes-bogo'];
const CONTAINER = '7875287254';

let pass = 0, fail = 0;
const say = (ok, m) => { ok ? pass++ : fail++; console.log(`    ${ok ? 'PASS' : 'FAIL'}  ${m}`); };

for (const slug of PAGES) {
  console.log(`\n  ${slug}`);
  const html = fs.readFileSync(path.join(ROOT, slug, 'index.html'), 'utf8');
  const head = html.slice(0, html.indexOf('</head>'));

  const loaders = (html.match(/icarusdigitalmarketing\.com\/s\.js/g) || []).length;
  say(loaders === 1, `exactly one loader (${loaders})`);
  say(head.includes('icarusdigitalmarketing.com/s.js'), 'loader is inside <head>');
  say(html.includes(`c=${CONTAINER}&p=other`), `container ${CONTAINER}, p=other`);

  // no auto events added by hand
  say(!/icTrack\(\s*["']PageView/.test(html), 'no manual PageView');
  say(!/icTrack\(\s*["']ViewContent/.test(html), 'no manual ViewContent');
  say(!/icTrack\(\s*["']InitiateCheckout/.test(html), 'no InitiateCheckout');

  // session guard: flag written before the event fires
  const h = html.indexOf('window.icATC');
  const helper = html.slice(h, h + 420);
  const setIdx = helper.indexOf('setItem("ic_atc_fired"');
  const fireIdx = helper.indexOf('icTrack("AddToCart"');
  say(setIdx > -1 && fireIdx > -1 && setIdx < fireIdx, 'guard flag set BEFORE the event');
  say(/currency:"CAD"/.test(helper), 'currency CAD');
  say(/content_type:"product"/.test(helper), 'content_type product');

  // every ATC site reached
  const calls = (html.match(/icATC\(/g) || []).length; // helper is 'icATC=function', not a call
  const tlqAtc = (html.match(/tlq\('track',\s*'AddToCart'|tlq\('track','AddToCart'/g) || []).length;
  say(calls >= 1, `${calls} icATC call site(s), alongside ${tlqAtc} tlq ATC lines`);

  // every inline script still parses
  const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
  let m, n = 0, errs = [];
  while ((m = re.exec(html)) !== null) {
    const code = m[1];
    if (!code.trim()) continue;
    if (/application\/ld\+json/i.test(m[0])) continue;
    n++;
    try { new vm.Script(code); } catch (e) { errs.push(`block ${n}: ${e.message}`); }
  }
  say(errs.length === 0, errs.length ? `JS errors: ${errs[0]}` : `all ${n} inline scripts parse`);
}

console.log(`\n  ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
