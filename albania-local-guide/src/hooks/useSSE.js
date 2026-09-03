// src/hooks/useSSE.js (or startSSE.js)

export default function startSSE(message, onChunk, onError, onComplete) {
  if (!message) return () => {};

  let baseUrl = import.meta.env.VITE_API_BASE_URL || "https://albania-ai-local-guide.onrender.com";
  baseUrl = baseUrl.trim().replace(/[()"'`]/g, "").replace(/\/$/, "");

  if (!baseUrl.startsWith("http")) {
    baseUrl = "https://albania-ai-local-guide.onrender.com";
  }

  const url = `${baseUrl}/api/stream?msg=${encodeURIComponent(message)}`;
  console.log("🔗 Connecting SSE to:", url);

  const es = new EventSource(url);

  // A. Listen for default message stream (LLM tokens)
  es.onmessage = (event) => {
    if (event.data === "[DONE]") {
      es.close();
      if (onComplete) onComplete();
      return;
    }

    try {
      const chunk = JSON.parse(event.data);
      onChunk(chunk); // Sends { token: "..." } to Chat.jsx
    } catch (err) {
      onChunk({ token: event.data });
    }
  };

  // B. SOLUTION 1: Listen explicitly for dedicated 'places' SSE event
  es.addEventListener("places", (event) => {
    try {
      const placesArray = JSON.parse(event.data);
      console.log("📍 Received dedicated places SSE event:", placesArray);
      onChunk({ places: placesArray }); // Sends { places: [...] } to Chat.jsx
    } catch (err) {
      console.error("Failed to parse SSE places payload:", err);
    }
  });

  es.onerror = (err) => {
    console.error("❌ SSE connection error:", err);
    es.close();
    if (onError) onError(err);
    if (onComplete) onComplete();
  };

  return () => es.close();
}