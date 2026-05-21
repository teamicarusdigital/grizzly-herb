"""
sync_bundle_products.py — Grizzly Herb bundle products sync
Fetches the products available in WooCommerce bundle 131822 and writes
bundle-products.json so the landing page picks up adds/removals automatically.

Auto-runs via GitHub Actions every 4 hours (alongside stock sync).
Manual run: python sync_bundle_products.py
"""

import os, re, json, sys
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError

WC_KEY    = os.environ.get('WC_KEY',    'ck_c566b213178cba2f87412909fd7fb60dc752df80')
WC_SECRET = os.environ.get('WC_SECRET', 'cs_03523d8e3ff2c454acf1b76fa37483570de32ef4')
WC_BASE   = 'https://grizzlyherb.co/wp-json/wc/v3'
BUNDLE_ID = 131822
OUT_FILE  = 'bundle-products.json'
NEW_DAYS  = 45   # badge a product "New Strain" if created within this many days


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
        print(f'  Error for {path}: {e}', flush=True)
        return None


def extract_product_ids(bundle):
    """
    Pull the set of product IDs out of whatever structure the bundle uses.
    Handles WC Bundles fixed items, WC Bundles variable items, and
    WooCommerce Mix & Match.
    """
    pids = set()

    # ── WC Bundles plugin ────────────────────────────────────────────────────
    items = bundle.get('bundled_items') or bundle.get('bundle_items') or []
    for item in items:
        pid = item.get('product_id') or item.get('product', {}).get('id', 0)
        if pid and int(pid) != BUNDLE_ID:
            pids.add(int(pid))

    # ── WC Mix & Match plugin ────────────────────────────────────────────────
    contents = bundle.get('mnm_contents') or bundle.get('mix_match_contents') or []
    for item in contents:
        pid = item.get('product_id') or item.get('id', 0)
        if pid:
            pids.add(int(pid))

    # ── Flat product_ids array (some plugins use this) ───────────────────────
    for pid in (bundle.get('product_ids') or []):
        pids.add(int(pid))

    return pids


def find_oz_variation(variations):
    """
    Find the 1oz (28g) variation. Strategy:
    1. Attribute option matches '28g', '1 oz', 'oz (28g)', or starts with 'oz' alone
    2. Fallback: lowest-priced in-stock variation (1oz is cheapest)
    3. Fallback: first variation
    """
    oz_patterns = re.compile(r'\b(oz\s*\(28|28\s*g|1\s*oz|^oz$)', re.IGNORECASE)

    # Strategy 1: attribute matching
    for v in variations:
        for attr in (v.get('attributes') or []):
            opt = str(attr.get('option', '') or attr.get('name', ''))
            if oz_patterns.search(opt):
                return v

    # Strategy 2: lowest-priced in-stock
    in_stock = [v for v in variations if v.get('stock_status', 'instock') == 'instock']
    if in_stock:
        return min(in_stock, key=lambda v: float(v.get('price') or v.get('regular_price') or 999))

    # Strategy 3: first variation
    return variations[0] if variations else None


def get_meta(product):
    """
    Try to build "Indica · AAAA+" style meta from product attributes or tags.
    """
    parts = []

    # Check attributes for strain type and quality grade
    for attr in (product.get('attributes') or []):
        name = (attr.get('name') or '').lower()
        opts = [str(o) for o in (attr.get('options') or [])]
        if not opts:
            continue
        val = opts[0]
        if any(k in name for k in ('strain', 'type', 'category')):
            parts.append(val)
        elif any(k in name for k in ('grade', 'quality', 'class', 'aaaa', 'tier')):
            parts.append(val)

    if parts:
        return ' · '.join(parts)

    # Fallback: look for AAAA/AAA in tags
    for tag in (product.get('tags') or []):
        t = tag.get('name', '')
        if re.search(r'AAAA?\+?', t):
            parts.append(t)
            break

    # Fallback: parse from product name
    m = re.search(r'\b(AAAA\+?|AAA\+?)\b', product.get('name', ''))
    if m and not parts:
        parts.append(m.group(1))

    return ' · '.join(parts) if parts else ''


def is_new(product):
    """True if product was created within NEW_DAYS days."""
    created_str = product.get('date_created', '')
    if not created_str:
        return False
    try:
        # WC returns ISO 8601 local time — treat as UTC
        created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created).days <= NEW_DAYS
    except Exception:
        return False


