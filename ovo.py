from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def screenshot_ovo(output_path: str = "/tmp/ovo_page.png"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ]
        )
        page = await browser.new_page()

        # Apply stealth here
        await stealth_async(page)

        # Optional: set realistic user agent
        await page.set_user_agent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )

        await page.goto("https://ovoenergypayments.paypoint.com/Guestpayment")
        await page.screenshot(path=output_path, full_page=True)
        await browser.close()
    return output_path
