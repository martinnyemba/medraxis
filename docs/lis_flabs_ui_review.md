# LIS Review — FLabs & OpenMRS lens (UI gap analysis + patches)

> Companion to `docs/flabs_research.md` (which covered the **backend/data-model**
> gap analysis and is now fully implemented). This document reviews the LIS from
> the **UI/UX** point of view — what FLabs surfaces to lab staff that Medraxis's
> backend already supports but the React SPA did **not** yet expose — and records
> the frontend patches made in this pass.

## 1. Method

FLabs (flabslis.com) is proprietary; this review uses its publicly described
product surface as *feature inspiration*, not a copy. The FLabs modules
referenced from public material:

- Dashboard for **referral sources, commissions and activity/incidents**.
- **Patient registration / front office** and sample lifecycle tracking
  (collection → analysis → reporting).
- **Bulk report delivery over WhatsApp / SMS / Email** with delivery tracking,
  plus **QR-coded reports** and customizable **report templates**.
- **Automated quality checks** before report release (auto-verification).
- **Inventory**, **camp registration**, **corporate logins** (B2B portal),
  multi-branch / **franchise** management.

Sources: see §6.

OpenMRS lens: the LIS keeps the OpenMRS spine — `TestOrder`/`DrugOrder` are MTI
subclasses of one `emr.Order`, released results post to the shared `emr.Obs`
chart. None of the UI patches below break that spine; they surface peripheral
lab context hung off it.

## 2. Backend was ahead of the frontend

The backend `lis` app already models essentially the whole FLabs feature set
(see `docs/flabs_research.md §6`): catalogue richness (`TestMethod`,
`ReferenceRange`, `TestProfile`, `ReportTemplate`), B2B/multi-branch (`Client`,
`ReferringDoctor`, `CollectionCenter`, `CollectionAppointment`, `ReferenceLab`,
`PriceList`), microbiology (`Organism`/`Antibiotic`/`MicrobiologyResult`/
`SensitivityResult`), QC (`QCMaterial`/`QCResult` with Westgard/Z-score),
auto-verification + reflex (`AutoVerificationRule`), and report delivery
(`ReportDelivery` over WhatsApp/SMS/email/portal). All have REST endpoints under
`/api/v1/lab/…`.

The **React SPA exposed only a thin slice**: worklist, new order, order detail
(specimens + numeric/text result entry), and the test catalog. Everything else
was reachable only via the API or Django admin. That is the gap this pass closes.

## 3. Frontend gap analysis

| FLabs UI surface | Backend endpoint | Before this pass | Status |
|---|---|---|---|
| Numeric/text result entry → verify → release | `/lab/results/…` | ✅ present | unchanged |
| Specimen accession / collect / receive / label | `/lab/specimens/…` | ✅ present | unchanged |
| Test catalog browse | `/lab/tests/` | ✅ present | unchanged |
| **Automated quality check (auto-verify + reflex)** | `results/{id}/auto_verify/` | ❌ no UI | **added** (per-result "Auto" action) |
| **WhatsApp/SMS/Email/portal report delivery + tracking** | `/lab/report-deliveries/` | ❌ no UI | **added** (order-detail panel + dispatch dialog) |
| **Microbiology culture & sensitivity (antibiogram)** | `/lab/microbiology-results/`, `/lab/organisms/`, `/lab/antibiotics/` | ❌ no UI | **added** (order-detail panel, micro sections only) |
| **Quality control (Levey-Jennings / Westgard)** | `/lab/qc-materials/`, `/lab/qc-results/` | ❌ no UI | **added** (`/lis/qc` page + L-J chart) |
| **B2B clients (corporate accounts, credit)** | `/lab/clients/` | ❌ no UI | **added** (`/lis/partners`) |
| **Referring doctors (+ commission)** | `/lab/referring-doctors/` | ❌ no UI | **added** (`/lis/partners`) |
| **Collection centres / home collection** | `/lab/collection-centers/` | ❌ no UI | **added** (`/lis/partners`) |
| LIS sub-navigation | — | ❌ flat single page | **added** (`LisTabs`) |
| Reference ranges (age/sex) management | `/lab/reference-ranges/` | ❌ no UI | recommended (§5) |
| Test methods / profiles / report templates management | `/lab/{test-methods,test-profiles,report-templates}/` | ❌ no UI | recommended (§5) |
| Auto-verification **rule** configuration | `/lab/auto-verification-rules/` | ❌ no UI | recommended (§5) |
| Analyzer + inbound message monitoring | `/lab/analyzers/`, `/lab/messages/` | ❌ no UI | recommended (§5) |
| Collection appointment scheduling | `/lab/appointments/` | ❌ no UI | recommended (§5) |
| Reference-lab outsourcing screen | `/lab/reference-labs/` | ❌ no UI | recommended (§5) |
| Referral/commission + TAT dashboard | (needs aggregation) | ❌ none | recommended (§5, backend work) |
| QR-coded reports | `test-orders/{id}/report/` | PDF only | recommended (§5) |
| Patient/doctor self-service portal | — | ❌ none | out of scope (§5) |

