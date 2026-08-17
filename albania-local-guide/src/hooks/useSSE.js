export default function startSSE(message, onChunk, onError, onComplete) {
  if (!message) return () => {};

  const url = `/api/stream?msg=${encodeURIComponent(message)}`;
  const es = new EventSource(url);

  es.onmessage = (event) => {
    if (event.data === "[DONE]") {
      es.close();
      if (onComplete) onComplete(); // <--- Notify Chat that streaming completed!
      return;
    }

    try {
      const chunk = JSON.parse(event.data);
      onChunk(chunk);
    } catch (err) {
      onChunk({ token: event.data });
    }
  };

  es.onerror = (err) => {
    console.error("SSE error:", err);
    es.close();
    if (onError) onError(err);
    if (onComplete) onComplete(); // <--- Clean up state even on error!
  };

  return () => es.close();
}