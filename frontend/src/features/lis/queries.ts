import { useQuery } from "@tanstack/react-query";
import { lisApi } from "./api";
import { emrApi } from "@/features/emr/api";
import type { LabTest } from "./types";

const CATALOGUE_STALE = 5 * 60_000;

/** Full test catalogue plus an id→test lookup for rendering order rows. */
export function useLabTests() {
  return useQuery({
    queryKey: ["lis", "tests", "all"],
    queryFn: () => lisApi.listTests({ page_size: 200, retired: false }),
    staleTime: CATALOGUE_STALE,
    select: (page) => {
      const byId = new Map<number, LabTest>(page.results.map((t) => [t.id, t]));
      return { list: page.results, byId };
    },
  });
}

export function useLabSections() {
  return useQuery({
    queryKey: ["lis", "sections"],
    queryFn: () => lisApi.listSections({ page_size: 200 }),
    staleTime: CATALOGUE_STALE,
    select: (page) => page.results,
  });
}

/** Resolve a single analyte/concept name (cached); used by result rows. */
export function useConcept(id: number | null) {
  return useQuery({
    queryKey: ["emr", "concept", id],
    queryFn: () => emrApi.getConcept(id as number),
    staleTime: CATALOGUE_STALE,
    enabled: id !== null,
  });
}
