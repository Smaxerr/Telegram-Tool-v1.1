from playwright.async_api import async_playwright

async def screenshot_ovo(output_path: str = "/tmp/ovo_page.png"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://ovoenergypayments.paypoint.com/Guestpayment")
        await page.screenshot(path=output_path, full_page=True)
        await browser.close()
    return output_path
