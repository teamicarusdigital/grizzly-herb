"""
update_all_pages.py
===================
Applies to all 4 flower pages:
  1. OOS product variant JS + CSS (rb already has it, applying to bb/bc/hsh)
  2. Top banner: marquee skill + premium per-item icons
  3. Hero stats ribbon: marquee skill
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
    'pages/premium-collection-hsh/index.html',
]

# ─────────────────────────────────────────────────────────────────────────────
# 1. OOS VARIANT CSS  (already on rb — add to bb/bc/hsh too)
# ─────────────────────────────────────────────────────────────────────────────
OOS_CSS_ANCHOR = '.gh-root .gh-products__card-variant--active {\n  border-color: #2d5016;\n  background: #2d5016;\n  color: #ffffff;\n}'
OOS_CSS_NEW    = OOS_CSS_ANCHOR + """
.gh-root .gh-products__card-variant--oos {
  opacity: 0.38;
  text-decoration: line-through;
  cursor: not-allowed;
  pointer-events: none;
}"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. OOS VARIANT JS — generation block  (rb already has it)
# ─────────────────────────────────────────────────────────────────────────────
OLD_VARIANT_JS = """  // === Generate variant selector pills for each product card ===
  var variantCards = root.querySelectorAll('.gh-products__card[data-variants]');
  for (var vc = 0; vc < variantCards.length; vc++) {
    var vCard = variantCards[vc];
    var variants = JSON.parse(vCard.getAttribute('data-variants'));
    var pillRow = document.createElement('div');
    pillRow.className = 'gh-products__card-variants';
    for (var vi = 0; vi < variants.length; vi++) {
      var pill = document.createElement('button');
      pill.className = 'gh-products__card-variant' + (vi === 0 ? ' gh-products__card-variant--active' : '');
      pill.setAttribute('data-vid', variants[vi].vid);
      pill.setAttribute('data-vprice', variants[vi].price);
      pill.setAttribute('data-vlabel', variants[vi].label);
      pill.textContent = variants[vi].label;
      pillRow.appendChild(pill);
    }
    var cardBottom = vCard.querySelector('.gh-products__card-bottom');
    vCard.insertBefore(pillRow, cardBottom);
    // Add THC badge if available
    var thc = vCard.getAttribute('data-thc');
    if (thc) {
      var thcEl = document.createElement('div');
      thcEl.className = 'gh-products__card-thc';
      thcEl.textContent = 'THC ' + thc;
      vCard.insertBefore(thcEl, pillRow);
    }
    // Set initial price from first variant (show regular price crossed out if on sale)
    vCard.setAttribute('data-product-price', variants[0].price);
    var priceEl = vCard.querySelector('.gh-products__card-price');
    if (priceEl) {
      var saleP = parseFloat(variants[0].price);
      var regP = variants[0].regular ? parseFloat(variants[0].regular) : null;
      if (regP && regP > saleP) {
        priceEl.innerHTML = '<span class="gh-products__card-price-old">$' + regP.toFixed(2) + '</span> <span class="gh-products__card-price-new">$' + saleP.toFixed(2) + '</span>';
      } else {
        priceEl.innerHTML = '$' + saleP.toFixed(2);
      }
    }
  }"""

