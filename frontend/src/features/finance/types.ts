/** Finance domain types mirroring apps/finance/api/serializers.py. */

export type AccountType = "CASH" | "BANK" | "MOBILE_MONEY" | "CARD";

export interface FinancialAccount {
  id: number;
  uuid: string;
  name: string;
  account_type: AccountType;
  account_number: string;
  bank_name: string;
  opening_balance: string;
  current_balance: string;
  is_default: boolean;
  retired: boolean;
}

export interface AccountTransaction {
  id: number;
  account: number;
  direction: "IN" | "OUT";
  amount: string;
  balance_after: string;
  reference_type: string;
  reference_id: string;
  note: string;
  occurred_at: string;
}

export interface ExpenseCategory {
  id: number;
  uuid: string;
  name: string;
  description: string;
  retired: boolean;
}

export interface Expense {
  id: number;
  number: string;
  category: number;
  category_name: string;
  account: number | null;
  account_name: string;
  supplier: number | null;
  supplier_name: string;
  amount: string;
  tax_amount: string;
  total: string;
  expense_date: string;
  payment_method: string;
  note: string;
}

export interface SupplierPaymentAllocation {
  id?: number;
  purchase_bill: number;
  amount: string;
}

export interface SupplierPayment {
  id: number;
  number: string;
  supplier: number;
  supplier_name: string;
  account: number | null;
  account_name: string;
  amount: string;
  paid_on: string;
  method: string;
  reference: string;
  note: string;
  allocations: SupplierPaymentAllocation[];
}

export type PurchaseBillStatus = "UNPAID" | "PARTIAL" | "PAID" | "CANCELLED";

export interface PurchaseBillItemInput {
  product: number;
  quantity: string;
  unit_cost: string;
  tax_percent?: string;
  batch_number?: string;
  expiry_date?: string | null;
}

export interface PurchaseBill {
  id: number;
  bill_number: string;
  supplier: number;
  supplier_name: string;
  purchase_order: number | null;
  location: number | null;
  location_name: string;
  bill_date: string;
  supplier_invoice_no: string;
  subtotal: string;
  tax_total: string;
  grand_total: string;
  amount_paid: string;
  balance_due: string;
  status: PurchaseBillStatus;
  note: string;
  items: PurchaseBillItemInput[];
}

export interface PartyLedgerEntry {
  id: number;
  entry_type: string;
  entry_date: string;
  debit: string;
  credit: string;
  balance: string;
  reference_type: string;
  reference_id: string;
  narration: string;
}

export type PartyType = "customer" | "supplier";

export interface PartyStatement {
  party_type: PartyType;
  party_id: number;
  balance: string;
  entries: PartyLedgerEntry[];
}

// --- Business reports ------------------------------------------------------

export interface BusinessSummary {
  date_from: string;
  date_to: string;
  sales_count: number;
  revenue: string;
  collected: string;
  expenses: string;
  supplier_payments: string;
  net_cash: string;
  expenses_by_category: { category: string | null; amount: string }[];
}

export interface DayBookEntry {
  id: number;
  account: string;
  direction: "IN" | "OUT";
  amount: string;
  balance_after: string;
  reference_type: string;
  reference_id: string;
  note: string;
  occurred_at: string;
}

export interface DayBook {
  date: string;
  money_in: string;
  money_out: string;
  net: string;
  entries: DayBookEntry[];
}

export interface OutstandingRow {
  party_type: string;
  party_id: number;
  party_name: string;
  balance: string;
}

export interface Outstanding {
  receivable_total: string;
  payable_total: string;
  receivables: OutstandingRow[];
  payables: OutstandingRow[];
}
