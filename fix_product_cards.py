"""
fix_product_cards.py
====================
Fixes four issues on rb/bb/bc individual product cards:
 1. data-thc added to all cards (sourced from Leafly / strain databases)
 2. Variant switch: strikethrough + old price now shown (was missing old price)
 3. Side cart: regular price stored + shown with strikethrough
 4. Card price: font-size 11px -> 13px, weight 500 -> 700
"""
import sys, re, os
sys.stdout.reconfigure(encoding='utf-8')

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

# ── 1. THC values per product ID ───────────────────────────────────────────────
THC_MAP = {
    '129248': '26%',   # Mike Tyson
    '148701': '22%',   # MKU
    '134438': '25%',   # Gouda Berry
    '168138': '19%',   # Key Lime Haze
    '168131': '20%',   # Grape Diesel
    '144038': '22%',   # Cali Z.Z.
    '144022': '25%',   # Super Lemon Haze
    '183881': '28%',   # Ghost Breath
    '357186': '22%',   # Purple Kush
    '357044': '26%',   # Peanut Butter Breath
    '356979': '22%',   # Vanilla Kush
    '183859': '24%',   # Golden Oreoz
}

# ── 2. Variant price handler: fix missing strikethrough old price ───────────────
OLD_VARIANT_PRICE = """        if (activeV && activeV.regular && parseFloat(activeV.regular) > origP) {
          priceEl.innerHTML = '<span class="gh-products__card-price-new">$' + origP.toFixed(2) + '</span>';
        } else {
          priceEl.innerHTML = '$' + origP.toFixed(2);
        }"""

NEW_VARIANT_PRICE = """        if (activeV && activeV.regular && parseFloat(activeV.regular) > origP) {
          priceEl.innerHTML = '<span class="gh-products__card-price-old">$' + parseFloat(activeV.regular).toFixed(2) + '</span> <span class="gh-products__card-price-new">$' + origP.toFixed(2) + '</span>';
        } else {
          priceEl.innerHTML = '$' + origP.toFixed(2);
        }"""

# ── 3a. addToCart signature + cart.push: add regular param ────────────────────
OLD_ATC_SIG  = "  function addToCart(id, vid, name, label, price, image) {"
NEW_ATC_SIG  = "  function addToCart(id, vid, name, label, price, image, regular) {"

OLD_CART_PUSH = "    cart.push({ id: id, vid: vid, name: displayName, price: parseFloat(price), image: image, qty: 1 });"
NEW_CART_PUSH = "    cart.push({ id: id, vid: vid, name: displayName, price: parseFloat(price), image: image, qty: 1, regular: regular ? parseFloat(regular) : null });"

# ── 3b. addToCart call site: look up + pass regular price ─────────────────────
OLD_ATC_CALL = """        var vid = activeVariant ? activeVariant.getAttribute('data-vid') : card.getAttribute('data-product-id');
        var label = activeVariant ? activeVariant.getAttribute('data-vlabel') : '';
        addToCart(
          card.getAttribute('data-product-id'),
          vid,
          card.getAttribute('data-product-name'),
          label,
          card.getAttribute('data-product-price'),
          card.getAttribute('data-product-image')
        );"""

NEW_ATC_CALL = """        var vid = activeVariant ? activeVariant.getAttribute('data-vid') : card.getAttribute('data-product-id');
        var label = activeVariant ? activeVariant.getAttribute('data-vlabel') : '';
        var regularP = '';
        var vDataAtc = JSON.parse(card.getAttribute('data-variants') || '[]');
        for (var vi4 = 0; vi4 < vDataAtc.length; vi4++) {
          if (String(vDataAtc[vi4].vid) === String(vid)) {
            if (vDataAtc[vi4].regular && vDataAtc[vi4].regular > vDataAtc[vi4].price) regularP = vDataAtc[vi4].regular;
            break;
          }
        }
        addToCart(
          card.getAttribute('data-product-id'),
          vid,
          card.getAttribute('data-product-name'),
          label,
          card.getAttribute('data-product-price'),
          card.getAttribute('data-product-image'),
          regularP
        );"""

# ── 3c. renderCart: show strikethrough in side cart ───────────────────────────
OLD_RENDER_ITEM = """          html += '<div class="gh-cart-panel__item" data-product-id="' + item.vid + '">'
            + '<img src="' + item.image + '" class="gh-cart-panel__item-img" alt="' + item.name + '">'
            + '<div class="gh-cart-panel__item-info">'
            + '<div class="gh-cart-panel__item-name">' + item.name + '</div>'
            + '<div class="gh-cart-panel__item-price">$' + item.price.toFixed(2) + '</div>'"""

NEW_RENDER_ITEM = """          var cartPriceHtml = (item.regular && item.regular > item.price)
            ? '<span class="gh-cart-panel__item-price-old">$' + item.regular.toFixed(2) + '</span> $' + item.price.toFixed(2)
            : '$' + item.price.toFixed(2);
          html += '<div class="gh-cart-panel__item" data-product-id="' + item.vid + '">'
            + '<img src="' + item.image + '" class="gh-cart-panel__item-img" alt="' + item.name + '">'
            + '<div class="gh-cart-panel__item-info">'
            + '<div class="gh-cart-panel__item-name">' + item.name + '</div>'
            + '<div class="gh-cart-panel__item-price">' + cartPriceHtml + '</div>'"""

# ── 4. CSS: card price size + weight + old price clarity + cart strikethrough ──
OLD_PRICE_CSS = """.gh-products__card-price {
  font-family: 'Poppins', sans-serif;
  font-size: 11px;
  font-weight: 500;
  color: #1f1f1f;
  margin-bottom: 8px;
  line-height: 1.3;
}"""

NEW_PRICE_CSS = """.gh-products__card-price {
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  font-weight: 700;
  color: #1f1f1f;
  margin-bottom: 8px;
  line-height: 1.3;
}"""

OLD_PRICE_OLD_CSS = """.gh-products__card-price-old {
  font-size: 10px;
  color: #aaa;
  text-decoration: line-through;
  margin-right: 3px;
  font-weight: 400;
}"""

NEW_PRICE_OLD_CSS = """.gh-products__card-price-old {
  font-size: 11px;
  color: #999;
  text-decoration: line-through;
  text-decoration-color: #e05555;
  margin-right: 4px;
  font-weight: 500;
}"""

CART_PRICE_OLD_CSS = """
    .gh-cart-panel__item-price-old {
      font-size: 11px;
      color: #999;
      text-decoration: line-through;
      text-decoration-color: #e05555;
      margin-right: 4px;
      display: inline;
    }"""

CART_CSS_ANCHOR = '/* ===== Bundle Cart Item ===== */'


def apply(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # 1. THC values
    thc_added = 0
    thc_already = 0
    for pid, thc in THC_MAP.items():
        # Only insert data-thc if not already present on that card's line
        # Pattern: finds ...data-product-url="..." followed directly by data-variants= (no data-thc yet)
        pattern = r'(data-product-id="' + pid + r'"[^\']*?data-product-url="[^"]*") (data-variants=)'
        repl    = r'\1 data-thc="' + thc + r'" \2'
        new_html, count = re.subn(pattern, repl, html)
        if count:
            html = new_html
            thc_added += count
        else:
            # Check if it already has data-thc for this pid
            if re.search(r'data-product-id="' + pid + r'"[^\']*?data-thc=', html):
                thc_already += 1
    steps.append(f'THC: {thc_added} added, {thc_already} already present')

    # 2. Variant handler: show old price on switch
    if OLD_VARIANT_PRICE in html:
        html = html.replace(OLD_VARIANT_PRICE, NEW_VARIANT_PRICE, 1)
        steps.append('Variant price handler: strikethrough old price added')
    elif 'gh-products__card-price-old' in html and 'parseFloat(activeV.regular).toFixed' in html:
        steps.append('Variant price handler: already fixed')
    else:
        steps.append('ERROR: variant price handler anchor not found')

    # 3a. addToCart signature
    if OLD_ATC_SIG in html:
        html = html.replace(OLD_ATC_SIG, NEW_ATC_SIG, 1)
        steps.append('addToCart: regular param added to signature')
    elif NEW_ATC_SIG in html:
        steps.append('addToCart signature: already updated')
    else:
        steps.append('ERROR: addToCart signature anchor not found')

    # 3b. cart.push
    if OLD_CART_PUSH in html:
        html = html.replace(OLD_CART_PUSH, NEW_CART_PUSH, 1)
        steps.append('cart.push: regular price stored')
    elif 'regular: regular ?' in html:
        steps.append('cart.push: already updated')
    else:
        steps.append('ERROR: cart.push anchor not found')

    # 3c. addToCart call site
    if OLD_ATC_CALL in html:
        html = html.replace(OLD_ATC_CALL, NEW_ATC_CALL, 1)
        steps.append('addToCart call: regular price passed')
    elif 'vDataAtc' in html:
        steps.append('addToCart call: already updated')
    else:
        steps.append('ERROR: addToCart call anchor not found')

    # 3d. renderCart strikethrough
    if OLD_RENDER_ITEM in html:
        html = html.replace(OLD_RENDER_ITEM, NEW_RENDER_ITEM, 1)
        steps.append('renderCart: strikethrough added to side cart')
    elif 'cartPriceHtml' in html:
        steps.append('renderCart: already updated')
    else:
        steps.append('ERROR: renderCart item anchor not found')

    # 4a. card price font size + weight
    if OLD_PRICE_CSS in html:
        html = html.replace(OLD_PRICE_CSS, NEW_PRICE_CSS, 1)
        steps.append('CSS: card price -> 13px bold')
    elif 'font-size: 13px' in html and 'gh-products__card-price {' in html:
        steps.append('CSS: card price already updated')
    else:
        steps.append('ERROR: card price CSS anchor not found')

    # 4b. price-old CSS clarity
    if OLD_PRICE_OLD_CSS in html:
        html = html.replace(OLD_PRICE_OLD_CSS, NEW_PRICE_OLD_CSS, 1)
        steps.append('CSS: price-old improved')
    elif 'text-decoration-color: #e05555' in html:
        steps.append('CSS: price-old already updated')
    else:
        steps.append('ERROR: price-old CSS anchor not found')

    # 4c. cart item price-old CSS
    if 'gh-cart-panel__item-price-old' not in html:
        pos = html.find(CART_CSS_ANCHOR)
        if pos != -1:
            html = html[:pos] + CART_PRICE_OLD_CSS + '\n    ' + html[pos:]
            steps.append('CSS: cart item price-old added')
        else:
            steps.append('ERROR: cart CSS anchor not found')
    else:
        steps.append('CSS: cart item price-old already present')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path}:')
    for s in steps:
        ok = 'ERROR' not in s
        print(f'  {"+" if ok else "!"} {s}')


if __name__ == '__main__':
    print('=== Fixing product card display issues ===')
    for p in PAGES:
        if os.path.exists(p):
            apply(p)
        else:
            print(f'\nSKIP: {p}')
    print('\nDone.')
