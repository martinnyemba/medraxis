import * as React from "react";
import { authApi } from "@/lib/api/endpoints/auth";
import { usersApi, type CurrentUser } from "@/lib/api/endpoints/users";
import { setAuthFailureHandler } from "@/lib/api/client";
import { tokenStore, orgStore } from "@/lib/api/tokens";

interface AuthContextValue {
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  /** True when the user holds the given OpenMRS-style privilege (or is staff). */
  can: (privilege: string) => boolean;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const logout = React.useCallback(() => {
    tokenStore.clear();
    orgStore.set(null);
    setUser(null);
  }, []);

  // When a token refresh ultimately fails, the API client calls this to log out.
  React.useEffect(() => {
    setAuthFailureHandler(() => setUser(null));
  }, []);

  // Restore the session on first load if an access token is present.
  React.useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      if (!tokenStore.getAccess()) {
        setIsLoading(false);
        return;
      }
      try {
        const me = await usersApi.me();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) tokenStore.clear();
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = React.useCallback(async (username: string, password: string) => {
    const tokens = await authApi.obtainToken(username, password);
    tokenStore.setTokens(tokens.access, tokens.refresh);
    const me = await usersApi.me();
    setUser(me);
  }, []);

  const can = React.useCallback(
    (privilege: string) =>
      Boolean(user && (user.is_staff || user.privileges.includes(privilege))),
    [user],
  );

  const value = React.useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: !!user, isLoading, login, logout, can }),
    [user, isLoading, login, logout, can],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
