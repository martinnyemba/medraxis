/** Mirrors apps/core/api/pagination.py StandardResultsSetPagination. */
export interface Paginated<T> {
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** Mirrors the {"error": {status, type, detail}} envelope from apps/core/api/exceptions.py. */
interface ErrorEnvelope {
  status: number;
  type: string;
  detail: unknown;
}

export class ApiError extends Error {
  status: number;
  type: string;
  detail: unknown;

  constructor(envelope: ErrorEnvelope) {
    super(typeof envelope.detail === "string" ? envelope.detail : envelope.type);
    this.name = "ApiError";
    this.status = envelope.status;
    this.type = envelope.type;
    this.detail = envelope.detail;
  }

  toUserMessage(): string {
    const { detail } = this;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.join("\n");
    if (detail && typeof detail === "object") {
      return Object.entries(detail as Record<string, unknown>)
        .map(([field, errors]) => {
          const text = Array.isArray(errors) ? errors.join(", ") : String(errors);
          return field === "non_field_errors" ? text : `${field}: ${text}`;
        })
        .join("\n");
    }
    return "Something went wrong.";
  }
}
