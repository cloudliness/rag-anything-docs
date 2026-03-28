import { useState } from "react";

import { AnswerView } from "../components/AnswerView";
import type { QueryPayload, QueryResponse } from "../types";


type QueryPageProps = {
  selectedKnowledgeBase: string | null;
  onQuery: (payload: QueryPayload) => Promise<QueryResponse>;
  isQuerying: boolean;
};


export function QueryPage(props: QueryPageProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<QueryResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!props.selectedKnowledgeBase) {
      setErrorMessage("Select a knowledge base before querying.");
      return;
    }

    setErrorMessage(null);

    try {
      const result = await props.onQuery({
        question,
        knowledge_bases: [props.selectedKnowledgeBase],
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
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.9rem" }}>
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
          <AnswerView answer={answer.answer} citations={answer.citations} />
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