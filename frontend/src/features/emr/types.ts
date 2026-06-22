/** EMR domain types mirroring apps/emr/api/serializers.py. */

export interface PersonName {
  id: number;
  preferred: boolean;
  prefix: string;
  given_name: string;
  middle_name: string;
  family_name: string;
  family_name_suffix: string;
}

export interface PatientIdentifier {
  id: number;
  identifier_type: number;
  identifier_type_name: string;
  identifier: string;
  location: number | null;
  preferred: boolean;
}

export type Gender = "M" | "F" | "O" | "U";

export interface Patient {
  id: number;
  uuid: string;
  gender: Gender | null;
  birthdate: string | null;
  names: PersonName[];
  identifiers: PatientIdentifier[];
  allergy_status: string;
  voided: boolean;
}

export interface PatientRegistrationInput {
  given_name: string;
  family_name: string;
  gender?: Gender;
  birthdate?: string | null;
  identifier_type?: number;
}

export interface Visit {
  id: number;
  uuid: string;
  patient: number;
  visit_type: number;
  location: number | null;
  started_at: string;
  stopped_at: string | null;
  voided: boolean;
}

export interface Encounter {
  id: number;
  uuid: string;
  patient: number;
  encounter_type: number;
  visit: number | null;
  location: number | null;
  encounter_datetime: string;
  form_reference: string;
  voided: boolean;
}

export type ObsInterpretation = "" | "NORMAL" | "ABNORMAL" | "CRITICAL" | "HIGH" | "LOW";

export interface Obs {
  id: number;
  uuid: string;
  person: number;
  concept: number;
  encounter: number | null;
  order: number | null;
  obs_datetime: string;
  location: number | null;
  obs_group: number | null;
  value_coded: number | null;
  value_numeric: number | null;
  value_text: string;
  value_datetime: string | null;
  value_boolean: boolean | null;
  interpretation: ObsInterpretation;
  comments: string;
  status: string;
  display_value: string;
  voided: boolean;
}

export interface Concept {
  id: number;
  uuid: string;
  name: string;
  short_name: string;
  concept_class: number;
  concept_class_name: string;
  datatype: number;
  datatype_name: string;
  is_set: boolean;
  units: string;
  hi_normal: number | null;
  low_normal: number | null;
  retired: boolean;
}

/** Reference metadata (read-only list endpoints). */
export interface NamedRef {
  id: number;
  uuid: string;
  name: string;
  description?: string;
  retired?: boolean;
}
