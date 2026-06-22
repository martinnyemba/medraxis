# Medraxis — System Design Research

> A Django reimplementation **inspired by OpenMRS**, extended into one unified
> healthcare business platform that also absorbs the ideas behind FLabs (LIS),
> Valeron Pro and Vyapar (POS / inventory / business operations).

This document is the design research requested in the brief. It explains
**what** we are building, **why** the architecture looks the way it does, and
**how** each source system maps onto our Django data model and workflows.

---

## 1. Goal and scope

Build a single, modular, configurable, healthcare-focused platform that behaves
as **one integrated system** for clinics, diagnostic centres, laboratories,
pharmacies and medical businesses, combining:

1. **EMR** — clinical records, inspired by OpenMRS.
2. **LIS / LIMS** — laboratory workflow, inspired by FLabs.
3. **POS, inventory & business operations** — inspired by Valeron Pro and Vyapar.

The unifying decision: **everything orderable or observable is a `Concept`, and
every request for a service or product is an `Order`.** A lab test, a
prescription and a consultation are all orders on the same patient timeline;
stock for a pharmacy and stock for a retail counter is the same ledger. This is
what makes the system *integrated* rather than three apps sharing a login.

---

## 2. Why OpenMRS as the architectural spine

OpenMRS is a mature, internationally deployed EMR whose design has been refined
over ~15 years. We follow its **architecture and data model** (not its Java
code line-by-line), because it solves the hard problems of clinical software:

| OpenMRS principle | What it gives us | Where it lives in Medraxis |
|---|---|---|
| **Concept dictionary** (EAV) | One definition of every clinical idea; analysable, interoperable data instead of free text | `apps/emr/models/concept.py` |
| **Observation model (`Obs`)** | A single flexible table stores vitals, diagnoses, lab results, anything | `apps/emr/models/obs.py` |
| **Encounter / Visit grouping** | Clinical events are grouped and attributable (who/what/where/when) | `apps/emr/models/encounter.py`, `visit.py` |
| **Soft deletion** (`voided` / `retired`) | Clinical & legal requirement: never hard-delete; keep an audit trail | `apps/core/models.py` base classes |
| **Universally unique IDs** (`uuid`) | Stable identity for FHIR/HL7 and cross-system references | `BaseOpenmrsObject.uuid` |
| **Metadata vs Data split** | Reference/config (`retired`) behaves differently from transactional data (`voided`) | `BaseOpenmrsMetadata` / `BaseOpenmrsData` |
| **Order model** | A generic request lifecycle that specialises into TestOrder / DrugOrder | `apps/emr/models/order.py` |
| **Provider / Role / Privilege** | Clinical authorship + fine-grained RBAC | `apps/users/models.py` |
| **Module/extensibility** | Add capability without forking core | Django apps + `GlobalProperty` + `PersonAttributeType` |

### The OpenMRS object hierarchy, in Django

OpenMRS Java has `BaseOpenmrsObject` → `BaseOpenmrsData` / `BaseOpenmrsMetadata`.
We translate this to **abstract Django models** that every domain model extends:

```
BaseOpenmrsObject         uuid
├── BaseOpenmrsData        + creator/created_at, changed_by/changed_at,
│                            voided/voided_by/voided_at/void_reason
│                            (Patient, Encounter, Obs, Order, Visit, Specimen…)
└── BaseOpenmrsMetadata    + name, description, retired/retired_by/…
                             (ConceptClass, EncounterType, Location, LabTest…)
```

`objects` hides voided/retired rows by default; `all_objects` exposes the full
table for auditing and restore. Audit stamping (`creator`, `changed_by`) is
applied automatically in `save()` via a thread-local current-user middleware,
mirroring OpenMRS's interceptor approach without threading the user through
every call.

---

## 3. The three source systems and how we absorb them

We were told to study **features, not branding**. Here is the feature
inspiration we extracted and where each lands in the build.

### 3.1 EMR — inspired by OpenMRS
Patient registration & identifiers, the concept dictionary, encounters &
visits, observations, allergies/conditions/diagnoses, orders, care programs,
location hierarchy, and a provider/role/privilege security model.
→ `apps/emr`, `apps/users`.

### 3.2 LIS / LIMS — inspired by FLabs
A laboratory needs more than "an order":

