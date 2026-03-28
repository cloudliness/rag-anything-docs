import type {
  DocumentRecord,
  HealthResponse,
  KnowledgeBase,
  QueryPayload,
  QueryResponse,
  UploadDocumentPayload,
} from "../types";


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";


async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}


export function getHealth() {
  return requestJson<HealthResponse>("/api/health");
}


export function getKnowledgeBases() {
  return requestJson<KnowledgeBase[]>("/api/kbs");
}


export function getDocumentsForKnowledgeBase(kbName: string) {
  return requestJson<DocumentRecord[]>(`/api/documents/kb/${encodeURIComponent(kbName)}`);
}


export function uploadDocument(payload: UploadDocumentPayload) {
  return requestJson<DocumentRecord>("/api/documents/upload", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}


export function queryKnowledgeBase(payload: QueryPayload) {
  return requestJson<QueryResponse>("/api/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}