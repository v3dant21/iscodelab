# Isocode DumHouse

Local reconstruction of the restaurant ordering project from the recovered design and deployment documents. The original conversation exposed no retrievable source attachment; the downloaded `isocode_submission_docs.zip` contained only documentation. This repository is newly implemented source, not a recovered original ZIP.

## Run locally

Requirements: Node 22+, Python 3.13, and Docker or Podman. The development setup uses PostgreSQL 17 on port 55432, FastAPI on 8000 and Next.js on 3000. Run commands from this repository.

```sh
podman run -d --name dumhouse-postgres \
  -e POSTGRES_USER=dumhouse -e POSTGRES_PASSWORD=local-demo-only \
  -e POSTGRES_DB=dumhouse -p 127.0.0.1:55432:5432 postgres:17
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.lock
cd frontend
npm ci
npm run build
cd ..
bash scripts/run-local.sh
```

If the database container already exists, run `podman start dumhouse-postgres` instead of creating it. `scripts/run-local.sh` applies migrations, idempotently seeds synthetic data, and starts both servers. Ctrl+C stops the app servers; the database container remains running. Stop it with `podman stop dumhouse-postgres`. Container data persists across stops; removing the container/volume can delete data.

Open . API reference: ./docs. Use the localhost hostname consistently for cookies. Demo mode does not charge money or send messages. Do not enter real payment credentials.

Alternatively, with Docker Compose installed:

```sh
cp .env.example .env
docker compose up --build
```

Stop local app servers before running Compose because both configurations use ports 3000 and 8000. Compose stores PostgreSQL data in its named `postgres` volume and does not expose the database port. Docker image builds require internet. The local native-app + Podman PostgreSQL path was verified; the full Compose build has not been verified.

## Demo accounts

All initial demo passwords are `DemoPass123!` (or the `DEMO_PASSWORD` selected before the first seed).

| Account | Role |
| --- | --- |
| customer@demo.test | Customer; synthetic trusted COD eligibility |
| kondapur@demo.test | Kondapur kitchen |
| gachibowli@demo.test | Gachibowli kitchen |
| admin@demo.test | Central menu administrator |

New accounts are customers and prepaid-only. Kitchen/admin roles cannot be selected during registration. Changing the seed password later does not update existing accounts.

## Walkthrough

1. Choose a sample delivery area or permit browser location access. The closest open outlet within its straight-line service radius is selected. Another eligible outlet can be selected explicitly.
2. Choose a portion and optional extra raita; add food. The bag survives reload for 60 minutes from its last item/quantity change. Switching area or kitchen requires clearing the cart.
3. Sign in, supply a synthetic address and choose test UPI/card. Checkout rechecks outlet serviceability, assignment, availability, options, and prices on the server.
4. Simulate failed payment; the order remains out of the kitchen. Simulate successful payment; it becomes New. A failed payment can be retried. Replayed checkout/payment requests do not duplicate acceptance.
5. Sign in as the assigned kitchen in a separate browser profile/private window. The board polls every 3 seconds. Advance New → Preparing → Ready → Handed off; customer tracking polls every 4 seconds.
6. In the kitchen Availability tab, mark a dish sold out. A stale cart cannot purchase it. Other outlets remain unaffected.
7. Sign in as admin to create/edit central dishes and assign/unassign them at outlets. Optional price overrides do not copy the catalog. Staff stockouts are separate from central assignments.

The demo COD rule accepts trusted-account orders up to ₹1,500; larger orders require a 20% simulated deposit. The remaining balance is displayed, but no cash collection is implemented.

The current direction replaces the quiet-premium menu with a dark mobile delivery-inspired interface for one Hyderabad restaurant chain: charcoal surfaces, orange actions, self-hosted Manrope and rounded photo cards. Combined search/category/vegetarian filters and inline “Make it yours” customization remain. Hearts save dishes in this browser; Saved shows matches from the selected kitchen. A dedicated bag supports quantity changes, address and test checkout, with a mobile shortcut above Home/Search/Orders/Saved/Account navigation. Desktop retains a sticky bag alongside the menu. On mobile, a 110px hero and hidden welcome subtitle, hero body/CTA and redundant Menu heading bring dishes closer to the opening; the preparation qualifier remains visible.

