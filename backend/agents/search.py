import asyncio

async def search_agent(msg):
    text = "According to the latest ferry schedules, boats to [Corfu] run every hour."
    for ch in text:
        yield ch
        await asyncio.sleep(0.01)
