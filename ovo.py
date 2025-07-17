from playwright.async_api import async_playwright

# ===== Take screenshot using Playwright =====
async def take_royalmail_screenshot(card: str) -> str:
    filename = f"screenshots/{uuid.uuid4()}.png"
    os.makedirs("screenshots", exist_ok=True)

    try:
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto("https://send.royalmail.com/send/youritem?country=GBR&format&weight=&weightUnit=G", timeout=60000)
            await page.wait_for_timeout(2000)  # Wait for full page load

            

            await page.screenshot(path=filename, full_page=True)
            await browser.close()
        return filename
    except Exception as e:
        print(f"[RoyalMail Screenshot Error]: {e}")
        return None
