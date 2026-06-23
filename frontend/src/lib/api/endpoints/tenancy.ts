import { api } from "../client";

export interface Organization {
  id: number;
  name: string;
  slug: string;
  org_type: string;
  is_active: boolean;
  legal_name: string;
  tax_identifier: string;
  phone: string;
  email: string;
  address: string;
  currency: string;
  timezone: string;
}

export const tenancyApi = {
  /** Organizations the authenticated user belongs to. */
  mine: () => api.get<Organization[]>("/organizations/mine/"),
  current: () => api.get<{ organization: Organization | null } | Organization>("/organizations/current/"),
};
