import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";

/** Inventory product. */
export interface Product {
  id: number;
  uuid: string;
  name: string;
  sku: string;
  barcode: string;
  category: number | null;
  unit: number | null;
  tax_rate: number | null;
  drug_concept: number | null;
  is_drug: boolean;
  is_controlled: boolean;
  strength: string;
  sale_price: string;
  cost_price: string;
  reorder_level: string;
  track_batches: boolean;
  track_expiry: boolean;
  quantity_on_hand: number;
  retired: boolean;
}

export interface NamedRef {
  id: number;
  uuid: string;
  name: string;
  description?: string;
  retired?: boolean;
}

export interface TaxRate {
  id: number;
  uuid: string;
  name: string;
  rate_percent: string;
  hsn_sac_code: string;
  retired: boolean;
}

export interface Supplier {
  id: number;
  uuid: string;
  name: string;
  contact_person: string;
  phone: string;
  email: string;
  address: string;
  tax_identifier: string;
  retired: boolean;
}

export interface StockBatch {
  id: number;
  product: number;
  product_name: string;
  location: number | null;
  batch_number: string;
  expiry_date: string | null;
  quantity_on_hand: string;
  cost_price: string;
}

export type TxnType =
  | "RECEIPT"
  | "SALE"
  | "DISPENSE"
  | "ADJUSTMENT"
  | "TRANSFER_IN"
  | "TRANSFER_OUT"
  | "RETURN"
  | "WASTAGE";

export interface StockTransaction {
  id: number;
  product: number;
  batch: number | null;
  location: number | null;
  transaction_type: TxnType;
  quantity: string;
  unit_cost: string;
  reference_type: string;
  reference_id: string;
  note: string;
  created_at: string;
}

export interface ReceiveStockInput {
  product: number;
  location: number;
  quantity: string;
  unit_cost?: string;
  batch_number?: string;
  expiry_date?: string | null;
}

export type PurchaseOrderStatus = "DRAFT" | "ORDERED" | "PARTIAL" | "RECEIVED" | "CANCELLED";

export interface PurchaseOrderItem {
  id?: number;
  product: number;
  quantity_ordered: string;
  quantity_received?: string;
  unit_cost: string;
}

export interface PurchaseOrder {
  id: number;
  po_number: string;
  supplier: number;
  location: number | null;
  status: PurchaseOrderStatus;
  expected_date: string | null;
  notes: string;
  items: PurchaseOrderItem[];
}

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const inventoryApi = {
  // Products ---------------------------------------------------------------
  listProducts: (params?: ListParams) => api.get<Paginated<Product>>("/inventory/products/", params),
  getProduct: (id: number) => api.get<Product>(`/inventory/products/${id}/`),
  createProduct: (data: Partial<Product>) => api.post<Product>("/inventory/products/", data),
  updateProduct: (id: number, data: Partial<Product>) =>
    api.patch<Product>(`/inventory/products/${id}/`, data),
  lowStock: (params?: ListParams) =>
    api.get<Paginated<Product>>("/inventory/products/low_stock/", params),
  receiveStock: (data: ReceiveStockInput) =>
    api.post<StockTransaction>("/inventory/products/receive/", data),

  // Reference data ---------------------------------------------------------
  listCategories: () => api.get<Paginated<NamedRef>>("/inventory/categories/", { page_size: 200 }),
  createCategory: (data: { name: string; description?: string }) =>
    api.post<NamedRef>("/inventory/categories/", data),
  listUnits: () => api.get<Paginated<NamedRef>>("/inventory/units/", { page_size: 200 }),
  createUnit: (data: { name: string }) => api.post<NamedRef>("/inventory/units/", data),
  listTaxRates: () => api.get<Paginated<TaxRate>>("/inventory/tax-rates/", { page_size: 200 }),

  // Suppliers --------------------------------------------------------------
  listSuppliers: (params?: ListParams) =>
    api.get<Paginated<Supplier>>("/inventory/suppliers/", params),
  createSupplier: (data: Partial<Supplier>) => api.post<Supplier>("/inventory/suppliers/", data),

  // Stock ------------------------------------------------------------------
  listBatches: (params?: ListParams) => api.get<Paginated<StockBatch>>("/inventory/batches/", params),
  expiringBatches: (params?: ListParams) =>
    api.get<Paginated<StockBatch>>("/inventory/batches/expiring/", params),
  listTransactions: (params?: ListParams) =>
    api.get<Paginated<StockTransaction>>("/inventory/transactions/", params),

  // Purchase orders --------------------------------------------------------
  listPurchaseOrders: (params?: ListParams) =>
    api.get<Paginated<PurchaseOrder>>("/inventory/purchase-orders/", params),
  createPurchaseOrder: (data: Partial<PurchaseOrder>) =>
    api.post<PurchaseOrder>("/inventory/purchase-orders/", data),
};
