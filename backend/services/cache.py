# backend/services/cache.py
import hashlib
import json
import redis
import numpy as np
import os
from groq import Groq

# 1. Initialize Redis connection safely (supports REDIS_URL from Render/Upstash)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=False)
except Exception:
    redis_client = None

EXACT_CACHE_TTL = 86400  # 24 hours in seconds
SEMANTIC_SIMILARITY_THRESHOLD = 0.92


def get_groq_client():
    """Lazily instantiate Groq client inside functions to prevent boot crashes."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)


def get_embedding(text: str) -> list[float]:
    """Generates an embedding vector using open-source model directly via Groq or fallback."""
    client = get_groq_client()
    if not client:
        return []

    # Using Groq's supported embedding model (e.g., nomic-embed-text)
    # If embeddings fail or aren't configured, return empty list to bypass cache gracefully
    try:
        response = client.embeddings.create(
            input=text,
            model="nomic-embed-text-v1_5"
        )
        return response.data[0].embedding
    except Exception:
        return []


def get_exact_cache(query: str) -> str | None:
    """Tier 1: Look up exact query hash in Redis."""
    if not redis_client:
        return None
    try:
        query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
        cached = redis_client.get(f"exact:{query_hash}")
        return cached.decode("utf-8") if cached else None
    except Exception:
        return None


def set_exact_cache(query: str, response_text: str) -> None:
    """Store result in Tier 1 Redis cache with TTL."""
    if not redis_client:
        return
    try:
        query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
        redis_client.setex(f"exact:{query_hash}", EXACT_CACHE_TTL, response_text)
    except Exception:
        pass


def get_semantic_cache(query: str) -> str | None:
    """Tier 2: Check cosine similarity of query embedding against cached vectors."""
    if not redis_client:
        return None
    
    query_vec = get_embedding(query)
    if not query_vec:
        return None

    try:
        query_arr = np.array(query_vec)
        keys = redis_client.keys("semantic:*")
        for key in keys:
            data = json.loads(redis_client.get(key))
            cached_vec = np.array(data["embedding"])
            
            # Calculate Cosine Similarity
            similarity = np.dot(query_arr, cached_vec) / (
                np.linalg.norm(query_arr) * np.linalg.norm(cached_vec)
            )
            
            if similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
                return data["response"]
    except Exception:
        return None

    return None


def set_semantic_cache(query: str, response_text: str) -> None:
    """Store query embedding and generated response in Tier 2 cache."""
    if not redis_client:
        return
        
    query_vec = get_embedding(query)
    if not query_vec:
        return

    try:
        query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
        payload = json.dumps({
            "query": query,
            "embedding": query_vec,
            "response": response_text
        })
        redis_client.setex(f"semantic:{query_hash}", EXACT_CACHE_TTL, payload)
    except Exception:
        pass