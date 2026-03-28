import type { CapabilityResponse, HealthResponse, IngestJob } from "../types";


type DashboardPageProps = {
  health: HealthResponse | null;
  knowledgeBaseCount: number;
  capabilities: CapabilityResponse | null;
  recentUploadJobs: IngestJob[];
};


export function DashboardPage(props: DashboardPageProps) {
  const activeJobs = props.recentUploadJobs.filter((job) => job.status === "queued" || job.status === "running").length;
  const completedJobs = props.recentUploadJobs.filter((job) => job.status === "completed").length;
  const failedJobs = props.recentUploadJobs.filter((job) => job.status === "failed").length;
  const recentDurationJobs = props.recentUploadJobs.filter((job) => typeof job.duration_ms === "number");
  const averageDurationMs = recentDurationJobs.length > 0
    ? Math.round(recentDurationJobs.reduce((total, job) => total + (job.duration_ms ?? 0), 0) / recentDurationJobs.length)
    : null;

  function formatDuration(durationMs: number | null) {
    if (durationMs == null) {
      return "n/a";
    }
    if (durationMs < 1000) {
      return `${durationMs} ms`;
    }
    return `${(durationMs / 1000).toFixed(1)} s`;
  }

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
      <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1fr)" }}>
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

        <div style={{ background: "rgba(255,255,255,0.12)", border: "1px solid rgba(255,255,255,0.16)", borderRadius: "18px", padding: "1rem" }}>
          <h3 style={{ marginTop: 0, marginBottom: "0.7rem" }}>Ingest Snapshot</h3>
          <div style={{ display: "grid", gap: "0.35rem" }}>
            <p style={{ margin: 0 }}>Active jobs: {activeJobs}</p>
            <p style={{ margin: 0 }}>Completed jobs: {completedJobs}</p>
            <p style={{ margin: 0 }}>Failed jobs: {failedJobs}</p>
            <p style={{ margin: 0 }}>Average duration: {formatDuration(averageDurationMs)}</p>
          </div>
          {props.recentUploadJobs.length > 0 ? (
            <div style={{ display: "grid", gap: "0.55rem", marginTop: "0.85rem" }}>
              {props.recentUploadJobs.slice(0, 3).map((job) => (
                <div key={job.job_id} style={{ background: "rgba(10, 26, 39, 0.22)", borderRadius: "12px", padding: "0.7rem 0.8rem" }}>
                  <div style={{ fontWeight: 700 }}>{job.file_name}</div>
                  <div style={{ fontSize: "0.9rem", opacity: 0.9 }}>{job.status} | {job.parser_backend}/{job.parse_method ?? "auto"}</div>
                  <div style={{ fontSize: "0.88rem", opacity: 0.84 }}>
                    {job.requested_page_count != null ? `${job.requested_page_count} page${job.requested_page_count === 1 ? "" : "s"}` : "all pages"} | {formatDuration(job.duration_ms ?? null)}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}