import { useQuery } from "@tanstack/react-query";
import { financeApi } from "./api";

const REFERENCE_STALE = 5 * 60_000;

export function useFinancialAccounts() {
  return useQuery({
    queryKey: ["finance", "accounts"],
    queryFn: () => financeApi.listAccounts({ page_size: 200 }),
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}

export function useExpenseCategories() {
  return useQuery({
    queryKey: ["finance", "expense-categories"],
    queryFn: financeApi.listExpenseCategories,
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}
