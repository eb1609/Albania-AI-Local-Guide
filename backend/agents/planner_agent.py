import logging
import os
from contextlib import nullcontext
from groq import Groq

# Configure logger for intent and fallback tracing
logger = logging.getLogger(__name__)

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

# System prompt for conversational fallback & greetings
GENERAL_GUIDE_SYSTEM_PROMPT = (
    "You are Shpresa, a warm and friendly AI travel assistant for Albania. "
    "If the user greets you or makes general conversation, respond naturally and warmly, "
    "then invite them to share which Albanian destinations, regions, or experiences "
    "they are interested in (e.g., Tirana, Shkoder, Saranda, Vlora, or Theth). "
    "If no specific destination is mentioned, offer helpful travel inspiration about Albania."
)

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

    # 2. Greeting / Ambiguous Input Fallback (Dynamic LLM Response)
    if not valid_locations:
        logger.info("[Shpresa Routing] No valid destinations detected. Triggering conversational LLM fallback.")
        try:
            res = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": GENERAL_GUIDE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=250
            )
            return res.choices[0].message.content
        except Exception as e:
            logger.error(f"[Fallback Error] Failed to complete fallback LLM call: {e}")
            # Resilient API failure fallback
            return (
                "Përshëndetje! I am Shpresa, your Albania travel guide. "
                "Which destinations in Albania would you like to explore? (e.g., Tirana, Saranda, Shkoder)"
            )

    logger.info(f"[Shpresa Routing] Valid destinations detected: {valid_locations}. Proceeding to pathfinding pipeline.")

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
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are Shpresa, an expert AI travel assistant for Albania. Synthesize engaging, well-structured travel itineraries."},
                {"role": "user", "content": prompt}
            ]
        )
        response_text = res.choices[0].message.content

    # 6. Populate Cache
    with langfuse_context.span("cache_write"):
        set_exact_cache(user_query, response_text)

    return response_text