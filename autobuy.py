import aiohttp
import json
import os

from check_bins import fetch_bin_availability
from database import get_api_token, get_autobuy_bins

PURCHASE_LOG_DIR = "./purchases"

async def purchase_bin(api_token: str, bin_code: str, count: int) -> dict:
    url = "https://api.razershop.cc/api/purchase"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    payload = {
        "filter": "bin",
        "category_id": 1,
        "positions": [
            {
                "value": bin_code,
                "count": count
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"Purchase failed with status {resp.status}: {text}")
            return await resp.json()

def save_purchase_result(user_id: int, purchase_data: dict):
    if not os.path.exists(PURCHASE_LOG_DIR):
        os.makedirs(PURCHASE_LOG_DIR)

    filepath = f"{PURCHASE_LOG_DIR}/user_{user_id}.txt"
    with open(filepath, "a") as f:
        f.write(json.dumps(purchase_data) + "\n")

async def run_autobuy(user_id: int) -> str:
    bins = await get_autobuy_bins(user_id)
    token = await get_api_token(user_id)

    if not token:
        return "❌ You haven't set your API token yet."
    if not bins:
        return "❌ You haven't added any BINs to autobuy."

    successful = 0
    failed = 0

    for bin_code in bins:
        try:
            available_count = await fetch_bin_availability(token, bin_code)
            if available_count <= 0:
                continue  # Skip if nothing available

            result = await purchase_bin(token, bin_code, available_count)

            # result is a list of purchase results
            all_data = []
            if isinstance(result, list):
                for item in result:
                    all_data.extend(item.get("data", []))
            else:
                all_data = result.get("data", [])

            save_purchase_result(user_id, {
                "bin": bin_code,
                "data": all_data,
                "success": True
            })
            successful += 1
        except Exception as e:
            save_purchase_result(user_id, {
                "bin": bin_code,
                "response": str(e),
                "success": False
            })
            failed += 1

    return (
        f"✅ Autobuy completed!\n"
        f"🟢 Success: {successful}\n"
        f"🔴 Failed: {failed}\n"
        f"📁 Log saved to: purchases/user_{user_id}.txt"
    )