NEW_VARIANT_JS = """  // === Generate variant selector pills for each product card ===
  var variantCards = root.querySelectorAll('.gh-products__card[data-variants]');
  for (var vc = 0; vc < variantCards.length; vc++) {
    var vCard = variantCards[vc];
    var variants = JSON.parse(vCard.getAttribute('data-variants'));
    var pillRow = document.createElement('div');
    pillRow.className = 'gh-products__card-variants';
    // Find first in-stock variant index (falls back to 0 if all are OOS)
    var firstInStock = -1;
    var allOos = true;
    for (var vi = 0; vi < variants.length; vi++) {
      if (variants[vi].inStock !== false) { if (firstInStock === -1) firstInStock = vi; allOos = false; }
    }
    if (firstInStock === -1) firstInStock = 0;
    if (allOos) vCard.classList.add('gh-products__card--out-of-stock');
    for (var vi = 0; vi < variants.length; vi++) {
      var isOos = variants[vi].inStock === false;
      var pill = document.createElement('button');
      pill.className = 'gh-products__card-variant' + (vi === firstInStock ? ' gh-products__card-variant--active' : '') + (isOos ? ' gh-products__card-variant--oos' : '');
      pill.setAttribute('data-vid', variants[vi].vid);
      pill.setAttribute('data-vprice', variants[vi].price);
      pill.setAttribute('data-vlabel', variants[vi].label);
      pill.textContent = variants[vi].label;
      pillRow.appendChild(pill);
    }
    var cardBottom = vCard.querySelector('.gh-products__card-bottom');
    vCard.insertBefore(pillRow, cardBottom);
    // Add THC badge if available
    var thc = vCard.getAttribute('data-thc');
    if (thc) {
      var thcEl = document.createElement('div');
      thcEl.className = 'gh-products__card-thc';
      thcEl.textContent = 'THC ' + thc;
      vCard.insertBefore(thcEl, pillRow);
    }
    // Set initial price from first in-stock variant
    var initV = variants[firstInStock];
    vCard.setAttribute('data-product-price', initV.price);
    var priceEl = vCard.querySelector('.gh-products__card-price');
    if (priceEl) {
      var saleP = parseFloat(initV.price);
      var regP = initV.regular ? parseFloat(initV.regular) : null;
      if (regP && regP > saleP) {
        priceEl.innerHTML = '<span class="gh-products__card-price-old">$' + regP.toFixed(2) + '</span> <span class="gh-products__card-price-new">$' + saleP.toFixed(2) + '</span>';
      } else {
        priceEl.innerHTML = '$' + saleP.toFixed(2);
      }
    }
  }"""

# ─────────────────────────────────────────────────────────────────────────────
# 3. OOS CLICK GUARD  (rb already has it)
# ─────────────────────────────────────────────────────────────────────────────
OLD_CLICK_GUARD = """    // Variant pill click
    var variantBtn = e.target.closest('.gh-products__card-variant');
    if(variantBtn){
      var card = variantBtn.closest('.gh-products__card');"""

NEW_CLICK_GUARD = """    // Variant pill click
    var variantBtn = e.target.closest('.gh-products__card-variant');
    if(variantBtn){
      if(variantBtn.classList.contains('gh-products__card-variant--oos')) return;
      var card = variantBtn.closest('.gh-products__card');"""

# ─────────────────────────────────────────────────────────────────────────────
# 4. BANNER — CSS (replace old animation+keyframes with clean version)
# ─────────────────────────────────────────────────────────────────────────────
OLD_BANNER_CSS = """.gh-banner__track {
  display: flex;
  align-items: center;
  white-space: nowrap;
  animation: gh-banner-scroll 28s linear infinite;
}

.gh-banner__inner {
  display: flex;
  align-items: center;
  gap: 32px;
  padding-right: 64px;
  flex-shrink: 0;
}

.gh-banner__icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.gh-banner__text {
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
  white-space: nowrap;
}

@keyframes gh-banner-scroll {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}"""

NEW_BANNER_CSS = """.gh-banner__track {
  display: flex;
  align-items: center;
  white-space: nowrap;
  cursor: grab;
}
.gh-banner__track--dragging { cursor: grabbing; }
.gh-banner__item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  flex-shrink: 0;
  margin-right: 32px;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
  white-space: nowrap;
}
.gh-banner__item svg { flex-shrink: 0; }
.gh-banner__sep {
  flex-shrink: 0;
  margin-right: 32px;
  color: rgba(255,255,255,0.5);
  font-size: 14px;
  font-weight: 300;
}"""