## 4. What was patched (frontend)

All additions reuse existing endpoints — **no backend or schema changes** — and
follow the established SPA conventions (TanStack Query, shadcn UI, `useToast`,
`ApiError.toUserMessage()`).

1. **LIS sub-navigation** — `features/lis/components/LisTabs.tsx`, mounted on the
   worklist, catalog, QC and partners pages: *Worklist · Catalog · Quality
   control · Clients & partners*.
2. **Report delivery** — `components/ReportDeliveryPanel.tsx` on the order-detail
   page: lists prior deliveries with status, and a dispatch dialog for channel
   (WhatsApp/SMS/Email/portal) + recipient (patient/referrer/client) + address.
   This is FLabs's flagship "share report on WhatsApp" workflow.
3. **Microbiology** — `components/MicrobiologyPanel.tsx`, shown on the order
   detail when the test's section name contains "micro": records growth,
   organism, colony count and an **antibiogram** (antibiotic → S/I/R + MIC), and
   renders saved cultures as colour-coded S/I/R chips.
4. **Auto-verification action** — `components/ResultRow.tsx` gains an **Auto**
   button on entered results that calls `auto_verify/`, reports whether the
   result was released or held, and surfaces any reflex order created.
5. **Quality control** — `QcPage.tsx` (`/lis/qc`): control-material list, a
   **Levey-Jennings** SVG chart with ±1/2/3 SD bands, a run log with Z-score and
   Westgard verdict, and a "record run" dialog (Z-score/Westgard computed
   server-side on save).
6. **Clients & partners** — `LabPartnersPage.tsx` (`/lis/partners`): tabbed CRUD
   for **B2B clients** (type, credit terms, credit limit), **referring doctors**
   (specialty, hospital, commission %) and **collection centres** (home
   collection).

API/type plumbing added in `features/lis/api.ts` and `types.ts` for deliveries,
microbiology, QC, clients, referring doctors, collection centres, methods,
reference ranges and profiles.

Verified: `npm run build` (tsc + vite) passes; `npm run lint` reports no new
issues.

## 5. Recommended next steps (prioritised)

**High value, endpoint already exists (frontend-only):**

- **Lab configuration area** (`/lis/admin` or settings): manage reference ranges
  (age/sex), test methods, test profiles + members, report templates and
  **auto-verification rules**. These are the catalogue/automation knobs that make
  the existing engine usable without Django admin.
- **Collection appointments / home-collection scheduling** UI over
  `/lab/appointments/` (status board: scheduled → en route → collected).
- **Reference-lab outsourcing** screen: flip `is_outsourced` and pick a reference
  lab on an order; show outsourced TAT.
- **Analyzer console**: list analyzers and inbound `AnalyzerMessage`s with parse
  outcomes (matched/unmatched), plus a manual HL7/ASTM `ingest/` paste box for
  testing instrument feeds.

**Needs modest backend work:**

- **Lab dashboard** with FLabs-style analytics: pending vs released counts, **TAT
  breaches**, referral-source volumes and **commission** summaries (aggregate
  endpoints over orders/results).
- **QR-coded reports**: embed a verification QR in `build_lab_report_pdf`
  (already a PDF) linking to a result-verify URL — a headline FLabs feature.
- **Bulk report send** and **bulk download** (camp/corporate batches) over the
  existing delivery service.

**Larger / separate epics:**

- **Patient & referring-doctor self-service portal** (corporate login) — a
  distinct authn surface; out of scope for the internal SPA.
- ML scorer behind the `automation_service` boundary (the rule engine is already
  the swappable seam).

## 6. Sources

- [Flabs — Pathology Lab Software](https://flabslis.com/)
- [Flabs reviews & features — G2](https://www.g2.com/products/flabs-pathology-software/reviews)
- [Flabs — Capterra](https://www.capterra.com/p/10009573/Flabs/)
- [LIS basics & RCM — LigoLab](https://www.ligolab.com/post/lis-systems-learn-the-basics-and-find-out-how-the-best-lab-management-software-efficiently-maximizes-growth-for-clinical-pathology-labs)
