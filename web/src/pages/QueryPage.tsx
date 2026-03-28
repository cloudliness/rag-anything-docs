import { Suspense, lazy, useState } from "react";

import type { CapabilityResponse, KnowledgeBase, QueryPayload, QueryResponse } from "../types";


const AnswerView = lazy(async () => {
  const module = await import("../components/AnswerView");
  return { default: module.AnswerView };
});


type QueryPageProps = {
  knowledgeBases: KnowledgeBase[];
  onQuery: (payload: QueryPayload) => Promise<QueryResponse>;
  onSelectedKnowledgeBasesChange: (knowledgeBaseNames: string[]) => void;
  selectedKnowledgeBases: string[];
  isQuerying: boolean;
  capabilities: CapabilityResponse | null;
};


export function QueryPage(props: QueryPageProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const maxSelectableKnowledgeBases = props.capabilities?.max_query_kbs ?? 1;

  function toggleKnowledgeBase(knowledgeBaseName: string) {
    const isSelected = props.selectedKnowledgeBases.includes(knowledgeBaseName);

    if (isSelected) {
      props.onSelectedKnowledgeBasesChange(
        props.selectedKnowledgeBases.filter((selectedKnowledgeBase) => selectedKnowledgeBase !== knowledgeBaseName),
      );
      return;
    }

    if (props.selectedKnowledgeBases.length >= maxSelectableKnowledgeBases) {
      return;
    }

    props.onSelectedKnowledgeBasesChange([...props.selectedKnowledgeBases, knowledgeBaseName]);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (props.selectedKnowledgeBases.length === 0) {
      setErrorMessage("Select at least one knowledge base before querying.");
      return;
    }

    setErrorMessage(null);

    try {
      const result = await props.onQuery({
        question,
        knowledge_bases: props.selectedKnowledgeBases,
        query_mode: "hybrid",
        answer_mode: "detailed",
      });

      setAnswer(result);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Query failed");
    }
  }

  return (
    <section style={panelStyle}>
      <h2 style={{ marginTop: 0 }}>Query</h2>
      {props.capabilities ? (
        <div style={noticeStyle}>
          Current limit: {props.capabilities.max_query_kbs} KB per query. Multi-KB query status: {props.capabilities.multi_kb_query_status}.
        </div>
      ) : null}
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.9rem" }}>
        <div style={{ display: "grid", gap: "0.55rem" }}>
          <span style={{ fontWeight: 600 }}>Query scope</span>
          <div style={scopePanelStyle}>
            {props.knowledgeBases.map((knowledgeBase) => {
              const isSelected = props.selectedKnowledgeBases.includes(knowledgeBase.name);
              const disableCheckbox = !isSelected && props.selectedKnowledgeBases.length >= maxSelectableKnowledgeBases;

              return (
                <label key={knowledgeBase.name} style={scopeOptionStyle}>
                  <input
                    checked={isSelected}
                    disabled={disableCheckbox}
                    onChange={() => toggleKnowledgeBase(knowledgeBase.name)}
                    type="checkbox"
                  />
                  <span>{knowledgeBase.name}</span>
                </label>
              );
            })}
          </div>
          <span style={{ color: "#52606d", fontSize: "0.92rem" }}>
            Selected {props.selectedKnowledgeBases.length} of {maxSelectableKnowledgeBases} knowledge bases.
          </span>
        </div>

        <label style={{ display: "grid", gap: "0.35rem" }}>
          <span style={{ fontWeight: 600 }}>Question</span>
          <textarea
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Explain how one of the problems on this page works."
            rows={5}
            style={textareaStyle}
            value={question}
          />
        </label>

        <button disabled={props.isQuerying} style={primaryButtonStyle} type="submit">
          {props.isQuerying ? "Querying..." : "Run Query"}
        </button>
      </form>

      {errorMessage ? <div style={{ color: "#9f1f1f", marginTop: "0.9rem" }}>{errorMessage}</div> : null}
      {answer ? (
        <div style={{ marginTop: "1rem" }}>
          <Suspense fallback={<div style={{ color: "#52606d" }}>Loading answer renderer...</div>}>
            <AnswerView answer={answer.answer} citations={answer.citations} />
          </Suspense>
        </div>
      ) : null}
    </section>
  );
}


const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7e0e7",
  borderRadius: "18px",
  padding: "1rem",
};


const textareaStyle = {
  background: "#ffffff",
  border: "1px solid #cad7df",
  borderRadius: "12px",
  padding: "0.85rem 0.95rem",
  resize: "vertical" as const,
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


const noticeStyle = {
  background: "#eef5f8",
  border: "1px solid #cad7df",
  borderRadius: "12px",
  color: "#234257",
  marginBottom: "1rem",
  padding: "0.75rem 0.85rem",
};


const scopePanelStyle = {
  background: "#f7fafc",
  border: "1px solid #d7e0e7",
  borderRadius: "12px",
  display: "grid",
  gap: "0.65rem",
  padding: "0.85rem 0.95rem",
};


const scopeOptionStyle = {
  alignItems: "center",
  display: "flex",
  gap: "0.5rem",
};