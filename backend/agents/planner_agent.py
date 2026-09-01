# backend/agents/planner_agent.py
import os
from contextlib import nullcontext
from groq import Groq

# Safe Langfuse fallback
try:
    from langfuse.decorators import observe, langfuse_context  # type: ignore
except (ImportError, ModuleNotFoundError):
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    class DummyLangfuseContext:
        def update_current_trace(self, *args, **kwargs):
            pass
        def span(self, *args, **kwargs):
            return nullcontext()

    langfuse_context = DummyLangfuseContext()

from services.config import ALBANIA_COORDS
from services.routing import get_osrm_distance_matrix, solve_tsp_nearest_neighbor
from services.cache import (
    get_exact_cache, set_exact_cache,
    get_semantic_cache, set_semantic_cache
)
from agents.intent_agent import extract_locations_and_intent


@observe(name="generate_shpresa_itinerary")
def run_planner_pipeline(user_query: str) -> str:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing from environment variables.")
    
    client = Groq(api_key=groq_api_key)

    # 1. Intent & Location Extraction Span
    with langfuse_context.span("intent_extraction"):
        intent_data = extract_locations_and_intent(user_query)
        is_greeting = intent_data.get("is_greeting", False)
        locations = intent_data.get("locations", [])

        # Normalize ALBANIA_COORDS keys for case-insensitive lookup
        coords_normalized = {k.lower(): v for k, v in ALBANIA_COORDS.items()}
        valid_locations = [loc for loc in locations if loc in coords_normalized]

    # 2. Greeting / Fallback Direct Response
    if is_greeting and not valid_locations:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are Shpresa, an AI travel assistant for Albania. Greet the user warmly and invite them to ask about destinations in Albania (like Tirana, Shkoder, Saranda, or Theth)."},
                {"role": "user", "content": user_query}
            ]
        )
        return res.choices[0].message.content

    if not valid_locations:
        return (
            "Përshëndetje! I couldn't spot any specific Albanian destinations in your message. "
            "Where would you like to go? (e.g., Tirana, Shkoder, Saranda, Vlora)"
        )

    # 3. Cache Check Span for Full Itineraries
    with langfuse_context.span("cache_check"):
        exact_hit = get_exact_cache(user_query)
        if exact_hit:
            return f"[Cache Hit - Exact]\n{exact_hit}"

    # 4. OSRM Distance Matrix & Pathfinding Span
    with langfuse_context.span("pathfinding_osrm_tsp"):
        coords = [coords_normalized[loc] for loc in valid_locations]
        matrix = get_osrm_distance_matrix(coords)
        route_order = solve_tsp_nearest_neighbor(matrix)
        optimized_locations = [valid_locations[i].capitalize() for i in route_order]

    # 5. Final LLM Itinerary Synthesis Span
    with langfuse_context.span("llm_narrative_synthesis"):
        prompt = (
            f"User request: {user_query}. "
            f"Build a personalized Albanian itinerary strictly following this optimal route: {' -> '.join(optimized_locations)}"
        )
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = res.choices[0].message.content

    # 6. Populate Cache
    with langfuse_context.span("cache_write"):
        set_exact_cache(user_query, response_text)

    return response_text