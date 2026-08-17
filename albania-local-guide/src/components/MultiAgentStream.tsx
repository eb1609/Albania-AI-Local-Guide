import React, { useState, useEffect } from 'react';

interface MultiAgentStreamProps {
  query: string;
}

export const MultiAgentStream: React.FC<MultiAgentStreamProps> = ({ query }) => {
  const [messages, setMessages] = useState<string[]>([]);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);

  useEffect(() => {
    if (!query) return;

    setIsStreaming(true);
    setMessages([]);

    const url = `/api/stream?msg=${encodeURIComponent(query)}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      if (event.data === '[DONE]') {
        eventSource.close();
        setIsStreaming(false);
        return;
      }

      try {
        const data = JSON.parse(event.data);
        const textChunk = data.token || data.message || event.data;
        setMessages((prev) => [...prev, textChunk]);
      } catch {
        setMessages((prev) => [...prev, event.data]);
      }
    };

    eventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      eventSource.close();
      setIsStreaming(false);
    };

    return () => {
      eventSource.close();
    };
  }, [query]);

  return (
    <div className="agent-stream-panel">
      {isStreaming && <div className="spinner">Agents responding...</div>}
      {messages.map((msg, idx) => (
        <div key={idx} className="stream-chunk">
          {msg}
        </div>
      ))}
    </div>
  );
};