import { useQuery } from "@tanstack/react-query";
import { emrApi } from "./api";

/** Cached reference metadata — rarely changes, safe to keep fresh for a while. */
const REFERENCE_STALE = 5 * 60_000;

export function useVisitTypes() {
  return useQuery({
    queryKey: ["emr", "visit-types"],
    queryFn: emrApi.listVisitTypes,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function useEncounterTypes() {
  return useQuery({
    queryKey: ["emr", "encounter-types"],
    queryFn: emrApi.listEncounterTypes,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function useLocations() {
  return useQuery({
    queryKey: ["emr", "locations"],
    queryFn: emrApi.listLocations,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

/** Concept search for observation entry (numeric/coded/etc.). */
export function useConceptSearch(search: string) {
  return useQuery({
    queryKey: ["emr", "concepts", search],
    queryFn: () => emrApi.listConcepts({ search, page_size: 20 }),
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
    enabled: search.length >= 2,
  });
}

/** Patient search for picking the "other" person in a relationship. */
export function usePatientSearch(search: string) {
  return useQuery({
    queryKey: ["emr", "patients", "search", search],
    queryFn: () => emrApi.listPatients({ search, page_size: 20 }),
    select: (page) => page.results,
    enabled: search.length >= 2,
  });
}

export function useRelationshipTypes() {
  return useQuery({
    queryKey: ["emr", "relationship-types"],
    queryFn: emrApi.listRelationshipTypes,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function usePatientIdentifierTypes() {
  return useQuery({
    queryKey: ["emr", "patient-identifier-types"],
    queryFn: emrApi.listPatientIdentifierTypes,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function usePersonAttributeTypes() {
  return useQuery({
    queryKey: ["emr", "person-attribute-types"],
    queryFn: emrApi.listPersonAttributeTypes,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function usePrograms() {
  return useQuery({
    queryKey: ["emr", "programs"],
    queryFn: emrApi.listPrograms,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function useProgramWorkflowStates(workflow?: number) {
  return useQuery({
    queryKey: ["emr", "program-workflow-states", workflow],
    queryFn: () => emrApi.listProgramWorkflowStates({ workflow }),
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
    enabled: !!workflow,
  });
}

export function useProgramWorkflows(program?: number) {
  return useQuery({
    queryKey: ["emr", "program-workflows", program],
    queryFn: () => emrApi.listProgramWorkflows({ program }),
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
    enabled: !!program,
  });
}
