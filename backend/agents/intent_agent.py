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
        f"Extract all mentioned Albanian cities or places from this text: '{user_query}'. "
        "Return strictly a JSON array of strings, e.g. [\"Tirana\", \"Saranda\"]."
    )

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = res.choices[0].message.content
        data = json.loads(content)
        # Handle cases where model wraps in a dict or returns raw list
        if isinstance(data, list):
            return data
        return data.get("locations", data.get("places", []))
    except Exception:
        return []