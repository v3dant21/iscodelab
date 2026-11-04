---
name: DumHouse
description: Quiet, premium restaurant menu in forest and bone.
colors:
  paper: "#f7f6f1"
  white: "#fffefa"
  ink: "#28372e"
  muted: "#656b60"
  brand: "#304c3a"
  line: "#dcded3"
  soft: "#eceee5"
  green: "#476146"
  brand-hover: "#203c2a"
  focus: "#778556"
typography:
  display:
    fontFamily: '"Cormorant", Georgia, serif'
    fontSize: "clamp(64px, 6.7vw, 96px)"
    fontWeight: 400
    lineHeight: 0.96
    letterSpacing: "-0.025em"
  headline:
    fontFamily: '"Cormorant", Georgia, serif'
    fontSize: "36px"
    fontWeight: 500
    lineHeight: 1.05
    letterSpacing: "-0.025em"
  title:
    fontFamily: '"Cormorant", Georgia, serif'
    fontSize: "29px"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  body:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "14px"
    lineHeight: 1.65
  label:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "11px"
    fontWeight: 650
  button:
    fontFamily: '"Manrope", sans-serif'
    fontSize: "12px"
    fontWeight: 650
rounded:
  control: "5px"
  surface: "12px"
  filter: "24px"
  mobile-bag: "8px"
spacing:
  compact: "8px"
  control-gap: "10px"
  small: "12px"
  medium: "20px"
  large: "24px"
  section: "30px"
components:
  button-primary:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.white}"
    typography: "{typography.button}"
    rounded: "{rounded.control}"
    padding: "11px 18px"
  button-primary-hover:
    backgroundColor: "{colors.brand-hover}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.brand}"
    rounded: "{rounded.control}"
    padding: "11px 18px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 18px"
  button-add:
    backgroundColor: "transparent"
    textColor: "{colors.brand}"
    rounded: "{rounded.control}"
    padding: "8px 13px"
  input:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "11px 12px"
  vegetarian-filter:
    backgroundColor: "transparent"
    textColor: "{colors.green}"
    rounded: "{rounded.filter}"
    padding: "8px 14px"
  bag-card:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.surface}"
    padding: "24px"
  mobile-bag:
    backgroundColor: "{colors.brand}"
    textColor: "{colors.white}"
    rounded: "{rounded.mobile-bag}"
    padding: "15px"
---

# Design System: DumHouse

## Overview

**Creative North Star: "Quiet, premium restaurant menu"**

Quiet, premium restaurant menu is the user-selected visual direction. Bone paper, forest ink and softened olive details create a restrained restaurant identity. Cormorant display type supplies warmth; Manrope keeps ordering controls precise and compact.

Fine rules and open dish rows carry the menu. A single atmospheric biryani image provides the expressive moment and is explicitly illustrative. Tonal surfaces separate the order summary without making every dish a raised card.

**Key Characteristics:**
- Bone paper and forest actions with softened olive accents.
- Expressive serif headings paired with compact sans-serif controls.
- Fine dividers, open dish rows and inline customization.
- One illustrative food asset and a persistent route to the bag.

This is a source-derived record of the implemented replacement world, using `frontend/app/style.css`, `frontend/app/page.tsx` and `.impeccable/menu-direction.md`. Product truth remains in `PRODUCT.md`. No pixel-comp approval, fresh screenshot review or quality score is asserted here.

## Colors

Forest and olive sit against warm bone neutrals; the frontmatter contains normative reusable values.

### Primary
- **Forest action / brand:** primary buttons, selected controls and action text; the deeper hover tone signals interaction.

### Secondary
- **Leaf green:** vegetarian controls and completed order stages.
- **Olive focus:** visible keyboard outlines; retain the two-pixel outline and four-pixel offset.

### Neutral
- **Bone paper:** page canvas.
- **Warm white:** bag, inputs and order cards.
- **Forest ink:** primary reading text.
- **Muted sage:** descriptions and supporting labels.
- **Fine divider:** row boundaries and card strokes.
- **Soft sage:** demo strip, quiet hover and editor surface.

Local error surfaces use warm clay tones; they are functional status exceptions, not a replacement brand accent. Sidecar tonal ramps are synthesized preview aids, not additional shipped CSS tokens.

## Typography

**Display Font:** self-hosted Cormorant Garamond, registered as "Cormorant", with Georgia and serif fallbacks.
**Body Font:** self-hosted Manrope, with sans-serif fallback.

The display face carries the wordmark, welcoming headlines and dish names. The UI face carries prices, labels and controls. Fonts load from `/fonts/cormorant-garamond.ttf` and `/fonts/manrope.ttf` with swap behavior.

### Hierarchy
- **Display:** hero title; italic emphasis retains the display family. At the intermediate breakpoint it becomes 76px, then 72px on mobile.
- **Headline:** general section headings. Menu heading is 41px on wide screens, 36px at the intermediate breakpoint, and 38px on mobile.
- **Title:** dish names, reducing to 27px on mobile. General h3 is 28px.
- **Body:** general reading text; dish descriptions use 1.8 line-height, 1.7 on mobile, and a 48ch maximum. Paragraphs otherwise cap at 70ch.
- **Label / button:** compact Manrope with semibold emphasis. Secondary annotations vary from 8–12px; these are observed implementation sizes, not an accessibility certification.

