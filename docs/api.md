# Medraxis — API Reference

All endpoints are versioned under `/api/v1/`. Interactive docs:

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI schema: `/api/swagger.json`

## Authentication

JWT (SimpleJWT). Obtain and refresh tokens, then send
`Authorization: Bearer <access>`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/token/` | Obtain access + refresh tokens |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token |
| POST | `/api/v1/auth/token/verify/` | Verify a token |

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "••••••"}'
```

## Conventions

- **Pagination:** `?page=<n>&page_size=<m>` (max 200). Responses include
  `count`, `total_pages`, `current_page`, `next`, `previous`, `results`.
- **Filtering / search / ordering:** `?<field>=<value>`, `?search=<term>`,
  `?ordering=<field>` / `-<field>`.
- **Error envelope:**
  ```json
  {"error": {"status": 400, "type": "ValidationError", "detail": "..."}}
  ```
- **Soft delete:** `DELETE` and list endpoints respect `voided`/`retired`.

## Resource groups

| Prefix | Domain | Notable endpoints |
|---|---|---|
| `users/`, `roles/`, `privileges/`, `providers/` | Access control | `GET users/me/` |
| `concepts/` | Concept dictionary | filter by `concept_class`, `datatype` |
| `patients/` | Registration | `POST` registers person+name+identifier atomically |
| `visits/`, `encounters/`, `observations/`, `orders/` | Clinical activity | |
| `lab/sections/`, `lab/tests/`, `lab/test-orders/`, `lab/specimens/`, `lab/results/`, `lab/analyzers/` | LIS | result actions below |
| `inventory/products/`, `inventory/batches/`, `inventory/transactions/`, `inventory/suppliers/`, `inventory/purchase-orders/`, `inventory/categories/`, `inventory/tax-rates/` | Inventory | |
| `pharmacy/drug-orders/`, `pharmacy/dispenses/` | Pharmacy | dispense issues stock |
| `pos/sales/`, `pos/payments/`, `pos/customers/` | POS | sale actions below |
| `billing/services/`, `billing/insurance-schemes/`, `billing/patient-insurance/` | Billing | |
| `organizations/`, `memberships/` | Tenancy | `GET organizations/current/`, `mine/` |
| `lab/messages/` | Analyzer interfacing | `POST lab/messages/ingest/` (HL7/ASTM) |
| `notifications/`, `reports/` | Async | in-app inbox; `POST reports/` to generate |

### FHIR R4 facade (mounted at `/fhir/`)

| Method | Path | Purpose |
|---|---|---|
| GET | `/fhir/metadata` | CapabilityStatement |
| GET | `/fhir/{ResourceType}` | Search → FHIR `Bundle` |
| GET | `/fhir/{ResourceType}/{id}` | Read a resource |

Resources: Patient, Encounter, Observation, ServiceRequest, MedicationRequest,
DiagnosticReport, Organization. See `docs/platform_features.md`.

### Multi-tenancy

Send `X-Organization: <slug>` to act within a specific facility. Tenant-scoped
list endpoints return only the active organization's records; an unauthorized
organization header returns `403`.

### Document downloads (PDF)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/pos/sales/{id}/receipt/` | Invoice/receipt PDF |
| GET | `/api/v1/lab/specimens/{id}/label/` | Specimen label PDF |
| GET | `/api/v1/lab/test-orders/{id}/report/` | Patient lab report PDF |

## Workflow actions (custom endpoints)

| Action | Endpoint | Effect |
|---|---|---|
| Enter lab result | `POST lab/results/{id}/enter/` | Records value, auto-computes flag, status→ENTERED |
| Verify lab result | `POST lab/results/{id}/verify/` | status→VERIFIED (must differ from enterer) |
| Release lab result | `POST lab/results/{id}/release/` | Creates patient `Obs`, completes order |
| Receive stock | `POST inventory/products/receive/` | Adds batch + RECEIPT ledger entry |
| Low stock | `GET inventory/products/low_stock/` | Products at/below reorder level |
| Expiring batches | `GET inventory/batches/expiring/?days=90` | Near-expiry stock |
| Complete sale | `POST pos/sales/{id}/complete/` | Issues stock for product lines (FEFO) |
| Take payment | `POST pos/sales/{id}/pay/` | Records a payment, updates sale status |

### Example: register a patient

```bash
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"gender": "F", "given_name": "Jane", "family_name": "Banda"}'
```

### Example: complete and pay a sale

```bash
curl -X POST http://localhost:8000/api/v1/pos/sales/1/complete/ -H "Authorization: Bearer $ACCESS"
curl -X POST http://localhost:8000/api/v1/pos/sales/1/pay/ \
  -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"method": "CASH", "amount": "23.63"}'
```

## Permissions

EMR `concepts/` and `patients/` enforce OpenMRS-style privileges
(`View/Add Patients`, `View/Manage Concepts`). Other resources require
authentication; tighten per deployment by setting `required_privilege` /
`required_privilege_map` on the relevant viewset.
