import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from bs4 import BeautifulSoup

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await stealth_async(page)
        
        # Go to a query that should yield a feed
        await page.goto("https://www.google.com/maps/search/restaurants+in+Defence+karachi")
        
        # Wait specifically for elements that look like business result cards in the feed
        # In the feed, items often have role="feed" and contain links
        # Let's dump the first result's structure
        await asyncio.sleep(5)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find potential business card containers
        cards = soup.select('[role="feed"] > div > div > a')
        print(f"Found {len(cards)} potential cards using [role='feed']")
        
        # If that fails, look for general results
        if not cards:
             # Just print all links with map-related hrefs to see what's there
             links = soup.find_all('a', href=True)
             map_links = [l['href'] for l in links if '/maps/place/' in l['href']]
             print(f"Found {len(map_links)} map links")
             if map_links:
                 print("First map link:", map_links[0])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
