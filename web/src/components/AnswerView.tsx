import "katex/dist/katex.min.css";

import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkMath from "remark-math";

import type { Citation } from "../types";


type AnswerViewProps = {
  answer: string;
  citations: Citation[];
};


export function AnswerView(props: AnswerViewProps) {
  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      <div
        style={{
          background: "#f7fafc",
          border: "1px solid #d7e0e7",
          borderRadius: "16px",
          lineHeight: 1.6,
          padding: "1rem",
        }}
      >
        <ReactMarkdown rehypePlugins={[rehypeKatex]} remarkPlugins={[remarkMath]}>{props.answer}</ReactMarkdown>
      </div>

      <div>
        <h4 style={{ marginBottom: "0.75rem" }}>Citations</h4>
        {props.citations.length === 0 ? (
          <div style={{ color: "#52606d" }}>No citations returned for this answer.</div>
        ) : (
          <ul style={{ display: "grid", gap: "0.75rem", listStyle: "none", margin: 0, padding: 0 }}>
            {props.citations.map((citation, index) => (
              <li
                key={`${citation.kb}-${citation.document}-${index}`}
                style={{
                  background: "#fffaf1",
                  border: "1px solid #ead8ab",
                  borderRadius: "14px",
                  padding: "0.85rem 0.95rem",
                }}
              >
                <div style={{ fontWeight: 700 }}>
                  {citation.document}
                  {citation.page ? `, page ${citation.page}` : ""}
                </div>
                <div style={{ color: "#55616c", fontSize: "0.92rem", marginTop: "0.15rem" }}>
                  KB: {citation.kb}
                  {citation.chunk_id ? ` | chunk ${citation.chunk_id}` : ""}
                </div>
                <div style={{ marginTop: "0.55rem" }}>{citation.snippet}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}