# ─────────────────────────────────────────────────────────────────────────────
# 5. BANNER — HTML (replace old duplicate structure with single-set + id)
# ─────────────────────────────────────────────────────────────────────────────
OLD_BANNER_HTML = """<div class="gh-banner" aria-label="Promotions">
    <div class="gh-banner__track">
      <!-- First copy -->
      <div class="gh-banner__inner">
        <span class="gh-banner__icon">
          <svg width="22" height="16" viewBox="0 0 22 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="3" width="14" height="9" rx="1.5" fill="white" opacity="0.9"/>
            <path d="M14 5H17.5L21 9V12H14V5Z" fill="white" opacity="0.9"/>
            <circle cx="4.5" cy="13" r="2" fill="#e85d35" stroke="white" stroke-width="1.2"/>
            <circle cx="17.5" cy="13" r="2" fill="#e85d35" stroke="white" stroke-width="1.2"/>
          </svg>
        </span>
        <span class="gh-banner__text">Free shipping over $90</span>
        <span class="gh-banner__text">|</span>
        <span class="gh-banner__text">Fast Canada wide delivery</span>
        <span class="gh-banner__text">|</span>
        <span class="gh-banner__text">8+ years serving Canadian buyers</span>
        <span class="gh-banner__text">|</span>
        <span class="gh-banner__text">Buy 4oz, Get 1oz Free</span>
        <span class="gh-banner__text">|</span>
      </div>
      <!-- Duplicate for seamless loop -->
      <div class="gh-banner__inner" aria-hidden="true">
        <span class="gh-banner__icon">
          <svg width="22" height="16" viewBox="0 0 22 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="0" y="3" width="14" height="9" rx="1.5" fill="white" opacity="0.9"/>
            <path d="M14 5H17.5L21 9V12H14V5Z" fill="white" opacity="0.9"/>
            <circle cx="4.5" cy="13" r="2" fill="#e85d35" stroke="white" stroke-width="1.2"/>
            <circle cx="17.5" cy="13" r="2" fill="#e85d35" stroke="white" stroke-width="1.2"/>
          </svg>
        </span>
        <span class="gh-banner__text">Free shipping over $90</span>
        <span class="gh-banner__text">|</span>
        <span class="gh-banner__text">Fast Canada wide delivery</span>
        <span class="gh-banner__text">|</span>
        <span class="gh-banner__text">8+ years serving Canadian buyers</span>
        <span class="gh-banner__text">|</span>
        <span class="gh-banner__text">Buy 4oz, Get 1oz Free</span>
        <span class="gh-banner__text">|</span>
      </div>
    </div>
  </div>"""

NEW_BANNER_HTML = """<div class="gh-banner" aria-label="Promotions">
    <div class="gh-banner__track" id="gh-banner-track">
      <span class="gh-banner__item">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="1" y="3" width="10" height="7" rx="1" fill="white" opacity="0.9"/>
          <path d="M11 5H13.5L15 8V10H11V5Z" fill="white" opacity="0.9"/>
          <circle cx="3.5" cy="11.5" r="1.5" fill="#e85d35" stroke="white" stroke-width="1"/>
          <circle cx="12.5" cy="11.5" r="1.5" fill="#e85d35" stroke="white" stroke-width="1"/>
        </svg>
        Free shipping over $90
      </span>
      <span class="gh-banner__sep">&middot;</span>
      <span class="gh-banner__item">
        <svg width="14" height="16" viewBox="0 0 14 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <polygon points="8,1 3,9 7,9 6,15 11,7 7,7" fill="white" opacity="0.9"/>
        </svg>
        Fast Canada wide delivery
      </span>
      <span class="gh-banner__sep">&middot;</span>
      <span class="gh-banner__item">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 1L10 6H15L11 9.5L12.5 14.5L8 11.5L3.5 14.5L5 9.5L1 6H6Z" fill="white" opacity="0.9"/>
        </svg>
        8+ years serving Canadian buyers
      </span>
      <span class="gh-banner__sep">&middot;</span>
      <span class="gh-banner__item">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="2" y="7" width="12" height="8" rx="1" fill="white" opacity="0.9"/>
          <rect x="1" y="5" width="14" height="3" rx="1" fill="white"/>
          <path d="M8 5C8 5 6 2 4 3C2 4 3 6 5 6" stroke="white" stroke-width="1.2" fill="none" stroke-linecap="round"/>
          <path d="M8 5C8 5 10 2 12 3C14 4 13 6 11 6" stroke="white" stroke-width="1.2" fill="none" stroke-linecap="round"/>
          <line x1="8" y1="5" x2="8" y2="15" stroke="#e85d35" stroke-width="1.2"/>
        </svg>
        Buy 4oz, Get 1oz Free
      </span>
      <span class="gh-banner__sep">&middot;</span>
      <span class="gh-banner__item">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M8 2C5.5 2 3.5 4 3.5 6.5C3.5 9 5 11 8 13C11 11 12.5 9 12.5 6.5C12.5 4 10.5 2 8 2Z" fill="white" opacity="0.9"/>
          <path d="M8 5V9M6 7H10" stroke="#e85d35" stroke-width="1.3" stroke-linecap="round"/>
        </svg>
        AAAA+ Quality Guaranteed
      </span>
      <span class="gh-banner__sep">&middot;</span>
    </div>
  </div>"""

