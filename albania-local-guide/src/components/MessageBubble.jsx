import React from "react";

export default function MessageBubble({ role, text, agent }) {
  const isUser = role === "user";

  // Friendly display names for your AI agents
  const agentLabels = {
    persona: "Local Guide",
    itinerary: "Itinerary Planner",
    search: "Quick Search",
  };

  // Agent badge background colors
  const agentColors = {
    persona: "#e0f2fe", // soft blue
    itinerary: "#fef3c7", // soft amber/yellow
    search: "#dcfce7", // soft green
  };

  const agentTextColors = {
    persona: "#0369a1",
    itinerary: "#b45309",
    search: "#15803d",
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isUser ? "flex-end" : "flex-start",
        marginBottom: 12,
        width: "100%",
      }}
    >
      {/* Agent Badge Header */}
      {!isUser && agent && (
        <span
          style={{
            fontSize: "0.75rem",
            fontWeight: "600",
            marginBottom: 4,
            padding: "2px 8px",
            borderRadius: "12px",
            backgroundColor: agentColors[agent] || "#f3f4f6",
            color: agentTextColors[agent] || "#374151",
            textTransform: "capitalize",
          }}
        >
          {agentLabels[agent] || agent}
        </span>
      )}

      {/* Speech Bubble Container */}
      <div
        style={{
          maxWidth: "80%",
          padding: "12px 16px",
          borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
          backgroundColor: isUser ? "var(--albanian-red, #e41e20)" : "#f3f4f6",
          color: isUser ? "#ffffff" : "#1f2937",
          boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
          fontSize: "0.95rem",
          lineHeight: "1.5",
          wordBreak: "break-word",
          whiteSpace: "pre-wrap",
        }}
      >
        {text}
      </div>
    </div>
  );
}