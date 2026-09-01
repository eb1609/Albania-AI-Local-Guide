# backend/agents/intent_agent.py
import os
import json
from groq import Groq

def extract_locations(user_query: str) -> list[str]:
    """Extracts Albanian location names from a user query using Groq."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return []

    client = Groq(api_key=groq_api_key)

    prompt = (
        f"Extract all mentioned Albanian cities, towns, or regions from this text: '{user_query}'. "
        "Return JSON strictly with format: {\"locations\": [\"city1\", \"city2\"]}. "
        "Use plain unaccented English names in lowercase, e.g. \"shkoder\", \"tirana\", \"saranda\", \"vlora\"."
    )

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = res.choices[0].message.content
        data = json.loads(content)
        
        raw_locations = data.get("locations", [])
        # Normalize extracted strings to lower-case stripped values
        return [str(loc).strip().lower() for loc in raw_locations]
    except Exception as e:
        print(f"Intent extraction error: {e}")
        return []