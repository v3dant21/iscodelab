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

## Configured Vercel projects

- Website: `iscodelab`, root `frontend`, Node.js 22, https://iscodelab.vercel.app.
- API: `iscodelab-api`, root `backend`, Python 3.13, https://iscodelab-api.vercel.app.
- Database: Neon `iscodelab-db`, free plan, Singapore; credentials remain in Vercel environment settings.
- Worker: `backend/vercel.json` declares one Singapore notification daemon using `Dockerfile.worker`. This bypasses the local Dockerfile's automatic seed command.
- Both projects connect to the repository's main branch for automatic deployments.

This is a hosted development deployment with mock payments enabled, not approval to accept real payments. The sample menu is loaded; known demo account passwords are disabled. New customer accounts can use email registration. Google login still needs GOOGLE_CLIENT_ID and the exact website origin authorized in Google Cloud. Phone OTP is not enabled.

After changing database schema, apply migrations before promoting new code. The initial hosted schema was migrated explicitly; builds do not mutate the database automatically. Preview environments must receive their own database and exact allowed origin before they can be tested.

## Customer pipeline and personal-data encryption

Release 005 adds encrypted customer name/email/phone fields, keyed email/phone indexes, an encrypted per-order contact snapshot, encrypted checkout requests/invoices/notification recipients, verified-email state and a transactional email outbox. Passwords remain Argon2 hashes. Database IDs relate orders to customers; phone numbers are not unique identifiers and accounts are never automatically merged by phone.

`PII_ENCRYPTION_KEYS` contains comma-separated Fernet keys (first encrypts; all decrypt). `PII_LOOKUP_KEY` is a separate random HMAC secret. Keep both outside the database and repository, back them up securely, and never replace the lookup key without a coordinated re-index. Losing encryption keys makes existing contact information unreadable. Local startup creates `.env.personal` once with mode 0600. Production keys are separate Vercel secrets; local backup is `backend/.env.pii.production` (ignored by Git). Do not copy local/test keys into production.

Upgrade order: configure secrets, apply migration 005, deploy API/worker/frontend, then run `backend/backfill_personal_data.py` with the production database and keys loaded. Compatibility reads allow existing plaintext records during this bounded rollout; new writes encrypt. Backfill encrypts historical emails, checkout requests, invoice snapshots and notification recipients and populates matching hashes. Existing provider backups may still contain historical plaintext; coordinate their retention separately. Never roll back to an API version that cannot read encrypted records.

Signup requires name and a phone number in international format (not OTP-verified). Google-authenticated customers complete missing contact fields before checkout. Existing customers complete missing profiles too. Email/password signup queues a one-use verification link, valid for 24 hours, with a 60-second resend cooldown. Confirmed orders queue an owner-authenticated tracking link and an actual PDF invoice; they wait for email verification before dispatch. Google-verified email is trusted only after server-side ID-token verification. Order tracking/bill access remains available without email delivery.

The prepared email adapter uses Resend: configure `RESEND_API_KEY` and `EMAIL_FROM` (a verified sender) on both the API and notification worker via the shared Vercel API project, then redeploy. No email is sent while those settings are absent. Service emails do not depend on marketing opt-in. The outbox retries bounded failures with a stable idempotency key and deterministic PDF bytes; provider acceptance is shown as `submitted`, never as delivered. Delivery/bounce webhooks are not implemented. Complete sender/domain verification, abuse controls and a real inbox test before enabling customer email delivery. Expired verification emails require a new request from the account screen.

PDF download: `/api/orders/{id}/invoice?format=pdf`, authenticated to the order owner. The endpoint retains HTML for in-browser printing. Bills remain explicitly marked sample until real seller/tax details and payment integration are supplied. Google sign-in still needs `GOOGLE_CLIENT_ID`; configuring email delivery does not enable Google OAuth or phone OTP.
