"""
copy_rb_sections.py
===================
Directly copies the top banner, stats ribbon, and bundle product
section from rb into bb and bc, then applies persona-specific text.
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

with open('pages/premium-collection-rb/index.html', encoding='utf-8') as f:
    rb = f.read()

# ── Extract blocks from rb ────────────────────────────────────────────────────

# Top banner: <div class="gh-banner" ...> ... </div>  (the 2nd closing </div>)
s_banner = rb.find('  <div class="gh-banner"')
e_banner = rb.find('  </div>', s_banner)          # first inner </div>
e_banner = rb.find('\n  </div>', e_banner + 1) + len('\n  </div>')
RB_BANNER = rb[s_banner:e_banner]

# Stats ribbon: <section class="gh-stats-ribbon"> ... </section>
s_ribbon = rb.find('  <section class="gh-stats-ribbon">')
e_ribbon = rb.find('  </section>', s_ribbon) + len('  </section>')
RB_RIBBON = rb[s_ribbon:e_ribbon]

# Bundle block: <!-- ======== BUNDLE BUY BOX --> through </section> of gh-bb
s_bundle = rb.find('<!-- ======== BUNDLE BUY BOX ======== -->')
e_bundle = rb.find('<section class="gh-catalog"')
RB_BUNDLE_BLOCK = rb[s_bundle:e_bundle]

# CSS blocks to inject if missing
s_css = rb.find('/* ===== Bundle Buy Box v3 (gh-bb) ===== */')
e_css = rb.find('</style>', s_css)
GH_BB_CSS = rb[s_css:e_css]

# Banner CSS
s_banner_css = rb.find('/* ===== Top Banner ===== */')
e_banner_css = rb.find('\n\n', s_banner_css + 50)   # end at next blank line gap
# fallback: grab until next major CSS comment
e_banner_css2 = rb.find('/* =====', s_banner_css + 10)
BANNER_CSS = rb[s_banner_css : min(e_banner_css2, e_css - 1)]

# Ribbon CSS
s_ribbon_css = rb.find('/* ===== Stats Ribbon ===== */')
e_ribbon_css = rb.find('/* =====', s_ribbon_css + 10)
RIBBON_CSS = rb[s_ribbon_css:e_ribbon_css]

# Bundle Picker v3 JS
s_js = rb.find('  // === Bundle Picker v3 ===')
e_js = rb.find('  // === Click delegation ===')
BUNDLE_PICKER_JS = rb[s_js:e_js]

# Marquee JS block
s_marquee = rb.find('  // === Marquee ===')
e_marquee = rb.find('\n\n  //', s_marquee + 10)
if e_marquee < 0:
    e_marquee = rb.find('\n  // ===', s_marquee + 10)
MARQUEE_JS = rb[s_marquee:e_marquee]


# ── Persona config ─────────────────────────────────────────────────────────────
PERSONAS = {
    'bb': {
        'path': 'pages/premium-collection-bb/index.html',
        # gh-bundle (green promo)
        'bundle_badge':    'BULK BUYER DEAL',
        'bundle_heading':  'Stock Up and <strong>Save Big</strong>',
        'bundle_sub':      'Mix any 5 strains. More volume, better value. The way bulk buyers order.',
        'bundle_features': [
            'Best price per oz in Canada',
            'QP and full pound on every strain',
            'Free shipping on orders over $90',
            'Same strains available every reorder',
        ],
        'bundle_cta':  'Stock Up Now &darr;',
        'bundle_note': 'Best per-oz price in Canada. 2,000+ orders and counting.',
        # gh-bb (buy box)
        'badge': 'BULK SAVER DEAL',
        'title': 'Stock Up With a 5-Oz Bundle',
        'sub':   'Pick any 5 strains. Best per-oz price when you buy in volume.',
        'trust': [
            'Best price per oz in Canada',
            'QP and full pound on every strain',
            'Free shipping on orders over $90',
            'Same strains available every reorder',
        ],
        'fine': 'Best per-oz price &middot; Free shipping over $90 &middot; Secure checkout',
        # catalog
        'catalog_heading': 'Bulk and Individual Strain Options',
        'catalog_sub':     'Oz, QP, and full pound options. Stack up and save the more you buy.',
    },
    'bc': {
        'path': 'pages/premium-collection-bc/index.html',
        # gh-bundle (green promo)
        'bundle_badge':    'TOP SHELF ONLY',
        'bundle_heading':  'Premium Flower for <strong>Discerning Buyers</strong>',
        'bundle_sub':      'Handpick 5 top-shelf strains. No guessing, no disappointment.',
        'bundle_features': [
            'Hand-selected AAAA+ flower only',
            'Lab-tested, batch-consistent quality',
            'No mystery bags, no nasty surprises',
            '60-day freshness guarantee',
        ],
        'bundle_cta':  'Curate Your Bundle &darr;',
        'bundle_note': 'Hand-selected AAAA+ only. Batch-tested, freshness guaranteed.',
        # gh-bb (buy box)
        'badge': 'TOP SHELF SELECTION',
        'title': 'Curate Your Connoisseur Bundle',
        'sub':   "Pick 5 premium strains. You've been burned before. This is the fix.",
        'trust': [
            'Hand-selected AAAA+ flower only',
            'Lab-tested, batch-consistent quality',
            'No mystery bags, no nasty surprises',
            '60-day freshness guarantee',
        ],
        'fine': 'AAAA+ premium flower &middot; Free shipping over $90 &middot; Secure checkout',
        # catalog
        'catalog_heading': 'The Premium Selection',
        'catalog_sub':     'AAAA+ strains for the serious buyer. Oz, QP, and full pound.',
    },
}


def make_bundle_block(p):
    block = RB_BUNDLE_BLOCK
    # gh-bundle
    block = block.replace('<div class="gh-bundle__badge">Most Popular Deal</div>',
                          f'<div class="gh-bundle__badge">{p["bundle_badge"]}</div>')
    block = block.replace('<h2 class="gh-bundle__heading">Buy 4oz, <strong>Get 1oz Free</strong></h2>',
                          f'<h2 class="gh-bundle__heading">{p["bundle_heading"]}</h2>')
    block = block.replace('<p class="gh-bundle__sub">Mix and match any AAAA strains. The way most of our regulars order.</p>',
                          f'<p class="gh-bundle__sub">{p["bundle_sub"]}</p>')
    features_html = '\n'.join(
        f'      <div class="gh-bundle__feature">'
        f'<span class="gh-bundle__feature-check">&#10003;</span>'
        f'<span>{f}</span></div>'
        for f in p['bundle_features']
    )
    block = re.sub(r'<div class="gh-bundle__features">.*?</div>\s*</div>',
                   f'<div class="gh-bundle__features">\n{features_html}\n    </div>',
                   block, count=1, flags=re.DOTALL)
    block = block.replace('<a href="#bundle" class="gh-bundle__cta">Build Your Bundle Below &darr;</a>',
                          f'<a href="#bundle" class="gh-bundle__cta">{p["bundle_cta"]}</a>')
    block = block.replace('<p class="gh-bundle__note">Our most popular order. 2,000+ orders and counting.</p>',
                          f'<p class="gh-bundle__note">{p["bundle_note"]}</p>')
    # gh-bb
    block = block.replace('<div class="gh-bb__badge">BEST VALUE DEAL</div>',
                          f'<div class="gh-bb__badge">{p["badge"]}</div>')
    block = block.replace('<h2 class="gh-bb__title">Build Your Mix and Match Bundle</h2>',
                          f'<h2 class="gh-bb__title">{p["title"]}</h2>')
    block = block.replace('<p class="gh-bb__sub">Pick any 5 strains below. The cheapest oz is free.</p>',
                          f'<p class="gh-bb__sub">{p["sub"]}</p>')
    trust_html = '\n'.join(f'        <div class="gh-bb__trust-item">{t}</div>' for t in p['trust'])
    block = re.sub(
        r'(<div class="gh-bb__trust">).*?(</div>\s*</div>\s*</div>)',
        lambda m: m.group(1) + '\n' + trust_html + '\n      ' + m.group(2),
        block, count=1, flags=re.DOTALL)
    block = block.replace(
        'Cheapest oz is free &middot; Free shipping over $90 &middot; Secure checkout',
        p['fine'])
    return block


def replace_section(html, old_start_str, old_end_str, new_content):
    """Replace everything from old_start_str to old_end_str (inclusive) with new_content."""
    s = html.find(old_start_str)
    if s < 0:
        return html, False
    e = html.find(old_end_str, s)
    if e < 0:
        return html, False
    e += len(old_end_str)
    return html[:s] + new_content + html[e:], True


def apply_persona(path, persona_key, p):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # ── 1. Replace top banner ─────────────────────────────────────────────────
    html, ok = replace_section(html,
                                '  <div class="gh-banner"',
                                '\n  </div>',
                                RB_BANNER)
    steps.append(f'Banner {"replaced" if ok else "NOT FOUND"}')

    # ── 2. Replace stats ribbon ───────────────────────────────────────────────
    html, ok = replace_section(html,
                                '  <section class="gh-stats-ribbon">',
                                '  </section>',
                                RB_RIBBON)
    steps.append(f'Ribbon {"replaced" if ok else "NOT FOUND"}')

    # ── 3. Replace/inject bundle block (gh-bundle + gh-bb) ───────────────────
    bundle_block = make_bundle_block(p)
    # Remove any existing bundle block first
    for marker in ['<!-- ======== BUNDLE BUY BOX', 'SECTION: Bundle Buy Box v3']:
        if marker in html:
            s = html.find('<!-- ======== BUNDLE BUY BOX')
            e = html.find('<section class="gh-catalog"')
            if s > 0 and e > s:
                html = html[:s] + html[e:]
                steps.append('Old bundle block removed')
            break
    # Inject fresh block before gh-catalog
    catalog_pos = html.find('<section class="gh-catalog"')
    if catalog_pos > 0:
        html = html[:catalog_pos] + bundle_block + html[catalog_pos:]
        steps.append('Bundle block injected')
    else:
        steps.append('ERROR: gh-catalog anchor not found')

    # ── 4. Ensure gh-bb CSS present ───────────────────────────────────────────
    if '/* ===== Bundle Buy Box v3 (gh-bb) ===== */' not in html:
        anchor = '/* ===== Catalog Section Header ===== */'
        if anchor in html:
            html = html.replace(anchor, GH_BB_CSS + '\n\n' + anchor, 1)
        else:
            style_end = html.rfind('</style>')
            html = html[:style_end] + GH_BB_CSS + '\n' + html[style_end:]
        steps.append('gh-bb CSS injected')
    else:
        steps.append('gh-bb CSS already present')

    # ── 5. Ensure Bundle Picker v3 JS present ────────────────────────────────
    click_anchor = '  // === Click delegation ==='
    if '// === Bundle Picker v3 ===' not in html and click_anchor in html:
        html = html.replace(click_anchor, BUNDLE_PICKER_JS + '\n\n' + click_anchor, 1)
        steps.append('Bundle Picker JS injected')
    else:
        steps.append('Bundle Picker JS already present')

    # ── 6. Update catalog heading + sub ──────────────────────────────────────
    m = re.search(r'<h2 class="gh-catalog__heading">[^<]+</h2>', html)
    if m:
        html = html[:m.start()] + f'<h2 class="gh-catalog__heading">{p["catalog_heading"]}</h2>' + html[m.end():]
        steps.append('Catalog heading updated')

    m = re.search(r'<p class="gh-catalog__sub">[^<]+</p>', html)
    if m:
        html = html[:m.start()] + f'<p class="gh-catalog__sub">{p["catalog_sub"]}</p>' + html[m.end():]
        steps.append('Catalog sub updated')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path} ({persona_key}):')
    for s in steps:
        ok = 'ERROR' not in s and 'NOT FOUND' not in s
        print(f'  {"✓" if ok else "✗"} {s}')
    print(f'  File size: {len(html)//1024}kb')


if __name__ == '__main__':
    print('=== Copying rb sections into bb and bc ===')
    for key, p in PERSONAS.items():
        if os.path.exists(p['path']):
            apply_persona(p['path'], key, p)
        else:
            print(f'\nSKIP (not found): {p["path"]}')
    print('\nDone.')
