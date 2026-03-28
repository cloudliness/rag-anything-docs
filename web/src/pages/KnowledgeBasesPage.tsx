import { useState } from "react";

import { KnowledgeBasePicker } from "../components/KnowledgeBasePicker";
import type { CapabilityResponse, CreateKnowledgeBasePayload, DocumentRecord, KnowledgeBase } from "../types";


type KnowledgeBasesPageProps = {
  knowledgeBases: KnowledgeBase[];
  selectedKnowledgeBase: string | null;
  onSelectKnowledgeBase: (knowledgeBaseName: string) => void;
  documents: DocumentRecord[];
  isLoadingDocuments: boolean;
  capabilities: CapabilityResponse | null;
  onCreateKnowledgeBase: (payload: CreateKnowledgeBasePayload) => Promise<void>;
};


function displayFileName(fileName: string) {
  const normalized = fileName.replaceAll("\\", "/");
  return normalized.split("/").at(-1) ?? fileName;
}


export function KnowledgeBasesPage(props: KnowledgeBasesPageProps) {
  const [kbName, setKbName] = useState("");
  const [kbDescription, setKbDescription] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [createMessage, setCreateMessage] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  async function handleCreateKnowledgeBase(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateMessage(null);
    setCreateError(null);
    setIsCreating(true);

    try {
      await props.onCreateKnowledgeBase({
        name: kbName,
        description: kbDescription || null,
      });
      setCreateMessage(`Created knowledge base ${kbName}.`);
      setKbName("");
      setKbDescription("");
    } catch (error) {
      setCreateError(error instanceof Error ? error.message : "Failed to create knowledge base");
    } finally {
      setIsCreating(false);
    }
  }

  return (
    <section style={sectionStyle}>
      <div style={headerRowStyle}>
        <div>
          <h2 style={headingStyle}>Knowledge Bases</h2>
          <p style={subtleTextStyle}>Pick a KB, review its current documents, then ingest or query against it.</p>
        </div>
      </div>

      {props.capabilities ? (
        <div style={capabilityBannerStyle}>
          Phase 1 supports one active KB for upload and query. Multi-KB query is {props.capabilities.multi_kb_query_status} and will use query-then-merge when enabled.
        </div>
      ) : null}

      <div style={twoColumnStyle}>
        <div>
          <div style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>Create KB</h3>
            <form onSubmit={handleCreateKnowledgeBase} style={{ display: "grid", gap: "0.75rem" }}>
              <input
                onChange={(event) => setKbName(event.target.value)}
                placeholder="math-notes"
                required
                style={inputStyle}
                value={kbName}
              />
              <textarea
                onChange={(event) => setKbDescription(event.target.value)}
                placeholder="Optional description for the UI"
                rows={3}
                style={textareaStyle}
                value={kbDescription}
              />
              <button disabled={isCreating || !props.capabilities?.kb_creation_enabled || !kbName.trim()} style={buttonStyle} type="submit">
                {isCreating ? "Creating..." : "Create Knowledge Base"}
              </button>
            </form>
            {createMessage ? <div style={successTextStyle}>{createMessage}</div> : null}
            {createError ? <div style={errorTextStyle}>{createError}</div> : null}
          </div>

          <KnowledgeBasePicker
            knowledgeBases={props.knowledgeBases}
            onSelect={props.onSelectKnowledgeBase}
            selectedKnowledgeBase={props.selectedKnowledgeBase}
          />
        </div>

        <div style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>Documents</h3>
          {!props.selectedKnowledgeBase ? <div style={subtleTextStyle}>No knowledge base selected.</div> : null}
          {props.isLoadingDocuments ? <div style={subtleTextStyle}>Loading documents...</div> : null}
          {!props.isLoadingDocuments && props.selectedKnowledgeBase && props.documents.length === 0 ? (
            <div style={subtleTextStyle}>No documents indexed yet for {props.selectedKnowledgeBase}.</div>
          ) : null}

          <ul style={{ display: "grid", gap: "0.75rem", listStyle: "none", margin: 0, padding: 0 }}>
            {props.documents.map((document) => (
              <li key={`${document.knowledge_base}-${document.file_name}`} style={documentRowStyle}>
                <div style={{ fontWeight: 700 }}>{displayFileName(document.file_name)}</div>
                <div style={{ color: "#52606d", fontSize: "0.92rem", marginTop: "0.15rem" }}>
                  Status: {document.status}
                </div>
                {document.parsed_output_path ? (
                  <div style={{ color: "#52606d", fontSize: "0.86rem", marginTop: "0.2rem" }}>
                    Parsed output: {document.parsed_output_path}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}


const sectionStyle = {
  display: "grid",
  gap: "1rem",
};


const headerRowStyle = {
  alignItems: "start",
  display: "flex",
  justifyContent: "space-between",
};


const twoColumnStyle = {
  display: "grid",
  gap: "1rem",
  gridTemplateColumns: "minmax(240px, 300px) minmax(0, 1fr)",
};


const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7e0e7",
  borderRadius: "18px",
  padding: "1rem",
};


const documentRowStyle = {
  background: "#f7fafc",
  border: "1px solid #d7e0e7",
  borderRadius: "12px",
  padding: "0.85rem 0.95rem",
};


const headingStyle = {
  marginBottom: "0.25rem",
  marginTop: 0,
};


const subtleTextStyle = {
  color: "#52606d",
  margin: 0,
};


const capabilityBannerStyle = {
  background: "#eef5f8",
  border: "1px solid #cad7df",
  borderRadius: "14px",
  color: "#234257",
  padding: "0.85rem 1rem",
};


const inputStyle = {
  background: "#ffffff",
  border: "1px solid #cad7df",
  borderRadius: "10px",
  padding: "0.75rem 0.9rem",
};


const textareaStyle = {
  ...inputStyle,
  resize: "vertical" as const,
};


const buttonStyle = {
  background: "#133b5c",
  border: "none",
  borderRadius: "999px",
  color: "#ffffff",
  cursor: "pointer",
  fontWeight: 700,
  padding: "0.8rem 1rem",
};


const successTextStyle = {
  color: "#125c2e",
  marginTop: "0.75rem",
};


const errorTextStyle = {
  color: "#9f1f1f",
  marginTop: "0.75rem",
};