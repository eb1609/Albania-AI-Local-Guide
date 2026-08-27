# backend/services/cache.py
import hashlib
import json
import redis
import numpy as np
import os
from groq import Groq
def get_groq_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key)
# Connect to Redis instance (local or hosted)
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=False)
client = OpenAI()

EXACT_CACHE_TTL = 86400  # 24 hours in seconds
SEMANTIC_SIMILARITY_THRESHOLD = 0.92


def get_embedding(text: str) -> list[float]:
    """Generates an embedding vector for a given text query."""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def get_exact_cache(query: str) -> str | None:
    """Tier 1: Look up exact query hash in Redis."""
    query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    cached = redis_client.get(f"exact:{query_hash}")
    return cached.decode("utf-8") if cached else None


def set_exact_cache(query: str, response_text: str) -> None:
    """Store result in Tier 1 Redis cache with TTL."""
    query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    redis_client.setex(f"exact:{query_hash}", EXACT_CACHE_TTL, response_text)


def get_semantic_cache(query: str) -> str | None:
    """Tier 2: Check cosine similarity of query embedding against cached vectors."""
    query_vec = np.array(get_embedding(query))
    
    # Retrieve all stored semantic keys from Redis
    keys = redis_client.keys("semantic:*")
    for key in keys:
        data = json.loads(redis_client.get(key))
        cached_vec = np.array(data["embedding"])
        
        # Calculate Cosine Similarity
        similarity = np.dot(query_vec, cached_vec) / (
            np.linalg.norm(query_vec) * np.linalg.norm(cached_vec)
        )
        
        if similarity >= SEMANTIC_SIMILARITY_THRESHOLD:
            return data["response"]
            
    return None


def set_semantic_cache(query: str, response_text: str) -> None:
    """Store query embedding and generated response in Tier 2 cache."""
    query_vec = get_embedding(query)
    query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()
    
    payload = json.dumps({
        "query": query,
        "embedding": query_vec,
        "response": response_text
    })
    
    redis_client.setex(f"semantic:{query_hash}", EXACT_CACHE_TTL, payload)