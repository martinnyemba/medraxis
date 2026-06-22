/** Billing domain types mirroring apps/billing/api/serializers.py. */

export interface BillableService {
  id: number;
  uuid: string;
  name: string;
  service_code: string;
  concept: number | null;
  price: string;
  tax_rate: number | null;
  retired: boolean;
}

export interface InsuranceScheme {
  id: number;
  uuid: string;
  name: string;
  payer_name: string;
  coverage_percent: string;
  contact: string;
  retired: boolean;
}

export interface PatientInsurance {
  id: number;
  patient: number;
  patient_name: string;
  scheme: number;
  scheme_name: string;
  policy_number: string;
  valid_from: string | null;
  valid_to: string | null;
  is_active: boolean;
}
