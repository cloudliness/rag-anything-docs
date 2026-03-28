import type { KnowledgeBase } from "../types";


type KnowledgeBasePickerProps = {
  knowledgeBases: KnowledgeBase[];
  selectedKnowledgeBase: string | null;
  onSelect: (knowledgeBaseName: string) => void;
};


export function KnowledgeBasePicker(props: KnowledgeBasePickerProps) {
  return (
    <div style={{ display: "grid", gap: "0.75rem" }}>
      {props.knowledgeBases.map((knowledgeBase) => {
        const isSelected = props.selectedKnowledgeBase === knowledgeBase.name;

        return (
          <button
            key={knowledgeBase.name}
            onClick={() => props.onSelect(knowledgeBase.name)}
            style={{
              background: isSelected ? "#133b5c" : "#f3f6f8",
              border: `1px solid ${isSelected ? "#133b5c" : "#d7e0e7"}`,
              borderRadius: "14px",
              color: isSelected ? "#ffffff" : "#173042",
              cursor: "pointer",
              padding: "0.9rem 1rem",
              textAlign: "left",
            }}
            type="button"
          >
            <div style={{ fontSize: "1rem", fontWeight: 700 }}>{knowledgeBase.name}</div>
            <div style={{ fontSize: "0.9rem", marginTop: "0.25rem", opacity: 0.85 }}>
              Documents: {knowledgeBase.document_count}
            </div>
          </button>
        );
      })}
    </div>
  );
}