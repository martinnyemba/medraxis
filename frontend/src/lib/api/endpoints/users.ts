import { api } from "../client";
import type { Paginated } from "../types";

/** Authenticated user, as returned by GET /users/me/. */
export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  is_active: boolean;
  is_staff: boolean;
  is_system_account: boolean;
  roles: string[];
  privileges: string[];
}

export interface Provider {
  id: number;
  uuid: string;
  name: string;
  identifier: string;
  provider_role: string;
  person: number | null;
  user: number | null;
  retired: boolean;
}

export const usersApi = {
  me: () => api.get<CurrentUser>("/users/me/"),
  providers: (params?: Record<string, string | number>) =>
    api.get<Paginated<Provider>>("/providers/", params),
};
