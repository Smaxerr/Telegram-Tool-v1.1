import aiohttp
import asyncio
import logging

from aiogram import Bot
from database import get_all_users, get_api_token

CHECK_INTERVAL = 5  # 5 seconds
last_notified = {}

async def fetch_bins_data(token: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.razershop.cc/api/counts", headers=headers) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

async def check_bins_loop(bot: Bot):
    while True:
        logging.info("Checking bins of interest...")
        users = await get_all_users()
        for user in users:
            user_id = user['id']
            api_token = await get_api_token(user_id)
            if not api_token:
                continue

            data = await fetch_bins_data(api_token)
            if not data:
                continue

            # Extract bins of interest
            bins_raw = user.get("bins_of_interest", "")
            bins = bins_raw.split(",") if bins_raw else []

            # Assuming data contains availability info under 'available_bins'
            available_bins = data.get("available_bins", [])

            for bin_info in available_bins:
                bin_code = bin_info.get("bin")
                logging.info(f"Checking bin: {bin_code}")
                count = bin_info.get("count", 0)
                if bin_code in bins and count > 0:
                    key = (user_id, bin_code)
                    if last_notified.get(key):
                        continue
                    last_notified[key] = True
                    await bot.send_message(user_id, f"✅ BIN {bin_code} is available with count {count}!")
        await asyncio.sleep(CHECK_INTERVAL)