# ─────────────────────────────────────────────────────────────────────────────
# 6. RIBBON — CSS (replace animation+keyframes+gap with clean version)
# ─────────────────────────────────────────────────────────────────────────────
OLD_RIBBON_CSS = """.gh-stats-ribbon__track {
  display: flex;
  align-items: center;
  animation: gh-ribbon-scroll 30s linear infinite;
}

@keyframes gh-ribbon-scroll {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

.gh-stats-ribbon__inner {
  display: flex;
  align-items: center;
  gap: 32px;
  padding-right: 32px;
  flex-shrink: 0;
}"""

NEW_RIBBON_CSS = """.gh-stats-ribbon__track {
  display: flex;
  align-items: center;
  cursor: grab;
}
.gh-stats-ribbon__track--dragging { cursor: grabbing; }
.gh-stats-ribbon__inner {
  display: flex;
  align-items: center;
  flex-shrink: 0;
  margin-right: 32px;
}"""

# ─────────────────────────────────────────────────────────────────────────────
# 7. RIBBON — HTML (remove hardcoded duplicate, add id to track)
# ─────────────────────────────────────────────────────────────────────────────
OLD_RIBBON_TRACK_OPEN  = '<div class="gh-stats-ribbon__track">'
NEW_RIBBON_TRACK_OPEN  = '<div class="gh-stats-ribbon__track" id="gh-ribbon-track">'

# Also need to remove the second .gh-stats-ribbon__inner (the duplicate copy)
# We'll handle this by finding the section and stripping the second inner block


