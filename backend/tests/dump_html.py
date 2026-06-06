import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page = await context.new_page()
        await stealth_async(page)
        
        await page.goto("https://www.google.com/search?tbm=lcl&q=restaurants+in+Defence+karachi")
        await asyncio.sleep(5)
        
        content = await page.content()
        with open("dump.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Full HTML dumped to dump.html")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
