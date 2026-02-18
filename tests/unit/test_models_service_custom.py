import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.models_service import ModelsService

@pytest.mark.asyncio
async def test_get_openai_models_with_custom_base_url():
    """Test fetching models from a custom OpenAI-compatible endpoint."""
    service = ModelsService()
    api_key = "test-key"
    effective_endpoint = "https://custom-provider.com/v1"
    
    # Response needs to support .json() (sync) but be returned effectively by async get
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "custom-model-1"},
            {"id": "gpt-4o"},
            {"id": "text-embedding-3-small"}
        ]
    }
    
    # Create a MagicMock for the client instance
    # We use MagicMock because we don't want the instance itself to be awaitable/async,
    # allows us to define specific async methods (__aenter__, get)
    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        result = await service.get_openai_models(api_key=api_key, endpoint=effective_endpoint)

        # Check call arguments
        mock_client_instance.get.assert_called_once()
        args, kwargs = mock_client_instance.get.call_args
        assert args[0] == f"{effective_endpoint}/models"
        
        # Verify filtering behavior
        model_ids = [m["value"] for m in result["language_models"]]
        assert "gpt-4o" in model_ids
        assert "custom-model-1" not in model_ids

@pytest.mark.asyncio
async def test_get_openai_compatible_models_no_filtering():
    """Test that openai-compatible provider does not filter models."""
    service = ModelsService()
    api_key = "test-key"
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {"id": "deepseek-chat"},
            {"id": "mistral-large"},
            {"id": "gpt-4o"},
            {"id": "custom-embedding-model"}
        ]
    }
    
    # Create a MagicMock for the client instance
    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    
    with patch("httpx.AsyncClient", return_value=mock_client_instance):
        result = await service.get_openai_models(api_key=api_key, provider="openai-compatible")
        
        # All models should be present in language_models
        model_ids = [m["value"] for m in result["language_models"]]
        assert "deepseek-chat" in model_ids
        assert "mistral-large" in model_ids
        assert "gpt-4o" in model_ids
        
        # Check embedding models too
        embedding_ids = [m["value"] for m in result["embedding_models"]]
        assert "custom-embedding-model" in embedding_ids
