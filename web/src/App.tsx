import { useEffect, useState } from "react";

import {
  cancelIngestJob,
  createKnowledgeBase,
  getCapabilities,
  getDocumentsForKnowledgeBase,
  getHealth,
  getIngestJob,
  getIngestJobs,
  getKnowledgeBases,
  queryKnowledgeBase,
  retryIngestJob,
  startBrowserUploadJob,
} from "./api/client";
import { DashboardPage } from "./pages/DashboardPage";
import { KnowledgeBasesPage } from "./pages/KnowledgeBasesPage";
import { QueryPage } from "./pages/QueryPage";
import { UploadPage } from "./pages/UploadPage";
import type {
  BrowserUploadPayload,
  CapabilityResponse,
  CreateKnowledgeBasePayload,
  DocumentRecord,
  HealthResponse,
  IngestJob,
  KnowledgeBase,
  QueryPayload,
  QueryResponse,
} from "./types";


export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [capabilities, setCapabilities] = useState<CapabilityResponse | null>(null);
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBase[]>([]);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [queryKnowledgeBases, setQueryKnowledgeBases] = useState<string[]>([]);
  const [currentUploadJob, setCurrentUploadJob] = useState<IngestJob | null>(null);
  const [recentUploadJobs, setRecentUploadJobs] = useState<IngestJob[]>([]);

  function syncCurrentUploadJob(jobs: IngestJob[]) {
    const activeJob = jobs.find((job) => job.status === "queued" || job.status === "running");
    setCurrentUploadJob(activeJob ?? jobs[0] ?? null);
  }

  async function refreshUploadJobs() {
    const jobs = await getIngestJobs(12);
    setRecentUploadJobs(jobs);
    syncCurrentUploadJob(jobs);
    return jobs;
  }

  async function waitForUploadJob(jobId: string) {
    let latestJob = await getIngestJob(jobId);
    setCurrentUploadJob(latestJob);

    while (latestJob.status === "queued" || latestJob.status === "running") {
      await new Promise((resolve) => window.setTimeout(resolve, 1500));
      latestJob = await getIngestJob(jobId);
      setCurrentUploadJob(latestJob);
      await refreshUploadJobs();
    }

    return latestJob;
  }

  useEffect(() => {
    async function load() {
      try {
        const [healthResponse, capabilityResponse, kbs, jobs] = await Promise.all([
          getHealth(),
          getCapabilities(),
          getKnowledgeBases(),
          getIngestJobs(12),
        ]);
        setHealth(healthResponse);
        setCapabilities(capabilityResponse);
        setKnowledgeBases(kbs);
        setRecentUploadJobs(jobs);
        syncCurrentUploadJob(jobs);
        setSelectedKnowledgeBase((currentSelection) => currentSelection ?? kbs[0]?.name ?? null);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "Unknown error");
        setHealth({ status: "error", version: "unknown" });
      }
    }

    void load();
  }, []);

  useEffect(() => {
    if (!recentUploadJobs.some((job) => job.status === "queued" || job.status === "running")) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      void refreshUploadJobs();
    }, 1500);

    return () => window.clearInterval(timer);
  }, [recentUploadJobs]);

  useEffect(() => {
    setQueryKnowledgeBases((currentSelection) => {
      const availableKnowledgeBases = new Set(knowledgeBases.map((knowledgeBase) => knowledgeBase.name));
      const filteredSelection = currentSelection.filter((knowledgeBaseName) => availableKnowledgeBases.has(knowledgeBaseName));

      if (filteredSelection.length > 0) {
        return filteredSelection;
      }

      if (selectedKnowledgeBase && availableKnowledgeBases.has(selectedKnowledgeBase)) {
        return [selectedKnowledgeBase];
      }

      return knowledgeBases[0]?.name ? [knowledgeBases[0].name] : [];
    });
  }, [knowledgeBases, selectedKnowledgeBase]);

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

  async function handleUpload(payload: BrowserUploadPayload) {
    setIsUploading(true);
    setErrorMessage(null);

    try {
      const job = await startBrowserUploadJob(payload);
      setCurrentUploadJob(job);
      await refreshUploadJobs();

      const latestJob = await waitForUploadJob(job.job_id);

      if (latestJob.status !== "completed") {
        throw new Error(latestJob.error || latestJob.message || "Upload failed");
      }

      const kbs = await refreshKnowledgeBases();
      const kbName = payload.knowledge_base ?? selectedKnowledgeBase;

      if (kbName) {
        setSelectedKnowledgeBase(kbName);
        await refreshDocuments(kbName);
      } else if (kbs[0]?.name) {
        setSelectedKnowledgeBase(kbs[0].name);
        await refreshDocuments(kbs[0].name);
      }
    } finally {
      setIsUploading(false);
      await refreshUploadJobs();
    }
  }


  async function handleRetryUpload(jobId: string) {
    setIsUploading(true);
    setErrorMessage(null);

    try {
      const job = await retryIngestJob(jobId);
      setCurrentUploadJob(job);
      await refreshUploadJobs();

      const latestJob = await waitForUploadJob(job.job_id);
      if (latestJob.status !== "completed") {
        throw new Error(latestJob.error || latestJob.message || "Retry failed");
      }

      await refreshKnowledgeBases();
      await refreshDocuments(latestJob.knowledge_base);
      setSelectedKnowledgeBase(latestJob.knowledge_base);
    } finally {
      setIsUploading(false);
      await refreshUploadJobs();
    }
  }


  async function handleCancelUpload(jobId: string) {
    setErrorMessage(null);
    await cancelIngestJob(jobId);
    await refreshUploadJobs();
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

  async function handleCreateKnowledgeBase(payload: CreateKnowledgeBasePayload) {
    setErrorMessage(null);
    const created = await createKnowledgeBase(payload);
    await refreshKnowledgeBases();
    setSelectedKnowledgeBase(created.name);
    setQueryKnowledgeBases([created.name]);
    setDocuments([]);
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
          Phase 1 now supports KB creation, browser upload, multi-KB query synthesis, and markdown plus math answer rendering.
        </p>
      </header>

      {errorMessage ? <p>Load error: {errorMessage}</p> : null}

      <div style={{ display: "grid", gap: "1rem" }}>
        <DashboardPage capabilities={capabilities} health={health} knowledgeBaseCount={knowledgeBases.length} recentUploadJobs={recentUploadJobs} />
        <KnowledgeBasesPage
          capabilities={capabilities}
          documents={documents}
          isLoadingDocuments={documentsLoading}
          knowledgeBases={knowledgeBases}
          onCreateKnowledgeBase={handleCreateKnowledgeBase}
          onSelectKnowledgeBase={setSelectedKnowledgeBase}
          selectedKnowledgeBase={selectedKnowledgeBase}
        />

        <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)" }}>
          <UploadPage
            capabilities={capabilities}
            currentUploadJob={currentUploadJob}
            isUploading={isUploading}
            onCancelUpload={handleCancelUpload}
            onRetryUpload={handleRetryUpload}
            onUpload={handleUpload}
            recentUploadJobs={recentUploadJobs}
            selectedKnowledgeBase={selectedKnowledgeBase}
          />
          <QueryPage
            capabilities={capabilities}
            isQuerying={isQuerying}
            knowledgeBases={knowledgeBases}
            onQuery={handleQuery}
            onSelectedKnowledgeBasesChange={setQueryKnowledgeBases}
            selectedKnowledgeBases={queryKnowledgeBases}
          />
        </div>
      </div>
    </main>
  );
}