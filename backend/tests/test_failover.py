import pytest
from unittest.mock import AsyncMock, MagicMock
from services.llm_service import LLMService

@pytest.mark.asyncio
async def test_llm_service_failover():
    """Test that LLMService fails over to OpenRouterProvider when GeminiProvider fails."""
    
    # Initialize LLMService with a mocked primary and failover
    service = LLMService(api_key="fake-gemini-key")
    
    # Mock primary (GeminiProvider) to fail
    service.primary.analyze_lead = AsyncMock(side_effect=Exception("Gemini failed"))
    
    # Mock failover (OpenRouterProvider) to succeed
    mock_failover = AsyncMock()
    mock_failover.analyze_lead.return_value = {"status": "success", "provider": "openrouter"}
    service.failover = mock_failover
    
    # Execute
    result = await service.analyze_lead({"name": "Test"})
    
    # Assertions
    assert service.primary.analyze_lead.called
    assert mock_failover.analyze_lead.called
    assert result["provider"] == "openrouter"
