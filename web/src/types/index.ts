export type Citation = {
  kb: string;
  document: string;
  page?: number;
  snippet: string;
};

export type HealthResponse = {
  status: string;
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