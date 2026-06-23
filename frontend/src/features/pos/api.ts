import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  Customer,
  Payment,
  Quotation,
  QuotationCreateInput,
  Sale,
  SaleCreateInput,
  PaymentMethod,
  SalesReturn,
  SalesReturnCreateInput,
} from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const posApi = {
  // Sales ------------------------------------------------------------------
  listSales: (params?: ListParams) => api.get<Paginated<Sale>>("/pos/sales/", params),
  getSale: (id: number) => api.get<Sale>(`/pos/sales/${id}/`),
  createSale: (data: SaleCreateInput) => api.post<Sale>("/pos/sales/", data),
  completeSale: (id: number) => api.post<Sale>(`/pos/sales/${id}/complete/`),
  paySale: (id: number, method: PaymentMethod, amount: string, reference = "") =>
    api.post<Sale>(`/pos/sales/${id}/pay/`, { method, amount, reference }),
  receiptUrl: (id: number) => `/api/v1/pos/sales/${id}/receipt/`,

  // Customers --------------------------------------------------------------
  listCustomers: (params?: ListParams) => api.get<Paginated<Customer>>("/pos/customers/", params),
  createCustomer: (data: Partial<Customer>) => api.post<Customer>("/pos/customers/", data),

  // Payments (read-only ledger) -------------------------------------------
  listPayments: (params?: ListParams) => api.get<Paginated<Payment>>("/pos/payments/", params),

  // Sales returns ------------------------------------------------------------
  listSalesReturns: (params?: ListParams) =>
    api.get<Paginated<SalesReturn>>("/pos/sales-returns/", params),
  getSalesReturn: (id: number) => api.get<SalesReturn>(`/pos/sales-returns/${id}/`),
  createSalesReturn: (data: SalesReturnCreateInput) =>
    api.post<SalesReturn>("/pos/sales-returns/", data),
  processSalesReturn: (id: number) => api.post<SalesReturn>(`/pos/sales-returns/${id}/process/`),

  // Quotations / estimates -------------------------------------------------
  listQuotations: (params?: ListParams) =>
    api.get<Paginated<Quotation>>("/pos/quotations/", params),
  getQuotation: (id: number) => api.get<Quotation>(`/pos/quotations/${id}/`),
  createQuotation: (data: QuotationCreateInput) =>
    api.post<Quotation>("/pos/quotations/", data),
  convertQuotation: (id: number) => api.post<Sale>(`/pos/quotations/${id}/convert/`),
};
