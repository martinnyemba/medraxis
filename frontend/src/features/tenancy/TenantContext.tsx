import * as React from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { tenancyApi, type Organization } from "@/lib/api/endpoints/tenancy";
import { orgStore } from "@/lib/api/tokens";
import { useAuth } from "@/features/auth/AuthContext";

interface TenantContextValue {
  organizations: Organization[];
  current: Organization | null;
  isLoading: boolean;
  /** Switch the active facility; resets cached server data scoped to a tenant. */
  setCurrent: (slug: string) => void;
}

const TenantContext = React.createContext<TenantContextValue | null>(null);

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const [currentSlug, setCurrentSlug] = React.useState<string | null>(orgStore.get());

  const { data: organizations = [], isLoading } = useQuery({
    queryKey: ["organizations", "mine"],
    queryFn: tenancyApi.mine,
    enabled: isAuthenticated,
  });

  // Default to the first available org if none is selected yet.
  React.useEffect(() => {
    if (!currentSlug && organizations.length > 0) {
      const slug = organizations[0].slug;
      orgStore.set(slug);
      setCurrentSlug(slug);
    }
  }, [currentSlug, organizations]);

  const setCurrent = React.useCallback(
    (slug: string) => {
      orgStore.set(slug);
      setCurrentSlug(slug);
      // Tenant-scoped lists (patients, visits, …) must be refetched.
      queryClient.invalidateQueries();
    },
    [queryClient],
  );

  const current = React.useMemo(
    () => organizations.find((o) => o.slug === currentSlug) ?? null,
    [organizations, currentSlug],
  );

  const value = React.useMemo<TenantContextValue>(
    () => ({ organizations, current, isLoading, setCurrent }),
    [organizations, current, isLoading, setCurrent],
  );

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
}

export function useTenant() {
  const ctx = React.useContext(TenantContext);
  if (!ctx) throw new Error("useTenant must be used within a TenantProvider");
  return ctx;
}
