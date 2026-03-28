import { useState } from "react";

import type { UploadDocumentPayload } from "../types";


type DocumentUploadPanelProps = {
  selectedKnowledgeBase: string | null;
  onUpload: (payload: UploadDocumentPayload) => Promise<void>;
  isUploading: boolean;
};


function numericValue(value: string): number | null {
  if (!value.trim()) {
    return null;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? null : parsed;
}


export function DocumentUploadPanel(props: DocumentUploadPanelProps) {
  const [sourcePath, setSourcePath] = useState("");
  const [parseMethod, setParseMethod] = useState("auto");
  const [page, setPage] = useState("");
  const [startPage, setStartPage] = useState("");
  const [endPage, setEndPage] = useState("");
  const [reset, setReset] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!props.selectedKnowledgeBase) {
      setErrorMessage("Select a knowledge base before uploading.");
      return;
    }

    setMessage(null);
    setErrorMessage(null);

    try {
      await props.onUpload({
        source_path: sourcePath,
        knowledge_bases: [props.selectedKnowledgeBase],
        parse_method: parseMethod || null,
        reset,
        page: numericValue(page),
        start_page: numericValue(startPage),
        end_page: numericValue(endPage),
      });

      setMessage(`Uploaded into ${props.selectedKnowledgeBase}.`);
      setSourcePath("");
      setPage("");
      setStartPage("");
      setEndPage("");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Upload failed");
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.9rem" }}>
      <label style={{ display: "grid", gap: "0.35rem" }}>
        <span style={{ fontWeight: 600 }}>Source path</span>
        <input
          onChange={(event) => setSourcePath(event.target.value)}
          placeholder="/home/bc/Documents/math1.pdf"
          style={inputStyle}
          value={sourcePath}
        />
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
        {props.isUploading ? "Uploading..." : "Upload Document"}
      </button>

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