| LIS feature | Medraxis design |
|---|---|
| Test catalogue with sections, sample type, TAT, price, LOINC | `lis.LabTest`, `lis.LabSection`, `lis.SpecimenType` |
| Lab request that is still part of the patient record | `lis.TestOrder` **extends** `emr.Order` (multi-table inheritance) |
| Specimen / accession tracking with status lifecycle | `lis.Specimen` (ORDERED→COLLECTED→RECEIVED→…→DISPOSED) |
| Result entry → technical verification → release | `lis.LabResult` + `lis/services.py` (two-person rule) |
| Auto high/low/critical flagging from reference ranges | `services.compute_flag()` using `Concept` normal/critical limits |
| Results appear on the patient chart | release creates an `emr.Obs` linked to the order |
| Instrument (analyzer) integration HL7/ASTM | `lis.Analyzer`, `lis.Worklist` |

**Integration point:** releasing a verified result writes an `Obs` and advances
the `Order.fulfiller_status` to `COMPLETED` — so the EMR, the lab and the bill
all see the same truth.

### 3.3 POS / Inventory / Business — inspired by Valeron Pro & Vyapar
| Feature | Medraxis design |
|---|---|
| Product catalogue (drugs + general goods) | `inventory.Product` (with `is_drug`, `drug_concept` link) |
| Batch & expiry tracking, FEFO issuing | `inventory.StockBatch` + `services.issue_stock()` |
| Append-only stock ledger (auditable on-hand) | `inventory.StockTransaction` |
| Suppliers & purchase orders / goods receipt | `inventory.Supplier`, `PurchaseOrder(Item)` |
| GST/VAT, HSN/SAC codes, tax-inclusive invoicing | `inventory.TaxRate`, line-level tax on `pos.SaleLine` |
| Invoices mixing products **and** services | `pos.Sale` + `pos.SaleLine` (PRODUCT / SERVICE / LAB_TEST / CONSULTATION) |
| Split payments (cash/card/mobile money/insurance) | `pos.Payment` |
| Walk-in customers vs registered patients | `pos.Customer` (optional `patient` link) |
| Reorder levels & expiry alerts | `Product.reorder_level`, `services.expiring_soon()` |

**Integration point:** completing a `Sale` issues stock through the *same*
inventory ledger the pharmacy uses; a `Dispense` in pharmacy and a `SALE` line
in POS are two doors into one stockroom.

---

## 4. How the modules connect (the integration map)

```
                    ┌──────────────────────────────────────────┐
                    │              Concept dictionary           │
                    │  (tests, drugs, diagnoses, questions …)   │
                    └──────────────────────────────────────────┘
                         ▲             ▲              ▲
            references   │             │ references   │ references
        ┌────────────────┴───┐   ┌─────┴──────┐   ┌───┴───────────────┐
        │        EMR         │   │    LIS     │   │   Inventory       │
        │ Patient/Encounter  │   │ LabTest /  │   │ Product (is_drug, │
        │ Obs / Order        │   │ TestOrder  │   │  drug_concept)    │
        └─────────┬──────────┘   └─────┬──────┘   └───────┬───────────┘
                  │  Order (base)      │ extends          │ stock ledger
                  │◄───────────────────┘                  │
                  │  Order (base)                          │
                  │◄──────────────┐                        │
        ┌─────────┴──────┐   ┌────┴───────┐        ┌───────┴───────────┐
        │   Pharmacy     │   │  (Drug/    │        │        POS        │
        │ DrugOrder/     │   │   Test     │        │  Sale/SaleLine/   │
        │ Dispense ──────┼───┤  orders)   │        │  Payment ─────────┼──► stock
        └────────────────┘   └────────────┘        └───────────────────┘
                  │                                         │
                  └─────────────► Billing ◄─────────────────┘
                         (BillableService, Insurance)
```

Key shared joins:
- `Order` is the single base for `TestOrder` (LIS) and `DrugOrder` (pharmacy) →
  one patient timeline, one numbering scheme, one fulfilment lifecycle.
- `Product.drug_concept` ties a sellable item to its clinical drug concept.
- `StockTransaction` is the one funnel for receipts, dispenses, sales,
  adjustments, transfers and wastage.
- `Sale` can bill a `Product`, a `LabTest` or a `BillableService` on one invoice.

---

## 5. Architecture & technology decisions

- **Modular Django apps** by business domain: `core, users, emr, lis, inventory,
  pharmacy, pos, billing`. Apps own their models, services, serializers and
  router; `config/api_router.py` only composes them.
- **Thin views, fat services.** Workflows with side effects (result release,
  stock issue, sale completion, dispensing) live in `app/services.py` and run
  inside `transaction.atomic()` so clinical and financial state never drift.
