import { tokenStore, orgStore } from "./tokens";
import { ApiError } from "./types";

type QueryParams = Record<string, string | number | boolean | undefined | null>;

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";
const API_V1 = `${API_BASE}/api/v1`;

type AuthFailureHandler = () => void;
let authFailureHandler: AuthFailureHandler | null = null;

/** Called when a token refresh ultimately fails, so the app can drop the session. */
export function setAuthFailureHandler(handler: AuthFailureHandler) {
  authFailureHandler = handler;
}

let refreshPromise: Promise<string | null> | null = null;

function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStore.getRefresh();
  if (!refresh) return Promise.resolve(null);
  if (!refreshPromise) {
    refreshPromise = fetch(`${API_V1}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    })
      .then(async (res) => {
        if (!res.ok) return null;
        const data = await res.json();
        tokenStore.setAccess(data.access);
        return data.access as string;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function buildHeaders(hasBody: boolean): Record<string, string> {
  const headers: Record<string, string> = {};
  if (hasBody) headers["Content-Type"] = "application/json";
  const access = tokenStore.getAccess();
  if (access) headers.Authorization = `Bearer ${access}`;
  const org = orgStore.get();
  if (org) headers["X-Organization"] = org;
  return headers;
}

async function parseErrorBody(response: Response): Promise<ApiError> {
  try {
    const data = await response.json();
    if (data && typeof data === "object" && "error" in data) {
      return new ApiError(data.error);
    }
    return new ApiError({ status: response.status, type: "Error", detail: data });
  } catch {
    return new ApiError({ status: response.status, type: "Error", detail: response.statusText });
  }
}

async function authorizedFetch(
  url: string,
  init: RequestInit,
  hasBody: boolean,
): Promise<Response> {
  const headers = { ...buildHeaders(hasBody), ...(init.headers as Record<string, string>) };
  let response = await fetch(url, { ...init, headers });

  if (response.status === 401) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      response = await fetch(url, {
        ...init,
        headers: { ...headers, Authorization: `Bearer ${newAccess}` },
      });
    } else {
      tokenStore.clear();
      authFailureHandler?.();
    }
  }
  return response;
}

function buildQuery(params?: QueryParams): string {
  if (!params) return "";
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) query.set(key, String(value));
  }
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  params?: QueryParams,
): Promise<T> {
  const hasBody = body !== undefined;
  const url = `${API_V1}${path}${method === "GET" ? buildQuery(params) : ""}`;
  const response = await authorizedFetch(
    url,
    { method, body: hasBody ? JSON.stringify(body) : undefined },
    hasBody,
  );

  if (!response.ok) {
    throw await parseErrorBody(response);
  }
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}

export const api = {
  get<T>(path: string, params?: QueryParams) {
    return request<T>("GET", path, undefined, params);
  },
  post<T>(path: string, data: unknown = {}) {
    return request<T>("POST", path, data);
  },
  patch<T>(path: string, data: unknown) {
    return request<T>("PATCH", path, data);
  },
  put<T>(path: string, data: unknown) {
    return request<T>("PUT", path, data);
  },
  delete<T>(path: string) {
    return request<T>("DELETE", path);
  },
};

/** Downloads a server-generated file (PDF report, receipt, label) that requires auth headers. */
export async function openAuthenticatedFile(absoluteUrl: string): Promise<void> {
  const url = `${API_BASE}${absoluteUrl}`;
  const response = await authorizedFetch(url, { method: "GET" }, false);
  if (!response.ok) {
    throw await parseErrorBody(response);
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  window.open(objectUrl, "_blank");
  setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
}
