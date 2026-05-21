"""
patch_bundle_dynamic.py
=======================
Replaces the hardcoded gh-bb__grid with a dynamic loader that fetches
bundle-products.json at page load.

Changes per page:
 1. Replace hardcoded <div class="gh-bb__grid">...</div> with loading placeholder
 2. Insert loadBundleGrid() + helpers inside Bundle Picker v3 IIFE (before })();)
 3. Add .gh-bb__loading and .gh-bb__strain--oos CSS
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

# ── 1. Grid placeholder ────────────────────────────────────────────────────────
GRID_START   = '      <div class="gh-bb__grid">'
GRID_END_ANC = '\n      <div class="gh-bb__summary'
NEW_GRID     = '      <div class="gh-bb__grid" id="gh-bb-grid">\n        <div class="gh-bb__loading">Loading strains...</div>\n      </div>'

# ── 2. loadBundleGrid() function + call (inserted inside IIFE) ─────────────────
LOAD_BUNDLE_JS = """
    // ── Dynamic bundle grid loader ─────────────────────────────────────────
    function makeStars(rating, reviews) {
      if (!reviews) return '';
      var filled = Math.round(rating || 0);
      var svgs = '';
      for (var s = 0; s < 5; s++) {
        svgs += '<svg width="10" height="10" viewBox="0 0 20 20"><polygon points="10,1 12.9,7 19.5,7.6 14.5,12 16.2,18.5 10,15 3.8,18.5 5.5,12 0.5,7.6 7.1,7" fill="' + (s < filled ? '#f8b300' : '#d1d5db') + '"/></svg>';
      }
      return '<div class="gh-bb__strain-social">' + svgs + '<span class="gh-bb__strain-reviews">' + reviews + '</span></div>';
    }
    function renderBundleProduct(p) {
      var priceHtml = p.regular && p.regular > p.price
        ? '<span class="gh-bb__price-old">$' + p.regular + '</span> <span class="gh-bb__price-cur">$' + p.price + '/oz</span>'
          + '<div class="gh-bb__price-save">Save $' + (p.regular - p.price) + '</div>'
        : '<span class="gh-bb__price-cur">$' + p.price + '/oz</span>';
      return '<div class="gh-bb__strain' + (p.inStock ? '' : ' gh-bb__strain--oos') + '"'
        + ' data-pid="' + p.pid + '"'
        + ' data-vid="' + p.vid + '"'
        + ' data-price="' + p.price + '"'
        + (p.regular ? ' data-regular="' + p.regular + '"' : '') + '>'
        + (p.isNew ? '<div class="gh-bb__strain-new">New Strain</div>' : '')
        + '<img class="gh-bb__strain-img" src="' + p.image + '" alt="' + p.name + '" loading="lazy">'
        + '<div class="gh-bb__strain-name">' + p.name + '</div>'
        + (p.meta ? '<div class="gh-bb__strain-meta">' + p.meta + '</div>' : '')
        + '<div class="gh-bb__strain-pricing">' + priceHtml + '</div>'
        + makeStars(p.rating, p.reviews)
        + '<div class="gh-bb__strain-qty">'
        + '<button class="gh-bb__qty-btn gh-bb__qty-minus">&#8722;</button>'
        + '<span class="gh-bb__qty-val">0</span>'
        + '<button class="gh-bb__qty-btn gh-bb__qty-plus">+</button>'
        + '</div>'
        + '</div>';
    }
    function loadBundleGrid() {
      var cacheBust = Math.floor(Date.now() / 3600000);
      fetch('/bundle-products.json?v=' + cacheBust)
        .then(function(r) {
          if (!r.ok) throw new Error('not found');
          return r.json();
        })
        .then(function(data) {
          if (!data || !data.products || !data.products.length) return;
          var grid = bbEl.querySelector('.gh-bb__grid');
          if (!grid) return;
          grid.innerHTML = data.products.map(renderBundleProduct).join('');
          selections = {};
          renderSummary();
          var collageImgs = document.querySelectorAll('.gh-bb__collage-img img');
          data.products.slice(0, collageImgs.length).forEach(function(p, i) {
            if (collageImgs[i]) { collageImgs[i].src = p.image; collageImgs[i].alt = p.name; }
          });
        })
        .catch(function() {
          var grid = bbEl.querySelector('.gh-bb__grid');
          if (grid && grid.querySelector('.gh-bb__loading')) {
            grid.innerHTML = '<div class="gh-bb__loading">Check back soon for available strains.</div>';
          }
        });
    }
    loadBundleGrid();"""

IIFE_CLOSE_ANCHOR = '    renderSummary();\n  })();'

# ── 3. CSS ─────────────────────────────────────────────────────────────────────
BUNDLE_GRID_CSS = """
    /* ===== Dynamic bundle grid ===== */
    .gh-bb__loading {
      grid-column: 1 / -1;
      text-align: center;
      padding: 32px 16px;
      color: #666;
      font-size: 14px;
    }
    .gh-bb__strain--oos {
      opacity: 0.45;
      pointer-events: none;
    }
"""

CSS_ANCHOR = '</style>'


def apply(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # 1. Replace hardcoded grid
    if 'loadBundleGrid' not in html:
        start = html.find(GRID_START)
        end   = html.find(GRID_END_ANC, start)
        if start != -1 and end != -1:
            html = html[:start] + NEW_GRID + html[end:]
            steps.append('gh-bb__grid replaced with loading placeholder')
        else:
            steps.append('ERROR: gh-bb__grid anchor not found')
    else:
        steps.append('loadBundleGrid already present — skipping grid replacement')

    # 2. Insert loadBundleGrid() inside IIFE (before last })();)
    if 'loadBundleGrid' not in html:
        pos = html.rfind(IIFE_CLOSE_ANCHOR)
        if pos != -1:
            html = (html[:pos]
                    + '    renderSummary();\n'
                    + LOAD_BUNDLE_JS + '\n'
                    + '  })();'
                    + html[pos + len(IIFE_CLOSE_ANCHOR):])
            steps.append('loadBundleGrid() inserted into Bundle Picker IIFE')
        else:
            steps.append('ERROR: IIFE close anchor not found')
    else:
        steps.append('loadBundleGrid already present — skipping JS insert')

    # 3. CSS
    if 'gh-bb__loading' not in html:
        pos = html.rfind(CSS_ANCHOR)
        if pos > 0:
            html = html[:pos] + BUNDLE_GRID_CSS + html[pos:]
            steps.append('Bundle grid CSS added')
        else:
            steps.append('ERROR: </style> anchor not found')
    else:
        steps.append('Bundle grid CSS already present')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path}:')
    for s in steps:
        ok = 'ERROR' not in s
        print(f'  {"+" if ok else "!"} {s}')


if __name__ == '__main__':
    print('=== Patching pages for dynamic bundle grid ===')
    for p in PAGES:
        if os.path.exists(p):
            apply(p)
        else:
            print(f'\nSKIP: {p}')
    print('\nDone.')
