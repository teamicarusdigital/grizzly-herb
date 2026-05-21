"""
sync_reviews.py
===============
Gets review data from Judge.me widget meta stored in WooCommerce product meta.
This is more accurate than WC's native rating_count (which only counts native reviews).
For fully live counts, set JDGM_TOKEN env var (Judge.me Public Token from WC admin).
"""
import os, re, json, sys
from urllib.request import urlopen, Request

sys.stdout.reconfigure(encoding='utf-8')

WC_KEY    = os.environ.get('WC_KEY',    'ck_c566b213178cba2f87412909fd7fb60dc752df80')
WC_SECRET = os.environ.get('WC_SECRET', 'cs_03523d8e3ff2c454acf1b76fa37483570de32ef4')
WC_BASE   = 'https://grizzlyherb.co/wp-json/wc/v3'
JDGM_TOKEN = os.environ.get('JDGM_TOKEN', '')  # Judge.me Public Token (optional)
JDGM_DOMAIN = 'grizzlyherb.com'

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

STAR_PATH = 'M8 0.5l2.12 4.3 4.74.69-3.43 3.34.81 4.73L8 11.27l-4.24 2.29.81-4.73L1.14 5.49l4.74-.69z'


def wc_get(path):
    sep = '&' if '?' in path else '?'
    url = f'{WC_BASE}{path}{sep}consumer_key={WC_KEY}&consumer_secret={WC_SECRET}'
    req = Request(url, headers={'User-Agent': 'WooCommerce/1.0'})
    try:
        with urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'  WC API error {path}: {e}', flush=True)
        return None


def jdgm_get(pid):
    """Fetch live review count from Judge.me API if token is set."""
    if not JDGM_TOKEN:
        return None, None
    url = (f'https://judge.me/api/v1/reviews?api_token={JDGM_TOKEN}'
           f'&shop_domain={JDGM_DOMAIN}&product_id={pid}&per_page=1')
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        cnt = data.get('total_results', 0)
        avg = data.get('rating', 0)
        return float(avg or 0), int(cnt or 0)
    except Exception as e:
        print(f'  Judge.me API error pid={pid}: {e}', flush=True)
        return None, None


def extract_jdgm_meta(meta_data):
    """Read cached Judge.me review count/avg from WC product meta."""
    count, avg = None, None
    for m in meta_data:
        if m['key'] == '_judgeme_widget_review_widget':
            v = m['value']
            html = v.get('widget', '') if isinstance(v, dict) else str(v)
            cnt_m = re.search(r"data-number-of-reviews=[\"'](\d+)[\"']", html)
            avg_m = re.search(r"data-average-rating=[\"']([\d.]+)[\"']", html)
            if cnt_m:
                count = int(cnt_m.group(1))
            if avg_m:
                avg = float(avg_m.group(1))
            break
    return avg, count


def stars_html(avg, cnt):
    n = max(0, min(5, round(float(avg or 0))))
    svgs = ''.join(
        f'<svg viewBox="0 0 16 16" fill="{"#f8b300" if i < n else "#e8e6e3"}"><path d="{STAR_PATH}"/></svg>'
        for i in range(5)
    )
    label = f'({cnt} Reviews)' if cnt else '(No Reviews)'
    return (
        f'<div class="gh-products__card-stars">\n'
        f'            {svgs}'
        f'<span class="gh-products__card-reviews">{label}</span>\n'
        f'          </div>'
    )


def collect_pids():
    pids = set()
    for path in PAGES:
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()
        for m in re.finditer(r'data-product-id="(\d+)"', html):
            pids.add(m.group(1))
    return sorted(pids)


def apply(path, ratings):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    updated = 0
    for pid, (avg, cnt) in ratings.items():
        card_start = html.find(f'data-product-id="{pid}"')
        if card_start == -1:
            continue
        stars_start = html.find('<div class="gh-products__card-stars">', card_start)
        if stars_start == -1:
            continue
        stars_end = html.find('</div>', stars_start) + len('</div>')
        html = html[:stars_start] + stars_html(avg, cnt) + html[stars_end:]
        updated += 1
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'  -> Updated {updated}/{len(ratings)} cards in {path}', flush=True)


def main():
    source = 'Judge.me live API' if JDGM_TOKEN else 'Judge.me WC meta (cached)'
    print(f'=== Review Sync [{source}] ===', flush=True)

    pids = collect_pids()
    print(f'Products: {pids}', flush=True)

    # Fetch all products in one API call
    ids_param = ','.join(pids)
    products = wc_get(f'/products?include={ids_param}&per_page=20') or []
    prod_map = {str(p['id']): p for p in products}

    ratings = {}
    for pid in pids:
        p = prod_map.get(pid)
        if not p:
            ratings[pid] = (0, 0)
            continue

        name = p['name'].split('|')[0].strip()[:22]

        # 1. Try Judge.me live API (if token set)
        avg, cnt = jdgm_get(pid)

        # 2. Fall back to cached Judge.me meta in WC
        if avg is None:
            avg, cnt = extract_jdgm_meta(p.get('meta_data', []))

        # 3. Fall back to WC native counts
        if avg is None:
            avg = float(p.get('average_rating') or 0)
            cnt = int(p.get('rating_count') or 0)
            src = 'WC native'
        else:
            src = 'JdgM meta' if not JDGM_TOKEN else 'JdgM API'

        ratings[pid] = (avg or 0, cnt or 0)
        print(f'  {pid}  {avg:.2f}★  {cnt} reviews  {name}  [{src}]', flush=True)

    print('\nUpdating pages...', flush=True)
    for path in PAGES:
        if os.path.exists(path):
            apply(path, ratings)
        else:
            print(f'  SKIP {path}', flush=True)

    print('Done.', flush=True)


if __name__ == '__main__':
    main()
