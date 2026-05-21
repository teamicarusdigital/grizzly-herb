"""
upgrade_gallery_v2.py
=====================
Replaces the 2x2 collage with a premium single-image gallery:
 1. Large main image (defaults to Flower 6.png) with zoom on hover
 2. Click opens a full lightbox
 3. Thumbnail strip below -- populated dynamically from bundle products
 4. Main image auto-switches when a product is selected via + / - buttons
"""
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

# ── 1. New gallery-main + thumbs HTML (replaces the collage div) ──────────────
GALLERY_MAIN_HTML = (
    '      <div class="gh-bb__gallery-main" id="gh-bb-main-wrap">\n'
    '        <img class="gh-bb__gallery-main-img" id="gh-bb-main-img"'
    ' src="/images/Flower%206.png" alt="Premium AAAA+ Flower" loading="eager">\n'
    '        <div class="gh-bb__gallery-zoom-hint">\n'
    '          <svg viewBox="0 0 20 20" fill="none" width="16" height="16"'
    ' xmlns="http://www.w3.org/2000/svg">'
    '<circle cx="8.5" cy="8.5" r="5.5" stroke="#fff" stroke-width="1.8"/>'
    '<path d="M14.5 14.5l3 3" stroke="#fff" stroke-width="1.8" stroke-linecap="round"/>'
    '<path d="M6 8.5h5M8.5 6v5" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>'
    '</svg>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div class="gh-bb__gallery-thumbs" id="gh-bb-thumbs">\n'
    '        <div class="gh-bb__gallery-thumb gh-bb__gallery-thumb--active"'
    ' data-src="/images/Flower%206.png" data-alt="Premium AAAA+ Flower">\n'
    '          <img src="/images/Flower%206.png" alt="" loading="lazy">\n'
    '        </div>\n'
    '      </div>'
)

# ── 2. CSS ────────────────────────────────────────────────────────────────────
GALLERY_V2_CSS = """
    /* ===== Gallery v2: single image + zoom + thumbs ===== */
    .gh-bb__gallery-main {
      position: relative;
      border-radius: 14px;
      overflow: hidden;
      background: #e5e7eb;
      margin-bottom: 10px;
      cursor: zoom-in;
      aspect-ratio: 1;
    }
    .gh-bb__gallery-main-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
      transition: transform 0.45s ease;
    }
    .gh-bb__gallery-main:hover .gh-bb__gallery-main-img { transform: scale(1.07); }
    .gh-bb__gallery-zoom-hint {
      position: absolute;
      top: 10px; right: 10px;
      background: rgba(0,0,0,0.38);
      border-radius: 50%;
      width: 30px; height: 30px;
      display: flex; align-items: center; justify-content: center;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.2s;
    }
    .gh-bb__gallery-main:hover .gh-bb__gallery-zoom-hint { opacity: 1; }
    .gh-bb__gallery-thumbs {
      display: flex;
      gap: 7px;
      overflow-x: auto;
      padding-bottom: 2px;
      margin-bottom: 14px;
      scrollbar-width: none;
    }
    .gh-bb__gallery-thumbs::-webkit-scrollbar { display: none; }
    .gh-bb__gallery-thumb {
      flex-shrink: 0;
      width: 54px; height: 54px;
      border-radius: 9px;
      overflow: hidden;
      cursor: pointer;
      border: 2.5px solid transparent;
      transition: border-color 0.2s, transform 0.15s;
    }
    .gh-bb__gallery-thumb:hover { transform: scale(1.06); }
    .gh-bb__gallery-thumb--active { border-color: #4a7c2c; }
    .gh-bb__gallery-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
    .gh-bb__lightbox {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.88); z-index: 9999;
      align-items: center; justify-content: center; cursor: zoom-out;
    }
    .gh-bb__lightbox.gh-bb__lightbox--open { display: flex; }
    .gh-bb__lightbox img {
      max-width: 92vw; max-height: 90vh;
      object-fit: contain; border-radius: 10px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.5);
    }
    .gh-bb__lightbox-close {
      position: absolute; top: 14px; right: 20px;
      color: #fff; font-size: 32px; line-height: 1; cursor: pointer; font-weight: 300;
    }
"""

