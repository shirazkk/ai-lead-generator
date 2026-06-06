import pytest
import uuid
from backend.services.supabase_service import SupabaseService

@pytest.mark.asyncio
async def test_supabase_persistence():
    """
    Directly test SupabaseService to verify data persistence.
    """
    db = SupabaseService()
    unique_id = str(uuid.uuid4())
    
    test_lead_data = {
        "id": unique_id,
        "business_name": f"Persistence Test {unique_id[:8]}",
        "business_type": "test",
        "phone": "1234567890",
        "address": "123 Persistence Lane",
        "city": "Test City",
        "country": "Test Country",
        "website_status": "none",
        "opportunity_score": 5,
        "identified_problem": "Testing persistence",
        "created_at": "2026-06-06T12:00:00Z"
    }
    
    try:
        # 1. Create Lead
        print(f"\nCreating lead with ID: {unique_id}")
        created_lead = await db.create_lead(test_lead_data)
        assert created_lead["id"] == unique_id
        
        # 2. Verify Lead in DB
        fetched_lead = await db.get_lead(unique_id)
        assert fetched_lead is not None
        assert fetched_lead["business_name"] == test_lead_data["business_name"]
        
        # 3. Create Outreach
        test_outreach_data = {
            "lead_id": unique_id,
            "subject": "Test Persistence",
            "message": "This is a test message",
            "tone": "friendly",
            "sent": False
        }
        print(f"Creating outreach for lead: {unique_id}")
        created_outreach = await db.create_outreach(test_outreach_data)
        assert created_outreach["lead_id"] == unique_id
        
        # 4. Verify Outreach in DB
        fetched_outreach = await db.get_outreach_by_lead(unique_id)
        assert fetched_outreach is not None
        assert fetched_outreach["subject"] == "Test Persistence"
        
        print("Persistence test passed successfully")
        
    finally:
        # Cleanup
        print(f"Cleaning up lead: {unique_id}")
        await db.delete_lead(unique_id)
