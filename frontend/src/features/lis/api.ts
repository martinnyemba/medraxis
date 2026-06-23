import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  Antibiotic,
  AutoVerifyResult,
  Client,
  CollectionCenter,
  LabResult,
  LabSection,
  LabTest,
  MicrobiologyResult,
  Organism,
  QCMaterial,
  QCResult,
  ReferenceRange,
  ReferringDoctor,
  ReportDelivery,
  Specimen,
  TestMethod,
  TestOrder,
  TestProfile,
} from "./types";

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
  autoVerifyResult: (id: number) => api.post<AutoVerifyResult>(`/lab/results/${id}/auto_verify/`),
  verifyResult: (id: number) => api.post<LabResult>(`/lab/results/${id}/verify/`),
  releaseResult: (id: number) => api.post<LabResult>(`/lab/results/${id}/release/`),

  // Catalogue richness (FLabs) ---------------------------------------------
  listTestMethods: (params?: ListParams) =>
    api.get<Paginated<TestMethod>>("/lab/test-methods/", params),
  listReferenceRanges: (params?: ListParams) =>
    api.get<Paginated<ReferenceRange>>("/lab/reference-ranges/", params),
  listProfiles: (params?: ListParams) =>
    api.get<Paginated<TestProfile>>("/lab/test-profiles/", params),
  createProfile: (data: Partial<TestProfile>) =>
    api.post<TestProfile>("/lab/test-profiles/", data),

  // Report delivery (WhatsApp / SMS / Email / portal) ----------------------
  listDeliveries: (params?: ListParams) =>
    api.get<Paginated<ReportDelivery>>("/lab/report-deliveries/", params),
  dispatchReport: (data: Partial<ReportDelivery>) =>
    api.post<ReportDelivery>("/lab/report-deliveries/", data),

  // Microbiology (culture & sensitivity) -----------------------------------
  listOrganisms: (params?: ListParams) =>
    api.get<Paginated<Organism>>("/lab/organisms/", params),
  listAntibiotics: (params?: ListParams) =>
    api.get<Paginated<Antibiotic>>("/lab/antibiotics/", params),
  listMicrobiology: (params?: ListParams) =>
    api.get<Paginated<MicrobiologyResult>>("/lab/microbiology-results/", params),
  createMicrobiology: (data: Partial<MicrobiologyResult>) =>
    api.post<MicrobiologyResult>("/lab/microbiology-results/", data),

  // Quality control (Westgard / Levey-Jennings) ----------------------------
  listQcMaterials: (params?: ListParams) =>
    api.get<Paginated<QCMaterial>>("/lab/qc-materials/", params),
  createQcMaterial: (data: Partial<QCMaterial>) =>
    api.post<QCMaterial>("/lab/qc-materials/", data),
  listQcResults: (params?: ListParams) =>
    api.get<Paginated<QCResult>>("/lab/qc-results/", params),
  recordQcResult: (data: Partial<QCResult>) => api.post<QCResult>("/lab/qc-results/", data),

  // B2B / multi-branch commercial layer ------------------------------------
  listClients: (params?: ListParams) => api.get<Paginated<Client>>("/lab/clients/", params),
  createClient: (data: Partial<Client>) => api.post<Client>("/lab/clients/", data),
  listReferringDoctors: (params?: ListParams) =>
    api.get<Paginated<ReferringDoctor>>("/lab/referring-doctors/", params),
  createReferringDoctor: (data: Partial<ReferringDoctor>) =>
    api.post<ReferringDoctor>("/lab/referring-doctors/", data),
  listCollectionCenters: (params?: ListParams) =>
    api.get<Paginated<CollectionCenter>>("/lab/collection-centers/", params),
  createCollectionCenter: (data: Partial<CollectionCenter>) =>
    api.post<CollectionCenter>("/lab/collection-centers/", data),
};
