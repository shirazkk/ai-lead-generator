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
        
        # Searching Google Search directly
        url = "https://www.google.com/search?q=restaurants+in+Defence+karachi"
        await page.goto(url)
        await asyncio.sleep(5)
        
        # Look for local pack results
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Elements containing local results usually have specific classes like 'rllt__details' 
        # or inside a 'g' container with local info
        # Let's see what we can grab
        local_results = soup.select('div.g')
        print(f"Found {len(local_results)} potential results")
        
        for res in local_results:
             name = res.select_one('h3')
             if name:
                 print(f"Name: {name.text}")
                 
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
