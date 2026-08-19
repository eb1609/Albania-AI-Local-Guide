export default function startSSE(message, onChunk, onError, onComplete) {
  if (!message) return () => {};

  // 1. Get raw base URL from environment or fallback
  let baseUrl = import.meta.env.VITE_API_BASE_URL || "https://albania-ai-local-guide.onrender.com";

  // 2. Strip parentheses, quotes, spaces, and trailing slashes
  baseUrl = baseUrl
    .trim()
    .replace(/[()"'`]/g, "")
    .replace(/\/$/, "");

  // 3. Fall back to Render URL if the sanitized string is empty or relative
  if (!baseUrl.startsWith("http")) {
    baseUrl = "https://albania-ai-local-guide.onrender.com";
  }

  // 4. Construct clean absolute URL
  const url = `${baseUrl}/api/stream?msg=${encodeURIComponent(message)}`;

  console.log("🔗 Connecting SSE to:", url);

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
    console.error("❌ SSE connection error:", err);
    es.close();
    if (onError) onError(err);
    if (onComplete) onComplete();
  };

  return () => es.close();
}