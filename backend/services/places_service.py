# backend/services/places_service.py
import os
import logging
import requests
from typing import List, Dict, Any

logger = logging.getLogger(__name__)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def fetch_place_details(place_id: str) -> Dict[str, Any]:
    """Fetches review snippets and editorial summaries for a specific place_id."""
    if not GOOGLE_PLACES_API_KEY or not place_id:
        return {}

    params = {
        "place_id": place_id,
        "fields": "reviews,editorial_summary,price_level",
        "key": GOOGLE_PLACES_API_KEY,
        "language": "en"
    }

    try:
        res = requests.get(DETAILS_URL, params=params, timeout=3)
        data = res.json()
        result = data.get("result", {})

        # Extract top 3 review text snippets
        raw_reviews = result.get("reviews", [])
        review_texts = [r.get("text", "") for r in raw_reviews if r.get("text")][:3]

        # Extract Google's official editorial summary if available
        editorial = result.get("editorial_summary", {}).get("overview", "")

        return {
            "editorial_summary": editorial,
            "reviews_snippets": review_texts,
            "price_level": result.get("price_level", None)
        }
    except Exception as e:
        logger.warning(f"[Google Place Details Exception] Failed for place_id {place_id}: {e}")
        return {}

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
        # Fetch detailed review data for top 5 places to keep response times fast
        for item in raw_results[:5]:
            loc = item.get("geometry", {}).get("location", {})
            types = item.get("types", [])
            category = types[0] if types else "attraction"
            place_id = item.get("place_id")

            # Fetch extra review context per place
            details = fetch_place_details(place_id) if place_id else {}

            places.append({
                "place_id": place_id,
                "name": item.get("name"),
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "address": item.get("formatted_address"),
                "rating": item.get("rating", "N/A"),
                "user_ratings_total": item.get("user_ratings_total", 0),
                "category": category,
                "editorial_summary": details.get("editorial_summary", ""),
                "reviews_snippets": details.get("reviews_snippets", []),
                "price_level": details.get("price_level")
            })
        return places
    except Exception as e:
        logger.error(f"[Google Places Exception] {e}")
        return []