---
name: DumHouse
description: Light, food-first ordering for one Hyderabad restaurant chain.
colors:
  paper: "#fffaf3"
  white: "#ffffff"
  ink: "#30251e"
  muted: "#716052"
  brand: "#c64a16"
  brand-ink: "#ffffff"
  line: "#e8dacf"
  soft: "#f6eee5"
  green: "#397640"
  brand-hover: "#a93b0e"
  focus: "#a63b0b"
  field: "#fffdf9"
  selected-surface: "#fff0df"
  placeholder-ink: "#87613c"
typography:
  display:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "clamp(25px, 3vw, 40px)"
    fontWeight: 800
    lineHeight: 1.17
    letterSpacing: "-0.03em"
  headline:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "23px"
    fontWeight: 750
    lineHeight: 1.25
    letterSpacing: "-0.03em"
  title:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "16px"
    fontWeight: 750
    lineHeight: 1.35
    letterSpacing: "-0.025em"
  body:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "14px"
    lineHeight: 1.6
  label:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "12px"
    fontWeight: 600
  button:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "13px"
    fontWeight: 750
rounded:
  field: "8px"
  control: "9px"
  category: "9px"
  surface: "14px"
  hero: "16px"
spacing:
  compact: "8px"
  small: "12px"
  medium: "18px"
  large: "22px"
  section: "32px"
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.brand-ink}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "11px 16px"
  button-secondary:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 16px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.muted}"
    rounded: "{rounded.control}"
    padding: "11px 16px"
  button-add:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.brand-ink}"
    rounded: "{rounded.control}"
    padding: "8px 12px"
  input:
    backgroundColor: "{colors.field}"
    textColor: "{colors.ink}"
    rounded: "{rounded.field}"
    padding: "11px 12px"
  bag-card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.surface}"
    padding: "22px"
---

# Design System: DumHouse

## Overview

**Creative North Star: "Light, food-first Hyderabad ordering"**

The user-approved light direction uses warm cream canvas, white cards, brown text, burnt-orange calls to action and bold Manrope. DumHouse remains a fictional single restaurant chain in Hyderabad, with a curated 70-dish menu and illustrative food imagery. The interface keeps its established ordering layout and real URL navigation.

**Key Characteristics:**
- Warm cream layers, brown text, burnt-orange actions and rounded food cards.
- Manrope throughout, with compact labels and prominent prices.
- Linked categories with counts, saved dishes, a dedicated bag and mobile bottom navigation.
- Staff-reported kitchen progress with explicit test-payment and illustration disclosures.

Source-derived from `frontend/app/storefront.tsx`, `style.css`, `order-history.tsx` and `food-image.tsx`. This is a code-led extension of the approved system, without a new visual comp. This documentation refresh includes no runtime, screenshot or test verification.

## Colors

Burnt orange is the primary action color with white text; green is reserved for vegetarian indicators and filters. Warm cream canvas, white cards, brown text and pale warm borders establish hierarchy. The stylesheet uses `color-scheme: light`; `--white` is the white card surface. Frontmatter values match the implementation; sidecar tonal ramps are synthesized preview aids, not shipped tokens.

## Typography

Self-hosted Manrope (`/fonts/manrope.ttf`, weights 200–800, swap) serves headings and controls with a sans-serif fallback. Cormorant is no longer used by the stylesheet. Hero headings use the display role; menu headings are 22px, dish names 16px and body copy 14px. On mobile these become 20px, 20px, 14px and 14px respectively; the Menu view hides its redundant menu heading, while Saved retains it. Dish descriptions are 12px on desktop and 11px on mobile and the visible preparation qualifier is 9px. Prices and order figures use tabular numerals. Small annotations are observed implementation choices, not an accessibility certification.

## Layout

Content caps at 1360px with 4vw gutters; the sticky header is at least 84px high. Delivery and kitchen selection precede a compact split hero (280px image height). Desktop has a two-column dish grid beside a 305px sticky bag, separated by 26px. The bag sticks at 104px; its dedicated view caps at 800px and removes sticky positioning.

At 1100px and below, the bag column becomes 275px and dish images 150px high. At 760px and below, gutters are 16px, the header is at least 72px, and the split hero and its image are 110px high, with a 14px bottom margin. The welcome subtitle, hero body and hero CTA are hidden; the welcome keeps its 23px heading with 14px/12px vertical margins. Only the Menu view hides the redundant menu-heading block. The preparation qualifier remains visible at 9px. Dish cards become single-column horizontal rows with a 112px image column; customization spans the row. Menu/Saved sidebars are hidden; checkout lives in the dedicated bag view. Orders and kitchen queues become single-column.

Mobile customer navigation is fixed at the bottom, 70px high, with Home, Search, Orders, Saved and Account. A nonempty bag on Menu/Saved adds a shortcut 80px above the bottom; main padding increases to avoid overlap. The dock opens and focuses the dedicated bag. Staff do not receive customer bottom navigation. Navigation uses real URLs: `/menu`, `/saved`, `/orders`, `/bag`, `/account` and `/signin`; dish pages use readable slugs such as `/menu/garlic-naan`. Legacy numeric dish URLs permanently redirect (308) to the slug. Category URLs use `/menu?category=breads` (or `/saved?category=breads` in Saved). The home URL `/` also presents the menu. Search remains a focused menu action.

Dish detail uses a `1.1fr 1fr` desktop grid with `clamp(24px, 5vw, 72px)` gap, a square image sticky at 110px and 40px bottom padding. At 760px and below it becomes one column with a 22px gap, a static 4:3 image and a 30px title. Portion choices wrap on mobile with a 130px minimum width.

