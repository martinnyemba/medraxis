/** Pharmacy domain types mirroring apps/pharmacy/api/serializers.py. */

export type FulfillerStatus =
  | ""
  | "RECEIVED"
  | "IN_PROGRESS"
  | "EXCEPTION"
  | "COMPLETED"
  | "DECLINED";

export type DurationUnit = "" | "DAYS" | "WEEKS" | "MONTHS";

export interface DrugOrder {
  id: number;
  uuid: string;
  order_number: string;
  order_type: number | null;
  concept: number | null;
  patient: number;
  encounter: number | null;
  orderer: number | null;
  drug: number;
  drug_name: string;
  dose: string | null;
  dose_units: string;
  frequency: string;
  route: string;
  duration: number | null;
  duration_units: DurationUnit;
  quantity: string;
  num_refills: number;
  as_needed: boolean;
  dosing_instructions: string;
  date_activated: string | null;
  fulfiller_status: FulfillerStatus;
  quantity_dispensed: string | number;
  voided: boolean;
}

export type DispenseStatus = "DISPENSED" | "RETURNED" | "CANCELLED";

export interface Dispense {
  id: number;
  drug_order: number | null;
  patient: number | null;
  product: number;
  product_name: string;
  location: number;
  quantity: string;
  unit_price: string;
  dispensed_by: number | null;
  status: DispenseStatus;
  note: string;
  line_total: string;
  created_at: string;
}

export interface PrescribeInput {
  patient: number;
  drug: number;
  dose?: string | null;
  dose_units?: string;
  frequency?: string;
  route?: string;
  duration?: number | null;
  duration_units?: DurationUnit;
  quantity?: string;
  num_refills?: number;
  as_needed?: boolean;
  dosing_instructions?: string;
}
