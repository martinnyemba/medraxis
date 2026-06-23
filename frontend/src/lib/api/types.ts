/** Shared API envelope types mirroring the Django REST Framework backend. */

/** Standard paginated list response (see core/api/pagination.py). */
export interface Paginated<T> {
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** Error envelope (see core/api/exceptions.py): {"error": {...}}. */
export interface ApiErrorEnvelope {
  error: {
    status: number;
    type: string;
    detail: unknown;
  };
}

/** Raised by the API client for any non-2xx response. */
export class ApiError extends Error {
  status: number;
  type: string;
  detail: unknown;

  constructor(status: number, type: string, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.type = type;
    this.detail = detail;
  }

  /** Flatten DRF field errors / string details into a human-readable string. */
  toUserMessage(): string {
    const d = this.detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) return d.join(", ");
    if (d && typeof d === "object") {
      return Object.entries(d as Record<string, unknown>)
        .map(([field, errs]) => {
          const msg = Array.isArray(errs) ? errs.join(", ") : String(errs);
          return field === "non_field_errors" ? msg : `${field}: ${msg}`;
        })
        .join("\n");
    }
    return this.message || "Request failed";
  }
}
