import type { CapabilityResponse, HealthResponse } from "../types";


type DashboardPageProps = {
  health: HealthResponse | null;
  knowledgeBaseCount: number;
  capabilities: CapabilityResponse | null;
};


export function DashboardPage(props: DashboardPageProps) {
  return (
    <section
      style={{
        background: "linear-gradient(135deg, #14324a 0%, #245d78 100%)",
        borderRadius: "24px",
        color: "#ffffff",
        padding: "1.4rem 1.5rem",
      }}
    >
      <h2 style={{ marginTop: 0 }}>Dashboard</h2>
      <div style={{ display: "grid", gap: "0.35rem" }}>
        <p style={{ margin: 0 }}>API status: {props.health?.status ?? "loading"}</p>
        <p style={{ margin: 0 }}>API version: {props.health?.version ?? "unknown"}</p>
        <p style={{ margin: 0 }}>Knowledge bases discovered: {props.knowledgeBaseCount}</p>
        {props.capabilities ? (
          <>
            <p style={{ margin: 0 }}>Current query scope: up to {props.capabilities.max_query_kbs} KB</p>
            <p style={{ margin: 0 }}>Multi-KB query: {props.capabilities.multi_kb_query_status}</p>
          </>
        ) : null}
      </div>
    </section>
  );
}