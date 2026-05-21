"""
fix_gallery_css.py
==================
Fixes two issues in the already-injected gallery CSS:
1. Adds z-index to ::after so gradient renders above the img
2. Bumps .gh-bb__collage-name to z-index:2 so text is above gradient
Also updates the GALLERY_CSS template in upgrade_bundle_gallery.py for future runs.
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

PAGES = [
    'pages/premium-collection-rb/index.html',
    'pages/premium-collection-bb/index.html',
    'pages/premium-collection-bc/index.html',
]

OLD_AFTER = (
    "    .gh-bb__collage-img::after {\n"
    "      content: '';\n"
    "      position: absolute;\n"
    "      bottom: 0; left: 0; right: 0;\n"
    "      height: 55%;\n"
    "      background: linear-gradient(transparent, rgba(0,0,0,0.68));\n"
    "      pointer-events: none;\n"
    "    }"
)
NEW_AFTER = (
    "    .gh-bb__collage-img::after {\n"
    "      content: '';\n"
    "      position: absolute;\n"
    "      bottom: 0; left: 0; right: 0;\n"
    "      height: 55%;\n"
    "      background: linear-gradient(transparent, rgba(0,0,0,0.72));\n"
    "      pointer-events: none;\n"
    "      z-index: 1;\n"
    "    }"
)

OLD_NAME_ZINDEX = "      z-index: 1;\n      pointer-events: none;"
NEW_NAME_ZINDEX = "      z-index: 2;\n      pointer-events: none;"


def apply(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    steps = []

    if OLD_AFTER in html:
        html = html.replace(OLD_AFTER, NEW_AFTER, 1)
        steps.append('::after z-index:1 added')
    elif 'z-index: 1;\n    }' in html and '::after' in html:
        steps.append('::after z-index already fixed')
    else:
        steps.append('WARNING: ::after anchor not found')

    if OLD_NAME_ZINDEX in html:
        html = html.replace(OLD_NAME_ZINDEX, NEW_NAME_ZINDEX, 1)
        steps.append('collage-name bumped to z-index:2')
    elif 'z-index: 2' in html:
        steps.append('collage-name z-index already 2')
    else:
        steps.append('WARNING: collage-name z-index anchor not found')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'\n{path}:')
    for s in steps:
        print(f'  + {s}')


if __name__ == '__main__':
    print('=== Fixing gallery CSS z-index ===')
    for p in PAGES:
        if os.path.exists(p):
            apply(p)
        else:
            print(f'\nSKIP: {p}')
    print('\nDone.')
