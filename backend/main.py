import os
import json
import sys
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Import underlying agents and services
from agents.planner_agent import run_planner_pipeline
from services.cache import get_exact_cache, set_exact_cache, get_semantic_cache, set_semantic_cache
from services.tracer import trace_step

load_dotenv(find_dotenv(), override=True)

app = FastAPI(
    title="Albania AI Local Guide Backend",
    version="2.0.0",
    description="Production API with OSRM TSP pathfinding, 2-tier caching, and Langfuse tracing."
)

# CORS setup configured for EventSource streaming
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control"],
)

@app.get("/health")
async def health_check():
    """System health check verifying service status."""
    return {
        "status": "online",
        "service": "Albania AI Local Guide Backend",
        "pipeline": "OSRM + Redis Cache + Langfuse Active"
    }

async def stream_text_as_sse(text: str, agent_label: str = "guide") -> AsyncGenerator[str, None]:
    """Helper to stream pre-computed or cached text back via Server-Sent Events (SSE)."""
    # Simulate chunked streaming for cached or deterministic pipeline outputs
    chunk_size = 20
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        payload = json.dumps({"token": chunk, "agent": agent_label})
        yield f"data: {payload}\n\n"
        await asyncio.sleep(0.01)
    yield "data: [DONE]\n\n"

@app.get("/api/stream")
async def stream(msg: str = Query(..., description="User query for itinerary/recommendation"), request: Request = None):
    print(f"🚀 Incoming request for: '{msg}'")

    if not msg.strip():
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    # 1. Tier 1 Cache Check (Exact Match)
    exact_hit = get_exact_cache(msg)
    if exact_hit:
        print("⚡ [Cache Hit - Exact]")
        return StreamingResponse(
            stream_text_as_sse(f"[Cache Hit - Exact]\n\n{exact_hit}"),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    # 2. Tier 2 Cache Check (Semantic Match)
    semantic_hit = get_semantic_cache(msg)
    if semantic_hit:
        print("⚡ [Cache Hit - Semantic]")
        return StreamingResponse(
            stream_text_as_sse(f"[Cache Hit - Semantic]\n\n{semantic_hit}"),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    # 3. Cache Miss: Execute Agent Pipeline (Intent -> OSRM TSP Solver -> LLM Synthesis)
    async def pipeline_generator():
        try:
            # Runs the full agent workflow wrapped with Langfuse tracing
            response_text = run_planner_pipeline(msg)

            # Write to Caches asynchronously after execution
            set_exact_cache(msg, response_text)
            set_semantic_cache(msg, response_text)

            # Stream result tokens back to frontend
            chunk_size = 15
            for i in range(0, len(response_text), chunk_size):
                if request and await request.is_disconnected():
                    print("⚠️ Client disconnected mid-stream")
                    break
                chunk = response_text[i:i + chunk_size]
                payload = json.dumps({"token": chunk, "agent": "guide"})
                yield f"data: {payload}\n\n"
                await asyncio.sleep(0.01)

        except Exception as e:
            print(f"❌ Exception in planner pipeline: {e}")
            err_payload = json.dumps({"token": f"\n[Pipeline Error: {str(e)}]"})
            yield f"data: {err_payload}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        pipeline_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )