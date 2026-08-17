import asyncio

async def persona_agent(msg):
    text = f"Po, shoku im. You asked about {msg}. Let me tell you something about [Sarandë]…"
    for ch in text:
        yield ch
        await asyncio.sleep(0.01)
