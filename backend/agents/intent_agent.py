# backend/agents/intent_agent.py
import json
from openai import OpenAI

client = OpenAI()

def extract_locations(user_prompt: str) -> list[str]:
    system_prompt = """
    Extract all requested locations/cities in Albania from the user prompt.
    Return ONLY a JSON object with a key 'locations' containing an array of strings.
    Example: {"locations": ["Tirana", "Berat", "Sarandë"]}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    data = json.loads(response.choices[0].message.content)
    return data.get("locations", [])