import type {
  CreateSessionResponse,
  ListDocumentsResponse,
  ListSessionsResponse,
  QueryResponse,
  SessionHistoryResponse,
  UploadDocumentResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
export const TOKEN_STORAGE_KEY = "cts_api_auth_token";

export function getAuthToken(): string {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (stored) return stored;
  }
  return "dev-secret-key-change-me";
}

export function setAuthToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }
}

function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const customHeaders = (options?.headers as Record<string, string>) || {};
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: getAuthHeaders({
      "Content-Type": "application/json",
      ...customHeaders,
    }),
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // keep generic detail
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function createSession(): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>("/createSession", { method: "POST" });
}

export function queryChat(sessionId: string, question: string): Promise<QueryResponse> {
  return request<QueryResponse>("/queryChat", {
    method: "POST",
    body: JSON.stringify({ sessionId, question }),
  });
}

export function getSessionHistory(sessionId: string): Promise<SessionHistoryResponse> {
  return request<SessionHistoryResponse>(`/sessionHistory/${sessionId}`);
}

export async function uploadDocument(
  file: File,
  docName?: string,
): Promise<UploadDocumentResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (docName) formData.append("docName", docName);

  const response = await fetch(`${API_BASE}/uploadDocument`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // keep generic detail
    }
    throw new Error(detail);
  }
  return (await response.json()) as UploadDocumentResponse;
}

export function listDocuments(): Promise<ListDocumentsResponse> {
  return request<ListDocumentsResponse>("/listDocuments");
}

export function listSessions(): Promise<ListSessionsResponse> {
  return request<ListSessionsResponse>("/listSessions");
}
