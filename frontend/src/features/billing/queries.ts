import { useQuery } from "@tanstack/react-query";
import { billingApi } from "./api";

const REFERENCE_STALE = 5 * 60_000;

export function useInsuranceSchemes() {
  return useQuery({
    queryKey: ["billing", "insurance-schemes"],
    queryFn: () => billingApi.listSchemes({ page_size: 200 }),
    staleTime: REFERENCE_STALE,
    select: (page) => page.results,
  });
}
