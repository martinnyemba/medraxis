import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type { BillableService, InsuranceScheme, PatientInsurance } from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const billingApi = {
  // Billable services --------------------------------------------------------
  listServices: (params?: ListParams) =>
    api.get<Paginated<BillableService>>("/billing/services/", params),
  createService: (data: Partial<BillableService>) =>
    api.post<BillableService>("/billing/services/", data),

  // Insurance schemes ---------------------------------------------------------
  listSchemes: (params?: ListParams) =>
    api.get<Paginated<InsuranceScheme>>("/billing/insurance-schemes/", params),
  createScheme: (data: Partial<InsuranceScheme>) =>
    api.post<InsuranceScheme>("/billing/insurance-schemes/", data),

  // Patient insurance policies -------------------------------------------------
  listPatientInsurance: (params?: ListParams) =>
    api.get<Paginated<PatientInsurance>>("/billing/patient-insurance/", params),
  createPatientInsurance: (data: Partial<PatientInsurance>) =>
    api.post<PatientInsurance>("/billing/patient-insurance/", data),
};
