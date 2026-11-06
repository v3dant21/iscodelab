# Deploy DumHouse

## Vercel website

Import `v3dant21/iscodelab`. Set Root Directory to `frontend`, framework to Next.js and Node.js to 22.x. Keep the lockfile and use `npm ci` / `npm run build` (configured in `frontend/vercel.json`).

Set these server-side environment variables before deploying:

| Variable | Value |
| --- | --- |
| API_INTERNAL_URL | Public HTTPS origin of the running FastAPI service, without `/api` |
| SITE_URL | The final website origin, e.g. `https://your-project.vercel.app` |

The website proxies `/api/*` to the API. This preserves same-origin cookies and avoids exposing database credentials. API_INTERNAL_URL is consumed at build time: redeploy after changing it. A Vercel build deliberately fails when the API destination is missing or not HTTPS, instead of publishing a site that sends orders to localhost.

## API, database and notification worker

Provision hosted PostgreSQL and run the API and `backend/notification_worker.py` against the same database. Do not copy the local test database or its public demo passwords into a live ordering deployment.

API environment:

- DATABASE_URL: `postgresql+psycopg://...` connection URL provided by your host; use its required TLS configuration.
- APP_ORIGIN: exactly the final website origin, no trailing slash. This controls allowed browser origins and CSRF checks; do not use a wildcard for preview URLs.
- SECURE_COOKIES: `true`.
- ALLOW_MOCK_PAYMENTS: `false` for a live service. Real online payments are not implemented yet; disabling mocks does not install a gateway.
- GOOGLE_CLIENT_ID: optional Google web client ID, with the website origin authorized in Google Console.

Install `backend/requirements.lock`, run `python -m alembic upgrade head` from `backend`, then start `python -m uvicorn main:app --host 0.0.0.0 --port PORT` using the port assigned by the host. Run migrations once per release. Do not use the existing local Dockerfile startup in production: it automatically seeds demonstration accounts.

Run `python notification_worker.py` as a persistent worker with DATABASE_URL and, once selected, NOTIFICATION_WEBHOOK_URL and NOTIFICATION_WEBHOOK_SECRET. Without that worker, overdue monitoring and queued messages do not run. Without a messaging provider, external WhatsApp/SMS delivery remains pending. An ordinary web request is not a replacement for this continuous process.

A fresh database requires deliberate outlet, menu and staff provisioning before taking orders. `seed.py` is a demonstration setup, not production onboarding.

## Release checks

Use a separate staging database for preview deployments. Verify sign-in, category and dish pages, stock changes, quote/checkout, order tracking, saved invoices, manager overrides, and delayed-order notifications over HTTPS. Verify the final APP_ORIGIN to prevent “Origin not allowed”. Keep preview and production secrets separate.

Current release blockers for accepting real orders: merchant/payment integration, verified seller/GST and outlet licence details, approved allergen data, production staff setup and privacy/operator contact details. A hosted development preview can be shared while these are completed, but it must retain its test-payment and sample-invoice disclosures.
