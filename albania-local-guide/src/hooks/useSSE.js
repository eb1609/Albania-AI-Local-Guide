export default function startSSE(message, onChunk, onError, onComplete) {
  if (!message) return () => {};

  let baseUrl = import.meta.env.VITE_API_BASE_URL || "https://albania-ai-local-guide.onrender.com";

  baseUrl = baseUrl
    .trim()
    .replace(/[()"'`]/g, "")
    .replace(/\/$/, "");

  if (!baseUrl.startsWith("http")) {
    baseUrl = "https://albania-ai-local-guide.onrender.com";
  }

  const url = `${baseUrl}/api/stream?msg=${encodeURIComponent(message)}`;
  console.log("🔗 Connecting SSE to:", url);

  const es = new EventSource(url);
  let isClosed = false;

  const handleClose = (callComplete = true) => {
    if (isClosed) return;
    isClosed = true;
    es.close();
    if (callComplete && onComplete) onComplete();
  };

  // 1. Standard text and inline payload streaming
  es.onmessage = (event) => {
    if (event.data === "[DONE]") {
      handleClose(true);
      return;
    }

    try {
      const chunk = JSON.parse(event.data);
      onChunk(chunk);
    } catch (err) {
      onChunk({ token: event.data });
    }
  };

  // 2. Custom event listener for explicit 'places' events
  es.addEventListener("places", (event) => {
    try {
      const placesData = JSON.parse(event.data);
      onChunk({ places: placesData });
    } catch (err) {
      console.error("Failed to parse places SSE event:", err);
    }
  });

  // 3. Custom event listener for explicit 'agents' events
  es.addEventListener("agents", (event) => {
    try {
      const agentsData = JSON.parse(event.data);
      onChunk({ agents: agentsData });
    } catch (err) {
      console.error("Failed to parse agents SSE event:", err);
    }
  });

  // 4. Error Handling
  es.onerror = (err) => {
    console.error("❌ SSE connection error:", err);
    if (onError && !isClosed) onError(err);
    handleClose(true);
  };

  return () => handleClose(false);
}