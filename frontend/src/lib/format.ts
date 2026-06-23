interface NamedPerson {
  names: { preferred: boolean; given_name: string; middle_name: string; family_name: string }[];
}

interface IdentifiedPatient {
  identifiers: { preferred: boolean; identifier: string }[];
}

export function money(amount: string | number | null | undefined, currency = "USD"): string {
  const value = amount === null || amount === undefined ? 0 : Number(amount);
  return new Intl.NumberFormat(undefined, { style: "currency", currency }).format(value);
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function patientName(patient: NamedPerson): string {
  const name = patient.names.find((n) => n.preferred) ?? patient.names[0];
  if (!name) return "Unknown";
  return [name.given_name, name.middle_name, name.family_name].filter(Boolean).join(" ");
}

export function preferredIdentifier(patient: IdentifiedPatient): string | null {
  const identifier = patient.identifiers.find((i) => i.preferred) ?? patient.identifiers[0];
  return identifier?.identifier ?? null;
}

export function genderLabel(gender: "M" | "F" | "O" | "U" | null | undefined): string {
  switch (gender) {
    case "M":
      return "Male";
    case "F":
      return "Female";
    case "O":
      return "Other";
    case "U":
      return "Unknown";
    default:
      return "—";
  }
}

export function ageFromBirthdate(birthdate: string | null | undefined): number | null {
  if (!birthdate) return null;
  const dob = new Date(birthdate);
  if (Number.isNaN(dob.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - dob.getFullYear();
  const monthDiff = now.getMonth() - dob.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && now.getDate() < dob.getDate())) {
    age -= 1;
  }
  return age;
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}
