import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page = await context.new_page()
        await stealth_async(page)
        
        # Try a different URL format
        url = "https://www.google.com/search?tbm=lcl&q=restaurants+in+Defence+karachi"
        print(f"Navigating to: {url}")
        await page.goto(url)
        
        await asyncio.sleep(10)
        
        # Take screenshot
        await page.screenshot(path="search_maps.png")
        print("Screenshot saved: search_maps.png")
        
        # Check for results
        content = await page.content()
        print("Content length:", len(content))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
