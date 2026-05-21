"""
sync_reviews.py
===============
Scrapes review count from each product's grizzlyherb.co page (most accurate).
Falls back to WooCommerce API for average rating.
Updates star SVGs and review count across rb/bb/bc pages.
"""
import os, re, json, sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

sys.stdout.reconfigure(encoding='utf-8')

WC_KEY    = os.environ.get('WC_KEY',    'ck_c566b213178cba2f87412909fd7fb60dc752df80')
WC_SECRET = os.environ.get('WC_SECRET', 'cs_03523d8e3ff2c454acf1b76fa37483570de32ef4')
WC_BASE   = 'https://grizzlyherb.co/wp-json/wc/v3'

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

STAR_PATH = 'M8 0.5l2.12 4.3 4.74.69-3.43 3.34.81 4.73L8 11.27l-4.24 2.29.81-4.73L1.14 5.49l4.74-.69z'


def fetch_html(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        with urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'  fetch error {url}: {e}', flush=True)
        return ''


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


def scrape_product_page(url):
    """Return (avg_rating, review_count) from the product page HTML."""
    html = fetch_html(url)
    if not html:
        return None, None

    # Review count: "30 reviews for" pattern
    cnt_match = re.search(r'(\d+)\s+reviews?\s+for\b', html, re.IGNORECASE)
    cnt = int(cnt_match.group(1)) if cnt_match else 0

    # Avg rating from JSON-LD structured data
    avg_match = re.search(r'"ratingValue"\s*:\s*"([\d.]+)"', html)
    avg = float(avg_match.group(1)) if avg_match else 0.0

    return avg, cnt


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


def collect_pid_urls():
    """Read all pid->url mappings from the HTML pages."""
    pid_url = {}
    for path in PAGES:
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()
        for m in re.finditer(
            r'data-product-id="(\d+)"[^>]*?data-product-url="([^"]+)"',
            html, re.DOTALL
        ):
            pid_url[m.group(1)] = m.group(2)
        # also reverse order
        for m in re.finditer(
            r'data-product-url="([^"]+)"[^>]*?data-product-id="(\d+)"',
            html, re.DOTALL
        ):
            pid_url[m.group(2)] = m.group(1)
    return pid_url


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
    print('=== Review Sync (product page scrape) ===', flush=True)

    pid_url = collect_pid_urls()
    print(f'Found {len(pid_url)} products with URLs', flush=True)

    ratings = {}
    for pid, url in sorted(pid_url.items()):
        avg, cnt = scrape_product_page(url)
        if avg is not None:
            ratings[pid] = (avg, cnt)
            print(f'  {pid}  {avg:.2f}★  {cnt} reviews  {url.split("/")[-2]}', flush=True)
        else:
            # Fallback to WC API
            p = wc_get(f'/products/{pid}')
            if p:
                avg = float(p.get('average_rating') or 0)
                cnt = int(p.get('rating_count') or 0)
                ratings[pid] = (avg, cnt)
                print(f'  {pid}  {avg:.2f}★  {cnt} reviews  (WC API fallback)', flush=True)
            else:
                ratings[pid] = (0, 0)
                print(f'  {pid}  no data', flush=True)

    print('\nUpdating pages...', flush=True)
    for path in PAGES:
        if os.path.exists(path):
            apply(path, ratings)
        else:
            print(f'  SKIP {path}', flush=True)

    print('Done.', flush=True)


if __name__ == '__main__':
    main()
