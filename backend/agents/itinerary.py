import asyncio

async def itinerary_agent(msg):
    text = "Here is a perfect 1‑day plan: Start in [Ksamil], then head to [Butrint]."
    for ch in text:
        yield ch
        await asyncio.sleep(0.01)
