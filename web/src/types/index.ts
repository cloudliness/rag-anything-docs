export type Citation = {
  kb: string;
  document: string;
  page?: number;
  snippet: string;
};

export type HealthResponse = {
  status: string;
  version: string;
};

export type CapabilityResponse = {
  max_query_kbs: number;
  max_upload_target_kbs: number;
  multi_kb_query_status: string;
  multi_kb_upload_status: string;
  kb_creation_enabled: boolean;
  path_upload_enabled: boolean;
  browser_upload_enabled: boolean;
  math_rendering_status: string;
  citation_grounding_status: string;
  notes: string[];
};

export type KnowledgeBase = {
  name: string;
  description?: string | null;
  document_count: number;
};

export type DocumentRecord = {
  file_name: string;
  knowledge_base: string;
  status: string;
  parsed_output_path?: string | null;
};

export type UploadDocumentPayload = {
  source_path: string;
  knowledge_bases: string[];
  parse_method?: string | null;
  reset?: boolean;
  page?: number | null;
  start_page?: number | null;
  end_page?: number | null;
};

export type BrowserUploadPayload = {
  file: File;
  knowledge_base: string;
  parse_method?: string | null;
  reset?: boolean;
  page?: number | null;
  start_page?: number | null;
  end_page?: number | null;
};

export type CreateKnowledgeBasePayload = {
  name: string;
  description?: string | null;
};

export type QueryPayload = {
  question: string;
  knowledge_bases: string[];
  query_mode?: string;
  answer_mode?: string;
};

export type QueryResponse = {
  answer: string;
  selected_kbs: string[];
  contributing_kbs: string[];
  citations: Citation[];
};