Orders include dish thumbnails, address, payment state and a kitchen timeline. All orders includes every status; Past includes kitchen handoffs only. Four-second polling reports staff updates, with preparation-only estimates and late notices. There is no rider GPS or delivery-completion tracking. Six local illustrative food images appear across the menu, categories, bag and orders; image notes are under `frontend/public/images/README.md`. Design guidance is in `DESIGN.md` and `.impeccable/menu-direction.md`. This documentation refresh did not run builds, tests or a rendered UI review.

## Architecture and invariants

- `frontend/app`: Next.js App Router, React, strict TypeScript. The same-origin `/api` rewrite connects to FastAPI. Responsive customer, kitchen and admin views share a small typed request helper.
- `backend/main.py`: validated request models and direct application functions. Integer-paise prices come from PostgreSQL; order lines are immutable JSON snapshots. SQLAlchemy transactions lock checkout customers and quote rows; payment locks the order. Unique keys enforce checkout/payment idempotency, and conditional version updates prevent stale kitchen transitions.
- `backend/models.py`: users, hashed opaque sessions, outlets, central dishes, outlet assignments, orders and payment attempts. Alembic contains the initial schema revision. For subsequent schema changes, add a new migration and freeze the initial revision's schema rather than changing the historical table definitions.
- Passwords use Argon2; random sessions are stored as SHA-256 digests. Cookies are HttpOnly/SameSite for sessions; authenticated mutations require the matching session-bound CSRF cookie/header and an allowed Origin. Customers see only their orders; kitchen accounts see and modify only their outlet; admins cannot inspect customer orders.
- `backend/training/train.py`: deterministic synthetic Ridge training, saved coefficients and held-out synthetic MAE. Inference validates the artifact and falls back to a queue/portion estimate. Predictions never advance physical kitchen stages. An order is marked late after estimate +10 minutes.

## Verification

Install test dependencies, then use an isolated test database. The PostgreSQL test suite clears tables only in a database whose name ends in `_test`; never point it at a valuable database.

