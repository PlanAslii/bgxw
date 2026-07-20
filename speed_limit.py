# speed_limit.py
import asyncio
from state import LINKS

async def throttle(uuid: str, chunk_size: int):
    """
    اعمال محدودیت سرعت نرم (Soft Throttling) با استفاده از تاخیر زمانی.
    این تابع جلوی اسپم شدن ترافیک سرور توسط یک کاربر پرمصرف را می‌گیرد.
    """
    link = LINKS.get(uuid)
    if not link:
        return

    # استخراج محدودیت بر حسب بایت بر ثانیه
    limit_bps = link.get("speed_limit_bytes", 0)
    
    if limit_bps <= 0:
        return

    # محاسبه خواب (Sleep) بر اساس حجم تکه دیتای عبوری
    delay = chunk_size / limit_bps
    if delay > 0:
        # برای جلوگیری از فریز شدن لوپ، تاخیرهای خیلی کوچک نادیده گرفته می‌شوند
        if delay > 0.005: 
            await asyncio.sleep(delay)
