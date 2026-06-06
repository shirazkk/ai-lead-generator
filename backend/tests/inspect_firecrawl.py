import inspect
from firecrawl import FirecrawlApp
import os

# Mock API key for inspection
app = FirecrawlApp(api_key="mock")

print("Methods in FirecrawlApp:")
for name, member in inspect.getmembers(app):
    if not name.startswith('_'):
        print(f"{name}: {inspect.signature(member) if inspect.ismethod(member) else 'attribute'}")

print("\n--- Inspecting scrape_url signature ---")
print(inspect.signature(app.scrape_url))
