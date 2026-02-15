# Grizzly Herb Landing Page — Agent Instructions

## Mission
Recreate the Grizzly Herb cannabis dispensary landing page as a **pixel-perfect 1:1 copy** of the provided Figma section screenshots. Every agent working on this project MUST treat the screenshot PNGs as the **single source of truth**. No guessing, no "close enough."

## Critical Rules — READ BEFORE WRITING ANY CODE

### 1. Pixel-Perfect Means Pixel-Perfect
- Match EXACT font sizes, weights, line-heights, letter-spacing from the screenshots
- Match EXACT spacing (padding, margin, gap) — measure relative to surrounding elements
- Match EXACT colors — use an eyedropper approach on the screenshot, not assumptions
- Match EXACT border-radius values — square corners vs rounded vs pill shapes matter
- Match EXACT element ordering, alignment, and positioning
- If a screenshot shows 12px of space between two elements, do NOT write 16px

### 2. Two Breakpoints: Mobile + Desktop
- Every section has TWO screenshots: `section-N-desktop.png` and `section-N-mobile.png`
- Write mobile-first CSS (base styles = mobile)
- Single breakpoint: `@media (min-width: 768px)` for desktop
- Both versions must be 1:1 matches to their respective screenshots

### 3. Measure Everything From Screenshots
Before writing CSS for any element, determine from the screenshot:
- Font: family, size, weight, style (italic?), line-height, color, letter-spacing
- Spacing: padding (top/right/bottom/left), margin, gap
- Dimensions: width, height, min/max constraints
- Borders: width, style, color, radius
- Background: color, gradient direction/stops, image positioning
- Layout: flex vs grid, direction, alignment, wrapping, gap
- Effects: shadows, opacity, transforms

### 4. Output Format
Each agent must output a **complete code block** containing:
```
<!-- SECTION N: Section Name -->
<!-- CSS -->
<style>
/* Mobile-first base styles */
.gh-sectionname { ... }

@media (min-width: 768px) {
  /* Desktop overrides */
  .gh-sectionname { ... }
}
</style>

<!-- HTML -->
<section class="gh-sectionname">
  ...
</section>
```

### 5. Do NOT Include
- JavaScript (handled separately)
- Styles for other sections
- Generic resets or root styles (handled by Section 0)
- Comments like "adjust as needed" or "approximately" — be exact

## Technical Standards

### CSS Architecture
- All classes prefixed with `gh-` and scoped under `.gh-root`
- BEM-like naming: `.gh-section__element--modifier`
- Mobile-first: base styles are mobile, desktop uses `@media (min-width: 768px)`
- No `!important` unless absolutely necessary
- Use `px` for all sizes (not rem/em) to ensure pixel-perfect rendering
- Prefer `flex` for layout; use `grid` when the screenshot clearly shows a grid

### Fonts
- Primary: `'Poppins', sans-serif` (weights: 300, 400, 500, 600, 700, 800)
- Accent/Cursive: `'Outfit', sans-serif` (weight: 700) — used for italic accent text
- Google Fonts link: `https://fonts.googleapis.com/css2?family=Poppins:wght@300``;400;500;600;700;800&family=Outfit:wght@700&display=swap`

### Color Palette (extract exact hex from screenshots, but these are the known brand colors)
- Primary Green: `#2d5016`
- Secondary Green: `#4a7c2c`
- Green Hover: `#3d6b12`
- Orange CTA: `#d97835`
- Orange Hover: `#c06a2a`
- Gold Accent: `#c9a961`
- Star Yellow: `#f8b300`
- Cream Background: `#f8f6f3`
- Light Gray: `#e8e6e3`
- Dark Text: `#1f1f1f`
- Body Text: `#3a3a3a`
- White: `#ffffff`
- Dark Section BG: `#1f1f1f`
- Red/Orange Banner: `#e85d35`

### Images
- All image paths use absolute URLs: `/images/filename.ext`
- Use `loading="lazy"` on all images below the fold
- Use descriptive `alt` text
- For placeholder images not yet provided, use: `<div class="gh-img-placeholder" style="width:Wpx;height:Hpx;background:``#e8e6e3``;border-radius:Rpx;"></div>`
- When an image is needed but not available, the agent MUST list it in the output as: `<!-- NEEDS IMAGE: description, approximate dimensions WxH -->`

### HTML Structure
- Single root: `<div class="gh-root">`
- Semantic elements: `<section>`, `<nav>`, `<footer>`, `<header>`, `<button>`, `<a>`
- All CTA buttons/links should use `href="``#products``"` as default target
- Buttons use `<button>` for actions, `<a>` for navigation/links

### Responsive Behavior
- Max content width: `1440px` (centered with `margin: 0 auto`)
- Mobile padding: `16px` horizontal
- Desktop padding: `160px` horizontal (or as shown in screenshot)
- Images: `max-width: 100%; display: block;`
- No horizontal scroll on any breakpoint

