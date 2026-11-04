# DumHouse interface

Warm paper restaurant menu, burgundy actions, generous serif headlines, direct sans-serif form controls. The menu is typographic, with no external photo dependency. Product truth is in PRODUCT.md.

Tokens in frontend/app/style.css: paper #f8f4eb, ink #29251f, muted #696052, brand #762e22, line #d9cfbd, white #fffdf8, green #355b36. Georgia headlines use -0.025em tracking; Arial body text is 16px. Controls have a 44px minimum height. Card radii are 12px; buttons 7px. Error, focus, hover, empty and disabled states are explicit.

Desktop shows menu and sticky bag side by side; mobile stacks them. Delivery location and outlet selection precede the menu. Kitchen queue uses three columns, stacking on mobile. Staff transitions always require a human action; estimates are not status indicators. Screenshots were inspected at 1440px and 390px with automated horizontal-overflow assertions.
