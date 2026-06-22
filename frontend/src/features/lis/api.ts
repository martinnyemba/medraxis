import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type { LabResult, LabSection, LabTest, Specimen, TestOrder } from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const lisApi = {
  // Catalogue --------------------------------------------------------------
  listSections: (params?: ListParams) => api.get<Paginated<LabSection>>("/lab/sections/", params),
  listTests: (params?: ListParams) => api.get<Paginated<LabTest>>("/lab/tests/", params),
  getTest: (id: number) => api.get<LabTest>(`/lab/tests/${id}/`),

  // Orders -----------------------------------------------------------------
  listOrders: (params?: ListParams) => api.get<Paginated<TestOrder>>("/lab/test-orders/", params),
  getOrder: (id: number) => api.get<TestOrder>(`/lab/test-orders/${id}/`),
  createOrder: (data: Partial<TestOrder>) => api.post<TestOrder>("/lab/test-orders/", data),
  /** Generate the per-analyte result shells for an order (idempotent). */
  buildWorksheet: (id: number) => api.post<LabResult[]>(`/lab/test-orders/${id}/worksheet/`),
  reportUrl: (id: number) => `/api/v1/lab/test-orders/${id}/report/`,

  // Specimens --------------------------------------------------------------
  listSpecimens: (params?: ListParams) => api.get<Paginated<Specimen>>("/lab/specimens/", params),
  createSpecimen: (data: Partial<Specimen>) => api.post<Specimen>("/lab/specimens/", data),
  collectSpecimen: (id: number) => api.post<Specimen>(`/lab/specimens/${id}/collect/`),
  receiveSpecimen: (id: number) => api.post<Specimen>(`/lab/specimens/${id}/receive/`),
  rejectSpecimen: (id: number, rejection_reason: string) =>
    api.post<Specimen>(`/lab/specimens/${id}/reject/`, { rejection_reason }),
  specimenLabelUrl: (id: number) => `/api/v1/lab/specimens/${id}/label/`,

  // Results ----------------------------------------------------------------
  listResults: (params?: ListParams) => api.get<Paginated<LabResult>>("/lab/results/", params),
  updateResult: (id: number, data: Partial<LabResult>) =>
    api.patch<LabResult>(`/lab/results/${id}/`, data),
  enterResult: (id: number) => api.post<LabResult>(`/lab/results/${id}/enter/`),
  verifyResult: (id: number) => api.post<LabResult>(`/lab/results/${id}/verify/`),
  releaseResult: (id: number) => api.post<LabResult>(`/lab/results/${id}/release/`),
};
