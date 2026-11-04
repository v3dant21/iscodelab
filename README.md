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

Open http://localhost:3000. API reference: http://localhost:8000/docs. Use the localhost hostname consistently for cookies. Demo mode does not charge money or send messages. Do not enter real payment credentials.

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

`DATABASE_URL` defaults to the dedicated local demo database on port 55432. `ALLOW_MOCK_PAYMENTS` defaults to false in the API and is explicitly enabled by the local launcher/Compose. `APP_ORIGIN` defaults to http://localhost:3000. `SECURE_COOKIES=true` requires HTTPS. `API_INTERNAL_URL` sets the Next.js rewrite destination at build time. `.env` is only loaded automatically by Compose; export variables for native commands.

## Scope and remaining limitations

Three synthetic outlets and six dishes demonstrate the single-chain model; the original 17-outlet production inventory was not available. No real payment gateway, rider GPS, address geocoding, delivery confirmation, refunds, real FSSAI/license data, notifications or public deployment is claimed. The model is trained on synthetic examples, not restaurant history. The interface deliberately uses a text menu without external food photographs.

This is a local demo, not a production launch: public hosting still needs HTTPS, non-demo accounts, login throttling, identity/contact verification, real payment verification, operational monitoring, backups, and load/security review. Current cookies expire in one day; expired session cleanup is not scheduled. Polling is near-live, not push delivery. Seed startup assumes one initial writer. The API currently uses synchronous database access and a compact monolithic module appropriate to this scope.

Implementation references: [Next.js build documentation](https://github.com/vercel/next.js/blob/canary/docs/01-app/02-guides/building.mdx), [SQLAlchemy sessions and row locking](https://docs.sqlalchemy.org/en/20/orm/session_api.html).
