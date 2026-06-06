import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await stealth_async(page)
        
        print("Navigating to Google Maps...")
        await page.goto("https://www.google.com/maps/search/restaurants+in+Defence+karachi")
        
        # Wait a bit for potential redirects or loading
        await asyncio.sleep(10)
        
        # Take screenshot
        await page.screenshot(path="diagnostic_maps.png")
        print("Screenshot saved: diagnostic_maps.png")
        
        # Save content
        content = await page.content()
        with open("diagnostic_maps.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Page content saved: diagnostic_maps.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
