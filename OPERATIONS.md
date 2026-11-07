# Restaurant operations

Implemented 7 November 2026 for Dum & Dastaan.

## Central menu CMS

Administrators use **Catalogue** to create/edit dishes, descriptions, portions, base prices, city prices, photo URLs/credits, dietary marks, allergens and spice level. They can add weekday serving windows in India time. Empty schedule means all day; overnight windows continue into the next day. A dish outside its serving hours is hidden from the outlet menu and rejected at quote/payment time, including automatic routing.

Price priority: outlet override → matching city price → base price. City names match after trimming and lowercasing. **Assignments** controls outlet membership, outlet city and price overrides; kitchen **Availability** controls stock. Prices remain integer paise internally, but all editing controls accept rupees. CMS photos use HTTPS or existing `/images/` assets; the browser loads them without a server-side image proxy. The administrator is responsible for image ownership and licence credits.

Existing photos and prices are preserved. Existing dishes are all-day until a schedule is explicitly configured; spice level remains unspecified until the kitchen supplies it. No city prices or spice facts are fabricated.

## Kitchen display

Outlet-bound kitchen staff/managers see only their queue. New → Preparing → Ready for pickup → Handed off uses version checks and records stage timestamps. The screen refreshes every five seconds, updates elapsed timers each second and marks overdue preparation in colour. Existing late-manager alerts remain ten minutes after the original promise. An optional rider/pickup reference is encrypted, and COD/deposit orders require confirmation that the outstanding balance was collected before handoff. This is a staff-recorded handoff, not live rider GPS or delivery completion.

Managers may cancel accepted orders before handoff with a customer-visible reason. Customers may cancel their own unpaid orders. Cancellation and points release commit together. Test payments are marked refunded in the test environment; if real payments are introduced, the state is `REFUND_REQUIRED` until a gateway refund workflow is added. No live refund is claimed.

## Loyalty

Approved policy: earn one point per ₹100 paid on direct orders; one point pays ₹1 at checkout. Points are awarded once, only at paid handoff. Earnings use the cash/payment amount after loyalty credit, rounded down per order. No rewards are backfilled for historical handoffs. No expiry is configured.

Points are a separate payment credit against the existing GST-inclusive menu total, not a price discount. Invoice snapshots show gross menu total, loyalty credit, paid amount and balance separately. This remains sample billing; production tax/accounting treatment needs merchant approval with the live payment setup.

The server validates balance and maximum credit. Points are reserved/debited when the order is created, including while payment is pending, and returned once on cancellation. A failed payment can be retried without another debit; customers can cancel an abandoned unpaid order to release its reservation. Customer-row locks serialize redemption/earning/refunds; unique order/kind ledger entries prevent duplicate effects. An all-points order needs no external payment and earns zero points. UI estimates are never trusted for money or reward balances.

## Party orders

Customers use **Party orders** from the header/footer/account. Name and phone are taken from the saved profile. Venue, menu/dietary preferences, party contact details and manager replies are encrypted. Event times are entered/displayed in IST and the server enforces a full 48-hour notice. Requests up to one year ahead and 1–1,000 guests are accepted for manual review; these bounds are input limits, not promised capacity.

Submission creates `REQUESTED`, not a paid booking or a regular kitchen order. Only central admins and a dedicated outlet-bound `catering_manager` may confirm/decline, with a required customer-visible message. The manager must agree pricing, menu and logistics; there is no automated catering quote, deposit or dispatch. Customers see decisions on the party page, refreshed every 15 seconds. No catering email/SMS notification is claimed.

Provision a dedicated manager using the existing secure prompt (no password argument):

```sh
cd backend
../.venv/bin/python provision_manager.py EMAIL OUTLET_ID catering_manager
```

Existing admins can review catering immediately. No new production staff identity or password is invented.

## Outlet reporting

Admins see every outlet; outlet managers see their own. Choose the last 7, 30 or 90 rolling days. Counts use order creation time and distinguish placed, accepted, cancelled and handed off. Gross sales exclude unpaid/cancelled orders. Measured preparation time is accepted-to-ready, with sample count; historical orders without stage timestamps are excluded. Repeat customers have at least two completed handoffs at the same outlet within the selected period. No customer contact details are exposed by the dashboard.

## Deployment and validation

Migration 006 adds columns/tables without rewriting historical orders or granting historical points. Migration 005 now tolerates a fresh database already created by the initial metadata migration. Migration 006 works for both an existing v005 database and a fresh setup. No existing production role is changed.

