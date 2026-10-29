import type { ApiError } from "./types";

const API_PREFIX = "/api/v1";

function csrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export class ApiRequestError extends Error {
  status: number;
  payload: ApiError | null;
  constructor(message: string, status: number, payload: ApiError | null) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const isForm = typeof FormData !== "undefined" && init.body instanceof FormData;
  if (!isForm && init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const method = (init.method || "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = csrfToken();
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : null;
  if (!response.ok) {
    const message = (payload && (payload.error || payload.detail)) || `Request failed (${response.status})`;
    throw new ApiRequestError(String(message), response.status, payload);
  }
  if (response.status === 204) return undefined as T;
  return (payload ?? (await response.text())) as T;
}

export async function apiBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_PREFIX}${path}`, { credentials: "include", cache: "no-store" });
  if (!response.ok) {
    throw new ApiRequestError("Download failed", response.status, null);
  }
  return response.blob();
}
