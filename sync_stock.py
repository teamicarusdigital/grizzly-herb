"""
sync_stock.py
=============
Fetches per-variation stock from WooCommerce REST API and updates
data-variants JSON in all landing pages so out-of-stock variants
show correctly without a page rebuild.

Run before every deploy:
    python sync_stock.py && vercel deploy --prod

Setup: create a Read-only REST API key in WooCommerce:
    WooCommerce > Settings > Advanced > REST API > Add key
    Set permissions to "Read"

Then put your credentials here (or in a .env file):
"""

import os, re, json, base64
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# ── Credentials ──────────────────────────────────────────────────────────────
# Paste your WooCommerce REST API keys here, OR set as environment variables:
#   set WC_KEY=ck_xxx   /   set WC_SECRET=cs_xxx
WC_KEY    = os.environ.get('WC_KEY',    'ck_PASTE_YOUR_KEY_HERE')
WC_SECRET = os.environ.get('WC_SECRET', 'cs_PASTE_YOUR_SECRET_HERE')
WC_BASE   = 'https://grizzlyherb.co/wp-json/wc/v3'

# ── Pages to update ───────────────────────────────────────────────────────────
FLOWER_PAGES = [
    r'pages\premium-collection-rb\index.html',
    r'pages\premium-collection-bb\index.html',
    r'pages\premium-collection-bc\index.html',
    r'pages\premium-collection-hsh\index.html',
]
VAPES_PAGE = r'pages\thca-vapes\index.html'


def wc_get(path):
    token = base64.b64encode(f'{WC_KEY}:{WC_SECRET}'.encode()).decode()
    req = Request(f'{WC_BASE}{path}', headers={'Authorization': f'Basic {token}'})
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f'  HTTP {e.code} for {path}')
        return None


def get_variation_stock(product_id):
    """Returns {variation_id: bool} — True = in stock."""
    result = {}
    page = 1
    while True:
        data = wc_get(f'/products/{product_id}/variations?per_page=100&page={page}')
        if not data:
            break
        for v in data:
            result[v['id']] = (v.get('stock_status', 'instock') == 'instock')
        if len(data) < 100:
            break
        page += 1
    return result


def get_product_stock(product_id):
    """Returns True if the simple product is in stock."""
    data = wc_get(f'/products/{product_id}')
    if not data:
        return True
    return data.get('stock_status', 'instock') == 'instock'


# ── Update flower pages ───────────────────────────────────────────────────────
def update_flower_pages():
    # Collect all unique product IDs across all flower pages
    all_pids = set()
    page_data = {}

    for path in FLOWER_PAGES:
        if not os.path.exists(path):
            print(f'  SKIP (not found): {path}')
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()
        cards = re.findall(
            r'(data-product-id="(\d+)"[^>]*data-variants=\'([^\']+)\')',
            html
        )
        page_data[path] = {'html': html, 'cards': cards}
        for _, pid, _ in cards:
            all_pids.add(int(pid))

    print(f'\nFetching variation stock for {len(all_pids)} products...')
    variation_stock = {}   # {pid: {vid: bool}}
    for pid in sorted(all_pids):
        stock = get_variation_stock(pid)
        variation_stock[pid] = stock
        in_ct  = sum(1 for v in stock.values() if v)
        out_ct = sum(1 for v in stock.values() if not v)
        print(f'  pid {pid}: {in_ct} in-stock, {out_ct} out-of-stock')

    # Apply updates to each page
    for path, info in page_data.items():
        html = info['html']
        changes = 0
        for full_attr, pid, varjson in info['cards']:
            pid_int = int(pid)
            variants = json.loads(varjson)
            stock_map = variation_stock.get(pid_int, {})
            updated = False
            for v in variants:
                vid = v['vid']
                in_stock = stock_map.get(vid, True)  # default True if API had no data
                if v.get('inStock') != in_stock:
                    v['inStock'] = in_stock
                    updated = True
                elif 'inStock' not in v:
                    v['inStock'] = in_stock
                    updated = True

            if updated:
                new_attr = full_attr.replace(
                    f"data-variants='{varjson}'",
                    f"data-variants='{json.dumps(variants, separators=(',', ':'))}'"
                )
                html = html.replace(full_attr, new_attr, 1)
                changes += 1

        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  Updated {path}: {changes} cards changed')


# ── Update vapes page ─────────────────────────────────────────────────────────
def update_vapes_page():
    if not os.path.exists(VAPES_PAGE):
        print(f'  SKIP (not found): {VAPES_PAGE}')
        return

    with open(VAPES_PAGE, encoding='utf-8') as f:
        html = f.read()

    # Extract CARTRIDGES array bounds
    cart_start = html.find('var CARTRIDGES')
    cart_end   = html.find('];', cart_start) + 2
    cart_block = html[cart_start:cart_end]

    # Find all pids in the CARTRIDGES array
    pids = re.findall(r"pid:'(\d+)'", cart_block)
    print(f'\nFetching stock for {len(pids)} vape products...')

    changes = 0
    new_block = cart_block
    for pid in pids:
        in_stock = get_product_stock(int(pid))
        # Replace inStock field for this pid
        old_pat = re.search(
            r"(pid:'" + re.escape(pid) + r"'[^}]*?inStock:)(true|false)",
            new_block
        )
        if old_pat:
            new_val = 'true' if in_stock else 'false'
            if old_pat.group(2) != new_val:
                new_block = new_block[:old_pat.start(1)] + old_pat.group(1) + new_val + new_block[old_pat.end(2):]
                changes += 1
                print(f'  pid {pid}: {"in stock" if in_stock else "OUT OF STOCK"}')

    if changes:
        html = html[:cart_start] + new_block + html[cart_end:]
        with open(VAPES_PAGE, 'w', encoding='utf-8') as f:
            f.write(html)
    print(f'  Updated vapes page: {changes} products changed')


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if 'PASTE_YOUR_KEY' in WC_KEY:
        print('ERROR: Set WC_KEY and WC_SECRET at the top of this script (or as env vars).')
        print('Get keys from: WooCommerce > Settings > Advanced > REST API > Add key')
        exit(1)

    print('=== Grizzly Herb Stock Sync ===')
    update_flower_pages()
    update_vapes_page()
    print('\nDone. Run: vercel deploy --prod')
