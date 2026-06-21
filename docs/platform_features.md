# Medraxis — Platform Features (FHIR, Interfacing, Async, Printing, Multi-tenancy)

This document covers the platform capabilities built on top of the core
EMR/LIS/POS domains: the FHIR facade, analyzer interfacing, asynchronous
notifications/reports, PDF printing and multi-tenant facility scoping.

---

## 1. Multi-tenant facility scoping (`apps/tenancy`)

Row-level multi-tenancy: an **`Organization`** (facility/tenant) owns its data;
tenant-scoped records carry a nullable `organization` FK and are isolated per
request.

### How a request is scoped
Because DRF authenticates inside the view (not in middleware), the tenant is
resolved **after authentication**:

- **API (DRF):** `TenantResolverMixin.initial()` resolves the organization from
  the `X-Organization` header or the user's default `Membership`, sets it in a
  thread-local, and stamps `request.organization`.
- **Admin/session:** `TenantMiddleware` resolves eagerly (the user is already
  known) and always clears the thread-local at request end.

### Guarantees
- **Writes** are auto-stamped: `TenantScopedModel.save()` assigns the active
  organization on create (no caller plumbing).
- **Reads** are filtered: `TenantScopedQuerySetMixin.get_queryset()` restricts
  results to the active organization.
- **Fail-closed:** an `X-Organization` header naming an organization the user
  cannot access returns **403**, never a silent unscoped response.
- **Scoped models:** `Patient`, `Visit`, `Encounter`, `Order` (and its
  `TestOrder`/`DrugOrder` subclasses), `Location`, `Product`, `Specimen`, `Sale`.

### API
`/api/v1/organizations/` (incl. `current/`, `mine/`), `/api/v1/memberships/`.
Send `X-Organization: <slug>` to act within a specific facility.

---

## 2. FHIR R4 facade (`apps/fhir`)

A read/search FHIR R4 server mounted at **`/fhir/`**, projecting Medraxis models
to FHIR resources. Querysets are tenant-scoped.

| Interaction | Endpoint |
|---|---|
| Capability statement | `GET /fhir/metadata` |
| Search | `GET /fhir/{ResourceType}?<params>` → `Bundle` |
| Read | `GET /fhir/{ResourceType}/{id}` |

Supported resources & key search params:

| Resource | Backed by | Search |
|---|---|---|
| Patient | `Patient`/`Person` | `identifier`, `name`, `family`, `gender` |
| Encounter | `Encounter` | `patient`, `subject` |
| Observation | `Obs` | `patient`, `code` |
| ServiceRequest | `Order` | `patient` |
| MedicationRequest | `DrugOrder` | `patient` |
| DiagnosticReport | `TestOrder` (+results) | `patient` |
| Organization | `Organization` | — |

Concept terminology mappings (LOINC/SNOMED/ICD-10/RxNorm) surface as FHIR
`coding`. Errors return a FHIR `OperationOutcome`. Writes are out of scope for
this iteration (read facade).

---

## 3. Analyzer interfacing — HL7 / ASTM drivers (`apps/lis/drivers`, `apps/lis/ingest.py`)

Laboratory instruments push results that are parsed and matched to open orders.

- **Drivers** (`drivers/hl7.py`, `drivers/astm.py`) are dependency-free parsers
  that normalise a transmission into `ResultMessage` records. They are lenient:
  a bad segment is logged, not fatal.
- **Ingestion** (`ingest.py`) matches each result to an open `TestOrder` via the
  **specimen accession number** and an analyte code (matching the test code,
  analyte short name, or a terminology mapping such as LOINC), then records a
  `LabResult` in the **ENTERED** state with an auto-computed flag. Verification
  and release remain human steps (two-person rule preserved).
- **Audit:** every transmission is stored as an `AnalyzerMessage` (raw payload +
  match/parse log), so results are replayable and traceable.

### API
- `POST /api/v1/lab/messages/ingest/` — submit `{protocol: HL7|ASTM, raw_payload, analyzer?}`.
- `GET /api/v1/lab/messages/` — review transmissions and outcomes.
- Async variant: `apps.lis.tasks.ingest_analyzer_message_task` (Celery).

---

## 4. Asynchronous notifications & reports (`apps/notifications`)

Celery-backed so request handlers never block. Runs **eagerly** when no broker
is configured (default), so it works in dev/tests without a worker.

### Notifications
- Channels: **email** (Django backend), **SMS** (pluggable via
  `NOTIFICATIONS_SMS_BACKEND`), **in-app**.
- `queue_notification(...)` creates a row and enqueues delivery; **idempotent**
  on `dedupe_key` (no duplicate alerts).
- Retries transient failures (`send_notification_task`, max 3).
- Event-driven example: a released **critical** lab result alerts the ordering
  provider (`signals.py`).
- API: `/api/v1/notifications/` (in-app inbox, `unread/`, `mark_read/`).

### Reports
- Async generation into a downloadable file on a `ReportRun`
  (`generate_report_task`). Tenant-aware.
- Built-in reports: `daily_sales`, `stock_valuation`, `expiring_stock`,
  `lab_turnaround` (register more in `reports.REPORT_REGISTRY`).
- API: `POST /api/v1/reports/` (request), `GET /api/v1/reports/` (track +
  download), `GET /api/v1/reports/types/`.

---

## 5. PDF printing (`apps/core/pdf.py`, `apps/*/documents.py`)

Reportlab-based document builders returning raw PDF bytes, served inline.

| Document | Endpoint | Builder |
|---|---|---|
| Invoice / receipt | `GET /api/v1/pos/sales/{id}/receipt/` | `pos/documents.py` |
| Specimen label (label-printer sized) | `GET /api/v1/lab/specimens/{id}/label/` | `lis/documents.py` |
| Patient lab report | `GET /api/v1/lab/test-orders/{id}/report/` | `lis/documents.py` |

Documents render an organization-branded header (`apps/core/pdf.org_header`)
so output is per-tenant.

---

## 6. Configuration notes

| Setting | Purpose | Default |
|---|---|---|
| `REDIS_URL` | Cache + Celery broker/result backend | unset → local cache, eager Celery |
| `CELERY_TASK_ALWAYS_EAGER` | Run tasks inline | `True` when no broker |
| `NOTIFICATIONS_SMS_BACKEND` | Dotted path to `send(to, body)` | console logger |
| `DEFAULT_FROM_EMAIL` | From address for email notifications | `no-reply@medraxis.local` |
| `X-Organization` (header) | Select active tenant for a request | user's default membership |

For production, set `REDIS_URL` and run a Celery worker (and beat for
`process_due_notifications`):

```bash
celery -A config worker -l info
celery -A config beat -l info
```
