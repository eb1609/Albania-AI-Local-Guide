export default function startSSE(message, onChunk, onError, onComplete) {
  if (!message) return () => {};

  // Read backend URL from environment, defaulting directly to your Render live backend
  const baseUrl = import.meta.env.VITE_API_BASE_URL || "https://albania-ai-local-guide.onrender.com";
  
  // Ensure no trailing slash on baseUrl
  const cleanBaseUrl = baseUrl.replace(/\/$/, "");
  const url = `${cleanBaseUrl}/api/stream?msg=${encodeURIComponent(message)}`;

  const es = new EventSource(url);

  es.onmessage = (event) => {
    if (event.data === "[DONE]") {
      es.close();
      if (onComplete) onComplete();
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
    if (onComplete) onComplete();
  };

  return () => es.close();
}