/** POS domain types mirroring apps/pos/api/serializers.py. */

export interface Customer {
  id: number;
  name: string;
  phone: string;
  email: string;
  address: string;
  tax_identifier: string;
  patient: number | null;
}

export type SaleStatus =
  | "DRAFT"
  | "COMPLETED"
  | "PARTIALLY_PAID"
  | "PAID"
  | "VOID"
  | "REFUNDED";

export type LineType = "PRODUCT" | "SERVICE" | "LAB_TEST" | "LAB_PROFILE" | "CONSULTATION";

export interface SaleLine {
  id?: number;
  line_type: LineType;
  product?: number | null;
  lab_test?: number | null;
  test_profile?: number | null;
  billable_service?: number | null;
  description: string;
  quantity: string;
  unit_price?: string;
  discount_percent?: string;
  tax_percent?: string;
  issued_stock?: boolean;
  discount_amount?: string;
  tax_amount?: string;
  line_total?: string;
}

export type PaymentMethod =
  | "CASH"
  | "CARD"
  | "MOBILE_MONEY"
  | "INSURANCE"
  | "BANK_TRANSFER"
  | "CREDIT";

export interface Payment {
  id: number;
  sale: number;
  method: PaymentMethod;
  status: string;
  amount: string;
  reference: string;
  received_by: number | null;
  created_at: string;
}

export interface Sale {
  id: number;
  invoice_number: string;
  customer: number | null;
  client: number | null;
  patient: number | null;
  location: number | null;
  status: SaleStatus;
  cashier: number | null;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  grand_total: string;
  amount_paid: string;
  balance_due: string;
  currency: string;
  note: string;
  lines: SaleLine[];
  payments: Payment[];
  created_at: string;
}

export interface SaleCreateInput {
  customer?: number | null;
  patient?: number | null;
  location?: number | null;
  note?: string;
  lines: SaleLine[];
}

export type SalesReturnStatus = "DRAFT" | "COMPLETED" | "CANCELLED";

export interface SalesReturnLine {
  id?: number;
  product: number | null;
  description: string;
  quantity: string;
  unit_price: string;
  line_total?: string;
}

export interface SalesReturn {
  id: number;
  return_number: string;
  sale: number;
  sale_invoice_number: string;
  location: number | null;
  return_date: string;
  reason: string;
  restock: boolean;
  total: string;
  status: SalesReturnStatus;
  lines: SalesReturnLine[];
}

export interface SalesReturnCreateInput {
  sale: number;
  location?: number | null;
  return_date: string;
  reason?: string;
  restock?: boolean;
  lines: SalesReturnLine[];
}

// --- Quotations / estimates (Vyapar-style estimate → invoice) --------------

export type QuotationStatus =
  | "DRAFT"
  | "SENT"
  | "ACCEPTED"
  | "CONVERTED"
  | "EXPIRED"
  | "REJECTED";

export interface QuotationLine {
  id?: number;
  line_type: LineType;
  product?: number | null;
  lab_test?: number | null;
  test_profile?: number | null;
  billable_service?: number | null;
  description: string;
  quantity: string;
  unit_price?: string;
  discount_percent?: string;
  tax_percent?: string;
}

export interface Quotation {
  id: number;
  quotation_number: string;
  customer: number | null;
  client: number | null;
  patient: number | null;
  location: number | null;
  status: QuotationStatus;
  valid_until: string | null;
  subtotal: string;
  discount_total: string;
  tax_total: string;
  grand_total: string;
  converted_sale: number | null;
  note: string;
  lines: QuotationLine[];
  created_at: string;
}

export interface QuotationCreateInput {
  customer?: number | null;
  patient?: number | null;
  location?: number | null;
  valid_until?: string | null;
  note?: string;
  lines: QuotationLine[];
}
