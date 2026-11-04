---
name: DumHouse
description: Dark mobile delivery-inspired ordering for one Hyderabad restaurant chain.
colors:
  paper: "#0e1212"
  white: "#181e1e"
  ink: "#f5f6f2"
  muted: "#aeb8b2"
  brand: "#ff7c35"
  brand-ink: "#211208"
  line: "#303b38"
  soft: "#202927"
  green: "#a9d87d"
  brand-hover: "#ff975d"
  focus: "#ffb184"
  field: "#111716"
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
  category: "12px"
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

**Creative North Star: "Dark, food-first Hyderabad ordering"**

The user-selected dark mobile delivery reference replaces the quiet-premium forest-and-bone direction. Charcoal surfaces, orange calls to action, bold Manrope and illustrative food photography define DumHouse, a fictional single restaurant chain in Hyderabad. The reference supplies visual inspiration, not marketplace features or delivery-service claims.

**Key Characteristics:**
- Charcoal layers, warm orange actions and rounded food cards.
- Manrope throughout, with compact labels and prominent prices.
- Photo categories, saved dishes, a dedicated bag and mobile bottom navigation.
- Staff-reported kitchen progress with explicit test-payment and illustration disclosures.

Source-derived from `frontend/app/page.tsx`, `style.css`, `order-history.tsx` and `food-image.tsx`. This documentation refresh includes no runtime, screenshot or test verification.

## Colors

Orange is the primary action color with dark text; pale green supports vegetarian and completion states. Charcoal canvas, slightly lighter cards and fine muted borders establish hierarchy. Warm white is reading text, not a surface: the legacy CSS name `--white` now means dark card background. Frontmatter values match the implementation; sidecar tonal ramps are synthesized preview aids, not shipped tokens.

## Typography

Self-hosted Manrope (`/fonts/manrope.ttf`, weights 200–800, swap) serves headings and controls with a sans-serif fallback. Cormorant is no longer used by the stylesheet. Hero headings use the display role; menu headings are 22px, dish names 16px and body copy 14px. On mobile these become 20px, 20px, 14px and 14px respectively; the Menu view hides its redundant menu heading, while Saved retains it. Dish descriptions are 11px and the visible preparation qualifier is 9px. Prices and order figures use tabular numerals. Small annotations are observed implementation choices, not an accessibility certification.

## Layout

Content caps at 1360px with 4vw gutters; the sticky header is at least 84px high. Delivery and kitchen selection precede a compact split hero (280px image height). Desktop has a two-column dish grid beside a 305px sticky bag, separated by 26px. The bag sticks at 104px; its dedicated view caps at 800px and removes sticky positioning.

At 1100px and below, the bag column becomes 275px and dish images 150px high. At 760px and below, gutters are 16px, the header is at least 72px, and the split hero and its image are 110px high, with a 14px bottom margin. The welcome subtitle, hero body and hero CTA are hidden; the welcome keeps its 23px heading with 14px/12px vertical margins. Only the Menu view hides the redundant menu-heading block. The preparation qualifier remains visible at 9px. Dish cards become single-column horizontal rows with a 112px image column; customization spans the row. Menu/Saved sidebars are hidden; checkout lives in the dedicated bag view. Orders and kitchen queues become single-column.

Mobile customer navigation is fixed at the bottom, 70px high, with Home, Search, Orders, Saved and Account. A nonempty bag on Menu/Saved adds a shortcut 80px above the bottom; main padding increases to avoid overlap. The dock opens and focuses the dedicated bag. Staff do not receive customer bottom navigation.

## Elevation & Depth

Tonal layering and fine borders provide depth. Dish, bag and order cards have no outer shadow. The mobile bag alone uses `0 6px 22px #0005`; translucent dark image overlays support the heart, diet badge and illustration caption.

## Shapes

Rounded rectangles define the system: 8px fields, 9px buttons, 12px category tiles, 14px dish/bag/order cards and a 16px desktop hero. Hearts and bag counts are circular. Category tiles use orange border/fill states rather than the former underline navigation.

## Components

- **Actions and fields:** orange primary/Add buttons, tonal secondary buttons and transparent quiet buttons. Standard controls are at least 44px high; compact controls have smaller exceptions. Hover transitions take 180ms. Focus uses a 2px peach outline with 4px offset. CSS disables transitions/animations under reduced motion; some navigation handlers still explicitly request smooth scrolling.
- **Menu:** combined text/category/vegetarian filters; photo category tiles; illustrative dish images, heart toggles, dietary badges, prices and inline native “Make it yours” disclosures for portion, extra raita and allergens. Added feedback and a live announcement last 1600ms.
- **Saved dishes:** numeric dish IDs persist in this browser, not a server account. The view shows matching dishes available from the selected kitchen and retains menu filters; opening Saved resets filters.
- **Bag/account:** thumbnails, quantity/remove controls, estimated total, address and test payment method. Header and mobile shortcuts open the dedicated bag. The account view links to orders, saved dishes and bag. Sign-in is required for checkout.
- **Food imagery:** six name-mapped local assets cover chicken/mutton/paneer biryani, Chicken 65, mirchi ka salan and double ka meetha. Images recur in categories, cards, bag and orders; the hero uses the chicken biryani image. FoodImage uses illustrative alt text and lazy loading; an unknown name renders no image. Photos are illustrative, not evidence of actual outlet food.
- **Orders:** All orders and Past (HANDED_OFF only), dish thumbnails, outlet, address, payment state, preparation estimate, late notice and staff-stage timeline. Orders poll every four seconds while the customer Orders view is active. NEW → PREPARING → READY → HANDED_OFF ends at kitchen handoff; no rider GPS or delivery completion is tracked. Pending payments expose simulated success/failure actions.
- **Supporting states:** explicit loading, empty menu/saved/bag/order states, dismissible errors, demo notices and shared dark styling across authentication, kitchen queues and admin editors.

## Do's and Don'ts

### Do
- Use charcoal surfaces, orange actions and Manrope throughout.
- Keep dish prices, dietary labels, inline options and illustrative-photo disclosures visible.
- Preserve loading, empty, error, keyboard-focus and test-payment states.
- Describe estimates as preparation time and completed orders as kitchen handoffs.

### Don’t
- Do not restore the superseded bone/forest palette, serif headings or open editorial dish rows.
- Do not turn this single-chain menu into a restaurant marketplace.
- Do not invent ratings, discounts, real outlet photography, rider GPS or delivery completion.
