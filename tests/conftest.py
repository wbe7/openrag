import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Force no-auth mode for testing by setting OAuth credentials to empty strings
# This ensures anonymous JWT tokens are created automatically
os.environ['GOOGLE_OAUTH_CLIENT_ID'] = ''
os.environ['GOOGLE_OAUTH_CLIENT_SECRET'] = ''

from src.config.settings import clients
from src.session_manager import SessionManager
from src.main import generate_jwt_keys


# Mock embeddings for CI environment to avoid rate limits
@pytest.fixture(scope="session", autouse=True)
def mock_openai_embeddings():
    """Mock OpenAI embeddings API calls in CI environment to avoid rate limits."""
    # Only mock in CI environment
    if os.getenv("CI") or os.getenv("MOCK_EMBEDDINGS", "false").lower() in ("true", "1", "yes"):
        print("[DEBUG] Mocking OpenAI embeddings for CI environment")
        
        def create_mock_embedding(texts, model="text-embedding-3-small", **kwargs):
            """Create mock embeddings with proper dimensions based on model."""
            # Get dimensions based on model
            from src.config.settings import OPENAI_EMBEDDING_DIMENSIONS, WATSONX_EMBEDDING_DIMENSIONS
            
            dimensions = OPENAI_EMBEDDING_DIMENSIONS.get(
                model, 
                WATSONX_EMBEDDING_DIMENSIONS.get(model, 1536)
            )
            
            # Handle both single string and list of strings
            if isinstance(texts, str):
                texts = [texts]
            
            # Create mock response
            mock_data = []
            for idx, text in enumerate(texts):
                # Create deterministic embeddings based on text hash for consistency
                import hashlib
                text_hash = int(hashlib.md5(text.encode()).hexdigest(), 16)
                # Use hash to seed pseudo-random values
                embedding = [(text_hash % 1000) / 1000.0 + i / dimensions for i in range(dimensions)]
                mock_data.append(MagicMock(embedding=embedding, index=idx))
            
            mock_response = MagicMock()
            mock_response.data = mock_data
            return mock_response
        
        async def async_create_mock_embedding(model, input, **kwargs):
            """Async version of mock embedding creation."""
            return create_mock_embedding(input, model, **kwargs)
        
        # Patch the OpenAI client's embeddings.create method
        with patch('openai.AsyncOpenAI') as mock_async_openai:
            # Create a mock client instance
            mock_client_instance = MagicMock()
            mock_embeddings = MagicMock()
            mock_embeddings.create = AsyncMock(side_effect=async_create_mock_embedding)
            mock_client_instance.embeddings = mock_embeddings
            mock_client_instance.close = AsyncMock()
            
            # Make AsyncOpenAI() return our mock instance
            mock_async_openai.return_value = mock_client_instance
            
            # Also patch the agentd patch function to return the mock
            with patch('agentd.patch.patch_openai_with_mcp', return_value=mock_client_instance):
                yield mock_client_instance
    else:
        # In non-CI environments, don't mock - use real API
        yield None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def onboard_system(mock_openai_embeddings):
    """Perform initial onboarding once for all tests in the session.

    This ensures the OpenRAG config is marked as edited and properly initialized
    so that tests can use the /settings endpoint.
    """
    from pathlib import Path
    import shutil

    # Delete any existing config to ensure clean onboarding
    config_file = Path("config/config.yaml")
    if config_file.exists():
        config_file.unlink()
    
    # Clean up OpenSearch data directory to ensure fresh state for tests
    opensearch_data_path = Path(os.getenv("OPENSEARCH_DATA_PATH", "./opensearch-data"))
    if opensearch_data_path.exists():
        try:
            shutil.rmtree(opensearch_data_path)
            print(f"[DEBUG] Cleaned up OpenSearch data directory: {opensearch_data_path}")
        except Exception as e:
            print(f"[DEBUG] Could not clean OpenSearch data directory: {e}")

    # If we're using mocks, patch the clients to use mock embeddings
    if mock_openai_embeddings is not None:
        print("[DEBUG] Using mock OpenAI embeddings client")
        # Replace the client's patched_async_client with our mock
        clients._patched_async_client = mock_openai_embeddings
    
    # Initialize clients
    await clients.initialize()

    # Create app and perform onboarding via API
    from src.main import create_app, startup_tasks
    import httpx

    app = await create_app()
    await startup_tasks(app.state.services)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        onboarding_payload = {
            "llm_provider": "openai",
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-small",
            "llm_model": "gpt-4o-mini",
            "sample_data": False,
        }
        resp = await client.post("/onboarding", json=onboarding_payload)
        if resp.status_code not in (200, 204):
            # If it fails, it might already be onboarded, which is fine
            print(f"[DEBUG] Onboarding returned {resp.status_code}: {resp.text}")
        else:
            print(f"[DEBUG] Session onboarding completed successfully")

    yield

    # Cleanup after all tests
    try:
        await clients.close()
    except Exception:
        pass


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def opensearch_client():
    """OpenSearch client for testing - requires running OpenSearch."""
    await clients.initialize()
    yield clients.opensearch
    # Cleanup test indices after tests
    try:
        await clients.opensearch.indices.delete(index="test_documents")
    except Exception:
        pass


@pytest.fixture
def session_manager():
    """Session manager for testing."""
    # Generate RSA keys before creating SessionManager
    generate_jwt_keys()
    sm = SessionManager("test-secret-key")
    print(f"[DEBUG] SessionManager created with keys: private={sm.private_key_path}, public={sm.public_key_path}")
    return sm


@pytest.fixture
def test_documents_dir():
    """Create a temporary directory with test documents."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        
        # Create some test files in supported formats
        (test_dir / "test1.md").write_text("# Machine Learning Document\n\nThis is a test document about machine learning.")
        (test_dir / "test2.md").write_text("# AI Document\n\nAnother document discussing artificial intelligence.")
        (test_dir / "test3.md").write_text("# Data Science Document\n\nThis is a markdown file about data science.")
        
        # Create subdirectory with files
        sub_dir = test_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "nested.md").write_text("# Neural Networks\n\nNested document about neural networks.")
        
        yield test_dir


@pytest.fixture
def test_single_file():
    """Create a single test file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='_test_document.md', delete=False) as f:
        f.write("# Single Test Document\n\nThis is a test document about OpenRAG testing framework. This document contains multiple sentences to ensure proper chunking. The content should be indexed and searchable in OpenSearch after processing.")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass