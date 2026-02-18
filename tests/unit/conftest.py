import pytest

@pytest.fixture(scope="session", autouse=True)
def onboard_system():
    """Override the global onboard_system fixture to do nothing for unit tests.
    
    This prevents the unit tests from trying to connect to OpenSearch or start the full app.
    """
    yield
