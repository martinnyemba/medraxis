import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type { Dispense, DrugOrder, PrescribeInput } from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const pharmacyApi = {
  // Prescriptions (drug orders) -------------------------------------------
  listDrugOrders: (params?: ListParams) =>
    api.get<Paginated<DrugOrder>>("/pharmacy/drug-orders/", params),
  getDrugOrder: (id: number) => api.get<DrugOrder>(`/pharmacy/drug-orders/${id}/`),
  prescribe: (data: PrescribeInput) => api.post<DrugOrder>("/pharmacy/drug-orders/", data),

  // Dispensing -------------------------------------------------------------
  listDispenses: (params?: ListParams) =>
    api.get<Paginated<Dispense>>("/pharmacy/dispenses/", params),
  dispense: (data: {
    drug_order?: number;
    product?: number;
    patient?: number | null;
    location: number;
    quantity: string;
    note?: string;
  }) => api.post<Dispense>("/pharmacy/dispenses/", data),
};