def fetch_product_entry(pid):
    """
    Fetch one product and its variations, return a bundle-products.json entry.
    Returns None if fetch fails or no usable variation found.
    """
    print(f'  Fetching pid {pid}...', flush=True)
    product = wc_get(f'/products/{pid}')
    if not product:
        print(f'    SKIP — could not fetch product', flush=True)
        return None

    raw_name = product.get('name', f'Product {pid}')
    # Clean pipe-delimited names like "Cherry Og | Smalls | Indica | Cannabis | AAA +"
    if '|' in raw_name:
        pipe_parts = [p.strip() for p in raw_name.split('|')]
        name = pipe_parts[0].strip()
        # Build meta from pipe parts: find type + grade, skip filler words
        _skip = {'smalls', 'cannabis', 'flower', 'bud', 'cannabis flower', 'indica dominant', 'sativa dominant'}
        _type, _grade = '', ''
        for p in pipe_parts[1:]:
            pl = p.strip().lower()
            if pl in _skip:
                continue
            if re.search(r'AAAA?\+?', p, re.IGNORECASE) and not _grade:
                _grade = re.sub(r'\s+', '', p.strip())  # "AAA +" → "AAA+"
            elif not _type and pl not in _skip:
                _type = p.strip()
        _pipe_meta = ' · '.join(x for x in [_type, _grade] if x)
    else:
        name = raw_name
        _pipe_meta = ''
    image = (product.get('images') or [{}])[0].get('src', '')
    avg_rating = float(product.get('average_rating') or 0)
    rating_ct  = int(product.get('rating_count') or 0)

    # Variations
    variations = []
    page = 1
    while True:
        batch = wc_get(f'/products/{pid}/variations?per_page=100&page={page}')
        if not batch:
            break
        variations.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    if not variations:
        # Simple product — use product-level price
        price = float(product.get('sale_price') or product.get('price') or 0)
        reg   = float(product.get('regular_price') or 0)
        in_stock = product.get('stock_status', 'instock') == 'instock'
        entry = {
            'pid':     pid,
            'vid':     pid,  # for simple products, vid = pid
            'name':    name,
            'meta':    _pipe_meta or get_meta(product),
            'price':   price,
            'regular': reg if reg > price else None,
            'image':   image,
            'inStock': in_stock,
            'rating':  avg_rating,
            'reviews': rating_ct,
            'isNew':   is_new(product),
        }
        if entry['regular'] is None:
            del entry['regular']
        print(f'    {name}: simple product ${price} ({"in" if in_stock else "OUT OF"} stock)', flush=True)
        return entry

    oz_var = find_oz_variation(variations)
    if not oz_var:
        print(f'    SKIP — no suitable variation found', flush=True)
        return None

    price    = float(oz_var.get('sale_price') or oz_var.get('price') or 0)
    reg      = float(oz_var.get('regular_price') or 0)
    in_stock = oz_var.get('stock_status', 'instock') == 'instock'
    vid      = int(oz_var['id'])

    print(f'    {name}: vid={vid} ${price} ({"in" if in_stock else "OUT OF"} stock)', flush=True)

    entry = {
        'pid':     pid,
        'vid':     vid,
        'name':    name,
        'meta':    _pipe_meta or get_meta(product),
        'price':   price,
        'image':   image,
        'inStock': in_stock,
        'rating':  avg_rating,
        'reviews': rating_ct,
        'isNew':   is_new(product),
    }
    if reg and reg > price:
        entry['regular'] = reg

    return entry


def main():
    print(f'=== Bundle Products Sync (bundle ID {BUNDLE_ID}) ===', flush=True)

    # ── Step 1: fetch bundle product ──────────────────────────────────────────
    print('Fetching bundle product from WC API...', flush=True)
    bundle = wc_get(f'/products/{BUNDLE_ID}')
    if not bundle:
        print('ERROR: Could not fetch bundle product. Aborting.', flush=True)
        sys.exit(1)

    print(f'  Bundle name: {bundle.get("name")}', flush=True)
    print(f'  Bundle type: {bundle.get("type")}', flush=True)

    # ── Step 2: extract product IDs ───────────────────────────────────────────
    pids = extract_product_ids(bundle)
    print(f'  Product IDs found in bundle: {sorted(pids) if pids else "NONE"}', flush=True)

    if not pids:
        print('\nWARNING: No product IDs extracted from bundle.', flush=True)
        print('Raw bundled_items keys:', list((bundle.get('bundled_items') or [{}])[0].keys()) if bundle.get('bundled_items') else 'bundled_items missing', flush=True)
        print('Aborting — existing bundle-products.json unchanged.', flush=True)
        sys.exit(0)  # exit 0 so GitHub Actions doesn't mark as failure

    # ── Step 3: fetch each product's details ──────────────────────────────────
    print(f'\nFetching details for {len(pids)} products...', flush=True)
    products = []
    for pid in sorted(pids):
        entry = fetch_product_entry(pid)
        if entry:
            products.append(entry)

    if not products:
        print('\nERROR: No products built. Aborting — existing JSON unchanged.', flush=True)
        sys.exit(0)

    # ── Step 4: write JSON ────────────────────────────────────────────────────
    out = {
        'updated':   datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'bundle_id': BUNDLE_ID,
        'products':  products,
    }
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)

    print(f'\nWrote {OUT_FILE} with {len(products)} products.', flush=True)
    sys.exit(0)


if __name__ == '__main__':
    main()
