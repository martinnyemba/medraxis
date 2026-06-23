# Pharmacy Review — OpenMRS lens (gap analysis + patches)

> Reviews the pharmacy module (prescribing + dispensing) against OpenMRS order
> semantics and real retail/clinical pharmacy workflows, and records the patches
> made in this pass on **both backend and frontend**.

## 1. Starting point

The pharmacy app was deliberately thin and well-integrated:

- `DrugOrder` is an MTI subclass of the EMR `Order` (shares the patient timeline,
  order number, fulfiller lifecycle) with dosing/route/duration/quantity/refills.
- `Dispense` issues stock through the shared inventory ledger (FEFO) and records
  the price charged, advancing the order to COMPLETED when fully dispensed.
- Frontend: prescriptions list, new prescription, prescription detail with a
  dispensing dialog and history.

What it lacked was the **clinical-safety and order-lifecycle** behaviour a real
pharmacy needs — exactly where OpenMRS invests (allergy module, order
DISCONTINUE/REVISE actions).

## 2. Gap analysis

| Capability (OpenMRS / real pharmacy) | Before | Status |
|---|---|---|
| Prescribe drug order, derive Order plumbing | ✅ | unchanged |
| Dispense against a prescription (FEFO stock draw-down) | ✅ | unchanged |
| Dispensing history + remaining quantity | ✅ | unchanged |
| **Allergy-aware prescribing** (block on documented allergy) | ❌ | **added** (backend gate + check endpoint + UI warning/override) |
| **Discontinue a prescription** (OpenMRS DISCONTINUE action) | ❌ no UI/endpoint | **added** (backend action + UI) |
| **Reverse / return a dispense** (restock) | enum existed, no behaviour | **added** (backend service + `inventory.return_to_stock` + UI) |
| Allergy override is audited | n/a | **added** (recorded in `fulfiller_comment` + audit log) |
| Drug–drug interaction checking | ❌ | recommended (§5) |
| Batch traceability on each dispense | ❌ (lost after FEFO split) | recommended (§5) |
| Refill tracking against `num_refills` | partial (field only) | recommended (§5) |
| Dispense → bill/charge link | ❌ | recommended (§5) |
| Pharmacy dispensing queue (worklist filter) | list only | recommended (§5) |

## 3. What was patched

### Backend

- **`pharmacy.services.check_drug_allergies(patient, product)`** — returns the
  patient's active (non-voided) DRUG allergies whose allergen concept equals the
  product's clinical `drug_concept`. This is the deterministic core of
  allergy-aware prescribing.
- **Allergy gate in `DrugOrderViewSet.perform_create`** — a documented allergy
  blocks prescribing (`400` with the matched allergies) unless the caller passes
  `override_allergy=true`; the override is recorded in the order's
  `fulfiller_comment` and the audit log.
- **`GET /api/v1/pharmacy/drug-orders/allergy_check/?patient=&drug=`** — lets the
  UI warn *before* submit; empty list ⇒ no documented allergy.
- **`POST /api/v1/pharmacy/drug-orders/{id}/discontinue/`** — sets
  `order_action=DISCONTINUE` + `date_stopped` (OpenMRS lifecycle); refuses if
  already inactive.
- **`pharmacy.services.reverse_dispense`** + **`inventory.services.return_to_stock`**
  — returns a dispensed quantity to stock via a RETURN ledger row, marks the
  dispense RETURNED, and reopens the prescription if it had been completed.
  Exposed as `POST /api/v1/pharmacy/dispenses/{id}/reverse/`.
- `DrugOrderSerializer` now exposes `order_action`, `date_stopped`,
  `fulfiller_comment` (read-only) for the UI.

Tests: `apps/pharmacy/tests/test_safety.py` (allergy block/override/check,
discontinue, dispense reversal restock + endpoint). Backend suite green
(pharmacy/inventory/pos: 42 passing).

### Frontend

- **New prescription** proactively calls `allergy_check` once a patient and drug
  are chosen, shows a red **Allergy alert** listing allergen/severity/reaction,
  and blocks submission until an **override** is acknowledged (passing
  `override_allergy`).
- **Prescription detail** gains a **Discontinue** action (active, not fully
  dispensed) and shows a discontinued badge; each dispensed row gets a **Return**
  action that restocks via the reverse endpoint.

Verified: `npm run build` (tsc + vite) passes; `npm run lint` at the prior
baseline (0 errors).

## 4. Design notes

- **Allergy match is exact-concept** (allergen concept == product drug concept).
  This is honest and false-positive-free; class/ingredient-level cross-reactivity
  (e.g. all penicillins) needs a concept hierarchy/drug-class mapping and is left
  as a recommendation rather than guessed.
- **Override is allowed, not forbidden** — mirroring OpenMRS, a prescriber can
  proceed with clinical justification; the override is audited.
- **Reversal restocks via the ledger**, not by un-writing the original issue, so
  the audit trail is preserved (issue + return both visible).

## 5. Recommended next steps (prioritised)

**Done in a follow-up pass:**

- ✅ **Class-level allergy cross-reactivity** — `check_drug_allergies` now matches
  at three levels: *exact* (allergen == drug concept), *ingredient* (allergen is
  an ingredient of a combination product, via `DrugIngredient`), and *class*
  (allergen is a drug-class concept set containing the product's concept, via
  `ConceptSetMembership`). Each match carries a `match_reason` surfaced in the UI.
- ✅ **Batch traceability per dispense** — a `DispenseBatch` records each
  (batch, quantity, cost) a FEFO dispense drew from; `reverse_dispense` restocks
  the *exact* originating batches (legacy dispenses fall back to the default
  batch).

**Needs modest backend:**

- **Refill tracking**: count dispenses/refills against `num_refills` and block
  over-dispensing beyond `quantity × (1 + num_refills)`.
- **Dispense → charge**: optionally create a POS `SaleLine`/charge on dispense so
  the medicine is billed through the one bill (the price is already captured).
- **Drug–drug / duplicate-therapy checks** using the concept hierarchy, behind
  the same `check_*` service boundary as the allergy check.

**Frontend-only:**

- **Pharmacy dispensing queue**: a worklist filter on the prescriptions list for
  active, not-fully-dispensed orders (status chips).
- Surface a patient's **active medications** on the patient summary.

## 6. Sources

- OpenMRS data model — Order (action/DISCONTINUE, previous_order), Allergy /
  AllergyIntolerance, DrugOrder. See `docs/openmrs_coverage.md`.