Validation includes PostgreSQL row-lock concurrency for spending points, reward/refund idempotency, overnight schedules, city/override pricing, access boundaries, catering notice/encryption, invoice credit rendering, and the customer→kitchen→rewards browser flow. Production-peak load and two-metre tablet readability still require representative hardware/traffic validation; these checks are not load or field studies.

## Automation safeguards (8 November 2026)

Order routing continues to enforce service area, opening status, serving windows and stock at checkout/payment. Reorder suggestions use only the signed-in customer's accepted, non-cancelled orders, hide closed outlets and currently unavailable dishes, and never add anything to the cart.

Prep prediction validates the model structure, numeric values and non-negative workload coefficients. Missing, malformed, non-finite or non-positive predictions use the queue/portion fallback. For workloads outside the synthetic training ranges, the promise uses the higher of the model and the queue fallback. The outlet minimum always applies. The estimate source is retained on the order; none of these safeguards claims calibrated statistical confidence.

After an outlet has at least 20 valid ready timestamps, the estimate also cannot be below the observed 90th-percentile accepted-to-ready duration from its latest 200 ready/handed-off orders accepted in the last 28 days. Cancelled orders, missing/invalid/future timestamps and other outlets are excluded. This conservative floor automatically uses actual kitchen observations without claiming that the synthetic model has been retrained. It can overestimate small orders after large catering-like loads; managers should review actual kitchen capacity and timing quality. Fewer than 20 observations leaves this safeguard inactive; no history is fabricated.

The ten-minute overdue worker still uses the original promise, creates one customer notice and one outlet-manager alert, and excludes ready/handed-off orders. Manager overrides retain the original promise and audit trail, cannot go below the estimate/minimum floor, and now reject blank/control-character reasons. WhatsApp/SMS remain a prepared provider bridge: pending is not delivered, failed submissions retry with backoff, and an unconfigured provider does not prevent in-app notices.

Regression coverage includes corrupted models, unfamiliar load, insufficient/history-isolated/stale measurements, cancelled-order recommendations, closed outlets and meaningful manager explanations, alongside the existing alert deduplication, stock routing and message-failure tests. Real kitchen calibration, provider delivery and production-load validation remain separate release requirements.

## Dedicated staff workspace (8 November 2026)

`/staff` and `/staff/signin` provide an assigned-account entrance without customer shopping navigation. Staff authentication rejects customer accounts and unassigned outlet staff before creating a session. Existing customer sign-in also takes authenticated staff to `/staff`. No public staff registration is offered. These routes are noindex and excluded from robots crawling; API role checks are the actual access protection.

Kitchen staff land on their live outlet queue and have availability controls plus paginated order history. Managers also have performance reports, cancellations and timing overrides; admins can select outlets and use central catalogue/catering tools. Catering managers see their catering desk. History filters confirmed/cancelled orders by stage, shows preparation details and loads older batches of 50. Pending payments stay out of kitchen history. A failed queue refresh blocks kitchen mutations until a successful refresh; no empty queue is shown before the first successful load.

Create an actual assigned staff account with the existing secure password prompt:

```sh
cd backend
../.venv/bin/python provision_manager.py STAFF_EMAIL OUTLET_ID kitchen
# Other supported roles: manager, catering_manager
```

Use an operator-approved email/outlet and a unique password. No production staff account was invented or created during implementation. This is administrator provisioning, not an invitation-email or password-recovery service. Staff history and authentication tests use isolated synthetic accounts; browser layout tests use mocked API fixtures, separately from backend access-control tests.

### Persistent outlet staff accounts

`provision_staff_accounts.py` creates Ayaan/Meera (Kondapur), Kabir/Nisha (Gachibowli), and Arjun/Sana (Madhapur), pairing a kitchen operator and manager at each outlet. Their `@dastan.local` identities are sign-in names, not deliverable mailboxes. Accounts are ordinary persistent users, not test-fixture or seed-only users. Each gets a separately generated random password stored as Argon2 in the database; names/emails remain encrypted with keyed lookup indexes. The one-time local credential handover is mode 0600 and gitignored. Existing identities are never reset or silently reassigned. Keep the handover in the operator's password manager and remove the local copy after distribution.

Confirmed prepaid or eligible COD orders appear in the assigned outlet queue with a preparation promise. Preparing, ready-for-pickup and rider-handoff actions update the same order; customer tracking polls every four seconds and kitchen queues every five. Handoff requires outstanding COD collection confirmation. Handoff is not proof of delivery; no customer-delivered status or rider GPS is fabricated. Gateway payment is still simulated, and external messaging still needs provider configuration.
