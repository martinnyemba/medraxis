import { ApiError, type ApiErrorEnvelope } from "./types";
import { orgStore, tokenStore } from "./tokens";

/**
 * Base URL for the versioned API. In dev, Vite proxies "/api" to Django
 * (see vite.config.ts); in prod set VITE_API_BASE_URL to the backend origin.
 */
const API_BASE = `${import.meta.env.VITE_API_BASE_URL ?? ""}/api/v1`;

/** Called when refresh fails — wired up by the auth layer to force logout. */
let onAuthFailure: (() => void) | null = null;
export function setAuthFailureHandler(fn: () => void) {
  onAuthFailure = fn;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Query params; undefined/null values are dropped. */
  params?: Record<string, string | number | boolean | undefined | null>;
  /** Skip the Authorization header (used by the login/refresh calls). */
  anonymous?: boolean;
  signal?: AbortSignal;
}

function buildUrl(path: string, params?: RequestOptions["params"]): string {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function parseError(response: Response): Promise<ApiError> {
  let type = "HttpError";
  let detail: unknown = response.statusText;
  try {
    const data = (await response.json()) as Partial<ApiErrorEnvelope>;
    if (data?.error) {
      type = data.error.type ?? type;
      detail = data.error.detail ?? detail;
    } else {
      detail = data;
    }
  } catch {
    /* non-JSON body — keep the status text */
  }
  return new ApiError(response.status, type, detail, `${response.status} ${type}`);
}

let refreshPromise: Promise<boolean> | null = null;

/** Attempt to mint a new access token from the stored refresh token. */
async function refreshAccessToken(): Promise<boolean> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return false;

  // De-duplicate concurrent refreshes into a single in-flight request.
  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(buildUrl("/auth/token/refresh/"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
        });
        if (!res.ok) return false;
        const data = (await res.json()) as { access: string; refresh?: string };
        tokenStore.setTokens(data.access, data.refresh);
        return true;
      } catch {
        return false;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

async function rawRequest(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = { Accept: "application/json" };

  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (!options.anonymous) {
    const access = tokenStore.getAccess();
    if (access) headers["Authorization"] = `Bearer ${access}`;
    const org = orgStore.get();
    if (org) headers["X-Organization"] = org;
  }

  return fetch(buildUrl(path, options.params), {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  });
}

/** Core request: handles JSON, the error envelope, and one transparent retry
 *  after refreshing an expired access token. */
async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await rawRequest(path, options);

  if (response.status === 401 && !options.anonymous) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await rawRequest(path, options);
    } else {
      tokenStore.clear();
      onAuthFailure?.();
    }
  }

  if (!response.ok) throw await parseError(response);
  if (response.status === 204) return undefined as T;

  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

/**
 * Fetch an authenticated binary endpoint (e.g. a PDF) and open it in a new tab.
 * `path` is an absolute API path such as `/api/v1/lab/specimens/1/label/`.
 */
export async function openAuthenticatedFile(path: string): Promise<void> {
  const headers: Record<string, string> = {};
  const access = tokenStore.getAccess();
  if (access) headers["Authorization"] = `Bearer ${access}`;
  const org = orgStore.get();
  if (org) headers["X-Organization"] = org;

  const base = import.meta.env.VITE_API_BASE_URL ?? "";
  let res = await fetch(`${base}${path}`, { headers });
  if (res.status === 401 && (await refreshAccessToken())) {
    const retryAccess = tokenStore.getAccess();
    if (retryAccess) headers["Authorization"] = `Bearer ${retryAccess}`;
    res = await fetch(`${base}${path}`, { headers });
  }
  if (!res.ok) throw await parseError(res);

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  // Give the browser a moment to load the blob before revoking.
  window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

export const api = {
  get: <T>(path: string, params?: RequestOptions["params"], signal?: AbortSignal) =>
    request<T>(path, { method: "GET", params, signal }),
  post: <T>(path: string, body?: unknown, params?: RequestOptions["params"]) =>
    request<T>(path, { method: "POST", body, params }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: "PUT", body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  /** Anonymous POST for the login endpoint. */
  login: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body, anonymous: true }),
};
