# 🇦🇱 Shpresa — AI Local Guide for Albania

An interactive, AI-powered local guide for Albania. Shpresa streams live travel recommendations and plots verified points of interest directly onto an interactive map.

🌐 **Live Demo:** [albania-ai-local-guide.vercel.app](https://albania-ai-local-guide.vercel.app)
🔧 **Backend:** [albania-ai-local-guide.onrender.com](https://albania-ai-local-guide.onrender.com)

[![Deployed with Vercel](https://img.shields.io/badge/Deployed%20with-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://albania-ai-local-guide.vercel.app)
[![Backend Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://albania-ai-local-guide.onrender.com)
[![Groq gpt-oss-120b](https://img.shields.io/badge/AI-Groq%20openai%2Fgpt--oss--120b-orange?style=for-the-badge)](https://groq.com)

---

## ✨ Features

- **Real-Time Streaming** — Server-Sent Events (SSE) stream AI responses from Groq's `openai/gpt-oss-120b`, so recommendations appear token-by-token instead of after a long wait.
- **Live Interactive Map** — A Leaflet map automatically extracts coordinates from the AI's recommendations and drops pins as the response streams in.
- **Verified Google Places Data** — Recommendations are backed by the Google Places API (New) for accurate ratings, addresses, and coordinates, rather than the model inventing details.
- **Redis Response Caching** — LLM and API responses are cached in Redis to cut latency and reduce repeated API calls for common queries.
- **Langfuse Observability** — LLM calls are instrumented with Langfuse for tracing and monitoring.

---

## Architecture & Tech Stack

```
┌──────────────────────────┐   SSE Stream    ┌───────────────────────────┐
│      React + Vite        │ ───────────────▶ │       FastAPI Backend     │
│   Tailwind + Leaflet     │                  │     (Python — Render)     │
│    (Vercel Hosting)      │ ◀─────────────── │                           │
└──────────────────────────┘   Place pins &   └─────────────┬─────────────┘
                                map data                     │
                                                    ┌─────────┴─────────┐
                                                    ▼                   ▼
                                        ┌───────────────────┐  ┌───────────────────┐
                                        │   Redis Cache      │  │  Langfuse Tracing  │
                                        │ (LLM/API responses)│  │  (observability)   │
                                        └─────────┬───────────┘  └───────────────────┘
                                                    ▼
                                        ┌───────────────────────────┐
                                        │      Groq LLM Engine       │
                                        │    (openai/gpt-oss-120b)   │
                                        └─────────────┬─────────────┘
                                                        │
                                                        ▼
                                        ┌───────────────────────────┐
                                        │  Google Places API (New)   │
                                        │  ratings · addresses ·     │
                                        │  coordinates                │
                                        └───────────────────────────┘
```

OpenAI's SDK is also used, for text embeddings.

### Stack Breakdown

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Leaflet, Tailwind CSS — hosted on Vercel |
| Backend | Python, FastAPI, Server-Sent Events (SSE) — hosted on Render |
| AI | Groq API (`openai/gpt-oss-120b`); OpenAI SDK for embeddings |
| Caching | Redis — caches LLM/API responses |
| Observability | Langfuse — LLM call tracing |
| Geospatial data | Google Places API (New) |

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