# ─────────────────────────────────────────────────────────────────────────────
# 8. MARQUEE JS  (injected before closing </script> of each page)
# ─────────────────────────────────────────────────────────────────────────────
MARQUEE_JS = """
  // === Marquee: Top Banner ===
  window.addEventListener('load', function() {
    var bTrack = document.getElementById('gh-banner-track');
    if (bTrack) {
      var bItems = Array.from(bTrack.children);
      while (bTrack.scrollWidth < window.innerWidth * 3) {
        bItems.forEach(function(el) { var c = el.cloneNode(true); c.setAttribute('aria-hidden','true'); bTrack.appendChild(c); });
      }
      var bSet = bItems.reduce(function(a, el) {
        return a + el.offsetWidth + parseFloat(window.getComputedStyle(el).marginRight);
      }, 0);
      var bStyle = document.createElement('style');
      bStyle.textContent = '@keyframes gh-b-tick{from{transform:translateX(0)}to{transform:translateX(-' + Math.round(bSet) + 'px)}}';
      document.head.appendChild(bStyle);
      bTrack.style.animation = 'gh-b-tick 28s linear infinite';
      var bDrag=false, bStartX=0, bFrozenX=0;
      function bGetX(){var t=window.getComputedStyle(bTrack).transform;if(!t||t==='none')return 0;return parseFloat(t.match(/matrix.*\((.+)\)/)[1].split(', ')[4])||0;}
      function bFreeze(x){bTrack.style.animation='none';bTrack.style.transform='translateX('+x+'px)';}
      function bResume(x){var p=x%bSet;if(p>0)p-=bSet;var e=(-p/bSet)*28;bTrack.style.transform='';bTrack.style.animation='gh-b-tick 28s linear -'+e.toFixed(3)+'s infinite';}
      bTrack.addEventListener('mouseenter',function(){if(!bDrag){bFrozenX=bGetX();bFreeze(bFrozenX);}});
      bTrack.addEventListener('mouseleave',function(){if(!bDrag)bResume(bFrozenX);});
      bTrack.addEventListener('mousedown',function(e){bDrag=true;bStartX=e.clientX;bFrozenX=bGetX();bFreeze(bFrozenX);bTrack.classList.add('gh-banner__track--dragging');e.preventDefault();});
      document.addEventListener('mousemove',function(e){if(!bDrag)return;bTrack.style.transform='translateX('+(bFrozenX+e.clientX-bStartX)+'px)';});
      document.addEventListener('mouseup',function(){if(!bDrag)return;bDrag=false;bTrack.classList.remove('gh-banner__track--dragging');bResume(bGetX());});
      bTrack.addEventListener('touchstart',function(e){bDrag=true;bStartX=e.touches[0].clientX;bFrozenX=bGetX();bFreeze(bFrozenX);},{passive:true});
      bTrack.addEventListener('touchmove',function(e){if(!bDrag)return;bTrack.style.transform='translateX('+(bFrozenX+e.touches[0].clientX-bStartX)+'px)';},{passive:true});
      bTrack.addEventListener('touchend',function(){if(!bDrag)return;bDrag=false;bResume(bGetX());});
    }

    // === Marquee: Hero Stats Ribbon ===
    var rTrack = document.getElementById('gh-ribbon-track');
    if (rTrack) {
      var rItems = Array.from(rTrack.children);
      while (rTrack.scrollWidth < window.innerWidth * 3) {
        rItems.forEach(function(el) { var c = el.cloneNode(true); c.setAttribute('aria-hidden','true'); rTrack.appendChild(c); });
      }
      var rSet = rItems.reduce(function(a, el) {
        return a + el.offsetWidth + parseFloat(window.getComputedStyle(el).marginRight);
      }, 0);
      var rStyle = document.createElement('style');
      rStyle.textContent = '@keyframes gh-r-tick{from{transform:translateX(0)}to{transform:translateX(-' + Math.round(rSet) + 'px)}}';
      document.head.appendChild(rStyle);
      rTrack.style.animation = 'gh-r-tick 30s linear infinite';
      var rDrag=false, rStartX=0, rFrozenX=0;
      function rGetX(){var t=window.getComputedStyle(rTrack).transform;if(!t||t==='none')return 0;return parseFloat(t.match(/matrix.*\((.+)\)/)[1].split(', ')[4])||0;}
      function rFreeze(x){rTrack.style.animation='none';rTrack.style.transform='translateX('+x+'px)';}
      function rResume(x){var p=x%rSet;if(p>0)p-=rSet;var e=(-p/rSet)*30;rTrack.style.transform='';rTrack.style.animation='gh-r-tick 30s linear -'+e.toFixed(3)+'s infinite';}
      rTrack.addEventListener('mouseenter',function(){if(!rDrag){rFrozenX=rGetX();rFreeze(rFrozenX);}});
      rTrack.addEventListener('mouseleave',function(){if(!rDrag)rResume(rFrozenX);});
      rTrack.addEventListener('mousedown',function(e){rDrag=true;rStartX=e.clientX;rFrozenX=rGetX();rFreeze(rFrozenX);rTrack.classList.add('gh-stats-ribbon__track--dragging');e.preventDefault();});
      document.addEventListener('mousemove',function(e){if(!rDrag)return;rTrack.style.transform='translateX('+(rFrozenX+e.clientX-rStartX)+'px)';});
      document.addEventListener('mouseup',function(){if(!rDrag)return;rDrag=false;rTrack.classList.remove('gh-stats-ribbon__track--dragging');rResume(rGetX());});
      rTrack.addEventListener('touchstart',function(e){rDrag=true;rStartX=e.touches[0].clientX;rFrozenX=rGetX();rFreeze(rFrozenX);},{passive:true});
      rTrack.addEventListener('touchmove',function(e){if(!rDrag)return;rTrack.style.transform='translateX('+(rFrozenX+e.touches[0].clientX-rStartX)+'px)';},{passive:true});
      rTrack.addEventListener('touchend',function(){if(!rDrag)return;rDrag=false;rResume(rGetX());});
    }
  });"""

MARQUEE_JS_ANCHOR = '\n})();\n</script>'


# ─────────────────────────────────────────────────────────────────────────────
# Helper: strip the second gh-stats-ribbon__inner (the hardcoded duplicate)
# ─────────────────────────────────────────────────────────────────────────────
def remove_ribbon_duplicate(html):
    track_start = html.find('<div class="gh-stats-ribbon__track" id="gh-ribbon-track">')
    if track_start < 0:
        return html  # id not yet added — shouldn't happen

    # Find the two .gh-stats-ribbon__inner blocks and remove the second
    first_inner = html.find('<div class="gh-stats-ribbon__inner">', track_start)
    if first_inner < 0:
        return html

    # Find the end of the first inner block (counting nested divs)
    depth = 0
    i = first_inner
    while i < len(html):
        if html[i:i+4] == '<div':
            depth += 1
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                first_inner_end = i + 6
                break
        i += 1

    # Find the second inner block
    second_inner = html.find('<div class="gh-stats-ribbon__inner"', first_inner_end)
    if second_inner < 0:
        return html  # no duplicate found

    # Find the end of the second inner block
    depth = 0
    i = second_inner
    while i < len(html):
        if html[i:i+4] == '<div':
            depth += 1
        elif html[i:i+6] == '</div>':
            depth -= 1
            if depth == 0:
                second_inner_end = i + 6
                break
        i += 1

    # Remove the second block (and any whitespace after it)
    after = html[second_inner_end:].lstrip('\n ')
    html = html[:second_inner] + html[second_inner_end:]
    return html


