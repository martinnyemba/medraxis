import { useQuery } from "@tanstack/react-query";
import { inventoryApi } from "./api";

const REFERENCE_STALE = 5 * 60_000;

export function useCategories() {
  return useQuery({
    queryKey: ["inventory", "categories"],
    queryFn: inventoryApi.listCategories,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function useUnits() {
  return useQuery({
    queryKey: ["inventory", "units"],
    queryFn: inventoryApi.listUnits,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function useTaxRates() {
  return useQuery({
    queryKey: ["inventory", "tax-rates"],
    queryFn: inventoryApi.listTaxRates,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}
