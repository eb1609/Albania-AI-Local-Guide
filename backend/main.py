import os
import json
import asyncio
import requests
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import AsyncGroq
from dotenv import load_dotenv, find_dotenv
GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")

def fetch_real_places(query: str) -> str:
    print(f"🔍 DEBUG: Searching Google Places for query: '{query}'")
    print(f"🔍 DEBUG: API Key present: {bool(GOOGLE_PLACES_API_KEY)}")
    
    if not GOOGLE_PLACES_API_KEY:
        print("❌ DEBUG: GOOGLE_PLACES_API_KEY is missing!")
        return ""
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"top restaurants in {query}" if "restaurant" not in query else query,
        "key": GOOGLE_PLACES_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=4)
        data = response.json()
        
        # Check API status returned by Google
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
# Force load .env from the current or parent directory
load_dotenv(find_dotenv(), override=True)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Print on startup so you can see if it loaded in terminal
print(f"🔑 GROQ_API_KEY Loaded: {'YES' if GROQ_API_KEY else 'NO'}")
app = FastAPI(title="Albania AI Local Guide Backend")

# Allow CORS for local Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq Client
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Unified Model Choice
# CHANGE THIS IN main.py
MODEL_NAME = "llama-3.3-70b-versatile"  # Replaces "llama-3.3-70b-versatile"

# System Prompt combining Persona, Practical Knowledge, and Itinerary Planning
UNIFIED_GUIDE_SYSTEM = (
    "You are 'Shpresa', an expert Albanian AI Local Guide. Your goal is to help visitors "
    "plan unforgettable trips across Albania. "
    "Always maintain a warm, welcoming, and hospitable tone ('Përshëndetje!'). "
    "Provide practical, insider travel advice, highlighting local culture, food, historic sites, "
    "and natural scenery (like the Albanian Riviera, Gjirokastër, Berat, Tirana, and the Accursed Mountains). "
    "When asked for recommendations or itineraries, structure your answer clearly using Markdown bold text "
    "and clean bullet points. Keep your responses concise, engaging, and directly useful."
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Albania AI Local Guide Backend",
        "endpoints": ["/api/stream?msg=..."]
    }

@app.get("/api/stream")
async def stream(msg: str, request: Request):
    if not client:
        # Error handling...
        return

    # 1. Fetch real venue data dynamically based on user prompt
    real_data = fetch_real_places(msg)
    
    # 2. Build dynamic system prompt grounded in real Google data
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
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": context_prompt},
                    {"role": "user", "content": msg}
                ],
                stream=True,
                temperature=0.2, # Keep low to stick to provided facts
                max_tokens=600
            )

            async for chunk in response:
                if await request.is_disconnected():
                    break
                content = chunk.choices[0].delta.content or ""
                if content:
                    payload = json.dumps({"token": content, "agent": "guide"})
                    yield f"data: {payload}\n\n"

        except Exception as e:
            err_payload = json.dumps({"token": f"\n[Error: {str(e)}]"})
            yield f"data: {err_payload}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")