import { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import startSSE from "../hooks/useSSE";

export default function Chat({ onAgentsUpdate, onPlacesUpdate }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const activeCleanupRef = useRef(null);

  const sendMessage = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    if (activeCleanupRef.current) {
      activeCleanupRef.current();
    }

    // Unique ID for this specific turn
    const turnId = Date.now();

    const userMsg = { id: `user-${turnId}`, role: "user", text: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);

    activeCleanupRef.current = startSSE(
      trimmed,
      // 1. On Chunk
      // Inside startSSE onChunk in Chat.jsx:
(chunk) => {
  const { token } = chunk;

  if (token) {
    setMessages((prev) => {
      const last = prev[prev.length - 1];
      if (last && last.role === "assistant") {
        return [
          ...prev.slice(0, -1),
          { ...last, text: last.text + token }
        ];
      }
      return [...prev, { role: "assistant", text: token }];
    });
  }
},
      // 2. On Error
      (err) => {
        console.error("Stream failed", err);
      },
      // 3. On Complete
      () => {
        setIsStreaming(false);
      }
    );
  };

  useEffect(() => {
    return () => {
      if (activeCleanupRef.current) {
        activeCleanupRef.current();
      }
    };
  }, []);

  return (
    <div style={{ padding: 20, height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {messages.map((m) => (
          <MessageBubble key={m.id || Math.random()} role={m.role} text={m.text} agent={m.agent} />
        ))}
      </div>

      <div style={{ display: "flex", gap: 10 }}>
        <input
          value={input}
          disabled={isStreaming}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !isStreaming && sendMessage()}
          placeholder={isStreaming ? "Thinking..." : "Ask your Albania local guide..."}
          style={{ flex: 1, padding: 10 }}
        />
        <button
          onClick={sendMessage}
          disabled={isStreaming}
          style={{
            background: isStreaming ? "#ccc" : "var(--albanian-red, #e41e20)",
            color: "white",
            padding: "10px 20px",
            cursor: isStreaming ? "not-allowed" : "pointer"
          }}
        >
          {isStreaming ? "Thinking..." : "Send"}
        </button>
      </div>
    </div>
  );
}