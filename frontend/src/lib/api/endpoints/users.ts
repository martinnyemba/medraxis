import { api } from "@/lib/api/client";

/** Mirrors apps/users/api/serializers.py UserSerializer. */
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

export const usersApi = {
  me() {
    return api.get<CurrentUser>("/users/me/");
  },
};
