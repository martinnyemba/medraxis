import { api } from "@/lib/api/client";

interface TokenPair {
  access: string;
  refresh: string;
}

export const authApi = {
  obtainToken(username: string, password: string) {
    return api.post<TokenPair>("/auth/token/", { username, password });
  },
};
