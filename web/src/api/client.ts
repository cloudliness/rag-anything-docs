import type {
  BrowserUploadPayload,
  CapabilityResponse,
  CreateKnowledgeBasePayload,
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


export function getCapabilities() {
  return requestJson<CapabilityResponse>("/api/health/capabilities");
}


export function getKnowledgeBases() {
  return requestJson<KnowledgeBase[]>("/api/kbs");
}


export function createKnowledgeBase(payload: CreateKnowledgeBasePayload) {
  return requestJson<KnowledgeBase>("/api/kbs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
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


export async function uploadBrowserFile(payload: BrowserUploadPayload) {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("knowledge_base", payload.knowledge_base);
  formData.append("reset", String(payload.reset ?? false));

  if (payload.parse_method) {
    formData.append("parse_method", payload.parse_method);
  }
  if (payload.page != null) {
    formData.append("page", String(payload.page));
  }
  if (payload.start_page != null) {
    formData.append("start_page", String(payload.start_page));
  }
  if (payload.end_page != null) {
    formData.append("end_page", String(payload.end_page));
  }

  const response = await fetch(`${API_BASE_URL}/api/documents/upload-file`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<DocumentRecord>;
}


export function queryKnowledgeBase(payload: QueryPayload) {
  return requestJson<QueryResponse>("/api/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}