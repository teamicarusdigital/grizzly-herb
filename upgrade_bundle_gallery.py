"""
upgrade_bundle_gallery.py
=========================
Redesigns the bundle section left column (gh-bb__gallery):
 1. Adds strain name labels overlaid on each collage photo
 2. Adds a dark-green value/savings card between collage and trust items
 3. Replaces plain-checkmark trust items with inline SVG icons
 4. Updates loadBundleGrid() JS to refresh name labels when images swap
 5. Injects CSS for all new elements
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

# ── New gallery HTML template (image src/alt filled in per page) ──────────────
def build_gallery(imgs):
    """
    imgs: list of (src, alt) tuples for up to 4 collage images.
    """
    def img_div(src, alt):
        return (
            f'        <div class="gh-bb__collage-img">\n'
            f'          <img src="{src}" alt="{alt}" loading="lazy">\n'
            f'          <span class="gh-bb__collage-name">{alt}</span>\n'
            f'        </div>'
        )
    all_imgs = list(imgs) + [('/images/Flower%206.png', '')]
    collage_items = '\n'.join(img_div(s, a) for s, a in all_imgs)

    return f"""    <div class="gh-bb__gallery">
      <div class="gh-bb__collage">
{collage_items}
      </div>
      <div class="gh-bb__value-card">
        <div class="gh-bb__value-meta">Bundle Price</div>
        <div class="gh-bb__value-pricing">
          <span class="gh-bb__value-was">$525</span>
          <span class="gh-bb__value-now">$340</span>
        </div>
        <div class="gh-bb__value-save">You save $185 &middot; 5th oz ships free</div>
      </div>
      <div class="gh-bb__trust">
        <div class="gh-bb__trust-item">
          <svg class="gh-bb__trust-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2L3 5v5.5c0 3.87 2.95 7.47 7 8 4.05-.53 7-4.13 7-8V5l-7-3z" fill="#4a7c2c" fill-opacity="0.15" stroke="#4a7c2c" stroke-width="1.5" stroke-linejoin="round"/><path d="M7 10.5l2 2 4-4" stroke="#4a7c2c" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          <span>2,000+ verified Canadian orders</span>
        </div>
        <div class="gh-bb__trust-item">
          <svg class="gh-bb__trust-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="7" width="11" height="8" rx="1.5" stroke="#4a7c2c" stroke-width="1.5"/><path d="M12 10h3.5L18 13v2h-6v-5z" stroke="#4a7c2c" stroke-width="1.5" stroke-linejoin="round"/><circle cx="5" cy="16.5" r="1.5" fill="#4a7c2c"/><circle cx="15" cy="16.5" r="1.5" fill="#4a7c2c"/></svg>
          <span>Free shipping on orders over $90</span>
        </div>
        <div class="gh-bb__trust-item">
          <svg class="gh-bb__trust-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 2l2.06 4.18L17 7.27l-3.5 3.41.83 4.82L10 13.27l-4.33 2.23.83-4.82L3 7.27l4.94-.09L10 2z" fill="#4a7c2c" fill-opacity="0.15" stroke="#4a7c2c" stroke-width="1.5" stroke-linejoin="round"/></svg>
          <span>Same AAAA+ quality, every order</span>
        </div>
        <div class="gh-bb__trust-item">
          <svg class="gh-bb__trust-icon" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="4" width="16" height="13" rx="2" stroke="#4a7c2c" stroke-width="1.5"/><path d="M2 8h16" stroke="#4a7c2c" stroke-width="1.5"/><path d="M6 2v3M14 2v3" stroke="#4a7c2c" stroke-width="1.5" stroke-linecap="round"/><path d="M6 12h4" stroke="#4a7c2c" stroke-width="1.5" stroke-linecap="round"/></svg>
          <span>60-day freshness guarantee</span>
        </div>
      </div>
    </div>"""


# ── CSS for new gallery elements ──────────────────────────────────────────────
GALLERY_CSS = """
    /* ===== Bundle gallery upgrade ===== */
    .gh-bb__collage-img { position: relative; }
    .gh-bb__collage-img:last-child { grid-column: 1 / -1; aspect-ratio: 2 / 1; }
    .gh-bb__collage-img::after {
      content: '';
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 55%;
      background: linear-gradient(transparent, rgba(0,0,0,0.68));
      pointer-events: none;
    }
    .gh-bb__collage-name {
      position: absolute;
      bottom: 7px; left: 0; right: 0;
      text-align: center;
      color: #fff;
      font-size: 9px;
      font-weight: 700;
      z-index: 1;
      pointer-events: none;
      letter-spacing: 0.03em;
      text-shadow: 0 1px 3px rgba(0,0,0,0.5);
      padding: 0 4px;
      line-height: 1.2;
    }
    .gh-bb__value-card {
      background: linear-gradient(135deg, #2d5016 0%, #4a7c2c 100%);
      border-radius: 12px;
      padding: 14px 18px;
      margin-bottom: 14px;
    }
    .gh-bb__value-meta {
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.65);
      margin-bottom: 4px;
    }
    .gh-bb__value-pricing {
      display: flex;
      align-items: baseline;
      gap: 10px;
      margin-bottom: 4px;
    }
    .gh-bb__value-was {
      font-size: 14px;
      font-weight: 400;
      color: rgba(255,255,255,0.45);
      text-decoration: line-through;
    }
    .gh-bb__value-now {
      font-size: 30px;
      font-weight: 800;
      color: #fff;
      line-height: 1;
    }
    .gh-bb__value-save {
      font-size: 11px;
      font-weight: 500;
      color: rgba(255,255,255,0.82);
    }
    .gh-bb__trust-item::before { display: none; }
    .gh-bb__trust-icon {
      width: 18px;
      height: 18px;
      flex-shrink: 0;
    }
