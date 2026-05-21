"""
update_offer_copy.py
====================
Updates all offer-related copy on flower pages to centre around
"Buy 4oz, Get 1oz Free" with persona-specific framing.

Touches: hero h1 + desc, gh-bundle section, gh-bb section,
         catalog label (inserted), catalog heading.
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

# ── Persona copy ──────────────────────────────────────────────────────────────
PERSONAS = {

    'rb': {
        'path': 'pages/premium-collection-rb/index.html',

        # Hero
        'hero_h1':   'Buy 4oz, Get 1oz Free.<br><strong>Mix and Match Any AAAA Strain.</strong>',
        'hero_desc': '2,000+ verified Canadian orders. Pick any 5 strains, the cheapest oz always ships free.',

        # gh-bundle (green promo)
        'bundle_badge':    'BUY 4, GET 1 FREE',
        'bundle_heading':  'Buy 4oz, <strong>Get 1oz Free</strong>',
        'bundle_sub':      'Mix and match any AAAA strains. Pick 5, the cheapest oz ships free.',
        'bundle_features': [
            'Any 4 strains, 1oz each',
            'Free oz of your choice',
            'Free shipping over $90',
            'Sale prices already applied',
        ],
        'bundle_cta':  'Build Your Bundle Below &darr;',
        'bundle_note': 'Our most popular order. 2,000+ orders and counting.',

        # gh-bb (buy box)
        'bb_badge': '4+1 FREE BUNDLE',
        'bb_title': 'Pick Any 4 Strains, Get the 5th Free',
        'bb_sub':   'Add 5 to your bundle. The cheapest oz always ships free.',

        # Catalog
        'catalog_label':   'BUY 4, GET 1 FREE',
        'catalog_heading': 'Pick Your Strains. Add to Your Bundle.',
        'catalog_sub':     'Oz, QP, and full pound options. Order individually or build your bundle above.',
    },

    'bb': {
        'path': 'pages/premium-collection-bb/index.html',

        # Hero
        'hero_h1':   'Buy 4oz in Bulk,<br><strong>Get 1oz Free.</strong>',
        'hero_desc': 'Best per-oz price in Canada. Mix any 4 strains, the cheapest oz ships free. QP and pound options too.',

        # gh-bundle
        'bundle_badge':    'BULK 4+1 FREE',
        'bundle_heading':  'Buy 4oz, <strong>Get 1oz Free</strong>',
        'bundle_sub':      'Mix any 5 strains. The cheapest oz ships free. Best per-oz price in Canada.',
        'bundle_features': [
            'Any 4 strains, 1oz each',
            'Free oz of your choice',
            'Best bulk pricing in Canada',
            'QP and pound options on every strain',
        ],
        'bundle_cta':  'Stock Up Now &darr;',
        'bundle_note': 'Best per-oz price in Canada. 2,000+ orders and counting.',

        # gh-bb
        'bb_badge': 'BULK 4+1 FREE',
        'bb_title': 'Pick Any 4 Strains, Get the 5th Free',
        'bb_sub':   'Pick 5, the cheapest oz ships free. Best bulk pricing in Canada.',

        # Catalog
        'catalog_label':   'BUY 4, GET 1 FREE',
        'catalog_heading': 'Buy Solo, in Bulk, or Bundle 4 for a Free Oz',
        'catalog_sub':     'Oz, QP, and full pound options. Stack up and save the more you buy.',
    },

    'bc': {
        'path': 'pages/premium-collection-bc/index.html',

        # Hero
        'hero_h1':   'Pick 4 Premium Oz,<br><strong>Get the 5th Free.</strong>',
        'hero_desc': 'AAAA+ strains only. The cheapest oz in your bundle always ships free. No guessing, no disappointment.',

        # gh-bundle
        'bundle_badge':    'AAAA+ 4+1 FREE',
        'bundle_heading':  'Pick 4 Premium Oz, <strong>Get 1 Free</strong>',
        'bundle_sub':      'AAAA+ strains only. Pick any 4, the cheapest oz ships free.',
        'bundle_features': [
            'Any 4 AAAA+ strains, 1oz each',
            'Free oz of your choice',
            'Lab-tested, batch-consistent quality',
            '60-day freshness guarantee',
        ],
        'bundle_cta':  'Curate Your Bundle &darr;',
        'bundle_note': 'Hand-selected AAAA+ only. Batch-tested, freshness guaranteed.',

        # gh-bb
        'bb_badge': 'AAAA+ 4+1 BUNDLE',
        'bb_title': 'Pick 4 Top-Shelf Strains, Get the 5th Free',
        'bb_sub':   'AAAA+ flower only. The cheapest oz is always free. This is what good flower feels like.',

        # Catalog
        'catalog_label':   'BUY 4, GET 1 FREE',
        'catalog_heading': 'AAAA+ Strains. Bundle 4 and Get 1 Free.',
        'catalog_sub':     'AAAA+ strains for the serious buyer. Oz, QP, and full pound.',
    },

    'hsh': {
        'path': 'pages/premium-collection-hsh/index.html',
        # Hero (no change — hsh is a different product line)
        # gh-bundle — update sub-elements but no gh-bb on this page
        # Catalog
        'catalog_label':   'BUY 4, GET 1 FREE',
        'catalog_heading': 'Shop and Bundle 4 for a Free Oz',
        'catalog_sub':     None,  # leave unchanged
    },
}


def swap(html, old, new):
    """Replace first occurrence; return (html, changed)."""
    if old in html and old != new:
        return html.replace(old, new, 1), True
    return html, False


def apply(path, p):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # ── Hero h1 ───────────────────────────────────────────────────────────────
    if 'hero_h1' in p:
        old_h1 = re.search(r'<h1 class="gh-hero__headline">(.*?)</h1>', html, re.DOTALL)
        if old_h1 and old_h1.group(1).strip() != p['hero_h1']:
            html = html[:old_h1.start(1)] + p['hero_h1'] + html[old_h1.end(1):]
            steps.append('Hero h1 updated')

    # ── Hero desc ─────────────────────────────────────────────────────────────
    if 'hero_desc' in p:
        old_desc = re.search(r'<p class="gh-hero__desc">(.*?)</p>', html, re.DOTALL)
        if old_desc and old_desc.group(1).strip() != p['hero_desc']:
            html = html[:old_desc.start(1)] + p['hero_desc'] + html[old_desc.end(1):]
            steps.append('Hero desc updated')

    # ── gh-bundle badge ───────────────────────────────────────────────────────
    if 'bundle_badge' in p:
        old = re.search(r'<div class="gh-bundle__badge">([^<]+)</div>', html)
        if old:
            html, c = swap(html, old.group(0), f'<div class="gh-bundle__badge">{p["bundle_badge"]}</div>')
            if c: steps.append('Bundle badge updated')

    # ── gh-bundle heading ─────────────────────────────────────────────────────
    if 'bundle_heading' in p:
        old = re.search(r'<h2 class="gh-bundle__heading">.*?</h2>', html, re.DOTALL)
        if old:
            new_h2 = f'<h2 class="gh-bundle__heading">{p["bundle_heading"]}</h2>'
            if old.group(0) != new_h2:
                html = html[:old.start()] + new_h2 + html[old.end():]
                steps.append('Bundle heading updated')

    # ── gh-bundle sub ─────────────────────────────────────────────────────────
    if 'bundle_sub' in p:
        old = re.search(r'<p class="gh-bundle__sub">(.*?)</p>', html, re.DOTALL)
        if old:
            html, c = swap(html, old.group(0), f'<p class="gh-bundle__sub">{p["bundle_sub"]}</p>')
            if c: steps.append('Bundle sub updated')

    # ── gh-bundle features ────────────────────────────────────────────────────
    if 'bundle_features' in p:
        feat_block = re.search(r'<div class="gh-bundle__features">.*?</div>\s*</div>', html, re.DOTALL)
        if feat_block:
            feat_html = '\n'.join(
                f'      <div class="gh-bundle__feature">'
                f'<span class="gh-bundle__feature-check">&#10003;</span>'
                f'<span>{f}</span></div>'
                for f in p['bundle_features']
            )
            new_block = f'<div class="gh-bundle__features">\n{feat_html}\n    </div>'
            if feat_block.group(0) != new_block:
                html = html[:feat_block.start()] + new_block + html[feat_block.end():]
                steps.append('Bundle features updated')

    # ── gh-bundle CTA ─────────────────────────────────────────────────────────
    if 'bundle_cta' in p:
        old = re.search(r'<a href="#bundle" class="gh-bundle__cta">.*?</a>', html)
        if old:
            html, c = swap(html, old.group(0),
                           f'<a href="#bundle" class="gh-bundle__cta">{p["bundle_cta"]}</a>')
            if c: steps.append('Bundle CTA updated')

    # ── gh-bundle note ────────────────────────────────────────────────────────
    if 'bundle_note' in p:
        old = re.search(r'<p class="gh-bundle__note">.*?</p>', html)
        if old:
            html, c = swap(html, old.group(0),
                           f'<p class="gh-bundle__note">{p["bundle_note"]}</p>')
            if c: steps.append('Bundle note updated')

    # ── gh-bb badge ───────────────────────────────────────────────────────────
    if 'bb_badge' in p:
        old = re.search(r'<div class="gh-bb__badge">([^<]+)</div>', html)
        if old:
            html, c = swap(html, old.group(0), f'<div class="gh-bb__badge">{p["bb_badge"]}</div>')
            if c: steps.append('BB badge updated')

    # ── gh-bb title ───────────────────────────────────────────────────────────
    if 'bb_title' in p:
        old = re.search(r'<h2 class="gh-bb__title">([^<]+)</h2>', html)
        if old:
            html, c = swap(html, old.group(0), f'<h2 class="gh-bb__title">{p["bb_title"]}</h2>')
            if c: steps.append('BB title updated')

    # ── gh-bb sub ─────────────────────────────────────────────────────────────
    if 'bb_sub' in p:
        old = re.search(r'<p class="gh-bb__sub">([^<]+)</p>', html)
        if old:
            html, c = swap(html, old.group(0), f'<p class="gh-bb__sub">{p["bb_sub"]}</p>')
            if c: steps.append('BB sub updated')

    # ── Catalog label (insert if missing, update if present) ─────────────────
    if 'catalog_label' in p:
        lbl_el = f'<div class="gh-catalog__label">{p["catalog_label"]}</div>'
        existing = re.search(r'<div class="gh-catalog__label">[^<]+</div>', html)
        if existing:
            if existing.group(0) != lbl_el:
                html = html.replace(existing.group(0), lbl_el, 1)
                steps.append('Catalog label updated')
        else:
            # Insert before catalog heading
            anchor = re.search(r'(\s*<h2 class="gh-catalog__heading">)', html)
            if anchor:
                html = html[:anchor.start()] + '\n      ' + lbl_el + html[anchor.start():]
                steps.append('Catalog label inserted')

    # ── Catalog heading ───────────────────────────────────────────────────────
    if 'catalog_heading' in p:
        old = re.search(r'<h2 class="gh-catalog__heading">([^<]+)</h2>', html)
        if old:
            html, c = swap(html, old.group(0),
                           f'<h2 class="gh-catalog__heading">{p["catalog_heading"]}</h2>')
            if c: steps.append('Catalog heading updated')

    # ── Catalog sub ───────────────────────────────────────────────────────────
    if p.get('catalog_sub'):
        old = re.search(r'<p class="gh-catalog__sub">([^<]+)</p>', html)
        if old:
            html, c = swap(html, old.group(0),
                           f'<p class="gh-catalog__sub">{p["catalog_sub"]}</p>')
            if c: steps.append('Catalog sub updated')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path}:')
    for s in steps:
        print(f'  + {s}')
    if not steps:
        print('  (no changes)')


if __name__ == '__main__':
    print('=== Updating offer copy on flower pages ===')
    for key, p in PERSONAS.items():
        path = p.pop('path')
        if os.path.exists(path):
            apply(path, p)
        else:
            print(f'\nSKIP: {path}')
    print('\nDone.')
