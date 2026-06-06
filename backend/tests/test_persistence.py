import asyncio
import logging
from services.supabase_service import SupabaseService

# Setup basic logging
logging.basicConfig(level=logging.INFO)

async def test_supabase():
    try:
        service = SupabaseService()
        print("SupabaseService initialized.")
        
        count = await service.count_leads()
        print(f"Count of leads: {count}")
        
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")

if __name__ == "__main__":
    asyncio.run(test_supabase())
