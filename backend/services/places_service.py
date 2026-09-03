# backend/services/places_service.py
import os
import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

def fetch_google_places(query: str, location_bias: str = None) -> List[Dict[str, Any]]:
    if not GOOGLE_PLACES_API_KEY:
        logger.error("[Google Places] GOOGLE_PLACES_API_KEY missing.")
        return []

    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY,
        "language": "en"
    }
    if location_bias:
        params["location"] = location_bias
        params["radius"] = 10000

    try:
        response = requests.get(TEXT_SEARCH_URL, params=params, timeout=5)
        data = response.json()
        raw_results = data.get("results", [])

        places = []
        for item in raw_results[:8]:
            loc = item.get("geometry", {}).get("location", {})
            types = item.get("types", [])
            category = types[0] if types else "attraction"

            places.append({
                "place_id": item.get("place_id"),
                "name": item.get("name"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "address": item.get("formatted_address"),
                "rating": item.get("rating", "N/A"),
                "user_ratings_total": item.get("user_ratings_total", 0),
                "category": category
            })
        return places
    except Exception as e:
        logger.error(f"[Google Places Exception] {e}")
        return []