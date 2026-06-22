/** LIS domain types mirroring apps/lis/api/serializers.py. */

export interface LabSection {
  id: number;
  uuid: string;
  name: string;
  description: string;
  location: number | null;
  retired: boolean;
}

export interface LabTest {
  id: number;
  uuid: string;
  name: string;
  test_code: string;
  concept: number;
  section: number;
  specimen_type: number | null;
  is_panel: boolean;
  analytes: number[];
  turnaround_hours: number;
  price: string;
  loinc_code: string;
  retired: boolean;
}

export type FulfillerStatus = "" | "RECEIVED" | "IN_PROGRESS" | "EXCEPTION" | "COMPLETED" | "DECLINED";

export interface TestOrder {
  id: number;
  uuid: string;
  order_number: string;
  order_type: number | null;
  concept: number | null;
  patient: number;
  encounter: number | null;
  orderer: number | null;
  lab_test: number;
  specimen_source: number | null;
  clinical_history: string;
  urgency: string;
  date_activated: string | null;
  fulfiller_status: FulfillerStatus;
  voided: boolean;
}

export type SpecimenStatus =
  | "ORDERED"
  | "COLLECTED"
  | "RECEIVED"
  | "IN_PROGRESS"
  | "REJECTED"
  | "DISPOSED";

export interface Specimen {
  id: number;
  uuid: string;
  accession_number: string;
  patient: number;
  specimen_type: number | null;
  orders: number[];
  status: SpecimenStatus;
  collected_at: string | null;
  collected_by: number | null;
  received_at: string | null;
  rejection_reason: string;
}

export type LabResultStatus = "PENDING" | "ENTERED" | "VERIFIED" | "RELEASED" | "REJECTED";
export type LabResultFlag = "" | "N" | "H" | "L" | "HH" | "LL" | "A";

export interface LabResult {
  id: number;
  uuid: string;
  test_order: number;
  specimen: number | null;
  analyte: number;
  value_numeric: number | null;
  value_text: string;
  value_coded: number | null;
  units: string;
  reference_range: string;
  flag: LabResultFlag;
  status: LabResultStatus;
  entered_by: number | null;
  entered_at: string | null;
  verified_by: number | null;
  verified_at: string | null;
  analyzer: number | null;
  obs: number | null;
}
