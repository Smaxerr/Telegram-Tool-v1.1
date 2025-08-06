import aiohttp
import json
import os

PURCHASE_LOG_DIR = "./purchases"

async def purchase_bin(api_token: str, bin_code: str) -> dict:
    url = "https://api.razershop.cc/api/purchase"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    payload = {
        "bin": bin_code
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Purchase failed with status {resp.status}: {text}")
            return await resp.json()

def save_purchase_result(user_id: int, purchase_data: dict):
    if not os.path.exists(PURCHASE_LOG_DIR):
        os.makedirs(PURCHASE_LOG_DIR)

    filepath = f"{PURCHASE_LOG_DIR}/user_{user_id}.txt"
    with open(filepath, "a") as f:
        f.write(json.dumps(purchase_data) + "\n")
