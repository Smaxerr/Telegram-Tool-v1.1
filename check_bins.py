import aiohttp
import asyncio
import logging

from aiogram import Bot
from database import get_all_users, get_api_token

CHECK_INTERVAL = 5  # 5 seconds
last_notified = {}

async def fetch_bin_availability(token: str, bin_code: str) -> int:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    url = f"https://api.razershop.cc/api/counts?category_id=1&filter=bin&value={bin_code}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                logging.warning(f"API call failed with status {resp.status} for BIN {bin_code}")
                return 0
            data = await resp.json()
            if not data:
                return 0
            return data[0].get("count", 0)


async def check_bins_loop(bot: Bot):
    logging.info("check_bins_loop started")
    while True:
        logging.info("Checking bins of interest...")
        users = await get_all_users()
        logging.info(f"Loaded {len(users)} users")

        for user in users:
            user_id = user['id']
            api_token = await get_api_token(user_id)
            logging.info(f"User {user_id} api_token: {'present' if api_token else 'missing'}")
            if not api_token:
                continue

            # Extract bins of interest and clean list
            bins_raw = user.get("bins_of_interest", "")
            bins = [b.strip() for b in bins_raw.split(",") if b.strip()]
            logging.info(f"User {user_id} bins_of_interest: {bins}")

            for bin_code in bins:
                count = await fetch_bin_availability(api_token, bin_code)
                logging.info(f"User {user_id} - BIN {bin_code} availability count: {count}")
                if count > 0:
                    key = (user_id, bin_code)
                    if last_notified.get(key):
                        logging.info(f"Already notified user {user_id} about bin {bin_code}")
                        continue
                    last_notified[key] = True
                    logging.info(f"Notifying user {user_id} about bin {bin_code} availability")
                    await bot.send_message(user_id, f"✅ BIN {bin_code} is available with count {count}!")
        
        await asyncio.sleep(CHECK_INTERVAL)
