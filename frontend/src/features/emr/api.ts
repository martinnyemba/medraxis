import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  Concept,
  Encounter,
  NamedRef,
  Obs,
  Patient,
  PatientRegistrationInput,
  Visit,
} from "./types";

type ListParams = Record<string, string | number | boolean | undefined | null>;

export const emrApi = {
  // Patients ---------------------------------------------------------------
  listPatients: (params?: ListParams) => api.get<Paginated<Patient>>("/patients/", params),
  getPatient: (id: number) => api.get<Patient>(`/patients/${id}/`),
  registerPatient: (data: PatientRegistrationInput) => api.post<Patient>("/patients/", data),
  updatePatient: (id: number, data: Partial<PatientRegistrationInput>) =>
    api.patch<Patient>(`/patients/${id}/`, data),

  // Visits -----------------------------------------------------------------
  listVisits: (params?: ListParams) => api.get<Paginated<Visit>>("/visits/", params),
  createVisit: (data: Partial<Visit>) => api.post<Visit>("/visits/", data),
  stopVisit: (id: number, stopped_at: string) =>
    api.patch<Visit>(`/visits/${id}/`, { stopped_at }),

  // Encounters -------------------------------------------------------------
  listEncounters: (params?: ListParams) => api.get<Paginated<Encounter>>("/encounters/", params),
  getEncounter: (id: number) => api.get<Encounter>(`/encounters/${id}/`),
  createEncounter: (data: Partial<Encounter>) => api.post<Encounter>("/encounters/", data),

  // Observations -----------------------------------------------------------
  listObs: (params?: ListParams) => api.get<Paginated<Obs>>("/observations/", params),
  createObs: (data: Partial<Obs>) => api.post<Obs>("/observations/", data),

  // Concepts (for observation entry) --------------------------------------
  listConcepts: (params?: ListParams) => api.get<Paginated<Concept>>("/concepts/", params),

  // Reference metadata -----------------------------------------------------
  listVisitTypes: () => api.get<Paginated<NamedRef>>("/visit-types/", { page_size: 200 }),
  listEncounterTypes: () =>
    api.get<Paginated<NamedRef>>("/encounter-types/", { page_size: 200 }),
  listLocations: () => api.get<Paginated<NamedRef>>("/locations/", { page_size: 200 }),
};
