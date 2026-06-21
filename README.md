# Medraxis — Unified Healthcare Business Platform

Medraxis is a **Django reimplementation inspired by the [OpenMRS](https://openmrs.org/)
architecture**, extended into a single integrated platform for clinics,
diagnostic centres, laboratories, pharmacies and medical businesses. It combines:

1. **EMR** — clinical records, modelled on the OpenMRS data model & workflows.
2. **LIS / LIMS** — laboratory ordering, specimen tracking and result
   verification (feature-inspired by FLabs).
3. **Pharmacy, Inventory & POS** — batch/expiry stock control, dispensing,
   GST-ready invoicing and payments (feature-inspired by Valeron Pro & Vyapar).

> One concept dictionary, one patient timeline, one stock ledger — so a
> consultation, a lab test, a prescription and a sale are all part of the same
> integrated record. See [`docs/research.md`](docs/research.md) for the full
> system-design research.

---

## Why it's built this way

The core architectural choices come straight from OpenMRS, because they solve
the hard problems of clinical software (see [`docs/research.md`](docs/research.md)):

- **Concept dictionary** — everything observable/orderable is defined once.
- **`Obs`** — one flexible table stores vitals, diagnoses and lab results.
- **`Encounter` / `Visit`** — attributable, grouped clinical events.
- **Soft deletion** (`voided`/`retired`) + **UUIDs** — never lose history;
  ready for FHIR.
- **Generic `Order`** — specialises into `TestOrder` (LIS) and `DrugOrder`
  (pharmacy), unifying lab requests and prescriptions.

## Documentation

| Doc | Contents |
|---|---|
| [`docs/research.md`](docs/research.md) | Full system-design research, source-system mapping, FHIR readiness |
| [`docs/requirements.md`](docs/requirements.md) | Roles, user stories, functional & non-functional requirements |
| [`docs/erd.md`](docs/erd.md) | Mermaid ER diagrams per domain + normalization notes |
| [`docs/api.md`](docs/api.md) | API reference, auth, conventions, workflow actions |
| [`docs/platform_features.md`](docs/platform_features.md) | FHIR facade, HL7/ASTM interfacing, async notifications/reports, PDF printing, multi-tenancy |
| [`docs/openmrs_coverage.md`](docs/openmrs_coverage.md) | Model-by-model coverage map vs. the OpenMRS Java domain model |
| [`docs/flabs_research.md`](docs/flabs_research.md) | Reverse-engineered FLabs LIS analysis + gap closure (catalogue, B2B/branch, microbiology, QC, auto-verification, WhatsApp delivery) |
| [`docs/business_ops_research.md`](docs/business_ops_research.md) | Reverse-engineered Valeron/Vyapar analysis + the accounting backbone (accounts, expenses, payables, party ledger, quotations, returns, GST) |
| [`docs/payment_gateways.md`](docs/payment_gateways.md) | Payment-gateway design + Stripe / Flutterwave (mobile money) / Lenco integration |
| [`SKILLS.md`](SKILLS.md) | Engineering standards followed by this project |

## Project structure

```
medraxis/
├── config/                 # settings (base/local/production), urls, celery, api_router
├── apps/
│   ├── core/               # OpenMRS base models, middleware, audit, RBAC plumbing, PDF helpers
│   ├── tenancy/            # Organization (tenant), Membership, request scoping
│   ├── users/              # custom User, Role/Privilege RBAC, Provider
│   ├── emr/                # Concept dictionary, Person/Patient, Encounter, Obs, Order, Programs
│   ├── lis/                # LabTest, TestOrder, Specimen, LabResult, Analyzer, HL7/ASTM drivers
│   ├── inventory/          # Product, StockBatch, StockTransaction ledger, PurchaseOrder
│   ├── pharmacy/           # DrugOrder, Dispense (stock-coupled)
│   ├── pos/                # Sale, SaleLine, Payment, Customer, PDF receipts
│   ├── billing/            # BillableService, InsuranceScheme, PatientInsurance
│   ├── finance/            # Cash/bank accounts, expenses, supplier payments, party ledger, GST components
│   ├── payments/           # Payment gateways: Stripe, Flutterwave (mobile money), Lenco
│   ├── notifications/      # Celery notifications + async report generation
│   └── fhir/               # FHIR R4 read/search facade (/fhir/)
├── docs/                   # research, erd, requirements, api
├── manage.py
├── requirements.txt
└── .env.example
```

Each app owns its `models`, `services` (business logic), `api/` (serializers,
views, routers) and `admin`. Views stay thin; multi-step workflows live in
`services.py` and run atomically.

## Quick start

```bash
# 1. Create a virtualenv and install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env          # edit DJANGO_SECRET_KEY etc.

# 3. Apply migrations (SQLite by default)
python manage.py migrate

# 4. Seed reference data (+ optional demo dataset)
python manage.py seed --demo

# 5. Create an admin login
python manage.py createsuperuser

# 6. Run
python manage.py runserver
```

Then open:

- Admin: <http://localhost:8000/admin/>
- Swagger API docs: <http://localhost:8000/api/docs/>
- ReDoc: <http://localhost:8000/api/redoc/>

### PostgreSQL (production)

Set `DATABASE_URL` and use the production settings:

```bash
export DJANGO_SETTINGS_MODULE=config.settings.production
export DATABASE_URL=postgres://medraxis:secret@localhost:5432/medraxis
python manage.py migrate
```

## Running tests

```bash
python manage.py test apps
```

The suite covers the integrative workflows: lab result entry/verify/release →
patient `Obs`, FEFO inventory issuing with rollback on shortage, POS totals
(discount + GST) and stock-coupled sale completion, and patient-registration
RBAC enforcement.

## Tech stack

Python 3.11+ · Django 5.1 · Django REST Framework · SimpleJWT · django-filter ·
drf-yasg (Swagger/OpenAPI) · Celery + Redis · PostgreSQL (prod) / SQLite (dev).

## Security & compliance highlights

Environment-based secrets · JWT + session auth with refresh rotation ·
server-side RBAC on protected endpoints · throttling · audit log + soft-delete
trails · immutable payments & append-only stock ledger · production hardening
(HTTPS/HSTS/secure cookies). See [`docs/requirements.md`](docs/requirements.md).

## Platform capabilities

Built on top of the core domains (see [`docs/platform_features.md`](docs/platform_features.md)):

- **FHIR R4 facade** at `/fhir/` (Patient, Encounter, Observation, ServiceRequest,
  MedicationRequest, DiagnosticReport, Organization) with tenant scoping.
- **Analyzer interfacing**: dependency-free HL7 v2 and ASTM drivers that ingest
  instrument results, match them to open orders and record auto-flagged results.
- **Async notifications & reports** via Celery (email/SMS/in-app, idempotent;
  CSV report generation) — runs eagerly without a broker in dev/tests.
- **PDF printing**: invoices/receipts, specimen labels and patient lab reports.
- **Multi-tenant facility scoping**: row-level isolation by `Organization`,
  fail-closed on unauthorized `X-Organization` headers.

## Status

Implemented across eleven apps: full data model, migrations, REST API, the
integrative clinical/lab/pharmacy/POS workflows, the platform capabilities
above, seed data, **31 passing tests**, and documentation. A front-end and
write-side FHIR remain on the roadmap — neither requires reworking the data
model.

## License & attribution

OpenMRS, FLabs, Valeron Pro and Vyapar are referenced **as design inspiration
only**; Medraxis is an independent Django implementation and contains none of
their source code or branding.
