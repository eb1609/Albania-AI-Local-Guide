# backend/agents/planner_agent.py
from openai import OpenAI
from langfuse.decorators import observe, langfuse_context

from ..services.config import ALBANIA_COORDS
from ..services.routing import get_osrm_distance_matrix, solve_tsp_nearest_neighbor
from ..services.cache import (
    get_exact_cache, set_exact_cache,
    get_semantic_cache, set_semantic_cache
)
from ..services.tracer import trace_step
from .intent_agent import extract_locations

client = OpenAI()

@observe(name="generate_shpresa_itinerary")
def run_planner_pipeline(user_query: str) -> str:
    # Set trace metadata
    langfuse_context.update_current_trace(
        name="itinerary_generation",
        user_id="anonymous_user",
        tags=["production", "routing-v1"]
    )

    # 1. Cache Check Span
    with langfuse_context.span("cache_check"):
        exact_hit = get_exact_cache(user_query)
        if exact_hit:
            langfuse_context.update_current_trace(metadata={"cache_status": "hit_exact"})
            return f"[Cache Hit - Exact]\n{exact_hit}"

        semantic_hit = get_semantic_cache(user_query)
        if semantic_hit:
            langfuse_context.update_current_trace(metadata={"cache_status": "hit_semantic"})
            return f"[Cache Hit - Semantic]\n{semantic_hit}"

    langfuse_context.update_current_trace(metadata={"cache_status": "miss"})

    # 2. Intent Extraction Span
    with langfuse_context.span("intent_extraction"):
        locations = extract_locations(user_query)
        valid_locations = [loc for loc in locations if loc in ALBANIA_COORDS]
        
        if not valid_locations:
            return "No recognized Albanian locations found in your request."

    # 3. OSRM Distance Matrix & Pathfinding Span
    with langfuse_context.span("pathfinding_osrm_tsp"):
        coords = [ALBANIA_COORDS[loc] for loc in valid_locations]
        matrix = get_osrm_distance_matrix(coords)
        route_order = solve_tsp_nearest_neighbor(matrix)
        optimized_locations = [valid_locations[i] for i in route_order]

    # 4. Final LLM Synthesis Span
    with langfuse_context.span("llm_narrative_synthesis"):
        prompt = (
            f"User request: {user_query}. "
            f"Build an itinerary strictly following this optimal path: {' -> '.join(optimized_locations)}"
        )
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        response_text = res.choices[0].message.content

    # 5. Populate Cache
    with langfuse_context.span("cache_write"):
        set_exact_cache(user_query, response_text)
        set_semantic_cache(user_query, response_text)

    return response_text