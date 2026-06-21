# Medraxis — Requirement Analysis

## 1. Business goal

Provide clinics, diagnostic centres, laboratories, pharmacies and medical
businesses with **one integrated system** covering clinical care (EMR),
laboratory operations (LIS), medication management (pharmacy) and commercial
operations (inventory, POS, billing) — instead of several disconnected tools.

## 2. User roles

| Role | Responsibilities | Representative privileges |
|---|---|---|
| Receptionist / Registrar | Register patients, start visits | View/Add Patients |
| Clinician (Doctor/Nurse) | Consult, observe, diagnose, order tests & drugs | View/Add/Edit Patients, Add Observations |
| Lab Technologist | Receive specimens, enter & verify results | Manage Lab Results |
| Pathologist / Lab Manager | Verify/release results, manage catalogue | Manage Lab Results |
| Pharmacist | Dispense drugs, manage stock | Manage Inventory, Run POS |
| Cashier | Create invoices, take payments | Run POS |
| Store Manager | Receive stock, raise purchase orders | Manage Inventory |
| System Administrator | Configure metadata, users, roles | All privileges |

RBAC is enforced server-side via OpenMRS-style `Privilege`/`Role`
(with role inheritance) and the `HasPrivilege` DRF permission.

## 3. Core workflows (user stories)

- *As a registrar, I want to register a patient and auto-assign a unique
  identifier, so that the patient can be found reliably later.*
- *As a clinician, I want to record vitals and diagnoses against an encounter,
  so that the patient history is complete and analysable.*
- *As a clinician, I want to order a lab test and a prescription in one place,
  so that everything I request sits on one timeline.*
- *As a lab technologist, I want to accession a specimen and enter results that
  auto-flag abnormal values, so that critical results are obvious.*
- *As a lab manager, I want results verified by a second person before release,
  so that quality is assured (two-person rule).*
- *As a pharmacist, I want dispensing to deduct stock by earliest expiry (FEFO),
  so that wastage is minimised and inventory stays accurate.*
- *As a cashier, I want one invoice to bill products, lab tests and services
  with GST and split payments, so that the patient pays once.*
- *As a store manager, I want alerts for low stock and near-expiry batches,
  so that I reorder and rotate stock in time.*

## 4. Functional requirements

1. Patient registration, identifiers, demographics, attributes.
2. Concept dictionary with terminology mapping (LOINC/SNOMED/ICD-10/RxNorm).
3. Visits, encounters, observations, allergies, conditions, diagnoses.
4. Orders (generic) specialised into lab test orders and drug orders.
5. LIS: catalogue, specimen/accession tracking, result entry → verify → release,
   auto-flagging, analyzer integration, worklists.
6. Inventory: products (drugs + goods), batches/expiry, append-only ledger,
   FEFO issue, suppliers, purchase orders, reorder & expiry alerts.
7. Pharmacy: prescriptions and dispensing coupled to inventory.
8. POS: invoices mixing products/tests/services, GST/VAT, discounts, multiple
   payment methods, walk-in customers and registered patients.
9. Billing: billable service catalogue, insurance schemes & policies.
10. RBAC, audit logging, configurable global properties.
11. Versioned REST API with documentation.

## 5. Non-functional requirements

- **Security:** env-based secrets, JWT + session auth, server-side
  authorization, throttling, audit trails, production hardening.
- **Integrity:** soft deletes, atomic multi-step workflows, FK constraints,
  unique constraints, append-only financial/stock records.
- **Performance:** pagination, `select_related`/`prefetch_related`, indexes on
  hot paths, ledger/date tables ready for partitioning.
- **Interoperability:** stable UUIDs, FHIR-shaped model, terminology mappings.
- **Maintainability:** modular apps, thin views/fat services, tests, docs.
- **Configurability:** runtime `GlobalProperty`, typed person attributes,
  drop-in apps for new domains.

## 6. Audit & compliance

- `AuditLog` for sensitive actions and login/logout.
- `voided/retired` soft deletion preserves history with who/when/why.
- Immutable `Payment` records and append-only `StockTransaction` ledger.
- `creator`/`changed_by` stamped automatically on every domain record.

## 7. Edge cases & failure handling

- Insufficient stock on dispense/sale → atomic rollback, clear 400 error.
- Result release blocked unless verified; verification blocked for the same
  person who entered it (two-person rule).
- Re-completing a sale must not double-deduct stock (idempotent via flag).
- Near-expiry / expired batches surfaced; FEFO prevents issuing newer over older.
- Non-unique identifiers handled per `PatientIdentifierType.uniqueness_behavior`.
