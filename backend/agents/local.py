import asyncio

async def local_agent(msg):
    text = "Locals will tell you the best food in [Gjirokastër] is qifqi."
    for ch in text:
        yield ch
        await asyncio.sleep(0.01)
