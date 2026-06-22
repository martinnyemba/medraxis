import { api } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/types";
import type {
  Allergy,
  Cohort,
  CohortMembership,
  Concept,
  Condition,
  Diagnosis,
  Encounter,
  NamedRef,
  Obs,
  Patient,
  PatientIdentifier,
  PatientIdentifierType,
  PatientProgram,
  PatientRegistrationInput,
  PatientState,
  PersonAddress,
  PersonAttribute,
  PersonAttributeType,
  PersonName,
  Program,
  ProgramWorkflow,
  ProgramWorkflowState,
  Relationship,
  RelationshipType,
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
  getConcept: (id: number) => api.get<Concept>(`/concepts/${id}/`),

  // Allergies ----------------------------------------------------------------
  listAllergies: (params?: ListParams) => api.get<Paginated<Allergy>>("/allergies/", params),
  createAllergy: (data: Partial<Allergy>) => api.post<Allergy>("/allergies/", data),

  // Conditions -----------------------------------------------------------------
  listConditions: (params?: ListParams) => api.get<Paginated<Condition>>("/conditions/", params),
  createCondition: (data: Partial<Condition>) => api.post<Condition>("/conditions/", data),

  // Diagnoses -------------------------------------------------------------------
  listDiagnoses: (params?: ListParams) => api.get<Paginated<Diagnosis>>("/diagnoses/", params),
  createDiagnosis: (data: Partial<Diagnosis>) => api.post<Diagnosis>("/diagnoses/", data),

  // Reference metadata -----------------------------------------------------
  listVisitTypes: () => api.get<Paginated<NamedRef>>("/visit-types/", { page_size: 200 }),
  listEncounterTypes: () =>
    api.get<Paginated<NamedRef>>("/encounter-types/", { page_size: 200 }),
  listLocations: () => api.get<Paginated<NamedRef>>("/locations/", { page_size: 200 }),

  // Person names & patient identifiers (post-registration editing) --------
  createPersonName: (data: Partial<PersonName> & { person: number }) =>
    api.post<PersonName>("/person-names/", data),
  createPatientIdentifier: (data: Partial<PatientIdentifier> & { patient: number }) =>
    api.post<PatientIdentifier>("/patient-identifiers/", data),
  listPatientIdentifierTypes: () =>
    api.get<Paginated<PatientIdentifierType>>("/patient-identifier-types/", { page_size: 200 }),

  // Person addresses --------------------------------------------------------
  listPersonAddresses: (params?: ListParams) =>
    api.get<Paginated<PersonAddress>>("/person-addresses/", params),
  createPersonAddress: (data: Partial<PersonAddress> & { person: number }) =>
    api.post<PersonAddress>("/person-addresses/", data),

  // Person attributes --------------------------------------------------------
  listPersonAttributeTypes: () =>
    api.get<Paginated<PersonAttributeType>>("/person-attribute-types/", { page_size: 200 }),
  listPersonAttributes: (params?: ListParams) =>
    api.get<Paginated<PersonAttribute>>("/person-attributes/", params),
  createPersonAttribute: (data: Partial<PersonAttribute> & { person: number }) =>
    api.post<PersonAttribute>("/person-attributes/", data),

  // Relationships -------------------------------------------------------------
  listRelationshipTypes: () =>
    api.get<Paginated<RelationshipType>>("/relationship-types/", { page_size: 200 }),
  listRelationships: (params?: ListParams) =>
    api.get<Paginated<Relationship>>("/relationships/", params),
  createRelationship: (data: Partial<Relationship>) =>
    api.post<Relationship>("/relationships/", data),

  // Programs & enrolment -----------------------------------------------------
  listPrograms: () => api.get<Paginated<Program>>("/programs/", { page_size: 200 }),
  listProgramWorkflows: (params?: ListParams) =>
    api.get<Paginated<ProgramWorkflow>>("/program-workflows/", params),
  listProgramWorkflowStates: (params?: ListParams) =>
    api.get<Paginated<ProgramWorkflowState>>("/program-workflow-states/", params),
  listPatientPrograms: (params?: ListParams) =>
    api.get<Paginated<PatientProgram>>("/patient-programs/", params),
  enrolPatientInProgram: (data: Partial<PatientProgram> & { patient: number; program: number }) =>
    api.post<PatientProgram>("/patient-programs/", data),
  completePatientProgram: (id: number, date_completed: string) =>
    api.patch<PatientProgram>(`/patient-programs/${id}/`, { date_completed }),
  addPatientState: (data: Partial<PatientState> & { patient_program: number; state: number }) =>
    api.post<PatientState>("/patient-states/", data),

  // Cohorts ---------------------------------------------------------------
  listCohorts: (params?: ListParams) => api.get<Paginated<Cohort>>("/cohorts/", params),
  getCohort: (id: number) => api.get<Cohort>(`/cohorts/${id}/`),
  createCohort: (data: Partial<Cohort>) => api.post<Cohort>("/cohorts/", data),
  listCohortMemberships: (params?: ListParams) =>
    api.get<Paginated<CohortMembership>>("/cohort-memberships/", params),
  addCohortMember: (data: Partial<CohortMembership> & { cohort: number; patient: number }) =>
    api.post<CohortMembership>("/cohort-memberships/", data),
  endCohortMembership: (id: number, end_date: string) =>
    api.patch<CohortMembership>(`/cohort-memberships/${id}/`, { end_date }),
};
