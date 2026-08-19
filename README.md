# Shpresa (Albania AI Local Guid

[![Deployed with Vercel](https://img.shields.io/badge/Deployed%20with-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://albania-ai-local-guide.vercel.app)
[![Backend Render](https://img.shields.io/badge/Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://albania-ai-local-guide.onrender.com)
[![Groq Llama 3.3](https://img.shields.io/badge/AI-Groq%20Llama%203.3-orange?style=for-the-badge)](https://groq.com)

> An interactive local guide for Albania powered by **Shpresa** (AI), streaming real-time travel advice and plotting verified Google Places directly onto an interactive map.

**Live Demo:** [https://albania-ai-local-guide.vercel.app](https://albania-ai-local-guide.vercel.app)

---

## Features

- **Real-Time Streaming:** Fast Server-Sent Events (SSE) AI streaming powered by Groq (Llama 3.3).
- **Live Interactive Map:** Automatically extracts coordinates for recommended locations and plots pins dynamically on Leaflet.
- **Verified Google Places:** Uses Google Places API (New) to return accurate ratings, addresses, and geographic coordinates.

---

## Architecture & Tech Stack

- **Frontend:** React, Vite, Leaflet Maps, Tailwind CSS (Hosted on Vercel)
- **Backend:** FastAPI, Server-Sent Events (SSE), Python (Hosted on Render)
- **AI & Data:** Groq API (`llama-3.3-70b-versatile`), Google Places API (New)
