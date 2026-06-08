import asyncio
import logging
import sys
import os

# Add backend directory to the BEGINNING of sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.discovery_agent import discover_businesses
# ... rest of code
# Configure logging to see the agent output
logging.basicConfig(level=logging.INFO)

async def test_discovery():
    city = "San Francisco"
    business_type = "cafe"
    count = 5

    print(f"Starting discovery for: {business_type} in {city} (count: {count})")

    try:
        leads = await discover_businesses(city, business_type, count)
        print(f"\nDiscovery complete. Found {len(leads)} leads.")
        for lead in leads:
            print(f"- {lead.business_name} | {lead.address} | ID: {lead.place_id}")
    except Exception as e:
        print(f"\nDiscovery failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_discovery())
