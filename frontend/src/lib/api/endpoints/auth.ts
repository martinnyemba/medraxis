import { api } from "../client";

export interface TokenPair {
  access: string;
  refresh: string;
}

export const authApi = {
  obtainToken: (username: string, password: string) =>
    api.login<TokenPair>("/auth/token/", { username, password }),
};
