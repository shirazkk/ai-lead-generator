import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page = await context.new_page()
        await stealth_async(page)
        
        # Searching Google Search with "map" keyword to trigger local pack
        url = "https://www.google.com/search?q=restaurants+in+Defence+karachi+map"
        print(f"Navigating to: {url}")
        await page.goto(url)
        
        await asyncio.sleep(10)
        
        # Dump content to check for local pack
        content = await page.content()
        with open("search_results_with_map.html", "w", encoding="utf-8") as f:
            f.write(content)
        
        print("HTML dumped to search_results_with_map.html")
        print("Content length:", len(content))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
