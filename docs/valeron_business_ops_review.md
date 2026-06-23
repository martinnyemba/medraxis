# Business Operations Review — Valeron Pro & Vyapar lens (gap analysis + patches)

> Companion to `docs/business_ops_research.md` (which covered the **backend/data
> model** gap analysis for the financial/accounting layer and is implemented).
> This document reviews **POS, inventory and business operations** from the
> Valeron Pro / Vyapar product-surface point of view, and records the patches
> made in this pass — frontend exposure of an already-built backend, plus a new
> business-reports capability (backend + frontend).

## 1. Method

Valeron Pro (clinic/diagnostic business management) and Vyapar (SMB billing +
accounting + inventory) are proprietary; this review uses their publicly
described feature surface as *feature inspiration*, not a copy.

Reference feature surface:

- **Vyapar**: party ledger (running balance per customer/supplier), GST documents
  — sale invoice, **purchase bill**, **quotation/estimate**, delivery challan,
  credit/debit note, payment-in/out, **expenses**, cash & bank accounts, and
  **business reports** (P&L, day book, outstanding, GST).
- **Valeron Pro**: appointments, billing, inventory, **expenses**, multi-branch,
  doctor commissions, and **business reports** (P&L, day book, outstanding).

## 2. Backend was (again) ahead of the frontend

`docs/business_ops_research.md` is fully implemented: the platform already has
the money ledger (`FinancialAccount`, `AccountTransaction`), party ledger
(`PartyLedgerEntry`), `Expense`/`ExpenseCategory`, `SupplierPayment`,
`PurchaseBill`/`PurchaseBillItem`, `TaxComponent` (GST split), `Quotation`/
`QuotationLine`, `SalesReturn`/`SalesReturnLine`, and the unified price resolver
(`pos.pricing`). The SPA already exposes most of it: POS sales/returns/customers,
inventory products/suppliers/stock-ledger/expiring-batches/purchase-orders,
finance accounts/expenses/supplier-payments/purchase-bills/party-ledger, and
billing services/insurance.

Two Valeron/Vyapar-defining gaps remained:

1. **Quotations / estimates** — full backend (model, serializer, viewset,
   `convert` action) but **zero frontend** and not in any nav.
2. **Business reports** — the P&L-style **summary**, **day book** and
   **outstanding** views that define "business operations" had **no endpoint and
   no UI** at all.

## 3. Gap analysis

| Valeron/Vyapar capability | Backend | Frontend before | Status |
|---|---|---|---|
| Sale invoice + line tax/discount + payments | ✅ | ✅ | unchanged |
| Sales return / credit note (+ restock) | ✅ | ✅ | unchanged |
| Customers, suppliers | ✅ | ✅ | unchanged |
| Product catalogue, batch/expiry, stock ledger (FEFO) | ✅ | ✅ | unchanged |
| Purchase orders, **purchase bills** (payables) | ✅ | ✅ | unchanged |
| Cash & bank accounts + money ledger | ✅ | ✅ | unchanged |
| Expenses (+ categories) | ✅ | ✅ | unchanged |
| Supplier payments (payment-out, allocations) | ✅ | ✅ | unchanged |
| Party ledger: statements & balance | ✅ | ✅ | unchanged |
| **Quotation / estimate → invoice** | ✅ | ❌ **none** | **added** (list/new/detail + convert) |
| **Business summary (revenue/collections/expenses/net)** | ❌ none | ❌ none | **added** (backend + UI) |
| **Day book (cash & bank movements for a day)** | ❌ none | ❌ none | **added** (backend + UI) |
| **Outstanding receivables/payables** | partial (per-party only) | ❌ none | **added** (aggregate backend + UI) |
| GST tax-component (CGST/SGST/IGST) management UI | ✅ `/finance/tax-components/` | ❌ none | recommended (§5) |
| Doctor/referrer commission report | partial (`ReferringDoctor.commission_percent`) | ❌ none | recommended (§5) |
| Stock valuation / low-stock report | derivable | partial (expiring only) | recommended (§5) |
| Barcode scan at POS | `Product.barcode` exists | search-only | recommended (§5) |
| Delivery challan / e-invoice / e-way bill | ❌ | ❌ | out of scope (§5) |

## 4. What was patched

### 4.1 Quotations (frontend only — backend already complete)

- `features/pos/QuotationsListPage.tsx` — list with status, totals, validity.
- `features/pos/NewQuotationPage.tsx` — product cart estimate builder with a
  *valid-until* date (mirrors the sale builder; server resolves catalogue
  pricing).
- `features/pos/QuotationDetailPage.tsx` — line detail, totals, and a
  **Convert to sale** action that posts to `convert/` and navigates to the
  created sale (or links to it once converted).
- Routes `/pos/quotations`, `/pos/quotations/new`, `/pos/quotations/:id`; a
  **Quotations** link added to the sales page. API/types added to
  `features/pos/{api,types}.ts`.

### 4.2 Business reports (backend + frontend — genuinely missing)

Backend — `apps/finance/reports.py` (read-only aggregations, tenant-scoped) and
`BusinessReportsViewSet` at `/api/v1/finance/reports/`:

- `GET summary/?from=&to=` — sales count, **revenue billed**, **collected**,
  **expenses** (incl. tax), **supplier payments**, **net cash**, and an
  **expenses-by-category** breakdown.
- `GET day_book/?date=` — every cash/bank movement on a date with **money in /
  out / net** totals and running balances.
- `GET outstanding/` — **receivables** and **payables** computed from each
  party's latest carried ledger balance, with per-party rows and totals.

Tests: `apps/finance/tests/test_reports.py` (3 tests; full suite green —
finance/pos/inventory: 38 passing).

Frontend — `features/finance/ReportsPage.tsx` at `/finance/reports`: tabbed
**Summary** (date range + stat cards + category table), **Day book** (date +
in/out/net + movement table) and **Outstanding** (receivables/payables cards).
A **Reports** link was added to the finance accounts header; API/types added to
`features/finance/{api,types}.ts`.

Verified: `npm run build` (tsc + vite) passes; `npm run lint` reports no new
issues (the New-Quotation effect warning matches the existing New-Sale page).

## 5. Recommended next steps (prioritised)

**Frontend-only (endpoint already exists):**

- **Tax-component (GST split) management** UI over `/finance/tax-components/`,
  and surface the CGST/SGST/IGST split on the sale receipt PDF.
- **Quotation polish**: customer/client selector and a printable estimate PDF
  (the sale receipt already has a PDF generator to mirror).
- **Account transfer** between financial accounts (a money-out + money-in pair)
  exposed on the accounts page.

**Needs modest backend:**

- **Profit & Loss** with COGS: extend `reports.summary` to subtract cost of
  goods sold from the stock ledger (`StockTransaction.unit_cost` on SALE rows)
  for a true gross-margin figure.
- **Commission report** for referring doctors (volume × `commission_percent`),
  a flagship Valeron number.
- **Stock valuation & low-stock** report (on-hand × cost; on-hand ≤
  `reorder_level`).
- **GST return summary** (taxable value and tax by rate/HSN) for filing.

**Larger / separate epics:**

- Delivery challan, e-invoice / e-way bill (jurisdiction-specific compliance).
- Formal double-entry GL behind the existing single-entry party ledger (the
  service boundary is already in place).

## 6. Sources

- [Vyapar — Business accounting & billing](https://vyaparapp.in/)
- [Valeron Pro](https://www.valeronpro.com/)
- See also `docs/business_ops_research.md` (backend gap analysis).