## Elevation & Depth

Tonal layering and fine borders provide depth. Dish, bag and order cards have no outer shadow. The mobile bag alone uses `0 6px 22px #0005`; translucent dark image overlays support the heart, diet badge and illustration caption.

## Shapes

Rounded rectangles define the system: 8px fields, 9px buttons, 9px category links, 14px dish/bag/order cards and a 16px desktop hero. Hearts and bag counts are circular. Category links use orange borders and warm selected fills.

## Components

- **Actions and fields:** orange primary/Add buttons, tonal secondary buttons and transparent quiet buttons. Standard controls are at least 44px high; compact controls have smaller exceptions. Hover transitions take 180ms. Focus uses a 2px burnt-orange outline with 4px offset. CSS disables transitions/animations under reduced motion; some navigation handlers still explicitly request smooth scrolling.
- **Menu:** 70 curated dishes: 35 vegetarian and 35 non-vegetarian. Extra kitchen assignments are hidden while the underlying dish records remain; combined text/category/vegetarian filters; URL-backed categories with counts and a labeled category select; illustrative dish images or labeled placeholders, heart toggles, dietary badges, prices and inline native “Make it yours” disclosures for portion, biryani-only extra raita and allergens. Dish images and titles are links to `/menu/[slug]`; clicking other non-control card space also opens that dish. Added feedback and a live announcement last 1600ms. The menu initially displays 12 matching dishes; Show more dishes adds 12 at a time. Category, search, vegetarian, view or kitchen changes reset this display limit. A single labeled category select replaces the duplicate category link strip. Counts in category controls reflect kitchen dishes, while the live results count reflects all active filters.
- **Dish detail:** dedicated `/menu/[slug]` page with menu and category breadcrumbs, an illustrative image or labeled placeholder, dish heading followed by category/diet metadata, description, per-portion price, radio portion choices and allergens. Extra raita (+₹30) appears only for biryani. Quantity is bounded to 1–20; the Add to bag action displays the selected total and adds the chosen quantity together. Adding beyond 20 of the same customization is rejected with an explicit message. Successful feedback offers View your bag. The shared `/catalog` preserves dish route identity when a dish sells out at a kitchen; the storefront shows a kitchen-specific unavailable message and a Browse menu link. Names absent from the shared catalog return not found. Selected portion options use the orange border and `#fff0df` fill.
- **Saved dishes:** numeric dish IDs persist in this browser, not a server account. The view shows matching dishes available from the selected kitchen and retains menu filters; opening Saved resets filters.
- **Bag/account:** thumbnails, quantity/remove controls, estimated total, address and test payment method. Header and mobile shortcuts open the dedicated bag. The account view links to orders, saved dishes and bag. Sign-in is required for checkout.
- **Food imagery:** all 70 curated dishes have illustrations. Six original dish-specific images combine with ten generated category illustrations mapped by `food-illustrations.json`; related dishes share a category image. Next Image provides responsive image delivery and lazy loading. Category-image alt text identifies the category, dish and “presentation may vary”; detail captions disclose illustrative imagery and variation. Images recur in cards, detail, bag and orders; the hero uses the original chicken biryani image. These are illustrations, not evidence of actual outlet food. Unmapped future names retain a labeled food-icon fallback with `#fff0df` fill, `#87613c` text, 12px gap and 20px padding (10px in mobile cards). Its detail aspect ratios match photos; compact bag/order fallbacks hide visible names while retaining accessible labels.
- **Orders:** All orders and Past (HANDED_OFF only), dish thumbnails, outlet, address, payment state, preparation estimate, late notice and staff-stage timeline. Orders poll every four seconds while the customer Orders view is active. NEW → PREPARING → READY → HANDED_OFF ends at kitchen handoff; no rider GPS or delivery completion is tracked. Pending payments expose simulated success/failure actions.
- **Footer:** warm `#f7ede2` surface with Menu, Orders and Account links and “© 2026 DumHouse. All rights reserved.” Desktop content is split across the row; mobile stacks it and left-aligns links.
- **Supporting states:** explicit loading, empty menu/saved/bag/order states, dismissible errors, demo notices and shared light styling across authentication, kitchen queues and admin editors.

## Do's and Don'ts

### Do
- Use warm cream surfaces, white cards, brown text, burnt-orange actions and Manrope throughout.
- Keep dish prices, dietary labels, portion options and illustration disclosures visible.
- Preserve loading, empty, error, keyboard-focus and test-payment states.
- Describe estimates as preparation time and completed orders as kitchen handoffs.

### Don’t
- Do not restore dark mode or expand the curated menu beyond 70 dishes without a new user request.
- Do not use green for neutral surfaces, action feedback or order completion; reserve it for vegetarian meaning.
- Do not turn this single-chain menu into a restaurant marketplace.
- Do not invent ratings, discounts, real outlet photography, rider GPS or delivery completion.

## Minimal menu and kitchen refinement — 6 November 2026

Food cards use 230px desktop and 210px mobile photography, 18px dish names and 22px prices. Remove boilerplate category descriptions while preserving specific descriptions and visible allergen information. GST-inclusive pricing remains visible on mobile. The menu has one compact introduction and a single category control; search and vegetarian filtering remain directly accessible.

Kitchen tickets use 32px order numbers, 26px dish lines, 24px preparation estimates and 60px action buttons. Overdue tickets use a pale red background, a full red border and explicit OVERDUE wording. Colour is never the only signal. Two-metre legibility on the actual tablet and sub-minute customer checkout remain field-validation targets, not measured guarantees.
