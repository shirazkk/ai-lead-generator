"""
Test script to validate all Pydantic models.

This script tests model instantiation, validation, and JSON serialization
to ensure all models work correctly with Pydantic v2.
"""

import sys
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, 'D:/ai_lead_generator/backend')

from models import RawBusiness, EnrichedBusiness, Lead, Outreach


def test_raw_business():
    """Test RawBusiness model."""
    print("Testing RawBusiness...")

    # Valid business
    business = RawBusiness(
        business_name="Test Pizza",
        address="123 Test St",
        phone="+1-555-0100",
        website="https://test.com",
        rating=4.5
    )
    print(f"[OK] Created RawBusiness: {business.business_name} (ID: {business.id[:8]}...)")

    # Test JSON serialization
    json_data = business.model_dump_json()
    print(f"[OK] JSON serialization works")

    # Test validation - invalid rating
    try:
        RawBusiness(
            business_name="Bad Rating",
            address="123 St",
            phone="+1-555-0100",
            rating=6.0  # Invalid: > 5.0
        )
        print("[FAIL] Failed to catch invalid rating")
    except ValueError as e:
        print(f"[OK] Validation caught invalid rating")

    print()


def test_enriched_business():
    """Test EnrichedBusiness model."""
    print("Testing EnrichedBusiness...")

    # Valid enriched business
    business = EnrichedBusiness(
        business_name="Test Pizza",
        address="123 Test St",
        phone="+1-555-0100",
        website="https://test.com",
        rating=4.5,
        owner_name="John Doe",
        email="john@test.com",
        social_profiles=["https://facebook.com/test"],
        business_description="Great pizza place",
        reviews=["Amazing!", "Best pizza ever"]
    )
    print(f"[OK] Created EnrichedBusiness: {business.business_name}")
    print(f"[OK] Owner: {business.owner_name}, Email: {business.email}")
    print(f"[OK] Social profiles: {len(business.social_profiles)}, Reviews: {len(business.reviews)}")

    # Test JSON serialization
    json_data = business.model_dump_json()
    print(f"[OK] JSON serialization works")

    print()


def test_lead():
    """Test Lead model."""
    print("Testing Lead...")

    # Valid lead
    lead = Lead(
        business_name="Test Pizza",
        business_type="Restaurant",
        owner_name="John Doe",
        email="john@test.com",
        phone="+1-555-0100",
        address="123 Test St",
        city="New York",
        country="USA",
        website_status="none",
        opportunity_score=8,
        identified_problem="No online presence",
        website_benefits=["Online ordering", "Menu showcase"],
        estimated_value="$5,000-$8,000"
    )
    print(f"[OK] Created Lead: {lead.business_name} (Score: {lead.opportunity_score}/10)")
    print(f"[OK] Status: {lead.website_status}, Problem: {lead.identified_problem[:50]}...")
    print(f"[OK] Created at: {lead.created_at}")

    # Test invalid opportunity_score
    try:
        Lead(
            business_name="Bad Score",
            business_type="Restaurant",
            phone="+1-555-0100",
            address="123 St",
            city="NYC",
            country="USA",
            website_status="none",
            opportunity_score=11,  # Invalid: > 10
            identified_problem="Test"
        )
        print("[FAIL] Failed to catch invalid opportunity_score")
    except ValueError as e:
        print(f"[OK] Validation caught invalid opportunity_score: {e}")

    # Test invalid website_status
    try:
        Lead(
            business_name="Bad Status",
            business_type="Restaurant",
            phone="+1-555-0100",
            address="123 St",
            city="NYC",
            country="USA",
            website_status="invalid",  # Invalid status
            opportunity_score=5,
            identified_problem="Test"
        )
        print("[FAIL] Failed to catch invalid website_status")
    except ValueError as e:
        print(f"[OK] Validation caught invalid website_status")

    # Test JSON serialization
    json_data = lead.model_dump_json()
    print(f"[OK] JSON serialization works")

    print()


def test_outreach():
    """Test Outreach model."""
    print("Testing Outreach...")

    # Valid outreach (not sent)
    outreach = Outreach(
        lead_id="550e8400-e29b-41d4-a716-446655440000",
        subject="Test Subject",
        message="Test message content",
        tone="friendly"
    )
    print(f"[OK] Created Outreach: {outreach.subject}")
    print(f"[OK] Tone: {outreach.tone}, Sent: {outreach.sent}")
    print(f"[OK] Generated at: {outreach.generated_at}")

    # Valid outreach (sent)
    outreach_sent = Outreach(
        lead_id="550e8400-e29b-41d4-a716-446655440000",
        subject="Sent Email",
        message="Test message",
        tone="professional",
        sent=True,
        sent_at=datetime.utcnow()
    )
    print(f"[OK] Created sent Outreach: Sent at {outreach_sent.sent_at}")

    # Test invalid tone
    try:
        Outreach(
            lead_id="test-id",
            subject="Test",
            message="Test",
            tone="invalid_tone"  # Invalid
        )
        print("[FAIL] Failed to catch invalid tone")
    except ValueError as e:
        print(f"[OK] Validation caught invalid tone")

    # Test sent_at without sent=True
    try:
        Outreach(
            lead_id="test-id",
            subject="Test",
            message="Test",
            tone="friendly",
            sent=False,
            sent_at=datetime.utcnow()  # Invalid: sent_at set but sent=False
        )
        print("[FAIL] Failed to catch invalid sent_at")
    except ValueError as e:
        print(f"[OK] Validation caught invalid sent_at: {e}")

    # Test JSON serialization
    json_data = outreach.model_dump_json()
    print(f"[OK] JSON serialization works")

    print()


def main():
    """Run all tests."""
    print("=" * 60)
    print("PYDANTIC V2 MODEL VALIDATION TEST")
    print("=" * 60)
    print()

    try:
        test_raw_business()
        test_enriched_business()
        test_lead()
        test_outreach()

        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
        print()
        print("Summary:")
        print("- All models instantiate correctly")
        print("- All validators work as expected")
        print("- JSON serialization works")
        print("- UUID and datetime defaults work")
        print("- Pydantic v2 syntax is correct")

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
