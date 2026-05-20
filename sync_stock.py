"""
sync_stock.py — Grizzly Herb stock sync
Fetches per-variation stock from WooCommerce REST API and updates
data-variants JSON in all landing pages.

Auto-runs via GitHub Actions every 4 hours.
Manual run: python sync_stock.py
"""

import os, re, json, base64, sys
from urllib.request import urlopen, Request
from urllib.error import HTTPError

WC_KEY    = os.environ.get('WC_KEY',    'ck_c566b213178cba2f87412909fd7fb60dc752df80')
WC_SECRET = os.environ.get('WC_SECRET', 'cs_03523d8e3ff2c454acf1b76fa37483570de32ef4')
WC_BASE   = 'https://grizzlyherb.co/wp-json/wc/v3'

FLOWER_PAGES = [
    os.path.join('pages', 'premium-collection-rb', 'index.html'),
    os.path.join('pages', 'premium-collection-bb', 'index.html'),
    os.path.join('pages', 'premium-collection-bc', 'index.html'),
    os.path.join('pages', 'premium-collection-hsh', 'index.html'),
]
VAPES_PAGE = os.path.join('pages', 'thca-vapes', 'index.html')


def wc_get(path):
    token = base64.b64encode(f'{WC_KEY}:{WC_SECRET}'.encode()).decode()
    req = Request(f'{WC_BASE}{path}', headers={'Authorization': f'Basic {token}'})
    try:
        with urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except HTTPError as e:
        print(f'  HTTP {e.code} for {path}', flush=True)
        return None
    except Exception as e:
        print(f'  Error for {path}: {e}', flush=True)
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


def update_flower_pages():
    all_pids = set()
    page_data = {}

    for path in FLOWER_PAGES:
        if not os.path.exists(path):
            print(f'  SKIP (not found): {path}', flush=True)
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

    print(f'Fetching variation stock for {len(all_pids)} products...', flush=True)
    variation_stock = {}
    for pid in sorted(all_pids):
        stock = get_variation_stock(pid)
        variation_stock[pid] = stock
        in_ct  = sum(1 for v in stock.values() if v)
        out_ct = sum(1 for v in stock.values() if not v)
        print(f'  pid {pid}: {in_ct} in-stock, {out_ct} out-of-stock', flush=True)

    changed_pages = 0
    for path, info in page_data.items():
        html = info['html']
        changes = 0
        for full_attr, pid, varjson in info['cards']:
            pid_int = int(pid)
            variants = json.loads(varjson)
            stock_map = variation_stock.get(pid_int, {})
            updated = False
            for v in variants:
                in_stock = stock_map.get(v['vid'], True)
                if v.get('inStock') != in_stock:
                    v['inStock'] = in_stock
                    updated = True
                elif 'inStock' not in v:
                    v['inStock'] = in_stock
                    updated = True
            if updated:
                new_json = json.dumps(variants, separators=(',', ':'))
                new_attr = full_attr.replace(f"data-variants='{varjson}'", f"data-variants='{new_json}'")
                html = html.replace(full_attr, new_attr, 1)
                changes += 1
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        if changes:
            changed_pages += 1
            print(f'  {path}: {changes} cards updated', flush=True)
        else:
            print(f'  {path}: no changes', flush=True)
    return changed_pages


def update_vapes_page():
    if not os.path.exists(VAPES_PAGE):
        print(f'  SKIP (not found): {VAPES_PAGE}', flush=True)
        return 0

    with open(VAPES_PAGE, encoding='utf-8') as f:
        html = f.read()

    cart_start = html.find('var CARTRIDGES')
    cart_end   = html.find('];', cart_start) + 2
    cart_block = html[cart_start:cart_end]
    pids = re.findall(r"pid:'(\d+)'", cart_block)

    print(f'Fetching stock for {len(pids)} vape products...', flush=True)
    changes = 0
    new_block = cart_block
    for pid in pids:
        in_stock = get_product_stock(int(pid))
        m = re.search(r"(pid:'" + re.escape(pid) + r"'[^}]*?inStock:)(true|false)", new_block)
        if m:
            new_val = 'true' if in_stock else 'false'
            if m.group(2) != new_val:
                new_block = new_block[:m.start(1)] + m.group(1) + new_val + new_block[m.end(2):]
                changes += 1
                print(f'  pid {pid}: {"in stock" if in_stock else "OUT OF STOCK"}', flush=True)

    if changes:
        html = html[:cart_start] + new_block + html[cart_end:]
        with open(VAPES_PAGE, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'  vapes: {changes} products updated', flush=True)
    else:
        print(f'  vapes: no changes', flush=True)
    return changes


if __name__ == '__main__':
    print('=== Grizzly Herb Stock Sync ===', flush=True)
    flower_changes = update_flower_pages()
    vape_changes   = update_vapes_page()
    total = flower_changes + vape_changes
    print(f'\nDone. {total} pages had stock changes.', flush=True)
    sys.exit(0)
