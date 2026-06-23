import { api } from "@/lib/api/client";

/** Mirrors apps/tenancy/api/serializers.py OrganizationSerializer. */
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
  mine() {
    return api.get<Organization[]>("/organizations/mine/");
  },
};
