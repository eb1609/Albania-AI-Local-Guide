import os
import json
from groq import Groq

def extract_locations_and_intent(user_query: str) -> dict:
    """Extracts locations and identifies if the user is just saying hello."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"is_greeting": False, "locations": []}

    client = Groq(api_key=groq_api_key)

    prompt = (
        f"Analyze this user query: '{user_query}'.\n"
        "1. Is it a general greeting or small talk (e.g. 'hi', 'hello', 'hey', 'who are you') without specific travel planning intent?\n"
        "2. Extract any mentioned Albanian cities, towns, or regions as lowercase unaccented strings (e.g. 'tirana', 'shkoder').\n\n"
        "Return STRICTLY JSON format:\n"
        "{\"is_greeting\": true/false, \"locations\": [\"city1\"]}"
    )

    try:
        # Using full model identifier openai/gpt-oss-120b
        res = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(res.choices[0].message.content)
        return {
            "is_greeting": bool(data.get("is_greeting", False)),
            "locations": [str(loc).strip().lower() for loc in data.get("locations", [])]
        }
    except Exception as e:
        print(f"Intent extraction error: {e}")
        return {"is_greeting": False, "locations": []}