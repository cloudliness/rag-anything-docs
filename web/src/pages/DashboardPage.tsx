type DashboardPageProps = {
  status: string;
  knowledgeBaseCount: number;
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
        <p style={{ margin: 0 }}>API status: {props.status}</p>
        <p style={{ margin: 0 }}>Knowledge bases discovered: {props.knowledgeBaseCount}</p>
      </div>
    </section>
  );
}