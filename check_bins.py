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

            data = await fetch_bins_data(api_token)
            if not data:
                logging.warning(f"No data received for user {user_id}")
                continue

            logging.info(f"API data for user {user_id}: {data}")

            # Extract bins of interest
            bins_raw = user.get("bins_of_interest", "")
            bins = [b.strip() for b in bins_raw.split(",") if b.strip()]
            logging.info(f"User {user_id} bins_of_interest: {bins}")

            available_bins = data.get("available_bins", [])
            logging.info(f"API available_bins for user {user_id}: {available_bins}")

            for bin_info in available_bins:
                bin_code = bin_info.get("bin")
                logging.info(f"Checking bin: {bin_code}")
                count = bin_info.get("count", 0)
                if bin_code in bins and count > 0:
                    key = (user_id, bin_code)
                    if last_notified.get(key):
                        logging.info(f"Already notified user {user_id} about bin {bin_code}")
                        continue
                    last_notified[key] = True
                    logging.info(f"Notifying user {user_id} about bin {bin_code} availability")
                    await bot.send_message(user_id, f"✅ BIN {bin_code} is available with count {count}!")
        
        await asyncio.sleep(CHECK_INTERVAL)