```sh
.venv/bin/pip install -r backend/requirements-dev.txt
podman exec dumhouse-postgres createdb -U dumhouse dumhouse_test
cd backend
../.venv/bin/pytest -q
TEST_DATABASE_URL=postgresql+psycopg://dumhouse:local-demo-only@127.0.0.1:55432/dumhouse_test ../.venv/bin/pytest -q
../.venv/bin/python training/train.py
cd ../frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser tests require both local servers already running and the initial demo accounts. `CHROMIUM_PATH` can select an existing Chromium executable. Browser tests create synthetic orders in the running app database. Tests cover cart persistence, successful/failed test payment, separate kitchen session, staff transitions, tracking, and 390/1440px overflow checks. API tests cover authorization, CSRF, service radius, prices/options, outlet isolation, stockouts, changed prices, idempotency, COD/deposit, mock gating, catalog assignment, fallback prediction and PostgreSQL concurrency.

## Configuration

`DATABASE_URL` defaults to the dedicated local demo database on port 55432. `ALLOW_MOCK_PAYMENTS` defaults to false in the API and is explicitly enabled by the local launcher/Compose. `APP_ORIGIN` defaults to . `SECURE_COOKIES=true` requires HTTPS. `API_INTERNAL_URL` sets the Next.js rewrite destination at build time. `.env` is only loaded automatically by Compose; export variables for native commands.

## Scope and remaining limitations

Three synthetic outlets and six dishes demonstrate the single-chain model; the original 17-outlet production inventory was not available. No real payment gateway, rider GPS, address geocoding, delivery confirmation, refunds, real FSSAI/license data, notifications or public deployment is claimed. The model is trained on synthetic examples, not restaurant history. The menu uses live dish data alongside six locally stored illustrative food images. Saved dishes are browser-local and do not sync across accounts or devices.

This is a local demo, not a production launch: public hosting still needs HTTPS, non-demo accounts, login throttling, identity/contact verification, real payment verification, operational monitoring, backups, and load/security review. Current cookies expire in one day; expired session cleanup is not scheduled. Polling is near-live, not push delivery. Seed startup assumes one initial writer. The API currently uses synchronous database access and a compact monolithic module appropriate to this scope.

Implementation references: [Next.js build documentation](https://github.com/vercel/next.js/blob/canary/docs/01-app/02-guides/building.mdx), [SQLAlchemy sessions and row locking](https://docs.sqlalchemy.org/en/20/orm/session_api.html).

## Google sign-in and public pages

Google sign-in is prepared but disabled until `GOOGLE_CLIENT_ID` is set on the backend. In Google Cloud / Google Auth Platform, configure your consent screen and create an OAuth **Web application** client. Add `` to its authorized JavaScript origins (and your HTTPS origin for deployment). Set `GOOGLE_CLIENT_ID` to the client ID, then restart the backend. This Google Identity Services popup flow does not need a client secret or redirect endpoint. Native startup uses exported environment variables; Compose reads `.env`.

The official Google button appears on sign-in when configured. Tokens are verified server-side with Google's library, including the client audience, expiry, issuer and a browser-bound nonce. Google accounts create customer accounts only; an existing email/password account must continue using its password, and is never silently linked or elevated. Live Google authentication still requires the real client configuration and an end-to-end account test.

Menu, dish, saved, bag, orders, account and sign-in now have direct URLs. `/menu/<dish-id>` includes kitchen-supported portions, quantity and biryani-only extra raita; the server rejects raita on sides or desserts. Personal pages are marked `noindex`. Public pages have titles, descriptions and canonical URLs, with `/sitemap.xml` and `/robots.txt`. Set `SITE_URL` on the frontend to your public HTTPS origin before deployment. Search engines cannot index localhost; these changes prepare indexing, they do not publish or submit the site. The sitemap currently lists the Kondapur menu.

The interface uses warm charcoal, saffron orange and cream; vegetarian badges remain green. The footer reads “© 2026 DumHouse. All rights reserved.” Test-payment labels remain beside payment flows.

## Reference-menu expansion and readable URLs

The demo now retains the original six dishes and adds 200 readable entries from the four user-provided Hyderabad restaurant menu photos (206 total). New entries use the reference prices in rupees, converted to integer paise. Blurred, cropped, repeated and ambiguous rows are omitted. Existing demo dish prices remain unchanged. Descriptions are short editorial labels, not verified recipes; reference-item allergens are explicitly unverified. Items without a matching illustration use a labelled food-icon placeholder rather than an unrelated photo.

`backend/reference_menu.py` is the reviewed import source. It runs during first-time seeding; for an already populated database run `.venv/bin/python backend/reference_menu.py` from the project root. It adds missing dishes and outlet assignments without overwriting staff prices or stock settings. Repeating it adds no duplicates. It has already been applied to this local demo database.

Dish links now use names, for example `/menu/dum-chicken-biryani`, `/menu/garlic-naan`, and `/menu/chicken-handi-biryani`. Existing `/menu/1` links permanently redirect to the named equivalent. Unknown dish names return 404. The shared `/catalog` endpoint supplies metadata and sitemap identities even while a dish is temporarily sold out; the selected kitchen's live menu still controls ordering. The sitemap includes enabled catalog dishes across outlets, replacing the earlier Kondapur-only list.

Category navigation uses links such as `/menu?category=breads`, with a category selector, counts, browser Back support, and batches of 24 items. Handi dishes retain the photographed two-person serving; family packs and half/full kebabs show their listed portions without invented size surcharges. Routes are derived from current dish names, so renaming a dish in admin changes its named URL; numeric legacy links still resolve to the current name.

## Current menu and light theme (supersedes the expansion above)

The user requested a smaller menu and light mode. The live catalog is now exactly **70 selected dishes: 35 vegetarian and 35 non-vegetarian**. This is an editorial selection across categories, not a sales-based ranking. `backend/curated_menu.py` contains the shortlist and can be run explicitly to apply it. Extra items are hidden through outlet assignments, preserving historical orders and dish records. Fresh seeding imports only the selected reference entries.

The interface now uses warm cream backgrounds, white surfaces, dark brown text and orange actions. All 70 dishes have images: the original six illustrations plus ten new AI-generated category photos. Related dishes share representative category images, not unique exact-dish photographs; captions and alternative text make that distinction. Image mapping lives in `frontend/app/food-illustrations.json`, and Next.js Image serves appropriately sized versions.

### Sample digital bills
Confirmed orders now save an immutable demo billing snapshot in `invoices` (migration 003). Customers can view/print/save as PDF or download an HTML copy from Your orders. Older confirmed orders receive a snapshot on their first bill request. The bill is private to its order owner and uses a stable DEMO order-based reference, fictional supplier details, and a deliberately invalid GSTIN placeholder. The illustrative inclusive 5% tax is split into CGST/SGST with explicit paise rounding; it is not a production tax determination. Simulated payment/deposit and outstanding amounts are distinguished.

These documents are prominently marked **DEMO TAX INVOICE — NOT VALID FOR TAX PURPOSES**. They are not GST portal e-invoices or digitally signed invoices. Live billing still requires verified supplier registrations, applicable tax treatment, recipient details where required, compliant numbering/issuance and a real payment workflow.

### Customer checkout journey
Customers review server-checked items, address, inclusive sample taxes, payment/deposit and the final total before creating an order. Changes detected at confirmation require another review. Payment then opens the specific `/orders/{id}` page; success shows an order confirmation with Track order and View bill actions. Your orders retains links to each order and its saved bill. Tracking polls kitchen preparation every four seconds and stops at kitchen handoff; live rider GPS and proof of delivery are not implemented. Test payment and sample-invoice restrictions remain in place.

### Real menu photographs
The 70 published dishes now use 70 distinct real photographs with source/author/license records in `frontend/app/food-photos.json`; none use the older generated category illustrations. The menu hero also uses a real biryani photograph. `/photo-credits.html` provides public attribution and links to each original. These are representative food photographs, not this restaurant's own product photography; some regional/portion variants use the closest available dish-family match. The live payment, real tax-invoice and merchant configuration work remains separate and unfinished; replacing images does not make the application production-ready.

### Outlet operations and notification integration
- Auto routing chooses the nearest open outlet in range that can supply the entire cart; checkout shows the actual kitchen and its prices before confirmation. Selecting a kitchen explicitly retains that choice. Payment revalidation never silently moves an existing order.
- Outlet stock is enforced on the server; customer menus refresh availability every 15 seconds while visible. History-based reorder rankings use only the signed-in customer's confirmed orders and currently available items. They link to dish details and never mutate a cart. This ranking is not an externally trained AI recommender.
- Prep promises use the higher of the current model estimate and outlet minimum with no 120-minute truncation. The present regression is trained on synthetic data, not validated production observations. Retraining/calibration against actual kitchen timings is a launch requirement.
- `notification_worker.py` independently checks the original preparation promise every five seconds. At 10 minutes overdue it creates one durable customer notice and one manager alert. Ready/handed-off orders are excluded. Revised estimates cannot erase a breached original promise. Manager/admin overrides require a reason, an order version, and cannot go below the AI/minimum floor; the audit retains before/after values and actor.
- Provision assigned managers explicitly using `backend/provision_manager.py EMAIL OUTLET_ID` (interactive password; no default manager credentials). The central administrator can review queues and override estimates for each outlet. Kitchen-only accounts cannot override promises.
- The local runner starts the monitor/dispatcher; Compose defines a separate `notifications` worker. Unconfigured SMS/WhatsApp requests stay `pending`, with the update visible in-app. To connect a provider, configure `NOTIFICATION_WEBHOOK_URL` (HTTPS) and `NOTIFICATION_WEBHOOK_SECRET` on the worker. The bridge receives `{id, channel, to, text}`, an `Idempotency-Key`, and HMAC-SHA256 of the exact JSON body in `X-Signature-SHA256`. The bridge must validate signatures, deduplicate IDs, enforce approved WhatsApp templates/provider policies, and implement delivery callbacks. HTTP acceptance means `submitted`, not `delivered`. Retries use backoff, stop after eight failures, and remain visible as failed. Real provider integration and delivery receipts are still pending.
- Four bounded dispatcher threads use PostgreSQL row locks with `SKIP LOCKED`; delay monitoring is independent of outbound provider latency. A local intake burst is only a smoke check, not proof of sustained 1,200/hour capacity with real provider traffic and tablet sessions.

### Food information and privacy launch requirements
Prices are displayed as including 5% GST per the operator requirement. Dietary markers use a green circle or brown triangle with text. Allergens appear on cards and details; missing declarations explicitly say unverified, not allergen-free. Each outlet has an optional 14-digit FSSAI field managed by the administrator after checking the actual licence. No invented licence numbers are seeded.
Marketing consent defaults to false and has a separate account control with a versioned timestamped audit trail. Order SMS/WhatsApp consent does not imply marketing consent. No marketing sender is connected. `/privacy.html` describes actual data uses and the unfinished operator/contact, retention, rights-request and processor requirements; it is not a DPDP compliance certification. Official references: https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa and https://www.fssai.gov.in/upload/uploadfiles/files/FAQ-%20Display%20of%20Information.pdf . Confirm applicability and phased commencement with qualified review before launch.
