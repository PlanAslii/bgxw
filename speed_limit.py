# speed_limit.py
import asyncio
from state import LINKS

async def throttle(uuid: str, chunk_size: int):
    link = LINKS.get(uuid)
    if not link:
        return
    limit_bps = link.get("speed_limit_bytes", 0)
    if limit_bps <= 0:
        return
    delay = chunk_size / limit_bps
    if delay > 0 and delay > 0.005:
        await asyncio.sleep(delay)
