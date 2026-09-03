import os
import json
import sys
import asyncio
from typing import AsyncGenerator
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv

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

def normalize_places(places_data: list) -> list:
    """Normalizes raw Google Places objects into a clean, predictable shape for MapView."""
    normalized = []
    if not isinstance(places_data, list):
        return normalized

    for p in places_data:
        if not isinstance(p, dict):
            continue
            
        # Support flat keys (lat/lng, latitude/longitude) or nested Google geometry
        lat = p.get("lat") or p.get("latitude") or p.get("geometry", {}).get("location", {}).get("lat")
        lng = p.get("lng") or p.get("longitude") or p.get("geometry", {}).get("location", {}).get("lng")
        
        if lat is None or lng is None:
            continue

        try:
            normalized.append({
                "place_id": p.get("place_id") or p.get("id") or f"place-{len(normalized)}",
                "name": p.get("name") or p.get("title") or "Recommended Place",
                "lat": float(lat),
                "lng": float(lng),
                "address": p.get("address") or p.get("formatted_address") or "",
                "rating": p.get("rating", "N/A")
            })
        except (ValueError, TypeError):
            continue

    return normalized

@app.get("/health")
async def health_check():
    """System health check verifying service status."""
    return {
        "status": "online",
        "service": "Albania AI Local Guide Backend",
        "pipeline": "OSRM + Redis Cache + Langfuse Active"
    }

async def stream_text_as_sse(text: str, places: list = None, agent_label: str = "guide") -> AsyncGenerator[str, None]:
    """Helper to stream pre-computed or cached text back via Server-Sent Events (SSE)."""
    # 1. Emit places event first if present in cached hit
    if places:
        places_json = json.dumps(places)
        yield f"event: places\ndata: {places_json}\n\n"

    # 2. Simulate chunked text streaming
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
        cached_data = json.loads(exact_hit) if isinstance(exact_hit, str) and exact_hit.startswith("{") else {"text": exact_hit}
        return StreamingResponse(
            stream_text_as_sse(cached_data.get("text", exact_hit), places=cached_data.get("places")),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    # 2. Tier 2 Cache Check (Semantic Match)
    semantic_hit = get_semantic_cache(msg)
    if semantic_hit:
        print("⚡ [Cache Hit - Semantic]")
        cached_data = json.loads(semantic_hit) if isinstance(semantic_hit, str) and semantic_hit.startswith("{") else {"text": semantic_hit}
        return StreamingResponse(
            stream_text_as_sse(cached_data.get("text", semantic_hit), places=cached_data.get("places")),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        )

    # 3. Cache Miss: Execute Agent Pipeline
    async def pipeline_generator():
        try:
            # Execute pipeline
            result = run_planner_pipeline(msg)

            # Unpack response if dictionary (text + places), or string fallback
            if isinstance(result, dict):
                response_text = result.get("text", "")
                raw_places = result.get("places", [])
            else:
                response_text = str(result)
                raw_places = []

            # Normalize place objects
            normalized_places = normalize_places(raw_places)

            # --- DEDICATED SSE EVENT FOR PLACES ---
            if normalized_places:
                print(f"📍 Emitting {len(normalized_places)} normalized places to map")
                places_payload = json.dumps(normalized_places)
                yield f"event: places\ndata: {places_payload}\n\n"

            # Cache the structured execution output
            cache_payload = json.dumps({"text": response_text, "places": normalized_places})
            set_exact_cache(msg, cache_payload)
            set_semantic_cache(msg, cache_payload)

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