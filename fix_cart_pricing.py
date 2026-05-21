"""
fix_cart_pricing.py
===================
The .gh-cart-panel__item-price-old CSS was never inserted because the
idempotency check matched the class name inside the JS string.
Also wraps the sale price in its own span for independent styling.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

# ── JS: wrap sale price in its own span ───────────────────────────────────────
OLD_PRICE_HTML = (
    "? '<span class=\"gh-cart-panel__item-price-old\">$' + item.regular.toFixed(2) + '</span> $' + item.price.toFixed(2)"
)
NEW_PRICE_HTML = (
    "? '<span class=\"gh-cart-panel__item-price-old\">$' + item.regular.toFixed(2) + '</span>"
    "<span class=\"gh-cart-panel__item-price-sale\">$' + item.price.toFixed(2) + '</span>'"
)

# ── CSS: insert before Bundle Cart Item section ───────────────────────────────
CART_PRICING_CSS = """
    /* ===== Cart Item Sale Pricing ===== */
    .gh-cart-panel__item-price-old {
      font-size: 10px;
      color: #bbb;
      text-decoration: line-through;
      text-decoration-color: #d44;
      font-weight: 400;
      display: inline;
      margin-right: 5px;
    }
    .gh-cart-panel__item-price-sale {
      font-size: 14px;
      color: #2d7a1a;
      font-weight: 700;
      display: inline;
    }
"""

CSS_ANCHOR = '</style>'  # insert before last </style>


def apply(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    steps = []

    # JS: wrap sale price in span
    if OLD_PRICE_HTML in html:
        html = html.replace(OLD_PRICE_HTML, NEW_PRICE_HTML, 1)
        steps.append('renderCart: sale price wrapped in span')
    elif 'gh-cart-panel__item-price-sale' in html:
        steps.append('renderCart: sale span already present')
    else:
        steps.append('ERROR: renderCart price HTML anchor not found')

    # CSS: add both rules if not already properly defined
    if '.gh-cart-panel__item-price-old {' not in html:
        pos = html.rfind(CSS_ANCHOR)  # last </style>
        if pos != -1:
            html = html[:pos] + CART_PRICING_CSS + html[pos:]
            steps.append('CSS: cart price-old + price-sale rules added')
        else:
            steps.append('ERROR: CSS anchor not found')
    else:
        steps.append('CSS: cart price rules already present')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'\n{path}:')
    for s in steps:
        print(f'  {"+" if "ERROR" not in s else "!"} {s}')


if __name__ == '__main__':
    print('=== Fixing cart item sale price display ===')
    for p in PAGES:
        if os.path.exists(p):
            apply(p)
        else:
            print(f'\nSKIP: {p}')
    print('\nDone.')
