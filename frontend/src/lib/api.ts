import type {
  CreateSessionResponse,
  ListDocumentsResponse,
  QueryResponse,
  SessionHistoryResponse,
  UploadDocumentResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // keep the generic detail
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
    body: formData,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // keep the generic detail
    }
    throw new Error(detail);
  }
  return (await response.json()) as UploadDocumentResponse;
}

export function listDocuments(): Promise<ListDocumentsResponse> {
  return request<ListDocumentsResponse>("/listDocuments");
}
