import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page = await context.new_page()
        await stealth_async(page)
        
        await page.goto("https://www.google.com/search?tbm=lcl&q=restaurants+in+Defence+karachi")
        await asyncio.sleep(5)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for business results in the 'tbm=lcl' view
        # Based on structure, results are usually in elements with specific classes
        results = soup.select('.rllt__details, .local_results > div')
        print(f"Found {len(results)} potential results")
        
        for i, res in enumerate(results[:3]):
            name = res.select_one('.OSrXXb, .LrzXr')
            if name:
                print(f"Result {i+1}: {name.text}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
