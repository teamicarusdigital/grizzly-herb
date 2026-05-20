"""
inject_bb_bc_bundle.py
======================
Adds the full bundle section (gh-bundle green promo + gh-bb buy box)
to bb and bc pages with persona-specific headings and copy.

bb = Bulk Buyers
bc = The Burned Connoisseur
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

# ── Extract source data from rb ───────────────────────────────────────────────
with open('pages/premium-collection-rb/index.html', encoding='utf-8') as f:
    rb = f.read()

# 1. gh-bb CSS block (everything from the comment to </style>)
s_css = rb.find('/* ===== Bundle Buy Box v3 (gh-bb) ===== */')
e_css = rb.find('</style>', s_css)
GH_BB_CSS = rb[s_css:e_css]

# 2. Full bundle block: <!-- ======== BUNDLE BUY BOX ======== --> through
#    the closing </section> of gh-bb (stops right before gh-catalog)
s_block = rb.find('<!-- ======== BUNDLE BUY BOX ======== -->')
e_block = rb.find('<section class="gh-catalog"')
GH_BUNDLE_BLOCK = rb[s_block:e_block]

# 3. Bundle Picker v3 JS
s_js = rb.find('  // === Bundle Picker v3 ===')
e_js = rb.find('  // === Click delegation ===')
BUNDLE_PICKER_JS = rb[s_js:e_js]


# ── Persona config ────────────────────────────────────────────────────────────
PERSONAS = {
    'bb': {
        'path': 'pages/premium-collection-bb/index.html',
        # gh-bundle (green promo) section
        'bundle_badge':    'BULK BUYER DEAL',
        'bundle_heading':  'Stock Up and <strong>Save Big</strong>',
        'bundle_sub':      'Mix any 5 strains. More volume, better value. The way bulk buyers order.',
        'bundle_features': [
            'Best price per oz in Canada',
            'QP and full pound on every strain',
            'Free shipping on orders over $90',
            'Same strains available every reorder',
        ],
        'bundle_cta':   'Stock Up Now &darr;',
        'bundle_note':  'Best per-oz price in Canada. 2,000+ orders and counting.',
        # gh-bb (bundle buy box) section
        'badge':  'BULK SAVER DEAL',
        'title':  'Stock Up With a 5-Oz Bundle',
        'sub':    'Pick any 5 strains. Best per-oz price when you buy in volume.',
        'trust': [
            'Best price per oz in Canada',
            'QP and full pound on every strain',
            'Free shipping on orders over $90',
            'Same strains available every reorder',
        ],
        'fine': 'Best per-oz price &middot; Free shipping over $90 &middot; Secure checkout',
        # catalog section
        'catalog_label':   'BULK PRICING AVAILABLE',
        'catalog_heading': 'Bulk and Individual Strain Options',
        'catalog_sub':     'Oz, QP, and full pound options. Stack up and save the more you buy.',
    },
    'bc': {
        'path': 'pages/premium-collection-bc/index.html',
        # gh-bundle (green promo) section
        'bundle_badge':    'TOP SHELF ONLY',
        'bundle_heading':  'Premium Flower for <strong>Discerning Buyers</strong>',
        'bundle_sub':      'Handpick 5 top-shelf strains. No guessing, no disappointment.',
        'bundle_features': [
            'Hand-selected AAAA+ flower only',
            'Lab-tested, batch-consistent quality',
            'No mystery bags, no nasty surprises',
            '60-day freshness guarantee',
        ],
        'bundle_cta':   'Curate Your Bundle &darr;',
        'bundle_note':  'Hand-selected AAAA+ only. Batch-tested, freshness guaranteed.',
        # gh-bb (bundle buy box) section
        'badge':  'TOP SHELF SELECTION',
        'title':  'Curate Your Connoisseur Bundle',
        'sub':    "Pick 5 premium strains. You've been burned before. This is the fix.",
        'trust': [
            'Hand-selected AAAA+ flower only',
            'Lab-tested, batch-consistent quality',
            'No mystery bags, no nasty surprises',
            '60-day freshness guarantee',
        ],
        'fine': 'AAAA+ premium flower &middot; Free shipping over $90 &middot; Secure checkout',
        # catalog section
        'catalog_label':   'AAAA+ ONLY',
        'catalog_heading': 'The Premium Selection',
        'catalog_sub':     'AAAA+ strains for the serious buyer. Oz, QP, and full pound.',
    },
}


def make_bundle_block(p):
    """Build the full bundle block with persona-specific content."""
    block = GH_BUNDLE_BLOCK

    # ── gh-bundle (green promo) replacements ────────────────────────────────
    block = block.replace(
        '<div class="gh-bundle__badge">Most Popular Deal</div>',
        f'<div class="gh-bundle__badge">{p["bundle_badge"]}</div>'
    )
    block = block.replace(
        '<h2 class="gh-bundle__heading">Buy 4oz, <strong>Get 1oz Free</strong></h2>',
        f'<h2 class="gh-bundle__heading">{p["bundle_heading"]}</h2>'
    )
    block = block.replace(
        '<p class="gh-bundle__sub">Mix and match any AAAA strains. The way most of our regulars order.</p>',
        f'<p class="gh-bundle__sub">{p["bundle_sub"]}</p>'
    )
    features_html = '\n'.join(
        f'      <div class="gh-bundle__feature"><span class="gh-bundle__feature-check">&#10003;</span>'
        f'<span>{f}</span></div>'
        for f in p['bundle_features']
    )
    block = re.sub(
        r'<div class="gh-bundle__features">.*?</div>\s*</div>',
        f'<div class="gh-bundle__features">\n{features_html}\n    </div>',
        block, count=1, flags=re.DOTALL
    )
    block = block.replace(
        '<a href="#bundle" class="gh-bundle__cta">Build Your Bundle Below &darr;</a>',
        f'<a href="#bundle" class="gh-bundle__cta">{p["bundle_cta"]}</a>'
    )
    block = block.replace(
        '<p class="gh-bundle__note">Our most popular order. 2,000+ orders and counting.</p>',
        f'<p class="gh-bundle__note">{p["bundle_note"]}</p>'
    )

    # ── gh-bb (buy box) replacements ─────────────────────────────────────────
    block = block.replace(
        '<div class="gh-bb__badge">BEST VALUE DEAL</div>',
        f'<div class="gh-bb__badge">{p["badge"]}</div>'
    )
    block = block.replace(
        '<h2 class="gh-bb__title">Build Your Mix and Match Bundle</h2>',
        f'<h2 class="gh-bb__title">{p["title"]}</h2>'
    )
    block = block.replace(
        '<p class="gh-bb__sub">Pick any 5 strains below. The cheapest oz is free.</p>',
        f'<p class="gh-bb__sub">{p["sub"]}</p>'
    )
    rb_trust_inner = (
        '        <div class="gh-bb__trust-item">2,000+ verified Canadian orders</div>\n'
        '        <div class="gh-bb__trust-item">Free shipping on orders over $90</div>\n'
        '        <div class="gh-bb__trust-item">Same quality flower, every order</div>\n'
        '        <div class="gh-bb__trust-item">60-day freshness guarantee</div>'
    )
    new_trust_inner = '\n'.join(
        f'        <div class="gh-bb__trust-item">{t}</div>' for t in p['trust']
    )
    block = block.replace(rb_trust_inner, new_trust_inner, 1)
    block = block.replace(
        'Cheapest oz is free &middot; Free shipping over $90 &middot; Secure checkout',
        p['fine']
    )

    return block


def apply_persona(path, persona_key, p):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # ── 1. Inject gh-bb CSS ──────────────────────────────────────────────────
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

    # ── 2. Inject bundle block (gh-bundle + gh-bb) before gh-catalog ────────
    if 'SECTION: Bundle Buy Box v3' not in html:
        catalog_pos = html.find('<section class="gh-catalog"')
        if catalog_pos > 0:
            bundle_block = make_bundle_block(p)
            html = html[:catalog_pos] + bundle_block + html[catalog_pos:]
            steps.append('Bundle block (gh-bundle + gh-bb) injected')
        else:
            steps.append('ERROR: gh-catalog anchor not found')
    else:
        steps.append('Bundle block already present')

    # ── 3. Inject Bundle Picker v3 JS ────────────────────────────────────────
    click_anchor = '  // === Click delegation ==='
    if '// === Bundle Picker v3 ===' not in html and click_anchor in html:
        html = html.replace(click_anchor, BUNDLE_PICKER_JS + '\n\n' + click_anchor, 1)
        steps.append('Bundle Picker v3 JS injected')
    elif '// === Bundle Picker v3 ===' in html:
        steps.append('Bundle Picker v3 JS already present')
    else:
        steps.append('ERROR: click delegation anchor not found')

    # ── 4. Update catalog label ───────────────────────────────────────────────
    old_lbl_m = re.search(r'<div class="gh-catalog__label">[^<]+</div>', html)
    new_label  = f'<div class="gh-catalog__label">{p["catalog_label"]}</div>'
    if old_lbl_m and old_lbl_m.group() != new_label:
        html = html[:old_lbl_m.start()] + new_label + html[old_lbl_m.end():]
        steps.append('Catalog label updated')
    elif old_lbl_m:
        steps.append('Catalog label already set')

    # ── 5. Update catalog heading ─────────────────────────────────────────────
    old_h2_m = re.search(r'<h2 class="gh-catalog__heading">[^<]+</h2>', html)
    new_h2   = f'<h2 class="gh-catalog__heading">{p["catalog_heading"]}</h2>'
    if old_h2_m and old_h2_m.group() != new_h2:
        html = html[:old_h2_m.start()] + new_h2 + html[old_h2_m.end():]
        steps.append('Catalog heading updated')
    elif old_h2_m:
        steps.append('Catalog heading already set')

    # ── 6. Update catalog sub ─────────────────────────────────────────────────
    old_sub_m = re.search(r'<p class="gh-catalog__sub">[^<]+</p>', html)
    new_sub   = f'<p class="gh-catalog__sub">{p["catalog_sub"]}</p>'
    if old_sub_m and old_sub_m.group() != new_sub:
        html = html[:old_sub_m.start()] + new_sub + html[old_sub_m.end():]
        steps.append('Catalog sub updated')
    elif old_sub_m:
        steps.append('Catalog sub already set')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path} ({persona_key}):')
    for s in steps:
        ok = 'ERROR' not in s
        print(f'  {"✓" if ok else "✗"} {s}')
    print(f'  File size: {len(html)//1024}kb')


if __name__ == '__main__':
    print('=== Injecting bundle section into bb and bc ===')
    for key, p in PERSONAS.items():
        if os.path.exists(p['path']):
            apply_persona(p['path'], key, p)
        else:
            print(f'\nSKIP (not found): {p["path"]}')
    print('\nDone.')