## Section Index
| # | Section Name | Description |
| --- | --- | --- |
| 0 | Hero | Top banner + Navigation + Hero content with background image |
| 1 | Explore | "Explore Our Handpicked Strains" — info card + image |
| 2 | Products | "Find Your Perfect Strain" — filter tabs + product grid |
| 3 | Reviews 1 | "From Buyers Who Know" — review carousel |
| 4 | Moments | "Find Your Perfect Strain for Every Moment" — image + feature card |
| 5 | Sample Pack | "Try It Once. Decide After." — dark section with product cards |
| 6 | Compare | "Why We Stand Above the Competition" — comparison table |
| 7 | Types | "Buy Weed According to Cannabis Type" — type cards grid |
| 8 | Why Choose | "Why Choose Grizzly Herb" — feature columns |
| 9 | Reviews 2 | Second review carousel |
| 10 | FAQ | Accordion FAQ section |
| 11 | Footer | Logo, links, email signup, payments, badges |

## Existing Assets (in /images/ directory)
- `grizzly-herb-logo.png` — Brand logo
- `hero-bg.jpg` — Hero background image (man with cannabis)
- `customer-avatar-1.png` through `customer-avatar-4.png`
- `curated-selection-icon.png`, `for-those-who-know-icon.png`
- `handpicked-strains-lifestyle-photo.png`
- `target-crosshair-icon-representing-strain-matching.png`
- `hand-picking-icon-representing-handpicked-quality-strains.png`
- `spectrum-range-icon-representing-indica-to-sativa-range.png`
- `cannabis-product-package-sample-bag-1.png`, `...bag-2.png`
- `green-indica-cannabis-leaf-illustration.png`
- `green-hybrid-cannabis-leaf-illustration.png`
- `green-sativa-cannabis-leaf-illustration.png`
- `full-spectrum-cannabis-extract-leaf-illustration.png`
- `shipping-truck-icon-for-free-express-delivery.png`
- `price-tag-icon-representing-best-price-guarantee.png`
- `quality-badge-icon-representing-highest-quality-standards.png`
- `purple-kush-cannabis-flower.jpg` (and other product images)
- `peanut-butter-breath-cannabis-flower.jpg`
- `vanilla-kush-cannabis-flower.jpg`
- `ghost-breath-cannabis-flower.jpg`
- `golden-oreoz-cannabis-flower.jpg`
- `key-lime-haze-cannabis-flower.jpg`
- `grape-diesel-cannabis-flower.jpg`
- `grizzly-herb-diamond-edition-50-pack-pre-rolls.jpg`
- `cannabis-buds-arranged-artistically.jpg`
- `dark-section-bg.png`
- `moment-icon1.png`, `moment-icon2.png`, `moment-icon3.png`

## Deployment
- Repo: `github.com/teamicarusdigital/grizzly-herb`
- Deploy: `vercel --prod --yes` from `C:\Users\Srrok\Documents\grizzly-herb-deploy`
- URL: `https://app.grizzlyherb.us`
- Custom routes: `/pages/perfect` and `/pages/premium-collection-hsh` (via vercel.json rewrites)

## Tracklution Pixel (REQUIRED on ALL pages)

Every page in this project MUST include the Tracklution tracking pixel in `<head>` before `</head>`:

```html
<!-- Tracklution Pixel -->
<script>
    !function(t,l,r,o,c,k,s)
    {if(t.tlq)return;c=t.tlq=function(){c.callMethod?
        c.callMethod(arguments):c.queue.push(arguments)};
        if(!t._tlq)t._tlq=c;c.push=c;c.loaded=!0;c.version='1.0';c.src=o;
        c.queue=[];k=l.createElement(r);k.async=!0;c.pd = false;c.tools = null;
        k.src=o;s=l.getElementsByTagName(r)[0];
        s.parentNode.insertBefore(k,s);k.onerror=function(){
        o='https://main-47660.trlution.com/js/script-dynamic.js?version=1771121839100';
        t._tlq.src=o;k=l.createElement(r);k.async=!0;k.src=o;
        s.parentNode.insertBefore(k, s)
        }}(window,document,'script',
        'https://tralut.grizzlyherb.com/js/script-dynamic.js?version=1771121839100')

    tlq('init', 'LS-25654158-0');
    tlq('track', 'PageView');
    tlq('track', 'ViewContent', {content_name: 'PAGE_NAME_HERE'});
</script>
```

### Required Events
- **PageView** — fires on every page load (included in pixel snippet above)
- **ViewContent** — fires on every page load with `content_name` set to the page name
- **AddToCart** — fires on every "Add to Stash" / add-to-cart action:
  ```js
  if (typeof tlq === 'function') {
    tlq('track', 'AddToCart', {
      content_name: 'Product Name (Variant)',
      content_ids: [variationId],
      value: price,
      currency: 'CAD'
    });
  }
  ```

## Quality Checklist (every agent must verify)
- [ ] Mobile screenshot matched 1:1
- [ ] Desktop screenshot matched 1:1
- [ ] All fonts, sizes, weights, colors extracted from screenshot
- [ ] All spacing (padding, margin, gap) measured from screenshot
- [ ] All border-radius values matched
- [ ] All images listed (available or marked as NEEDS IMAGE)
- [ ] No hardcoded widths that break responsiveness
- [ ] Semantic HTML used
- [ ] Class naming follows gh- prefix + BEM convention
