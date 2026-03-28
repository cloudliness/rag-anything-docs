import { useEffect, useState } from "react";

import {
  getDocumentsForKnowledgeBase,
  getHealth,
  getKnowledgeBases,
  queryKnowledgeBase,
  uploadDocument,
} from "./api/client";
import { DashboardPage } from "./pages/DashboardPage";
import { KnowledgeBasesPage } from "./pages/KnowledgeBasesPage";
import { QueryPage } from "./pages/QueryPage";
import { UploadPage } from "./pages/UploadPage";
import type { DocumentRecord, KnowledgeBase, QueryPayload, QueryResponse, UploadDocumentPayload } from "./types";


export function App() {
  const [healthStatus, setHealthStatus] = useState("loading");
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [health, kbs] = await Promise.all([getHealth(), getKnowledgeBases()]);
        setHealthStatus(health.status ?? "unknown");
        setKnowledgeBases(kbs);
        setSelectedKnowledgeBase((currentSelection) => currentSelection ?? kbs[0]?.name ?? null);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "Unknown error");
        setHealthStatus("error");
      }
    }

    void load();
  }, []);

  useEffect(() => {
    async function loadDocuments() {
      if (!selectedKnowledgeBase) {
        setDocuments([]);
        return;
      }

      setDocumentsLoading(true);

      try {
        const records = await getDocumentsForKnowledgeBase(selectedKnowledgeBase);
        setDocuments(records);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "Failed to load documents");
      } finally {
        setDocumentsLoading(false);
      }
    }

    void loadDocuments();
  }, [selectedKnowledgeBase]);

  async function refreshKnowledgeBases() {
    const kbs = await getKnowledgeBases();
    setKnowledgeBases(kbs);
    return kbs;
  }

  async function refreshDocuments(kbName: string) {
    const records = await getDocumentsForKnowledgeBase(kbName);
    setDocuments(records);
  }

  async function handleUpload(payload: UploadDocumentPayload) {
    setIsUploading(true);
    setErrorMessage(null);

    try {
      await uploadDocument(payload);
      const kbs = await refreshKnowledgeBases();
      const kbName = payload.knowledge_bases[0] ?? selectedKnowledgeBase;

      if (kbName) {
        setSelectedKnowledgeBase(kbName);
        await refreshDocuments(kbName);
      } else if (kbs[0]?.name) {
        setSelectedKnowledgeBase(kbs[0].name);
        await refreshDocuments(kbs[0].name);
      }
    } finally {
      setIsUploading(false);
    }
  }

  async function handleQuery(payload: QueryPayload): Promise<QueryResponse> {
    setIsQuerying(true);
    setErrorMessage(null);

    try {
      return await queryKnowledgeBase(payload);
    } finally {
      setIsQuerying(false);
    }
  }

  return (
    <main
      style={{
        background: "linear-gradient(180deg, #edf4f7 0%, #f8fafb 100%)",
        color: "#173042",
        fontFamily: '"Segoe UI", "Helvetica Neue", sans-serif',
        margin: "0 auto",
        maxWidth: "1200px",
        minHeight: "100vh",
        padding: "2rem 1.25rem 3rem",
      }}
    >
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "2.2rem", marginBottom: "0.3rem", marginTop: 0 }}>RAG Pipeline Product UI</h1>
        <p style={{ color: "#52606d", margin: 0 }}>
          Phase 1 now supports real KB selection, document listing, path-based ingest, and single-KB querying with citations.
        </p>
      </header>

      {errorMessage ? <p>Load error: {errorMessage}</p> : null}

      <div style={{ display: "grid", gap: "1rem" }}>
        <DashboardPage status={healthStatus} knowledgeBaseCount={knowledgeBases.length} />

        <KnowledgeBasesPage
          documents={documents}
          isLoadingDocuments={documentsLoading}
          knowledgeBases={knowledgeBases}
          onSelectKnowledgeBase={setSelectedKnowledgeBase}
          selectedKnowledgeBase={selectedKnowledgeBase}
        />

        <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)" }}>
          <UploadPage isUploading={isUploading} onUpload={handleUpload} selectedKnowledgeBase={selectedKnowledgeBase} />
          <QueryPage isQuerying={isQuerying} onQuery={handleQuery} selectedKnowledgeBase={selectedKnowledgeBase} />
        </div>
      </div>
    </main>
  );
}