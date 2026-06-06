import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page = await context.new_page()
        await stealth_async(page)
        
        # Navigate without waiting for a specific selector immediately
        print("Navigating to Google Maps...")
        await page.goto("https://www.google.com/maps", wait_until="domcontentloaded")
        
        await asyncio.sleep(10)
        
        # Take screenshot and dump content
        await page.screenshot(path="maps_debug.png")
        content = await page.content()
        with open("maps_debug.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Screenshot saved: maps_debug.png")
        print("Content saved: maps_debug.html")
        print("Content length:", len(content))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
