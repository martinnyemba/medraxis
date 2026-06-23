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

export interface AutoVerifyResult {
  auto_verified: boolean;
  status: LabResultStatus;
  reflex_order: string | null;
}

// --- Catalogue richness (FLabs) -------------------------------------------

export interface TestMethod {
  id: number;
  uuid: string;
  name: string;
  lab_test: number;
  instrument: string;
  is_default: boolean;
  retired: boolean;
}

export interface ReferenceRange {
  id: number;
  lab_test: number;
  analyte: number | null;
  method: number | null;
  sex: "A" | "M" | "F";
  age_min_days: number | null;
  age_max_days: number | null;
  low_normal: number | null;
  hi_normal: number | null;
  low_critical: number | null;
  hi_critical: number | null;
  units: string;
  text_range: string;
}

export interface TestProfile {
  id: number;
  uuid: string;
  name: string;
  code: string;
  price: string;
  retired: boolean;
}

// --- Report delivery -------------------------------------------------------

export type DeliveryChannel = "whatsapp" | "sms" | "email" | "portal";
export type DeliveryRecipient = "PATIENT" | "REFERRER" | "CLIENT";
export type DeliveryStatus = "PENDING" | "SENT" | "DELIVERED" | "READ" | "FAILED";

export interface ReportDelivery {
  id: number;
  test_order: number;
  channel: DeliveryChannel;
  recipient_type: DeliveryRecipient;
  recipient_address: string;
  status: DeliveryStatus;
  sent_at: string | null;
  error: string;
  created_at: string;
}

// --- Microbiology ----------------------------------------------------------

export interface Organism {
  id: number;
  uuid: string;
  name: string;
  code: string;
  gram_stain: string;
  retired: boolean;
}

export interface Antibiotic {
  id: number;
  uuid: string;
  name: string;
  code: string;
  abbreviation: string;
  retired: boolean;
}

export type Interpretation = "S" | "I" | "R";

export interface SensitivityResult {
  id?: number;
  antibiotic: number;
  interpretation: Interpretation;
  mic: string;
}

export type MicroGrowth = "NO_GROWTH" | "GROWTH" | "MIXED" | "CONTAMINATED";

export interface MicrobiologyResult {
  id: number;
  uuid: string;
  test_order: number;
  specimen: number | null;
  growth: MicroGrowth;
  organism: number | null;
  colony_count: string;
  status: string;
  comments: string;
  sensitivities: SensitivityResult[];
}

// --- Quality control -------------------------------------------------------

export interface QCMaterial {
  id: number;
  uuid: string;
  name: string;
  lot_number: string;
  analyte: number;
  analyzer: number | null;
  level: string;
  target_mean: number;
  target_sd: number;
  units: string;
  expiry_date: string | null;
  retired: boolean;
}

export interface QCResult {
  id: number;
  qc_material: number;
  analyzer: number | null;
  measured_value: number;
  z_score: number | null;
  westgard_rule: string;
  accepted: boolean;
  run_at: string;
}

// --- B2B / multi-branch ----------------------------------------------------

export type ClientType = "HOSPITAL" | "CORPORATE" | "COLLECTION_CENTER" | "CAMP" | "OTHER";

export interface Client {
  id: number;
  uuid: string;
  name: string;
  code: string;
  client_type: ClientType;
  phone: string;
  email: string;
  address: string;
  credit_limit: string;
  is_credit: boolean;
  retired: boolean;
}

export interface ReferringDoctor {
  id: number;
  uuid: string;
  name: string;
  code: string;
  specialty: string;
  phone: string;
  email: string;
  hospital: string;
  commission_percent: string;
  retired: boolean;
}

export interface CollectionCenter {
  id: number;
  uuid: string;
  name: string;
  code: string;
  location: number | null;
  processing_lab: number | null;
  phone: string;
  is_home_collection: boolean;
  retired: boolean;
}