"""

# ── JS: update collage name labels when bundle products load ──────────────────
OLD_COLLAGE_JS = (
    "            if (collageImgs[i]) { collageImgs[i].src = p.image; collageImgs[i].alt = p.name; }"
)
NEW_COLLAGE_JS = (
    "            if (collageImgs[i]) { collageImgs[i].src = p.image; collageImgs[i].alt = p.name;\n"
    "              var nameEl = collageImgs[i].parentNode.querySelector('.gh-bb__collage-name');\n"
    "              if (nameEl) nameEl.textContent = p.name; }"
)


def extract_collage_imgs(html):
    """Extract current (src, alt) from gh-bb__collage-img divs."""
    imgs = []
    for m in re.finditer(
        r'<div class="gh-bb__collage-img">.*?<img src="([^"]+)" alt="([^"]*)"',
        html, re.DOTALL
    ):
        imgs.append((m.group(1), m.group(2)))
    return imgs[:4]


def apply(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # 1. Replace gallery block
    if '<div class="gh-bb__value-card">' not in html:
        imgs = extract_collage_imgs(html)
        if not imgs:
            steps.append('ERROR: could not extract collage images')
        else:
            new_gallery = build_gallery(imgs)
            start = html.find('    <div class="gh-bb__gallery">')
            info_pos = html.find('\n    <div class="gh-bb__info">', start)
            if start != -1 and info_pos != -1:
                gallery_end = html.rfind('</div>', start, info_pos) + len('</div>')
                html = html[:start] + new_gallery + html[gallery_end:]
                steps.append(f'Gallery HTML rebuilt with {len(imgs)} images')
            else:
                steps.append('ERROR: gallery anchor not found')
    else:
        steps.append('Gallery already upgraded')

    # 2. Update loadBundleGrid JS
    if OLD_COLLAGE_JS in html:
        html = html.replace(OLD_COLLAGE_JS, NEW_COLLAGE_JS, 1)
        steps.append('loadBundleGrid: name label update added')
    elif '.gh-bb__collage-name' in html:
        steps.append('loadBundleGrid: name update already present')
    else:
        steps.append('ERROR: loadBundleGrid collage JS anchor not found')

    # 3. CSS
    if 'gh-bb__value-card {' not in html:
        pos = html.rfind('</style>')
        if pos != -1:
            html = html[:pos] + GALLERY_CSS + html[pos:]
            steps.append('Gallery CSS injected')
        else:
            steps.append('ERROR: </style> not found')
    else:
        steps.append('Gallery CSS already present')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path}:')
    for s in steps:
        print(f'  {"+" if "ERROR" not in s else "!"} {s}')


if __name__ == '__main__':
    print('=== Upgrading bundle gallery ===')
    for p in PAGES:
        if os.path.exists(p):
            apply(p)
        else:
            print(f'\nSKIP: {p}')
    print('\nDone.')