- **DRF API** under `/api/v1/`, JWT + session auth, consistent error envelope,
  page-number pagination, filtering/search/ordering, Swagger/ReDoc docs.
- **RBAC** via OpenMRS-style `Privilege`/`Role` with role inheritance, enforced
  server-side by the `HasPrivilege` permission class.
- **PostgreSQL** in production (via `DATABASE_URL`), SQLite for local/tests.
- **Celery + Redis** for background work (notifications, report/PDF generation,
  analyzer polling, reconciliation); eager mode when no broker is configured.
- **Auditability everywhere:** soft deletes, `AuditLog`, append-only stock
  ledger, immutable payments.

---

## 6. FHIR / interoperability readiness

The model is deliberately FHIR-shaped so a resource layer can be added without
schema churn:

| FHIR resource | Backing model(s) |
|---|---|
| Patient | `Patient` + `Person`, `PersonName`, `PersonAddress`, `PatientIdentifier` |
| Practitioner / PractitionerRole | `users.Provider`, `EncounterProvider` |
| Encounter | `Encounter` (+ `Visit`) |
| Observation | `Obs` (and released `LabResult`) |
| Condition / AllergyIntolerance | `Condition`, `Allergy` |
| ServiceRequest | `Order` / `TestOrder` |
| MedicationRequest / MedicationDispense | `DrugOrder` / `Dispense` |
| DiagnosticReport | `TestOrder` + its `LabResult`/`Obs` set |
| Location / Organization | `Location` (tagged) |
| Coding / CodeSystem | `ConceptReferenceTerm`, `ConceptSource`, `ConceptMapping` (LOINC/SNOMED/ICD-10/RxNorm) |

Every record exposes a stable `uuid`, the natural FHIR `id`.

---

## 7. Security, compliance & non-functional requirements

- Environment-based secrets (`django-environ`); nothing hardcoded.
- Strong password hashing (Django), JWT with refresh rotation, throttling.
- Server-side authorization on every protected endpoint; never trust the client.
- Audit log for sensitive actions + authentication events; soft-delete trails.
- Production hardening: HTTPS redirect, secure cookies, HSTS, nosniff, X-Frame.
- Data integrity: FKs with deliberate `on_delete`, unique constraints, indexes
  on high-traffic filters/joins, atomic multi-step workflows.
- Scalability: pagination everywhere, `select_related`/`prefetch_related`,
  date/ledger tables designed for future partitioning.

---

## 8. Extensibility (the "module" spirit of OpenMRS)

Three mechanisms let deployments adapt without forking core:

1. **`GlobalProperty`** — runtime configuration (identifier formats, locale,
   currency, tax behaviour) editable by admins.
2. **`PersonAttributeType` / typed attributes** — add demographic fields
   (next-of-kin, insurance number, occupation) without migrations.
3. **New Django apps** — drop-in domains (radiology, billing claims, telehealth)
   that reuse the `Concept`/`Order`/`Obs` spine and register their own routes.

---

## 9. What is implemented in this iteration vs. roadmap

**Implemented:** full data model across all 8 apps; migrations; RBAC; audit
infrastructure; REST API for the core resources of every domain; the three
integrative workflows (lab result release → Obs, FEFO stock issue,
sale completion + payment, pharmacy dispense); idempotent seed; tests; Swagger.

**Roadmap (designed for, not yet built):** FHIR REST facade, HL7/ASTM analyzer
drivers, Celery notification/report tasks, label/receipt PDF printing,
multi-tenant facility scoping, GraphQL for complex client queries, and a
front-end. None of these require reworking the data model — that is the point of
following the OpenMRS architecture.

See [`packaging_architecture.md`](packaging_architecture.md) for how
medraxis's *build/bundle* architecture compares to OpenMRS's (Maven/`.omod`
modules, the O3 Module Federation frontend, and the `docker-compose`-based
distro), and the resulting packaging decisions.

---

## 10. References (used as design inspiration only)

- OpenMRS — <https://openmrs.org/>, source <https://github.com/openmrs>,
  developer docs on the OpenMRS Atlassian wiki.
- FLabs LIS — <https://flabslis.com/> (laboratory workflow features).
- Valeron Pro — <https://www.valeronpro.com/> (clinic business operations).
- Vyapar — <https://vyaparapp.in/> (GST invoicing, inventory, billing).
- HL7 FHIR R4 (interoperability target).
