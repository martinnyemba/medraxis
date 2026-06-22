import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";

/** Inventory product (subset used by POS and stock views). */
export interface Product {
  id: number;
  uuid: string;
  name: string;
  sku: string;
  barcode: string;
  category: number | null;
  unit: number | null;
  tax_rate: number | null;
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

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const inventoryApi = {
  listProducts: (params?: ListParams) => api.get<Paginated<Product>>("/inventory/products/", params),
  lowStock: (params?: ListParams) =>
    api.get<Paginated<Product>>("/inventory/products/low_stock/", params),
};
