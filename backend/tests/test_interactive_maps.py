import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page = await context.new_page()
        await stealth_async(page)
        
        # Trying a more explicit maps-based URL that might be less restricted
        # We can also try navigating to google.com/maps first, then typing the search
        await page.goto("https://www.google.com/maps")
        await page.wait_for_selector('input#searchboxinput')
        await page.fill('input#searchboxinput', 'restaurants in Defence karachi')
        await page.press('input#searchboxinput', 'Enter')
        
        await asyncio.sleep(10)
        
        await page.screenshot(path="maps_interactive.png")
        print("Screenshot saved: maps_interactive.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
