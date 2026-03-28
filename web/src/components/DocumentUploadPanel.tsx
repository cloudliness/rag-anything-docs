import { useRef, useState } from "react";

import type { BrowserUploadPayload, IngestJob } from "../types";


type DocumentUploadPanelProps = {
  selectedKnowledgeBase: string | null;
  onUpload: (payload: BrowserUploadPayload) => Promise<void>;
  onRetryUpload: (jobId: string) => Promise<void>;
  onCancelUpload: (jobId: string) => Promise<void>;
  isUploading: boolean;
  currentUploadJob: IngestJob | null;
  recentUploadJobs: IngestJob[];
};


function numericValue(value: string): number | null {
  if (!value.trim()) {
    return null;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
}


export function DocumentUploadPanel(props: DocumentUploadPanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parseMethod, setParseMethod] = useState("auto");
  const [page, setPage] = useState("");
  const [startPage, setStartPage] = useState("");
  const [endPage, setEndPage] = useState("");
  const [reset, setReset] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function formatTimestamp(value: string) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  }

  function formatDuration(durationMs?: number | null) {
    if (durationMs == null) {
      return "n/a";
    }
    if (durationMs < 1000) {
      return `${durationMs} ms`;
    }
    return `${(durationMs / 1000).toFixed(1)} s`;
  }

  function formatRequestedPages(job: IngestJob) {
    if (job.requested_page != null) {
      return `page ${job.requested_page}`;
    }
    if (job.requested_start_page != null && job.requested_end_page != null) {
      return `pages ${job.requested_start_page}-${job.requested_end_page}`;
    }
    if (job.requested_start_page != null) {
      return `from page ${job.requested_start_page}`;
    }
    return "all pages";
  }

  async function handleRetryAction(jobId: string) {
    setMessage(null);
    setErrorMessage(null);

    try {
      await props.onRetryUpload(jobId);
      setMessage("Retry started and completed successfully.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Retry failed");
    }
  }

  async function handleCancelAction(jobId: string) {
    setMessage(null);
    setErrorMessage(null);

    try {
      await props.onCancelUpload(jobId);
      setMessage("Cancellation request sent.");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Cancel failed");
    }
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!props.selectedKnowledgeBase) {
      setErrorMessage("Select a knowledge base before uploading.");
      return;
    }
    if (!selectedFile) {
      setErrorMessage("Choose a file before uploading.");
      return;
    }

    setMessage(null);
    setErrorMessage(null);

    try {
      await props.onUpload({
        file: selectedFile,
        knowledge_base: props.selectedKnowledgeBase,
        parse_method: parseMethod || null,
        reset,
        page: numericValue(page),
        start_page: numericValue(startPage),
        end_page: numericValue(endPage),
      });

      setMessage(`Uploaded ${selectedFile.name} into ${props.selectedKnowledgeBase}.`);
      setSelectedFile(null);
      setPage("");
      setStartPage("");
      setEndPage("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Upload failed");
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.9rem" }}>
      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span style={{ fontWeight: 600 }}>File</span>
        <input
          accept=".pdf,.md,.markdown,.txt,.doc,.docx,.ppt,.pptx,.xls,.xlsx"
          onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          ref={fileInputRef}
          style={inputStyle}
          type="file"
        />
        {selectedFile ? <span style={{ color: "#52606d", fontSize: "0.92rem" }}>Selected: {selectedFile.name}</span> : null}
      </label>

      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span style={{ fontWeight: 600 }}>Parse method</span>
        <select onChange={(event) => setParseMethod(event.target.value)} style={inputStyle} value={parseMethod}>
          <option value="auto">auto</option>
          <option value="ocr">ocr</option>
          <option value="txt">txt</option>
        </select>
      </label>

      <div style={{ display: "grid", gap: "0.75rem", gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span style={{ fontWeight: 600 }}>Page</span>
          <input onChange={(event) => setPage(event.target.value)} style={inputStyle} value={page} />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span style={{ fontWeight: 600 }}>Start page</span>
          <input onChange={(event) => setStartPage(event.target.value)} style={inputStyle} value={startPage} />
        </label>
        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span style={{ fontWeight: 600 }}>End page</span>
          <input onChange={(event) => setEndPage(event.target.value)} style={inputStyle} value={endPage} />
        </label>
      </div>

      <label style={{ alignItems: "center", display: "flex", gap: "0.5rem" }}>
        <input checked={reset} onChange={(event) => setReset(event.target.checked)} type="checkbox" />
        <span>Reset KB before ingest</span>
      </label>

      <button disabled={props.isUploading} style={primaryButtonStyle} type="submit">
        {props.isUploading ? "Processing Upload..." : "Upload Document"}
      </button>

      {props.currentUploadJob ? (
        <div style={jobPanelStyle}>
          <div style={{ alignItems: "center", display: "flex", justifyContent: "space-between" }}>
            <strong>Ingest job</strong>
            <span>{props.currentUploadJob.progress}%</span>
          </div>
          <div style={jobBarTrackStyle}>
            <div style={{ ...jobBarFillStyle, width: `${props.currentUploadJob.progress}%` }} />
          </div>
          <div style={{ color: "#52606d", fontSize: "0.92rem" }}>
            {props.currentUploadJob.file_name} in {props.currentUploadJob.knowledge_base}: {props.currentUploadJob.message}
          </div>
          <div style={{ color: "#52606d", fontSize: "0.88rem" }}>
            Parser {props.currentUploadJob.parser_backend} / {props.currentUploadJob.parse_method ?? "auto"} | {formatRequestedPages(props.currentUploadJob)} | duration {formatDuration(props.currentUploadJob.duration_ms)}
          </div>
          <div style={{ display: "flex", gap: "0.6rem" }}>
            <button
              disabled={!props.currentUploadJob.can_cancel}
              onClick={() => void handleCancelAction(props.currentUploadJob!.job_id)}
              style={secondaryButtonStyle}
              type="button"
            >
              Cancel Job
            </button>
            <button
              disabled={!props.currentUploadJob.can_retry || props.isUploading}
              onClick={() => void handleRetryAction(props.currentUploadJob!.job_id)}
              style={secondaryButtonStyle}
              type="button"
            >
              Retry Job
            </button>
          </div>
        </div>
      ) : null}

      {props.recentUploadJobs.length > 0 ? (
        <div style={historyPanelStyle}>
          <h3 style={{ margin: 0 }}>Recent Ingest Jobs</h3>
          <div style={{ display: "grid", gap: "0.75rem" }}>
            {props.recentUploadJobs.map((job) => (
              <div key={job.job_id} style={historyItemStyle}>
                <div style={{ alignItems: "start", display: "flex", justifyContent: "space-between", gap: "1rem" }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{job.file_name}</div>
                    <div style={{ color: "#55616c", fontSize: "0.92rem", marginTop: "0.2rem" }}>
                      {job.knowledge_base} | {job.status} | updated {formatTimestamp(job.updated_at)}
                    </div>
                    <div style={{ color: "#55616c", fontSize: "0.88rem", marginTop: "0.25rem" }}>
                      {job.parser_backend}/{job.parse_method ?? "auto"} | {formatRequestedPages(job)} | duration {formatDuration(job.duration_ms)}
                    </div>
                    <div style={{ color: "#52606d", fontSize: "0.92rem", marginTop: "0.35rem" }}>{job.message}</div>
                    {job.error ? <div style={{ color: "#9f1f1f", fontSize: "0.92rem", marginTop: "0.35rem" }}>{job.error}</div> : null}
                    {job.retry_of ? <div style={{ color: "#52606d", fontSize: "0.86rem", marginTop: "0.25rem" }}>Retry of {job.retry_of}</div> : null}
                  </div>
                  <div style={{ display: "grid", gap: "0.5rem", minWidth: "126px" }}>
                    <div style={statusPillStyle}>{job.progress}%</div>
                    <button
                      disabled={!job.can_cancel}
                      onClick={() => void handleCancelAction(job.job_id)}
                      style={secondaryButtonStyle}
                      type="button"
                    >
                      Cancel
                    </button>
                    <button
                      disabled={!job.can_retry || props.isUploading}
                      onClick={() => void handleRetryAction(job.job_id)}
                      style={secondaryButtonStyle}
                      type="button"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {message ? <div style={{ color: "#125c2e" }}>{message}</div> : null}
      {errorMessage ? <div style={{ color: "#9f1f1f" }}>{errorMessage}</div> : null}
    </form>
  );
}


const inputStyle = {
  background: "#ffffff",
  border: "1px solid #cad7df",
  borderRadius: "10px",
  padding: "0.75rem 0.9rem",
};


const primaryButtonStyle = {
  background: "#133b5c",
  border: "none",
  borderRadius: "999px",
  color: "#ffffff",
  cursor: "pointer",
  fontWeight: 700,
  padding: "0.8rem 1rem",
};


const jobPanelStyle = {
  background: "#eef5f8",
  border: "1px solid #cad7df",
  borderRadius: "12px",
  display: "grid",
  gap: "0.6rem",
  padding: "0.85rem 0.95rem",
};


const jobBarTrackStyle = {
  background: "#d7e0e7",
  borderRadius: "999px",
  height: "10px",
  overflow: "hidden",
};


const jobBarFillStyle = {
  background: "#133b5c",
  height: "100%",
  transition: "width 180ms ease",
};


const historyPanelStyle = {
  borderTop: "1px solid #d7e0e7",
  display: "grid",
  gap: "0.85rem",
  paddingTop: "0.25rem",
};


const historyItemStyle = {
  background: "#fbfdfe",
  border: "1px solid #d7e0e7",
  borderRadius: "12px",
  padding: "0.85rem 0.95rem",
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