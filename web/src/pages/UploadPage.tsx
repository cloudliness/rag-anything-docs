import { DocumentUploadPanel } from "../components/DocumentUploadPanel";
import type { UploadDocumentPayload } from "../types";


type UploadPageProps = {
  selectedKnowledgeBase: string | null;
  onUpload: (payload: UploadDocumentPayload) => Promise<void>;
  isUploading: boolean;
};


export function UploadPage(props: UploadPageProps) {
  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>Ingest Document</h2>
      <p style={subtleTextStyle}>
        Upload is currently path-based for Phase 1. Point at a local file and the backend will ingest it into the selected KB.
      </p>
      <DocumentUploadPanel
        isUploading={props.isUploading}
        onUpload={props.onUpload}
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