# ─────────────────────────────────────────────────────────────────────────────
# Apply all changes to a page
# ─────────────────────────────────────────────────────────────────────────────
def apply(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    orig = html
    steps = []

    # 1. OOS CSS
    if OOS_CSS_ANCHOR in html and OOS_CSS_NEW not in html:
        html = html.replace(OOS_CSS_ANCHOR, OOS_CSS_NEW, 1)
        steps.append('OOS CSS added')
    elif OOS_CSS_NEW in html:
        steps.append('OOS CSS already present')

    # 2. OOS variant JS
    if OLD_VARIANT_JS in html:
        html = html.replace(OLD_VARIANT_JS, NEW_VARIANT_JS, 1)
        steps.append('OOS variant JS updated')
    elif 'allOos' in html:
        steps.append('OOS variant JS already present')
    else:
        steps.append('OOS variant JS: OLD not found')

    # 3. OOS click guard
    if OLD_CLICK_GUARD in html:
        html = html.replace(OLD_CLICK_GUARD, NEW_CLICK_GUARD, 1)
        steps.append('OOS click guard added')
    elif 'classList.contains(\'gh-products__card-variant--oos\')' in html:
        steps.append('OOS click guard already present')

    # 4. Banner CSS
    if OLD_BANNER_CSS in html:
        html = html.replace(OLD_BANNER_CSS, NEW_BANNER_CSS, 1)
        steps.append('Banner CSS updated')
    elif 'gh-banner__track--dragging' in html:
        steps.append('Banner CSS already updated')
    else:
        steps.append('Banner CSS: anchor not found')

    # 5. Banner HTML
    if OLD_BANNER_HTML in html:
        html = html.replace(OLD_BANNER_HTML, NEW_BANNER_HTML, 1)
        steps.append('Banner HTML updated')
    elif 'id="gh-banner-track"' in html:
        steps.append('Banner HTML already updated')
    else:
        steps.append('Banner HTML: anchor not found')

    # 6. Ribbon CSS
    if OLD_RIBBON_CSS in html:
        html = html.replace(OLD_RIBBON_CSS, NEW_RIBBON_CSS, 1)
        steps.append('Ribbon CSS updated')
    elif 'gh-stats-ribbon__track--dragging' in html:
        steps.append('Ribbon CSS already updated')
    else:
        steps.append('Ribbon CSS: anchor not found')

    # 7. Ribbon track: add id
    if OLD_RIBBON_TRACK_OPEN in html:
        html = html.replace(OLD_RIBBON_TRACK_OPEN, NEW_RIBBON_TRACK_OPEN, 1)
        steps.append('Ribbon track id added')
    elif 'id="gh-ribbon-track"' in html:
        steps.append('Ribbon track id already present')

    # 8. Remove ribbon duplicate
    if 'id="gh-ribbon-track"' in html:
        html_before = html
        html = remove_ribbon_duplicate(html)
        if html != html_before:
            steps.append('Ribbon duplicate removed')
        else:
            steps.append('Ribbon duplicate: already removed or not found')

    # 9. Marquee JS
    if 'gh-b-tick' not in html:
        html = html.replace(MARQUEE_JS_ANCHOR, MARQUEE_JS + MARQUEE_JS_ANCHOR, 1)
        steps.append('Marquee JS injected')
    else:
        steps.append('Marquee JS already present')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    changed = html != orig
    print(f'\n{path}:')
    for s in steps:
        print(f'  {"✓" if "not found" not in s and "already" not in s or "present" in s else "~"} {s}')
    print(f'  File {"CHANGED" if changed else "unchanged"} ({len(html)//1024}kb)')


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('=== Updating all flower pages ===')
    for page in PAGES:
        if os.path.exists(page):
            apply(page)
        else:
            print(f'\nSKIP (not found): {page}')
    print('\nDone.')