Prices, totals and order information use tabular numerals. Do not apply the wordmark's expanded tagline tracking to ordinary controls.

## Layout

Main content caps at 1512px with 5vw horizontal padding. A sticky header (96px minimum, top 0, z-index 10) precedes the demo strip. The opening uses a .95fr/1.05fr split, 48px gap, and a 400px-tall image.

Delivery selection is a compact ruled grid (1.15fr 1.2fr .9fr auto), followed by the menu and a 310px bag column with a 56px gap. The bag is sticky at 120px. Dish rows remain open with bottom rules; search, vegetarian filtering and horizontally scrollable category controls precede them.

At max-width 1100px, the image becomes 355px high; the bag column becomes 280px with a 30px gap. Delivery controls occupy three columns with the location action on its own row.

At max-width 760px, the hero and menu/bag stack, main gutters become 20px, the image becomes 240px high, and delivery controls use two columns. The header wraps with an 84px minimum height. The bag becomes static in document flow. A nonempty customer bag exposes a fixed dock at bottom 12px and left/right 14px, z-index 20; the body gains 76px bottom padding while it exists. Kitchen queues change from three columns to one.

Spacing values in the frontmatter are recurring extracted measurements, not a newly imposed modular scale.

## Elevation & Depth

Depth comes mainly from tonal surfaces and fine borders. Menu rows and the desktop bag have no outer shadow. The mobile bag dock alone uses a structural floating shadow (`0 8px 24px rgb(25 46 30 / 20%)`). The small diet marker uses an inset one-pixel paper edge, not surface elevation. The hero caption uses a dark translucent overlay to maintain legibility.

## Shapes

Controls have modest corners; bag, order, editor and image surfaces use the larger surface radius. The vegetarian filter is a pill, while category selections and the hero link use square underline treatments. Bag counts are circular. Fine strokes carry boundaries without ornamental frames.

## Components

### Buttons
Primary actions use forest fill and warm-white text. Secondary buttons have a muted border; quiet buttons are transparent. Both use soft-sage hover. Add buttons begin outlined, then fill forest on hover or the brief Added state. Standard buttons have a 44px minimum height. Disabled buttons use half opacity and a not-allowed cursor.

Color, background and border transitions last 0.2s with ease. Global focus uses a visible olive outline. Reduced-motion disables transitions and animations and changes smooth scrolling to immediate scrolling.

### Inputs / Fields
Warm-white inputs use a fine sage border and the control radius. Search is a transparent underline field. Delivery selects are compact, borderless controls with a 32px minimum height; the vegetarian filter is 38px minimum. Do not claim every control meets the standard button height. Textareas resize vertically.

### Navigation and filters
Selected top navigation uses an underline, not a filled pill. Category buttons show counts, use a two-pixel selected underline and expose pressed state. Search, category and vegetarian filters combine. The vegetarian control uses a pale green active fill and a darker border.

### Cards / Containers
The desktop bag uses a warm-white surface, fine border and surface radius; padding reduces to 20px at the intermediate breakpoint and returns to 24px on mobile. Order cards share that surface language. Loading, no-results, no-menu and empty-bag messages remain explicit.

### Illustrative food asset
`/images/dumhouse-biryani.png` supplies the single focal image. It is cropped with object-fit cover and carries meaningful alt text plus the visible "Illustrative food image" caption. Its source dimensions are 1536 × 1024. It is neither an actual outlet photograph nor an approved UI specification.

### Inline customization and bag
Each dish uses a native details/summary disclosure for portion, extra raita and allergens. Price reflects the chosen options. Add feedback lasts 1600ms and includes a live status announcement. Header and mobile bag actions return to the menu, scroll to the bag and focus it. The dock appears only on the customer menu with at least one item, and shows count, estimated amount and View bag.

### Status and supporting surfaces
Errors use a dismissible alert; loading exposes busy/status semantics. Checkout distinguishes test payments. Order timelines reflect staff-reported stages, with preparation estimates separately labeled. Shared typography and controls carry through authentication, orders, kitchen queues and administrative editors.

## Do's and Don'ts

### Do:
- Do use forest actions, bone surfaces and the Cormorant/Manrope pairing.
- Do keep dish customization inline and preserve visible price and diet information.
- Do label the food asset as illustrative and keep demo/payment disclosures visible.
- Do preserve keyboard focus, loading and empty states, and reduced-motion behavior.

### Don't:
- Don't restore the superseded burgundy/Arial visual system.
- Don't turn each menu row into a raised card or introduce decorative shadows throughout.
- Don't present the illustrative image as an actual outlet's food or invent ratings and awards.
- Don't describe preparation estimates as delivery or automatic staff progress.
