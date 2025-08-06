import aiohttp
import asyncio
import logging
import time

from aiogram import Bot
from database import get_all_users, get_api_token

CHECK_INTERVAL = 30  # seconds between checks
NOTIFY_COOLDOWN = 3600  # 60 minutes cooldown in seconds

last_notified = {}

async def fetch_bin_availability(token: str, bin_code: str) -> int:
    """Fetch availability count for a specific bin_code using the API."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    url = f"https://api.razershop.cc/api/counts?category_id=1&filter=bin&value={bin_code}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                logging.warning(f"API request failed with status {resp.status} for bin {bin_code}")
                return 0
            data = await resp.json()
            if not data:
                return 0
            # Example response: [{filter: '492181', count: 34}]
            count = 0
            if isinstance(data, list) and len(data) > 0:
                count = data[0].get("count", 0)
            return count

async def check_bins_loop(bot: Bot):
    while True:
        users = await get_all_users()

        for user in users:
            user_id = user['id']
            api_token = await get_api_token(user_id)
            if not api_token:
                continue

            bins_raw = user.get("bins_of_interest", "")
            bins = [b.strip() for b in bins_raw.split(",") if b.strip()]

            for bin_code in bins:
                count = await fetch_bin_availability(api_token, bin_code)
                if count > 0:
                    key = (user_id, bin_code)
                    now = time.time()
                    last_time = last_notified.get(key, 0)
                    if now - last_time < NOTIFY_COOLDOWN:
                        continue
                    last_notified[key] = now
                    logging.info(f"Notifying user {user_id} about bin {bin_code} availability")
                    await bot.send_message(user_id, f"✅ BIN {bin_code} is available with count {count}!")

        await asyncio.sleep(CHECK_INTERVAL)
