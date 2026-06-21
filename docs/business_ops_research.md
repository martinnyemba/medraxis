# Valeron Pro & Vyapar — Business-Operations Research

> **Disclaimer.** Valeron Pro and Vyapar are proprietary; their source and schema
> are not public. This is a reverse-engineered analysis from their publicly
> described feature sets, used only as *feature inspiration* to decide what
> Medraxis must model so the platform is a complete business system for clinics,
> diagnostic centres, pharmacies and medical businesses — not a copy.

Medraxis already had the **operational** half of commerce (catalogue, stock
ledger, sales invoice, POs). What was missing is the **financial/accounting**
half that turns transactions into a running business: money accounts, expenses,
payables, party balances, and the pre/post-sale documents.

---

## 1. What these products are, as systems

* **Vyapar** — an SMB billing + accounting + inventory app (India-first, GST).
  Its spine is the **Party ledger** (every customer/supplier has a running
  balance) plus **GST documents**: sale invoice, purchase bill, quotation,
  delivery challan, credit/debit note, payment-in/out, expenses, and the
  **cash & bank** accounts everything settles into.
* **Valeron Pro** — clinic/diagnostic business management: appointments,
  billing, inventory, **expenses**, multi-branch, doctor commissions and
  business reports (P&L, day book, outstanding).

Both center on a simple truth Medraxis was missing: **a sale is only half a
transaction; the other half is money landing in an account and a party's balance
changing.**

---

## 2. Gap analysis vs current Medraxis

| Capability (Vyapar/Valeron) | Medraxis before | Action |
|---|---|---|
| Cash & bank accounts, money movements | — (payments recorded, money untracked) | **add `FinancialAccount`, `AccountTransaction`** |
| Business expenses | — | **add `ExpenseCategory`, `Expense`** |
| Pay suppliers (Payment-Out) | only Payment-In on sales | **add `SupplierPayment`** |
| Purchase bill (supplier payable) | `PurchaseOrder` only (a request) | **add `PurchaseBill`/`PurchaseBillItem`** |
| Party ledger: receivables & payables, statements | — | **add `PartyLedgerEntry`** (+ posting service) |
| Quotation / estimate → invoice | — | **add `Quotation`/`QuotationLine`** |
| Sales return / credit note (+ restock) | `StockTransaction` RETURN type only | **add `SalesReturn`/`SalesReturnLine`** |
| GST split CGST/SGST/IGST, HSN | flat `TaxRate` + `hsn_sac_code` | **add `TaxComponent`** |
| Opening balances for parties | — | opening-balance ledger entry |
| Outstanding / P&L / day-book reports | generic `ReportRun` | new report generators |

Already covered: product catalogue, batch/expiry, append-only **stock** ledger
(FEFO), sale invoice with discounts + line tax, payments, POs, multi-tenant
isolation, and the unified price resolver (`pos.pricing`).

---

## 3. The accounting model (how it stays consistent)

Two complementary ledgers, both append-only (mirroring the audit-first design of
the stock ledger):

```
 Money ledger (per account)            Party ledger (per customer/supplier/client)
 ──────────────────────────            ───────────────────────────────────────────
 FinancialAccount (Cash / Bank)        PartyLedgerEntry (debit / credit / balance)
   └─ AccountTransaction (IN/OUT)        INVOICE      → customer debit  (owes us)
        ▲        ▲        ▲              PAYMENT_IN   → customer credit
        │        │        │              PURCHASE_BILL→ supplier credit (we owe)
   Payment   Supplier   Expense          PAYMENT_OUT  → supplier debit
   (sale)    Payment                     CREDIT_NOTE  → customer credit (return)
```

* A **sale payment** puts money INTO an account and CREDITS the customer's party
  balance. **Completing** a credit sale DEBITS the customer (they owe).
* A **supplier payment** takes money OUT of an account and DEBITS the supplier.
* A **purchase bill** CREDITS the supplier (payable) and (optionally) receives
  stock through the existing inventory ledger.
* An **expense** takes money OUT of an account.
* A party's **outstanding** is the running balance; a **statement** is its
  ledger entries.

This is single-entry party accounting (Vyapar-style), not full double-entry —
the pragmatic, auditable core, with a clean service boundary if formal GL is
needed later.

---

## 4. Design boundaries (no duplication)

| New model | vs existing | Distinction |
|---|---|---|
| `PurchaseBill` | `PurchaseOrder` | PO = *request* to a supplier; Bill = the *payable invoice* received. A bill may be raised from a PO. |
| `SupplierPayment` | `pos.Payment` | Payment = money **in** against a Sale; SupplierPayment = money **out** to a Supplier. |
| `FinancialAccount` | `inventory` stock | Stock ledger tracks *goods*; financial accounts track *money*. Orthogonal. |
| `Quotation` | `Sale` | Quotation = non-binding estimate that **converts** into a Sale; no stock/money effect until converted. |
| `SalesReturn` | `Sale` | A credit document referencing a Sale; restocks via the inventory RETURN ledger and credits the party. |
| `PartyLedgerEntry` | `Payment`/`Sale` | Those are documents; the ledger is the running balance derived from them, enabling statements & outstanding. |
| `TaxComponent` | `TaxRate` | TaxRate is the headline % (e.g. GST 18%); components split it (CGST 9% + SGST 9%) for compliant invoices. |
| `Expense` | `StockTransaction WASTAGE` | Wastage is a *stock* loss; an Expense is a *cash* cost (rent, salary, utilities). |

The **integration spine is unchanged**: these hang off existing parties
(`Customer`/`Supplier`/`Client`), the existing `Sale`/`PurchaseOrder`, and the
existing stock ledger. They add the money/accounting dimension, not a parallel
system.

---

## 5. FHIR / standards note
Financial models are out of FHIR's clinical scope; where billing interop is
needed, `Sale`/`PurchaseBill` map to FHIR `Invoice` and `ChargeItem`, and GST
data rides on the existing tax fields. No clinical model is affected.
