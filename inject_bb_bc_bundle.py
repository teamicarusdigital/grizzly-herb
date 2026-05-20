"""
inject_bb_bc_bundle.py
======================
Adds the full gh-bb bundle buy box section to bb and bc pages
with persona-specific headings. Also updates the green promo
section and catalog headings for each persona.

bb = Bulk Buyers
bc = The Burned Connoisseur
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

# ── Extract source data from rb ───────────────────────────────────────────────
with open('pages/premium-collection-rb/index.html', encoding='utf-8') as f:
    rb = f.read()

# 1. gh-bb CSS block
s_css = rb.find('/* ===== Bundle Buy Box v3 (gh-bb) ===== */')
e_css = rb.find('</style>', s_css)
GH_BB_CSS = rb[s_css:e_css]

# 2. gh-bb HTML section (comment + section tag through closing section tag)
s_html = rb.find('<!-- ============================================================\n     SECTION: Bundle Buy Box v3')
e_html = rb.find('\n<!-- ============================================================\n     SECTION:', s_html + 50)
GH_BB_HTML_RB = rb[s_html:e_html]

# 3. Bundle Picker v3 JS
s_js = rb.find('  // === Bundle Picker v3 ===')
e_js = rb.find('  // === Click delegation ===')
BUNDLE_PICKER_JS = rb[s_js:e_js]


# ── Persona config ────────────────────────────────────────────────────────────
PERSONAS = {
    'bb': {
        'path': 'pages/premium-collection-bb/index.html',
        # gh-bb info section
        'badge':   'BULK SAVER DEAL',
        'title':   'Stock Up With a 5-Oz Bundle',
        'sub':     'Pick any 5 strains. Best per-oz price when you buy in volume.',
        'trust': [
            'Best price per oz in Canada',
            'QP and full pound on every strain',
            'Free shipping on orders over $90',
            'Same strains available every reorder',
        ],
        # green promo (gh-bundle) section
        'bundle_heading': 'Stock Up and <strong>Save Big</strong>',
        'bundle_sub':     'Mix any 5 strains. More volume, better value. The way bulk buyers order.',
        # catalog section
        'catalog_label':   'BULK PRICING AVAILABLE',
        'catalog_heading': 'Bulk and Individual Strain Options',
        'catalog_sub':     'Oz, QP, and full pound options. Stack up and save the more you buy.',
    },
    'bc': {
        'path': 'pages/premium-collection-bc/index.html',
        # gh-bb info section
        'badge':   'TOP SHELF SELECTION',
        'title':   'Curate Your Connoisseur Bundle',
        'sub':     "Pick 5 premium strains. You've been burned before. This is the fix.",
        'trust': [
            'Hand-selected AAAA+ flower only',
            'Lab-tested, batch-consistent quality',
            'No mystery bags, no nasty surprises',
            '60-day freshness guarantee',
        ],
        # green promo (gh-bundle) section
        'bundle_heading': 'Premium Flower for <strong>Discerning Buyers</strong>',
        'bundle_sub':     'Handpick 5 top-shelf strains. No guessing, no disappointment.',
        # catalog section
        'catalog_label':   'AAAA+ ONLY',
        'catalog_heading': 'The Premium Selection',
        'catalog_sub':     'AAAA+ strains for the serious buyer. Oz, QP, and full pound.',
    },
}


def make_bb_html(p):
    """Build the gh-bb info section with persona-specific content."""
    trust_html = '\n'.join(
        f'        <div class="gh-bb__trust-item">{t}</div>' for t in p['trust']
    )
    # Replace just the info panel text in the rb HTML
    html = GH_BB_HTML_RB
    html = html.replace(
        '<div class="gh-bb__badge">BEST VALUE DEAL</div>',
        f'<div class="gh-bb__badge">{p["badge"]}</div>'
    )
    html = html.replace(
        '<h2 class="gh-bb__title">Build Your Mix and Match Bundle</h2>',
        f'<h2 class="gh-bb__title">{p["title"]}</h2>'
    )
    html = html.replace(
        '<p class="gh-bb__sub">Pick any 5 strains below. The cheapest oz is free.</p>',
        f'<p class="gh-bb__sub">{p["sub"]}</p>'
    )
    # Replace trust items
    html = re.sub(
        r'(<div class="gh-bb__trust">).*?(</div>\s*</div>\s*</div>)',
        lambda m: m.group(1) + '\n' + trust_html + '\n      ' + m.group(2),
        html, count=1, flags=re.DOTALL
    )
    return html


def apply_persona(path, persona_key, p):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # ── 1. Inject gh-bb CSS before closing </style> ──────────────────────────
    if '/* ===== Bundle Buy Box v3 (gh-bb) ===== */' not in html:
        # Insert before the catalog section CSS comment or </style>
        anchor = '/* ===== Catalog Section Header ===== */'
        if anchor in html:
            html = html.replace(anchor, GH_BB_CSS + '\n\n' + anchor, 1)
        else:
            style_end = html.rfind('</style>')
            html = html[:style_end] + GH_BB_CSS + '\n' + html[style_end:]
        steps.append('gh-bb CSS injected')
    else:
        steps.append('gh-bb CSS already present')

    # ── 2. Inject gh-bb HTML before the gh-bundle green promo section ────────
    if 'SECTION: Bundle Buy Box v3' not in html:
        anchor = html.find('<section class="gh-bundle">')
        if anchor < 0:
            # bb/bc may not have gh-bundle; fall back to gh-catalog
            anchor = html.find('<section class="gh-catalog"')
        if anchor > 0:
            bb_html = make_bb_html(p)
            html = html[:anchor] + bb_html + '\n\n' + html[anchor:]
            steps.append('gh-bb HTML injected')
        else:
            steps.append('gh-bb HTML: anchor not found')
    else:
        steps.append('gh-bb HTML already present')

    # ── 3. Inject Bundle Picker v3 JS before click delegation ────────────────
    click_anchor = '  // === Click delegation ==='
    if '// === Bundle Picker v3 ===' not in html and click_anchor in html:
        html = html.replace(click_anchor, BUNDLE_PICKER_JS + '\n\n' + click_anchor, 1)
        steps.append('Bundle Picker v3 JS injected')
    elif '// === Bundle Picker v3 ===' in html:
        steps.append('Bundle Picker v3 JS already present')
    else:
        steps.append('Bundle Picker v3 JS: click anchor not found')

    # ── 4. Update green promo (gh-bundle) headings ───────────────────────────
    old_bundle_h2 = re.search(r'<h2 class="gh-bundle__heading">[^<]*(?:<[^<]*>[^<]*</[^>]*>)*[^<]*</h2>', html)
    if old_bundle_h2:
        html = html[:old_bundle_h2.start()] + \
               f'<h2 class="gh-bundle__heading">{p["bundle_heading"]}</h2>' + \
               html[old_bundle_h2.end():]
        steps.append('Green promo heading updated')

    old_bundle_sub = re.search(r'<p class="gh-bundle__sub">[^<]+</p>', html)
    if old_bundle_sub:
        html = html[:old_bundle_sub.start()] + \
               f'<p class="gh-bundle__sub">{p["bundle_sub"]}</p>' + \
               html[old_bundle_sub.end():]
        steps.append('Green promo sub updated')

    # ── 5. Update catalog section headings ───────────────────────────────────
    # Label
    old_label = '<div class="gh-catalog__label">SHOP ALL STRAINS</div>'
    new_label = f'<div class="gh-catalog__label">{p["catalog_label"]}</div>'
    if old_label in html:
        html = html.replace(old_label, new_label, 1)
        steps.append('Catalog label updated')
    elif p['catalog_label'] in html:
        steps.append('Catalog label already set')
    else:
        # Try any existing label
        old_lbl_m = re.search(r'<div class="gh-catalog__label">[^<]+</div>', html)
        if old_lbl_m:
            html = html[:old_lbl_m.start()] + new_label + html[old_lbl_m.end():]
            steps.append('Catalog label updated (generic)')

    # Heading
    old_heading = '<h2 class="gh-catalog__heading">Shop Individual Strains</h2>'
    new_heading = f'<h2 class="gh-catalog__heading">{p["catalog_heading"]}</h2>'
    if old_heading in html:
        html = html.replace(old_heading, new_heading, 1)
        steps.append('Catalog heading updated')
    elif p['catalog_heading'] in html:
        steps.append('Catalog heading already set')

    # Sub
    old_sub_bb = '<p class="gh-catalog__sub">Oz, QP, and full pound options. Add to your bundle or order solo.</p>'
    old_sub_rb = '<p class="gh-catalog__sub">Oz, QP, and full pound options. Order individually or build your bundle above.</p>'
    new_sub = f'<p class="gh-catalog__sub">{p["catalog_sub"]}</p>'
    if old_sub_bb in html:
        html = html.replace(old_sub_bb, new_sub, 1)
        steps.append('Catalog sub updated')
    elif old_sub_rb in html:
        html = html.replace(old_sub_rb, new_sub, 1)
        steps.append('Catalog sub updated')
    elif p['catalog_sub'] in html:
        steps.append('Catalog sub already set')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path} ({persona_key}):')
    for s in steps:
        print(f'  {"✓" if "not found" not in s and "anchor" not in s else "~"} {s}')
    print(f'  File size: {len(html)//1024}kb')


if __name__ == '__main__':
    print('=== Injecting bundle section into bb and bc ===')
    for key, p in PERSONAS.items():
        if os.path.exists(p['path']):
            apply_persona(p['path'], key, p)
        else:
            print(f'\nSKIP (not found): {p["path"]}')
    print('\nDone.')