# ── 3. JS to insert before loadBundleGrid(); call inside the IIFE ────────────
GALLERY_JS = """
    // ─── Gallery v2 ────────────────────────────────────────────────────
    var ghMainImg  = document.getElementById('gh-bb-main-img');
    var ghThumbsEl = document.getElementById('gh-bb-thumbs');
    function ghSetImage(src, alt) {
      if (!ghMainImg) return;
      ghMainImg.src = src; ghMainImg.alt = alt || '';
      if (ghThumbsEl) {
        var ts = ghThumbsEl.querySelectorAll('.gh-bb__gallery-thumb');
        for (var ti = 0; ti < ts.length; ti++) {
          ts[ti].classList.toggle('gh-bb__gallery-thumb--active',
            ts[ti].getAttribute('data-src') === src);
        }
      }
    }
    function ghBuildThumbs(products) {
      if (!ghThumbsEl) return;
      ghThumbsEl.innerHTML = '';
      var td = [{ src: '/images/Flower%206.png', alt: 'Premium AAAA+ Flower' }];
      products.slice(0, 5).forEach(function(p) { td.push({ src: p.image, alt: p.name }); });
      td.forEach(function(item, idx) {
        var t = document.createElement('div');
        t.className = 'gh-bb__gallery-thumb' + (idx === 0 ? ' gh-bb__gallery-thumb--active' : '');
        t.setAttribute('data-src', item.src);
        t.setAttribute('data-alt', item.alt);
        t.innerHTML = '<img src="' + item.src + '" alt="' + item.alt + '" loading="lazy">';
        t.addEventListener('click', function() { ghSetImage(item.src, item.alt); });
        ghThumbsEl.appendChild(t);
      });
    }
    var ghLightbox = document.createElement('div');
    ghLightbox.className = 'gh-bb__lightbox';
    ghLightbox.innerHTML = '<span class="gh-bb__lightbox-close">&times;</span><img>';
    document.body.appendChild(ghLightbox);
    ghLightbox.addEventListener('click', function() {
      ghLightbox.classList.remove('gh-bb__lightbox--open');
    });
    var ghMainWrap = document.getElementById('gh-bb-main-wrap');
    if (ghMainWrap) {
      ghMainWrap.addEventListener('click', function() {
        var lbImg = ghLightbox.querySelector('img');
        if (lbImg && ghMainImg) { lbImg.src = ghMainImg.src; }
        ghLightbox.classList.add('gh-bb__lightbox--open');
      });
    }
    bbEl.addEventListener('click', function(e) {
      if (e.target.classList.contains('gh-bb__qty-plus') ||
          e.target.classList.contains('gh-bb__qty-minus')) {
        var card = e.target.closest('.gh-bb__strain');
        if (card) {
          var img = card.querySelector('.gh-bb__strain-img');
          if (img && img.src) { ghSetImage(img.src, img.alt); }
        }
      }
    });
"""

# ── 4. Old collage JS to replace (inside loadBundleGrid fetch success) ────────
OLD_COLLAGE_JS = (
    "var collageImgs = document.querySelectorAll('.gh-bb__collage-img img');\n"
    "          data.products.slice(0, collageImgs.length).forEach(function(p, i) {\n"
    "            if (collageImgs[i]) { collageImgs[i].src = p.image; collageImgs[i].alt = p.name;\n"
    "              var nameEl = collageImgs[i].parentNode.querySelector('.gh-bb__collage-name');\n"
    "              if (nameEl) nameEl.textContent = p.name; }"
)
NEW_COLLAGE_JS = "ghBuildThumbs(data.products);"

# Anchor for inserting gallery JS just before loadBundleGrid() invocation
LOAD_BG_ANCHOR = "    loadBundleGrid();\n  })();"
GALLERY_JS_INSERT = GALLERY_JS + "    loadBundleGrid();\n  })();"


def apply(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    steps = []

    # 1. Replace collage block with gallery-main + thumbs
    if '<div class="gh-bb__gallery-main"' not in html:
        collage_start = html.find('      <div class="gh-bb__collage">')
        value_card_pos = html.find('\n      <div class="gh-bb__value-card">', collage_start)
        if collage_start != -1 and value_card_pos != -1:
            # Find the closing </div> of the collage block
            collage_end = html.rfind('      </div>', collage_start, value_card_pos) + len('      </div>')
            html = html[:collage_start] + GALLERY_MAIN_HTML + html[collage_end:]
            steps.append('Gallery-main + thumbs HTML inserted')
        else:
            steps.append('ERROR: collage block anchor not found')
    else:
        steps.append('Gallery-main already present')

    # 2. Replace old collage JS in loadBundleGrid
    if OLD_COLLAGE_JS in html:
        html = html.replace(OLD_COLLAGE_JS, NEW_COLLAGE_JS, 1)
        steps.append('loadBundleGrid: replaced collage update with ghBuildThumbs()')
    elif 'ghBuildThumbs' in html:
        steps.append('loadBundleGrid: ghBuildThumbs already present')
    else:
        steps.append('WARNING: collage JS anchor not found -- check manually')

    # 3. Insert gallery JS before loadBundleGrid() call
    if LOAD_BG_ANCHOR in html and 'ghSetImage' not in html:
        html = html.replace(LOAD_BG_ANCHOR, GALLERY_JS_INSERT, 1)
        steps.append('Gallery v2 JS injected')
    elif 'ghSetImage' in html:
        steps.append('Gallery JS already present')
    else:
        steps.append('ERROR: loadBundleGrid() invocation anchor not found')

    # 4. Inject CSS (before last </style>)
    if 'gh-bb__gallery-main {' not in html:
        pos = html.rfind('</style>')
        if pos != -1:
            html = html[:pos] + GALLERY_V2_CSS + html[pos:]
            steps.append('Gallery v2 CSS injected')
        else:
            steps.append('ERROR: </style> anchor not found')
    else:
        steps.append('Gallery v2 CSS already present')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path}:')
    for s in steps:
        ok = 'ERROR' not in s and 'WARNING' not in s
        print(f'  {"+" if ok else "!"} {s}')


if __name__ == '__main__':
    print('=== Upgrading bundle gallery to v2 (single image + zoom + thumbs) ===')
    for p in PAGES:
        if os.path.exists(p):
            apply(p)
        else:
            print(f'\nSKIP: {p}')
    print('\nDone.')
