import os
import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Fetch API key from environment variables
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


def fetch_google_places(query: str, location_bias: str = None) -> List[Dict[str, Any]]:
    """
    Fetches real places from the Google Places API (Text Search endpoint).
    Logs request details and returns a normalized list of top place records.
    """
    if not GOOGLE_PLACES_API_KEY:
        logger.error("[Google Places] GOOGLE_PLACES_API_KEY is missing from environment variables.")
        return []

    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "en"
    }

    # Optional coordinate bias (e.g., '42.0683,19.5126' for Shkodër)
    if location_bias:
        params["location"] = location_bias
        params["radius"] = 10000  # 10 km radius around location

    logger.info(f"[Google Places Request] Executing search for Query: '{query}'")

    try:
        response = requests.get(TEXT_SEARCH_URL, params=params, timeout=5)
        data = response.json()

        status = data.get("status")
        logger.info(f"[Google Places API Response] Status: {status}")

        if status != "OK":
            logger.warning(
                f"[Google Places Warning] Non-OK status: {status}. "
                f"Error Message: {data.get('error_message', 'No error message provided.')}"
            )
            return []

        raw_results = data.get("results", [])
        logger.info(f"[Google Places Count] Found {len(raw_results)} raw place results.")

        # Extract top 5 structured results
        places = []
        for item in raw_results[:5]:
            places.append({
                "name": item.get("name"),
                "address": item.get("formatted_address"),
                "rating": item.get("rating", "N/A"),
                "user_ratings_total": item.get("user_ratings_total", 0),
                "place_id": item.get("place_id")
            })

        return places

    except Exception as e:
        logger.error(f"[Google Places Exception] Call failed: {e}")
        return []