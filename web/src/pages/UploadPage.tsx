import { DocumentUploadPanel } from "../components/DocumentUploadPanel";
import type { BrowserUploadPayload, CapabilityResponse, IngestJob } from "../types";


type UploadPageProps = {
  selectedKnowledgeBase: string | null;
  onUpload: (payload: BrowserUploadPayload) => Promise<void>;
  onRetryUpload: (jobId: string) => Promise<void>;
  onCancelUpload: (jobId: string) => Promise<void>;
  isUploading: boolean;
  capabilities: CapabilityResponse | null;
  currentUploadJob: IngestJob | null;
  recentUploadJobs: IngestJob[];
};


export function UploadPage(props: UploadPageProps) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>Ingest Document</h2>
      <p style={subtleTextStyle}>
        Browser upload is enabled. Choose a local file and the backend will ingest it into the selected knowledge base.
      </p>
      {props.capabilities ? (
        <div style={noticeStyle}>
          Current limit: {props.capabilities.max_upload_target_kbs} KB per upload. Browser upload: {props.capabilities.browser_upload_enabled ? "enabled" : "disabled"}. Multi-KB ingest status: {props.capabilities.multi_kb_upload_status}. Background ingest: {props.capabilities.background_ingest_status}.
        </div>
      ) : null}
      <DocumentUploadPanel
        currentUploadJob={props.currentUploadJob}
        isUploading={props.isUploading}
        onCancelUpload={props.onCancelUpload}
        onRetryUpload={props.onRetryUpload}
        onUpload={props.onUpload}
        recentUploadJobs={props.recentUploadJobs}
        selectedKnowledgeBase={props.selectedKnowledgeBase}
      />
    </section>
  );
}


const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7e0e7",
  borderRadius: "18px",
  padding: "1rem",
};


const subtleTextStyle = {
  color: "#52606d",
  marginTop: 0,
};


const noticeStyle = {
  background: "#f5f1e6",
  border: "1px solid #e4d4a0",
  borderRadius: "12px",
  color: "#5d4b12",
  marginBottom: "1rem",
  padding: "0.75rem 0.85rem",
};