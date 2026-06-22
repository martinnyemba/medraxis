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
