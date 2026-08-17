export default function AgentBar({ agents }) {
  return (
    <div style={{ padding: 10, background: "var(--adriatic)", color: "white" }}>
      {agents.map((a) => (
        <span key={a} style={{ marginRight: 10 }}>
          {a}
        </span>
      ))}
    </div>
  )
}
