import { useState } from "react";

import type { IngestJob, KnowledgeBase } from "../types";


type JobsPageProps = {
  jobs: IngestJob[];
  knowledgeBases: KnowledgeBase[];
  isUploading: boolean;
  onRetryUpload: (jobId: string) => Promise<void>;
  onCancelUpload: (jobId: string) => Promise<void>;
};


function formatDuration(durationMs?: number | null) {
  if (durationMs == null) {
    return "n/a";
  }
  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }
  return `${(durationMs / 1000).toFixed(1)} s`;
}


function formatActualPages(job: IngestJob) {
  if (job.actual_processed_page_count != null) {
    if (job.actual_processed_start_page != null && job.actual_processed_end_page != null) {
      return `${job.actual_processed_page_count} processed page${job.actual_processed_page_count === 1 ? "" : "s"} (${job.actual_processed_start_page}-${job.actual_processed_end_page})`;
    }
    return `${job.actual_processed_page_count} processed page${job.actual_processed_page_count === 1 ? "" : "s"}`;
  }
  if (job.requested_page_count != null) {
    return `${job.requested_page_count} requested page${job.requested_page_count === 1 ? "" : "s"}`;
  }
  return "all pages requested";
}


export function JobsPage(props: JobsPageProps) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [knowledgeBaseFilter, setKnowledgeBaseFilter] = useState("all");
  const [sortOrder, setSortOrder] = useState("updated-desc");
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const normalizedSearch = search.trim().toLowerCase();
  const filteredJobs = props.jobs
    .filter((job) => {
      if (statusFilter !== "all" && job.status !== statusFilter) {
        return false;
      }
      if (knowledgeBaseFilter !== "all" && job.knowledge_base !== knowledgeBaseFilter) {
        return false;
      }
      if (!normalizedSearch) {
        return true;
      }
      return [job.file_name, job.knowledge_base, job.parser_backend, job.parse_method ?? "auto"].some((value) => value.toLowerCase().includes(normalizedSearch));
    })
    .sort((left, right) => {
      switch (sortOrder) {
        case "duration-desc":
          return (right.duration_ms ?? -1) - (left.duration_ms ?? -1);
        case "progress-desc":
          return right.progress - left.progress;
        case "file-asc":
          return left.file_name.localeCompare(right.file_name);
        case "updated-asc":
          return left.updated_at.localeCompare(right.updated_at);
        case "updated-desc":
        default:
          return right.updated_at.localeCompare(left.updated_at);
      }
    });

  async function handleRetry(jobId: string) {
    setMessage(null);
    setErrorMessage(null);
    try {
      await props.onRetryUpload(jobId);
      setMessage("Retry requested successfully.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Retry failed");
    }
  }

  async function handleCancel(jobId: string) {
    setMessage(null);
    setErrorMessage(null);
    try {
      await props.onCancelUpload(jobId);
      setMessage("Cancellation request sent.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Cancel failed");
    }
  }

  return (
    <section style={panelStyle}>
      <div style={{ alignItems: "start", display: "flex", justifyContent: "space-between", gap: "1rem" }}>
        <div>
          <h2 style={{ marginTop: 0, marginBottom: "0.3rem" }}>Jobs</h2>
          <p style={subtleTextStyle}>Filter, sort, retry, and cancel ingest work from a dedicated operations view.</p>
        </div>
        <div style={summaryPillStyle}>{filteredJobs.length} visible job{filteredJobs.length === 1 ? "" : "s"}</div>
      </div>

      <div style={controlsGridStyle}>
        <label style={fieldStyle}>
          <span style={labelStyle}>Search jobs</span>
          <input aria-label="Search jobs" onChange={(event) => setSearch(event.target.value)} placeholder="file, KB, parser" style={inputStyle} value={search} />
        </label>
        <label style={fieldStyle}>
          <span style={labelStyle}>Status</span>
          <select aria-label="Filter by status" onChange={(event) => setStatusFilter(event.target.value)} style={inputStyle} value={statusFilter}>
            <option value="all">all</option>
            <option value="queued">queued</option>
            <option value="running">running</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
            <option value="canceled">canceled</option>
          </select>
        </label>
        <label style={fieldStyle}>
          <span style={labelStyle}>Knowledge base</span>
          <select aria-label="Filter by knowledge base" onChange={(event) => setKnowledgeBaseFilter(event.target.value)} style={inputStyle} value={knowledgeBaseFilter}>
            <option value="all">all</option>
            {props.knowledgeBases.map((knowledgeBase) => (
              <option key={knowledgeBase.name} value={knowledgeBase.name}>{knowledgeBase.name}</option>
            ))}
          </select>
        </label>
        <label style={fieldStyle}>
          <span style={labelStyle}>Sort</span>
          <select aria-label="Sort jobs" onChange={(event) => setSortOrder(event.target.value)} style={inputStyle} value={sortOrder}>
            <option value="updated-desc">Recently updated</option>
            <option value="updated-asc">Oldest updated</option>
            <option value="duration-desc">Duration (slowest first)</option>
            <option value="progress-desc">Progress</option>
            <option value="file-asc">File name</option>
          </select>
        </label>
      </div>

      {message ? <div style={{ color: "#125c2e" }}>{message}</div> : null}
      {errorMessage ? <div style={{ color: "#9f1f1f" }}>{errorMessage}</div> : null}

      <div style={{ display: "grid", gap: "0.85rem" }}>
        {filteredJobs.length === 0 ? (
          <div style={emptyStateStyle}>No jobs match the current filters.</div>
        ) : (
          filteredJobs.map((job) => (
            <article key={job.job_id} style={jobCardStyle}>
              <div style={{ alignItems: "start", display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                <div style={{ minWidth: 0 }}>
                  <h3 style={{ margin: 0 }}>{job.file_name}</h3>
                  <div style={jobMetaStyle}>{job.knowledge_base} | {job.status} | {job.parser_backend}/{job.parse_method ?? "auto"}</div>
                  <div style={jobMetaStyle}>{formatActualPages(job)} | duration {formatDuration(job.duration_ms)} | progress {job.progress}%</div>
                  <div style={{ color: "#52606d", fontSize: "0.92rem", marginTop: "0.35rem" }}>{job.message}</div>
                  {job.error ? <div style={{ color: "#9f1f1f", fontSize: "0.92rem", marginTop: "0.35rem" }}>{job.error}</div> : null}
                  {job.retry_of ? <div style={{ color: "#52606d", fontSize: "0.86rem", marginTop: "0.35rem" }}>Retry of {job.retry_of}</div> : null}
                </div>
                <div style={{ display: "grid", gap: "0.55rem", minWidth: "152px" }}>
                  <div style={statusPillStyle}>{job.progress}%</div>
                  <button disabled={!job.can_cancel} onClick={() => void handleCancel(job.job_id)} style={secondaryButtonStyle} type="button">Cancel</button>
                  <button disabled={!job.can_retry || props.isUploading} onClick={() => void handleRetry(job.job_id)} style={secondaryButtonStyle} type="button">Retry</button>
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </section>
  );
}


const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7e0e7",
  borderRadius: "18px",
  display: "grid",
  gap: "1rem",
  padding: "1rem",
};


const subtleTextStyle = {
  color: "#52606d",
  margin: 0,
};


const summaryPillStyle = {
  background: "#edf4f7",
  border: "1px solid #cad7df",
  borderRadius: "999px",
  color: "#234257",
  fontSize: "0.92rem",
  fontWeight: 700,
  padding: "0.55rem 0.85rem",
};


const controlsGridStyle = {
  display: "grid",
  gap: "0.85rem",
  gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
};


const fieldStyle = {
  display: "grid",
  gap: "0.35rem",
};


const labelStyle = {
  fontWeight: 600,
};


const inputStyle = {
  background: "#ffffff",
  border: "1px solid #cad7df",
  borderRadius: "10px",
  padding: "0.75rem 0.9rem",
};


const emptyStateStyle = {
  background: "#f7fafc",
  border: "1px dashed #cad7df",
  borderRadius: "14px",
  color: "#52606d",
  padding: "1rem",
};


const jobCardStyle = {
  background: "#fbfdfe",
  border: "1px solid #d7e0e7",
  borderRadius: "14px",
  padding: "0.95rem 1rem",
};


const jobMetaStyle = {
  color: "#55616c",
  fontSize: "0.9rem",
  marginTop: "0.25rem",
};


const statusPillStyle = {
  background: "#edf4f7",
  border: "1px solid #cad7df",
  borderRadius: "999px",
  color: "#234257",
  fontSize: "0.86rem",
  padding: "0.35rem 0.7rem",
  textAlign: "center" as const,
};


const secondaryButtonStyle = {
  background: "#ffffff",
  border: "1px solid #cad7df",
  borderRadius: "999px",
  color: "#173042",
  cursor: "pointer",
  fontWeight: 600,
  padding: "0.55rem 0.75rem",
};