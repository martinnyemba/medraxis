import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type { AllergyMatch, Dispense, DrugOrder, PrescribeInput } from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const pharmacyApi = {
  // Prescriptions (drug orders) -------------------------------------------
  listDrugOrders: (params?: ListParams) =>
    api.get<Paginated<DrugOrder>>("/pharmacy/drug-orders/", params),
  getDrugOrder: (id: number) => api.get<DrugOrder>(`/pharmacy/drug-orders/${id}/`),
  prescribe: (data: PrescribeInput) => api.post<DrugOrder>("/pharmacy/drug-orders/", data),
  /** Documented drug allergies for a patient against a specific drug. */
  allergyCheck: (patient: number, drug: number) =>
    api.get<{ allergies: AllergyMatch[] }>("/pharmacy/drug-orders/allergy_check/", {
      patient, drug,
    }),
  discontinue: (id: number, reason = "") =>
    api.post<DrugOrder>(`/pharmacy/drug-orders/${id}/discontinue/`, { reason }),

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
  reverseDispense: (id: number, note = "") =>
    api.post<Dispense>(`/pharmacy/dispenses/${id}/reverse/`, { note }),
};
