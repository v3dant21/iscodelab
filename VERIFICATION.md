# Verification — 5 November 2026

Executed on the user's local Linux workspace, using Node 22.22.0, Python 3.13.13, Next.js 16.4.5 and a PostgreSQL 17 Podman container.

| Check | Result |
| --- | --- |
| Next.js production build and strict TypeScript check | Passed |
| PostgreSQL Alembic migration and idempotent seed | Passed |
| PostgreSQL integration suite | 15 passed |
| SQLite integration suite before PostgreSQL concurrency test was added | 14 passed |
| Chromium customer-to-kitchen order/payment/tracking test | Passed |
| Chromium 390px and 1440px menu overflow checks | Passed |
| Desktop and mobile menu screenshot inspection | No clipping or overlapping controls observed |
| Installed Python dependency consistency | Passed |
| npm installation audit | 0 reported vulnerabilities at install time |

The PostgreSQL suite includes simultaneous checkout retries and replayed successful payments. It also covers customer ownership, staff outlet isolation, role escalation rejection, CSRF, menu and price revalidation, assignment and stockout changes, invalid/stale transitions, COD/deposit rules and prediction fallback.

Browser tests run the production Next.js server through its real API proxy against FastAPI and PostgreSQL. A separate browser context signs in as kitchen staff and advances a paid order through Preparing, Ready and Handed off; the customer observes each update by polling. Test orders remain as synthetic review data.

The trained Ridge artifact reports a held-out synthetic MAE of approximately 2.345 minutes. This is not measured restaurant accuracy.

Warnings: Starlette reports that its httpx-based test client is deprecated; tests still pass. Next.js reports a parent-directory package lock outside this independent repository; the local production build succeeds. These do not constitute a production security or performance assessment.

Not verified: complete Compose image build, public deployment, real payment processing, rider tracking, peak-load targets, accessibility audit, or real-world prediction accuracy. The original source archive was not retrievable; this code is a reconstruction of the locally recovered specification.

## Premium-menu redesign

The user selected a quiet, premium restaurant menu. The rebuilt interface uses local Cormorant Garamond and Manrope fonts, a labeled generated food image, a compact delivery/outlet bar, combined search/category/vegetarian filtering, inline customization, and a mobile bag shortcut. The existing payment and kitchen APIs were unchanged.

Production build and strict TypeScript pass. All three browser tests pass. The original browser order/payment/kitchen tracking workflow passes after changing the customization selector to open its disclosure. Search, vegetarian/category combinations, empty-result recovery and mobile bag focus are covered by a new browser test. Layout/image-load checks now cover 390, 942 and 1440 pixels. An independent Impeccable review requested larger dish metadata/descriptions and restoration of geolocation access at tablet widths; both were implemented, and the reviewer scored both resolved with a ship verdict scoped to those fixes. Final captures are stored in `.impeccable/review/`.
