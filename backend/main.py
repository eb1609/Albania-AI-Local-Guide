import os
import json
import asyncio
import requests
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from dotenv import load_dotenv, find_dotenv

# 1. ALWAYS load environment variables FIRST
load_dotenv(find_dotenv(), override=True)

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

print(f"🔑 GROQ_API_KEY Loaded: {'YES' if GROQ_API_KEY else 'NO'}")
print(f"🔑 GOOGLE_PLACES_API_KEY Loaded: {'YES' if GOOGLE_PLACES_API_KEY else 'NO'}")

app = FastAPI(title="Albania AI Local Guide Backend")

# 2. CORS Middleware configured for cross-origin EventSource (Safari/Chrome fix)
# NOTE: When allow_origins is ["*"], allow_credentials MUST be False for browser SSE compliance
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Cache-Control"],
)

# Initialize Groq Client
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def fetch_real_places(query: str) -> str:
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY", GOOGLE_PLACES_API_KEY)
    print(f"🔍 DEBUG: Searching Google Places for query: '{query}'")
    
    if not api_key:
        print("❌ DEBUG: GOOGLE_PLACES_API_KEY is missing!")
        return ""
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"top restaurants in {query}" if "restaurant" not in query else query,
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=4)
        data = response.json()
        
        status = data.get("status")
        print(f"🔍 DEBUG: Google Places API Status: {status}")
        
        if status != "OK":
            print(f"❌ DEBUG: Google API Error Details: {data.get('error_message')}")
            return ""

        results = data.get("results", [])[:5]
        formatted_places = [
            f"- {p.get('name')} (Rating: {p.get('rating', 'N/A')}/5, Address: {p.get('formatted_address')})"
            for p in results
        ]
        
        output = "\n".join(formatted_places)
        print(f"✅ DEBUG: Fetched Places:\n{output}")
        return output

    except Exception as e:
        print("❌ DEBUG: Exception in fetch_real_places:", e)
        return ""

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Albania AI Local Guide Backend",
        "endpoints": ["/api/stream?msg=..."]
    }

@app.get("/api/stream")
async def stream(msg: str, request: Request):
    print(f"🚀 Incoming stream request for message: '{msg}'")

    if not client:
        err_payload = json.dumps({"token": "[Error: GROQ_API_KEY is not configured on backend server]"})
        return StreamingResponse(
            iter([f"data: {err_payload}\n\n", "data: [DONE]\n\n"]),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )

    real_data = fetch_real_places(msg)
    
    context_prompt = (
        "You are 'Shpresa', an expert Albanian AI Local Guide. "
        "Keep your tone warm, welcoming, and concise. "
    )
    
    if real_data:
        context_prompt += (
            f"\n\nCRITICAL INSTRUCTION: You MUST only recommend places from this verified real-world list:\n{real_data}\n"
            "Do NOT invent or hallucinate any business names not listed above."
        )

    async def event_generator():
        try:
            response = await client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": msg}
                ],
                stream=True,
                temperature=0.2,
                max_tokens=600
            )

            async for chunk in response:
                if await request.is_disconnected():
                    print("⚠️ Client disconnected early")
                    break
                content = chunk.choices[0].delta.content or ""
                if content:
                    payload = json.dumps({"token": content, "agent": "guide"})
                    yield f"data: {payload}\n\n"

        except Exception as e:
            print(f"❌ Exception during streaming: {e}")
            err_payload = json.dumps({"token": f"\n[Error: {str(e)}]"})
            yield f"data: {err_payload}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        }
    )