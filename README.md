# 🇦🇱 Shpresa — AI Local Guide for Albania

An interactive, AI-powered local guide for Albania. Shpresa streams live travel recommendations and plots verified points of interest directly onto an interactive map.

🌐 **Live Demo:** [albania-ai-local-guide.vercel.app](https://albania-ai-local-guide.vercel.app)
🔧 **Backend:** [albania-ai-local-guide.onrender.com](https://albania-ai-local-guide.onrender.com)

[![Deployed with Vercel](https://img.shields.io/badge/Deployed%20with-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://albania-ai-local-guide.vercel.app)
[![Backend Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://albania-ai-local-guide.onrender.com)
[![Groq Llama 3.3](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange?style=for-the-badge)](https://groq.com)

---

## ✨ Features

- ⚡ **Real-Time Streaming** — Server-Sent Events (SSE) stream AI responses from Groq's `llama-3.3-70b-versatile`, so recommendations appear token-by-token instead of after a long wait.
- 🗺️ **Live Interactive Map** — A Leaflet map automatically extracts coordinates from the AI's recommendations and drops pins as the response streams in.
- 📍 **Verified Google Places Data** — Recommendations are backed by the Google Places API (New) for accurate ratings, addresses, and coordinates, rather than the model inventing details.
- ⚡ **Redis Response Caching** — LLM and API responses are cached in Redis to cut latency and reduce repeated API calls for common queries.
- 🛡️ **Langfuse Observability** — LLM calls are instrumented with Langfuse for tracing and monitoring.

---

## 🏗️ Architecture & Tech Stack

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
                                        │  (llama-3.3-70b-versatile) │
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
| AI | Groq API (`llama-3.3-70b-versatile`); OpenAI SDK for embeddings |
| Caching | Redis — caches LLM/API responses |
| Observability | Langfuse — LLM call tracing |
| Geospatial data | Google Places API (New) |

---

## 🛠️ Local Development Setup

> The exact folder layout and env var names below are inferred from the repo structure — check `backend/` and `albania-local-guide/` directly and adjust as needed.

### Prerequisites

- Python 3.10+
- Node.js 18+
- A running Redis instance (local or hosted)
- API keys: `GROQ_API_KEY`, `GOOGLE_PLACES_API_KEY`, `OPENAI_API_KEY` (embeddings), `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` (tracing)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/eb1609/Albania-AI-Local-Guide.git
cd Albania-AI-Local-Guide/backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file
echo "GROQ_API_KEY=your_groq_key" >> .env
echo "GOOGLE_PLACES_API_KEY=your_google_places_key" >> .env
echo "OPENAI_API_KEY=your_openai_key" >> .env
echo "REDIS_URL=your_redis_url" >> .env
echo "LANGFUSE_PUBLIC_KEY=your_langfuse_public_key" >> .env
echo "LANGFUSE_SECRET_KEY=your_langfuse_secret_key" >> .env

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd ../albania-local-guide

# Install dependencies
npm install

# Start the Vite dev server
npm run dev
```

Then open [http://localhost:5173](http://localhost:5173) in your browser.

### Docker

A `Dockerfile` is included at the repo root for containerized deployment — check it for the exact build/run commands the project uses in production.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
