# Payment Gateways — Research & Integration Design

Integrates multiple payment providers behind **one provider-agnostic interface**
so the POS/finance layer settles a `Sale` the same way regardless of how the
money arrived: **Stripe** (global cards), **Flutterwave** (African cards + mobile
money: M-Pesa, MoMo, etc.), and **Lenco** (African collections incl. mobile
money & bank).

> Provider APIs are summarised from public docs and used as integration targets.
> All secrets are read from the environment — never stored in code or the DB.

---

## 1. Provider summary (reverse-engineered from public docs)

| Provider | Strengths | Init call (hosted checkout) | Webhook auth | Success signal |
|---|---|---|---|---|
| **Stripe** | Global cards, wallets | `POST /v1/checkout/sessions` (Bearer secret) → `url` | `Stripe-Signature` HMAC-SHA256 over `t.payload` with `whsec_…` | `checkout.session.completed` / `payment_intent.succeeded` |
| **Flutterwave** | Cards + **mobile money** (M-Pesa, MTN/Airtel MoMo), bank, USSD | `POST /v3/payments` (Bearer secret) → `data.link` | `verif-hash` header == configured secret hash | webhook `data.status == "successful"` (confirm via `GET /v3/transactions/{id}/verify`) |
| **Lenco** | African **mobile money** & bank collections | `POST {base}/collections/...` (Bearer API key) → checkout/reference | signature header (HMAC) | webhook `status == "successful"` (confirm via verify endpoint) |

Common shape across all three: **(1)** create a payment → get a reference + a
hosted URL/instructions; **(2)** the customer pays; **(3)** the provider calls our
**webhook** (must verify signature) and/or we **verify** by reference; **(4)** on
success we settle the invoice.

---

## 2. Architecture

```
 POS Sale ──┐
            │  create intent (amount, channel, customer)
            ▼
   PaymentIntent ──► PaymentProvider.initiate() ──► provider hosted checkout/URL
        ▲                                                   │
        │  settle on success                                │ customer pays
        │                                                   ▼
   services.handle_successful_payment() ◄── webhook ── provider callback
        │     (verify signature, idempotent)
        ├─► pos.add_payment(sale, account=…)   (money in + party PAYMENT_IN)
        └─► PaymentIntent.status = SUCCEEDED
```

* **`PaymentProvider`** ABC — `initiate`, `verify`, `verify_signature`,
  `parse_webhook`. One adapter per provider; a registry resolves by code.
* **`PaymentGateway`** (model) — per-tenant, non-secret config (provider, channels,
  test flag, default financial account). **Secrets resolve from env**
  (`settings.PAYMENTS[...]`).
* **`PaymentIntent`** — one payment attempt: amount, channel (CARD/MOBILE_MONEY/
  BANK), provider reference, status, checkout URL, raw response.
* **`WebhookEvent`** — every inbound callback, stored with signature-validity and a
  `processed` flag for **idempotency** (a provider may retry).

---

## 3. Settling into the existing system (no duplication)

A gateway payment is **not** a new money concept — on success it calls the
existing `pos.add_payment(sale, method, amount, account=…)`, which already posts
to the **financial account** (money-in) and the **party ledger** (PAYMENT_IN).
So gateway money lands in exactly the same books as cash. `PaymentIntent` is the
*provider-side* record (reference, status, raw payload) that links a `Sale` to
its external transaction; it does not replace `pos.Payment`.

| New | vs existing | Boundary |
|---|---|---|
| `PaymentIntent` | `pos.Payment` | Intent = the external attempt + provider reference/status; Payment = the settled money line it produces on success. |
| `PaymentGateway` | `finance.FinancialAccount` | Gateway = how money is collected; Account = where settled money is held (gateway has a `settlement_account`). |
| `payments.WebhookEvent` | `notifications` | Inbound provider callbacks (idempotent), not outbound messages. |

---

## 4. Security
- Secrets (`*_SECRET_KEY`, `*_WEBHOOK_SECRET`, `FLW_SECRET_HASH`) come from env via
  `settings.PAYMENTS`; the DB stores none.
- Every webhook **verifies the provider signature** before acting; invalid
  signatures are stored (`signature_valid=False`) and ignored.
- Webhooks are **idempotent** by provider event id; replays are no-ops.
- Webhook endpoints are `AllowAny` (providers are unauthenticated to us) but
  signature-gated; everything else requires auth.
- Amounts/currency are validated against the intent before settling.

## 5. Test strategy
A built-in **`manual`** provider (no network) exercises the full lifecycle
(intent → simulated webhook → Sale settled + account posted) in tests. The real
Stripe/Flutterwave/Lenco adapters are unit-tested on their pure logic —
signature verification and webhook parsing with sample payloads — without live
network or credentials.
