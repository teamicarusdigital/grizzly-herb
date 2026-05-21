"""
sync_reviews.py
===============
Fetches average_rating and rating_count from WooCommerce for every product
card on rb/bb/bc pages, then updates the star SVGs and review count in HTML.
"""
import os, re, json, sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError

sys.stdout.reconfigure(encoding='utf-8')

WC_KEY    = os.environ.get('WC_KEY',    'ck_c566b213178cba2f87412909fd7fb60dc752df80')
WC_SECRET = os.environ.get('WC_SECRET', 'cs_03523d8e3ff2c454acf1b76fa37483570de32ef4')
WC_BASE   = 'https://grizzlyherb.co/wp-json/wc/v3'

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

STAR_PATH   = 'M8 0.5l2.12 4.3 4.74.69-3.43 3.34.81 4.73L8 11.27l-4.24 2.29.81-4.73L1.14 5.49l4.74-.69z'
FILLED      = '#f8b300'
EMPTY       = '#e8e6e3'


def wc_get(path):
    sep = '&' if '?' in path else '?'
    url = f'{WC_BASE}{path}{sep}consumer_key={WC_KEY}&consumer_secret={WC_SECRET}'
    req = Request(url, headers={'User-Agent': 'WooCommerce/1.0'})
    try:
        with urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f'  HTTP {e.code} for {path}', flush=True)
        return None
    except Exception as e:
        print(f'  Error: {e}', flush=True)
        return None


def stars_html(avg, cnt):
    """5 SVGs + review count span."""
    n = max(0, min(5, round(float(avg or 0))))
    svgs = ''.join(
        f'<svg viewBox="0 0 16 16" fill="{"#f8b300" if i < n else "#e8e6e3"}"><path d="{STAR_PATH}"/></svg>'
        for i in range(5)
    )
    label = f'({cnt} Reviews)' if cnt else '(No Reviews)'
    return f'<div class="gh-products__card-stars">\n            {svgs}<span class="gh-products__card-reviews">{label}</span>\n          </div>'


def apply(path, ratings):
    with open(path, encoding='utf-8') as f:
        html = f.read()

    updated = 0
    for pid, (avg, cnt) in ratings.items():
        # Find the opening tag for this product card
        card_start = html.find(f'data-product-id="{pid}"')
        if card_start == -1:
            continue

        # Find the gh-products__card-stars div that follows
        stars_start = html.find('<div class="gh-products__card-stars">', card_start)
        if stars_start == -1:
            continue

        # Find end of the stars div (its closing </div>)
        stars_end = html.find('</div>', stars_start) + len('</div>')

        # Build replacement
        new_stars = stars_html(avg, cnt)

        html = html[:stars_start] + new_stars + html[stars_end:]
        updated += 1

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  -> Updated {updated}/{len(ratings)} cards in {path}', flush=True)


def main():
    print('=== Review Sync ===', flush=True)

    # Collect unique PIDs
    all_pids = set()
    for path in PAGES:
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()
        for m in re.finditer(r'data-product-id="(\d+)"', html):
            all_pids.add(m.group(1))

    print(f'Products: {sorted(all_pids)}', flush=True)

    ratings = {}
    for pid in sorted(all_pids):
        p = wc_get(f'/products/{pid}')
        if p:
            avg = float(p.get('average_rating') or 0)
            cnt = int(p.get('rating_count') or 0)
            ratings[pid] = (avg, cnt)
            name = p.get('name', pid)[:28]
            print(f'  {pid}  {avg:.2f}★  {cnt} reviews  {name}', flush=True)
        else:
            ratings[pid] = (0, 0)

    print('\nUpdating pages...', flush=True)
    for path in PAGES:
        if os.path.exists(path):
            apply(path, ratings)
        else:
            print(f'  SKIP {path}', flush=True)

    print('Done.', flush=True)


if __name__ == '__main__':
    main()
