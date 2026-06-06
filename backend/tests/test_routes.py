import pytest
from httpx import AsyncClient
from main import app
from services.supabase_service import SupabaseService

# Initialize Supabase service for direct database verification
db = SupabaseService()

import pytest_asyncio

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health_check(async_client):
    """Test the health check endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_search_pipeline_data_persistence(async_client, mocker):
    """
    Test the full search pipeline with mocked agent calls to focus on data persistence.
    """
    # Mocking agent calls to avoid external API dependencies and costs
    mocker.patch("backend.routers.search.discover_leads", return_value=[
        mocker.Mock(
            business_name="Test Business",
            business_type="restaurant",
            address="123 Test St",
            phone="+1234567890",
            google_maps_url="https://maps.google.com/test",
            website_status="none",
            rating=4.0
        )
    ])
    
    mocker.patch("backend.routers.search.enrich_business", return_value=mocker.Mock(
        business_name="Test Business",
        business_type="restaurant",
        address="123 Test St",
        phone="+1234567890",
        google_maps_url="https://maps.google.com/test",
        website_status="none",
        owner_name="Test Owner",
        email="test@example.com",
        city="Test City",
        country="Test Country",
        social_profiles=[],
        business_description="Test Description",
        rating=4.0
    ))
    
    mocker.patch("backend.routers.search.analyze_lead", return_value={
        "opportunity_score": 8,
        "identified_problem": "No website",
        "website_benefits": "Increased visibility, online orders",
        "estimated_value": "$1000/mo"
    })
    
    mocker.patch("backend.routers.search.generate_outreach", return_value=mocker.Mock(
        id="test-outreach-id",
        lead_id="placeholder",
        subject="Your business needs a website",
        message="Hi Test Owner, we noticed you don't have a website...",
        tone="friendly",
        generated_at=mocker.Mock(isoformat=lambda: "2026-06-06T12:00:00Z"),
        model_dump=lambda: {
            "id": "test-outreach-id",
            "lead_id": "placeholder",
            "subject": "Your business needs a website",
            "message": "Hi Test Owner, we noticed you don't have a website...",
            "tone": "friendly",
            "sent": False
        }
    ))

    # Mock DB calls to ensure they are called with correct data
    mock_create_lead = mocker.patch.object(SupabaseService, "create_lead", return_value={"id": "test-lead-id"})
    mock_create_outreach = mocker.patch.object(SupabaseService, "create_outreach", return_value={"id": "test-outreach-id"})

    search_data = {
        "city": "Test City",
        "business_type": "restaurant",
        "count": 1
    }

    response = await async_client.post("/api/search", json=search_data)
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify DB insertion calls
    assert mock_create_lead.called
    assert mock_create_outreach.called
    
    # Verify the data passed to create_lead
    lead_call_args = mock_create_lead.call_args[0][0]
    assert lead_call_args["business_name"] == "Test Business"
    assert lead_call_args["city"] == "Test City"
    assert lead_call_args["opportunity_score"] == 8

@pytest.mark.asyncio
async def test_leads_crud(async_client, mocker):
    """Test Leads CRUD operations."""
    test_lead = {
        "id": "test-uuid",
        "business_name": "CRUD Test Business",
        "business_type": "barber",
        "city": "NYC",
        "country": "USA",
        "phone": "+1234567890",
        "address": "123 St",
        "website_status": "none",
        "opportunity_score": 7,
        "identified_problem": "No website",
        "created_at": "2026-06-06T12:00:00Z"
    }
    
    # Mock database retrieval
    mocker.patch.object(SupabaseService, "get_leads", return_value=[test_lead])
    mocker.patch.object(SupabaseService, "get_lead", return_value=test_lead)
    mocker.patch.object(SupabaseService, "get_outreach_by_lead", return_value=None)
    mocker.patch.object(SupabaseService, "delete_lead", return_value=True)

    # Test list
    response = await async_client.get("/api/leads")
    assert response.status_code == 200
    assert len(response.json()["data"]) > 0
    assert response.json()["data"][0]["business_name"] == "CRUD Test Business"

    # Test get single
    response = await async_client.get("/api/leads/test-uuid")
    assert response.status_code == 200
    assert response.json()["data"]["lead"]["business_name"] == "CRUD Test Business"

    # Test delete
    response = await async_client.delete("/api/leads/test-uuid")
    assert response.status_code == 200
    assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_outreach_regeneration(async_client, mocker):
    """Test outreach regeneration route."""
    test_lead = {
        "id": "test-uuid",
        "business_name": "Outreach Test",
        "business_type": "salon",
        "city": "London",
        "address": "123 St",
        "phone": "123",
        "email": "test@test.com",
        "opportunity_score": 9,
        "identified_problem": "None",
        "website_benefits": ["SEO"],
        "estimated_value": "High",
        "country": "UK",
        "website_status": "none",
        "created_at": "2026-06-06T12:00:00Z"
    }

    mocker.patch.object(SupabaseService, "get_lead", return_value=test_lead)
    mocker.patch.object(SupabaseService, "get_outreach_by_lead", return_value=None)
    mocker.patch.object(SupabaseService, "create_outreach", return_value={
        "id": "new-outreach",
        "lead_id": "test-uuid",
        "subject": "Hello",
        "message": "World",
        "tone": "friendly",
        "generated_at": "2026-06-06T12:00:00Z",
        "sent": False
    })
    
    mocker.patch("backend.routers.outreach.generate_outreach", return_value=mocker.Mock(
        id="new-outreach",
        lead_id="test-uuid",
        subject="Hello",
        message="World",
        tone="friendly",
        generated_at=mocker.Mock(isoformat=lambda: "2026-06-06T12:00:00Z"),
        model_dump=lambda: {"id": "new-outreach", "lead_id": "test-uuid", "subject": "Hello", "message": "World", "tone": "friendly"}
    ))

    response = await async_client.post("/api/outreach/regenerate/test-uuid")
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["subject"] == "Hello"
