import { KnowledgeBasePicker } from "../components/KnowledgeBasePicker";
import type { DocumentRecord, KnowledgeBase } from "../types";


type KnowledgeBasesPageProps = {
  knowledgeBases: KnowledgeBase[];
  selectedKnowledgeBase: string | null;
  onSelectKnowledgeBase: (knowledgeBaseName: string) => void;
  documents: DocumentRecord[];
  isLoadingDocuments: boolean;
};


function displayFileName(fileName: string) {
  const normalized = fileName.replaceAll("\\", "/");
  return normalized.split("/").at(-1) ?? fileName;
}


export function KnowledgeBasesPage(props: KnowledgeBasesPageProps) {
  return (
    <section style={sectionStyle}>
      <div style={headerRowStyle}>
        <div>
          <h2 style={headingStyle}>Knowledge Bases</h2>
          <p style={subtleTextStyle}>Pick a KB, review its current documents, then ingest or query against it.</p>
        </div>
      </div>

      <div style={twoColumnStyle}>
        <div>
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