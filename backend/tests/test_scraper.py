import asyncio
import logging
import sys
import os

# Add backend directory to the BEGINNING of sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.scraper_agent import enrich_business
from models import RawBusiness

# Configure logging to see the scraper agent output
logging.basicConfig(level=logging.INFO)

async def test_scraper():
    # Create a minimal RawBusiness object (like the output of discovery_agent)
    raw_lead = RawBusiness(
        business_name="",
        business_type="cafe",
        address="123 Test St, Chicago, IL",
        city="Chicago",
        country="USA",
        google_maps_url="https://maps.google.com/?cid=123",
        website_status="none"
    )
    
    print(f"Starting enrichment for: {raw_lead.business_name}")
    
    try:
        enriched_lead = await enrich_business(raw_lead)
        print("\nEnrichment complete.")
        print(f"Description: {enriched_lead.business_description}")
        print(f"Owner: {enriched_lead.owner_name}")
        print(f"Email: {enriched_lead.email}")
        print(f"Social Profiles found: {len(enriched_lead.social_profiles)}")
        print(f"Reviews found: {len(enriched_lead.reviews)}")
    except Exception as e:
        print(f"\nEnrichment failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
