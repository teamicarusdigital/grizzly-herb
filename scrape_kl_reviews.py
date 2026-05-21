"""
scrape_kl_reviews.py
====================
Uses Playwright (headless Chromium) to render each WooCommerce product page
and extract the live Klaviyo Reviews count from:
  <div class="kl_reviews__summary__stars__count">53 reviews</div>

Writes kl-review-counts.json, which sync_reviews.py reads as its primary
source on every run (no API key needed, works with any reviews plugin).

Run locally:
  pip install playwright
  playwright install chromium --with-deps
  python scrape_kl_reviews.py

In GitHub Actions this is triggered by review-scrape.yml weekly.
"""
import os, re, json, sys
from datetime import datetime, timezone
from urllib.request import urlopen, Request

sys.stdout.reconfigure(encoding='utf-8')

WC_KEY    = os.environ.get('WC_KEY',    'ck_c566b213178cba2f87412909fd7fb60dc752df80')
WC_SECRET = os.environ.get('WC_SECRET', 'cs_03523d8e3ff2c454acf1b76fa37483570de32ef4')
WC_BASE   = 'https://grizzlyherb.co/wp-json/wc/v3'
OUTPUT    = 'kl-review-counts.json'

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]


def wc_get(path):
    sep = '&' if '?' in path else '?'
    url = f'{WC_BASE}{path}{sep}consumer_key={WC_KEY}&consumer_secret={WC_SECRET}'
    req = Request(url, headers={'User-Agent': 'WooCommerce/1.0'})
    try:
        with urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f'  WC API error: {e}', flush=True)
        return None


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


def scrape_all(pid_to_url):
    from playwright.sync_api import sync_playwright

    results = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
        )
        ctx = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            viewport={'width': 1280, 'height': 800},
        )

        for pid, url in pid_to_url.items():
            page = ctx.new_page()
            cnt, avg = 0, 0.0
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=40000)

                # Wait up to 12 seconds for the kl_reviews widget to render
                try:
                    page.wait_for_selector(
                        '.kl_reviews__summary__stars__count', timeout=12000
                    )
                except Exception:
                    print(f'  {pid}: widget timeout — will use 0', flush=True)

                # Count
                el = page.query_selector('.kl_reviews__summary__stars__count')
                if el:
                    m = re.search(r'(\d+)', el.inner_text())
                    if m:
                        cnt = int(m.group(1))

                # Average — try several selectors used by Klaviyo Reviews
                for sel in [
                    '.kl_reviews__summary__average',
                    '.kl_reviews__summary__rating',
                    '[data-average-rating]',
                    '[data-rating]',
                ]:
                    el2 = page.query_selector(sel)
                    if el2:
                        # Try attribute first
                        for attr in ('data-average-rating', 'data-rating'):
                            val = el2.get_attribute(attr)
                            if val:
                                try:
                                    avg = float(val)
                                    break
                                except ValueError:
                                    pass
                        # Fall back to text content
                        if avg == 0:
                            m2 = re.search(r'([\d]+\.[\d]+|[\d]+)', el2.inner_text())
                            if m2:
                                avg = float(m2.group(1))
                        if avg:
                            break

                slug = url.rstrip('/').split('/')[-1]
                print(f'  {pid}  {avg:.1f}*  {cnt} reviews  {slug}', flush=True)

            except Exception as e:
                print(f'  {pid}: ERROR {e}', flush=True)
            finally:
                page.close()

            results[pid] = {'avg': round(avg, 2), 'cnt': cnt}

        browser.close()

    return results


def main():
    print('=== Klaviyo Reviews Scraper (Playwright) ===', flush=True)

    pids = collect_pids()
    print(f'Products found: {pids}', flush=True)

    products = wc_get(f'/products?include={",".join(pids)}&per_page=20') or []
    pid_to_url = {str(p['id']): p['permalink'] for p in products if p.get('permalink')}
    print(f'Permalinks resolved: {len(pid_to_url)}/{len(pids)}', flush=True)

    results = scrape_all(pid_to_url)

    data = {
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'counts': results,
    }
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f'\nWrote {OUTPUT} ({len(results)} products)', flush=True)
    print('Done.', flush=True)


if __name__ == '__main__':
    main()
