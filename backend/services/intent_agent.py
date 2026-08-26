import json
from openai import OpenAI

client = OpenAI()

def extract_locations(user_prompt: str) -> list[str]:
    system_prompt = "Extract requested locations in Albania. Return JSON: {\"locations\": [\"City1\", ...]}"
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    )
    return json.loads(res.choices[0].message.content).get("locations", [])