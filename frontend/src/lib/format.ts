import type { Patient, PersonName } from "@/features/emr/types";

/** Compose a display name from a person's preferred (or first) name. */
export function formatName(name?: PersonName | null): string {
  if (!name) return "Unnamed";
  return [name.given_name, name.middle_name, name.family_name]
    .filter(Boolean)
    .join(" ")
    .trim() || "Unnamed";
}

export function patientName(patient: Patient): string {
  const preferred = patient.names.find((n) => n.preferred) ?? patient.names[0];
  return formatName(preferred);
}

export function initials(value: string): string {
  return value
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

export function preferredIdentifier(patient: Patient): string | null {
  const id = patient.identifiers.find((i) => i.preferred) ?? patient.identifiers[0];
  return id?.identifier ?? null;
}

const GENDER_LABELS: Record<string, string> = {
  M: "Male",
  F: "Female",
  O: "Other",
  U: "Unknown",
};

export function genderLabel(gender?: string | null): string {
  if (!gender) return "—";
  return GENDER_LABELS[gender] ?? gender;
}

/** Whole-year age from an ISO birthdate, or null if unknown. */
export function ageFromBirthdate(birthdate?: string | null): number | null {
  if (!birthdate) return null;
  const dob = new Date(birthdate);
  if (Number.isNaN(dob.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - dob.getFullYear();
  const m = now.getMonth() - dob.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < dob.getDate())) age--;
  return age;
}

/** Format a decimal-string/number as money with an optional currency code. */
export function money(value: string | number | null | undefined, currency?: string): string {
  const n = typeof value === "string" ? Number(value) : (value ?? 0);
  const amount = Number.isFinite(n) ? n : 0;
  const formatted = amount.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return currency ? `${currency} ${formatted}` : formatted;
}

export function formatDate(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
