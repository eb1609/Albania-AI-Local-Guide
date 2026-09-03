import logging
import os
from contextlib import nullcontext
from groq import Groq

# Configure logger for intent, routing, and fallback tracing
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
from services.places_service import fetch_google_places
from agents.intent_agent import extract_locations_and_intent

# System prompt for conversational fallback & general greetings
GENERAL_GUIDE_SYSTEM_PROMPT = (
    "You are Shpresa, a warm and friendly AI travel assistant for Albania. "
    "If the user greets you or makes general conversation, respond naturally and warmly, "
    "then invite them to share which Albanian destinations, regions, or experiences "
    "they are interested in (e.g., Tirana, Shkoder, Saranda, Vlora, or Theth). "
    "If no specific destination is mentioned, offer helpful travel inspiration about Albania."
)

# Strict system prompt for place, restaurant, and hotel recommendations
PLACES_STRICT_FORMATTER_PROMPT = (
    "You are Shpresa, an expert AI travel guide for Albania.\n"
    "CRITICAL CONSTRAINTS FOR PLACES/RESTAURANTS/HOTELS:\n"
    "1. ONLY present the exact places provided in the 'VERIFIED_PLACES_DATA' block.\n"
    "2. Do NOT invent, supplement, add, or suggest any other restaurants, hotels, or attractions under any circumstances.\n"
    "3. Display each place's name, formatted address, and rating exactly as provided in the data.\n"
    "4. If 'VERIFIED_PLACES_DATA' is empty or contains no records, inform the user clearly that no verified places were found."
)

MODEL_NAME = "openai/gpt-oss-120b"


def is_place_seeking_query(user_query: str) -> bool:
    """Helper to detect whether the query is asking for restaurants, hotels, or local spots."""
    query_lower = user_query.lower()
    place_keywords = [
        "restaurant", "restaurants", "food", "eat", "cafe", "cafes",
        "hotel", "hotels", "stay", "accommodation", "bar", "bars",
        "place to eat", "where to eat", "attractions", "things to do"
    ]
    return any(keyword in query_lower for keyword in place_keywords)


@observe(name="generate_shpresa_itinerary")
def run_planner_pipeline(user_query: str) -> dict:
    """Executes the planner pipeline and returns both synthesized text and structured place objects."""
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

    # 2. Places API Grounding Branch (Restaurants, Hotels, Points of Interest)
    if is_place_seeking_query(user_query):
        with langfuse_context.span("google_places_grounding"):
            logger.info(f"[Shpresa Routing] Place-seeking query detected: '{user_query}'")
            
            # Fetch real places from Google Places API
            real_places = fetch_google_places(query=user_query)
            
            # Prevent LLM hallucination on 0 results
            if not real_places:
                logger.info(f"[Google Places] Zero results returned for query: '{user_query}'.")
                return {
                    "text": f"I couldn't find any verified places matching '{user_query}' in Albania. Try searching for a different city or category!",
                    "places": []
                }

            # Build grounded data string for LLM
            formatted_data = "\n".join([
                f"- Name: {p['name']} | Address: {p.get('address', '')} | Rating: {p.get('rating', 'N/A')} ({p.get('user_ratings_total', 0)} reviews)"
                for p in real_places
            ])

            logger.info(f"[Google Places] Grounding LLM response with {len(real_places)} real places.")

            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": PLACES_STRICT_FORMATTER_PROMPT},
                    {"role": "user", "content": f"User Query: {user_query}\n\nVERIFIED_PLACES_DATA:\n{formatted_data}"}
                ],
                temperature=0.1
            )
            
            # Return both text and structured ground-truth places
            return {
                "text": res.choices[0].message.content,
                "places": real_places
            }

    # 3. Conversational / Generic Greeting Fallback Branch
    if not valid_locations:
        logger.info("[Shpresa Routing] No valid destinations or place intents detected. Triggering conversational fallback.")
        try:
            res = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": GENERAL_GUIDE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=250
            )
            return {
                "text": res.choices[0].message.content,
                "places": []
            }
        except Exception as e:
            logger.error(f"[Fallback Error] Failed to execute conversational fallback call: {e}")
            return {
                "text": (
                    "Përshëndetje! I am Shpresa, your Albania travel guide. "
                    "Which destinations in Albania would you like to explore? (e.g., Tirana, Saranda, Shkoder)"
                ),
                "places": []
            }

    logger.info(f"[Shpresa Routing] Multi-destination route detected: {valid_locations}. Proceeding to pathfinding pipeline.")

    # 4. Cache Check Span for Full Itineraries
    with langfuse_context.span("cache_check"):
        exact_hit = get_exact_cache(user_query)
        if exact_hit:
            return {
                "text": f"[Cache Hit - Exact]\n{exact_hit}",
                "places": []
            }

    # 5. OSRM Distance Matrix & Pathfinding Span
    with langfuse_context.span("pathfinding_osrm_tsp"):
        coords = [coords_normalized[loc] for loc in valid_locations]
        matrix = get_osrm_distance_matrix(coords)
        route_order = solve_tsp_nearest_neighbor(matrix)
        optimized_locations = [valid_locations[i].capitalize() for i in route_order]

    # 6. Final LLM Itinerary Synthesis Span
    with langfuse_context.span("llm_narrative_synthesis"):
        prompt = (
            f"User request: {user_query}. "
            f"Build a personalized Albanian itinerary strictly following this optimal route: {' -> '.join(optimized_locations)}"
        )
        res = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are Shpresa, an expert AI travel assistant for Albania. Synthesize engaging, well-structured travel itineraries."},
                {"role": "user", "content": prompt}
            ]
        )
        response_text = res.choices[0].message.content

    # 7. Populate Cache
    with langfuse_context.span("cache_write"):
        set_exact_cache(user_query, response_text)

    return {
        "text": response_text,
        "places": []
    }