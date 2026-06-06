import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to example.com...")
        await page.goto("https://example.com", wait_until="networkidle")
        
        title = await page.title()
        print(f"Page title: {title}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
