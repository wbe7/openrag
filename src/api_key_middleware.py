"""
API Key middleware for authenticating public API requests.

This middleware validates API keys and generates ephemeral JWTs with the
key's specific roles and groups for downstream security enforcement.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from session_manager import User
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _extract_api_key(request: Request) -> str | None:
    """
    Extract API key from request headers.

    Supports:
    - X-API-Key header
    - Authorization: Bearer orag_... header
    """
    # Try X-API-Key header first
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key.startswith("orag_"):
        return api_key

    # Try Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        if token.startswith("orag_"):
            return token

    return None


def require_api_key(api_key_service, session_manager=None):
    """
    Decorator to require API key authentication for public API endpoints.
    
    Generates an ephemeral JWT with the API key's specific roles and groups
    to enforce RBAC in downstream services (OpenSearch, tools, etc.).

    Usage:
        @require_api_key(api_key_service, session_manager)
        async def my_endpoint(request):
            user = request.state.user
            jwt_token = request.state.jwt_token  # Ephemeral restricted JWT
            ...
    """

    def decorator(handler):
        async def wrapper(request: Request):
            # Extract API key from headers
            api_key = _extract_api_key(request)

            if not api_key:
                return JSONResponse(
                    {
                        "error": "API key required",
                        "message": "Provide API key via X-API-Key header or Authorization: Bearer header",
                    },
                    status_code=401,
                )

            # Validate the key and get RBAC claims
            user_info = await api_key_service.validate_key(api_key)

            if not user_info:
                return JSONResponse(
                    {
                        "error": "Invalid API key",
                        "message": "The provided API key is invalid or has been revoked",
                    },
                    status_code=401,
                )

            # Extract RBAC fields from API key
            key_roles = user_info.get("roles", ["openrag_user"])
            key_groups = user_info.get("groups", [])

            # Create a User object with the API key's roles and groups
            user = User(
                user_id=user_info["user_id"],
                email=user_info["user_email"],
                name=user_info.get("name", "API User"),
                picture=None,
                provider="api_key",
                roles=key_roles,
                groups=key_groups,
            )

            # Set request state
            request.state.user = user
            request.state.api_key_id = user_info["key_id"]

            # Generate ephemeral JWT with the API key's restricted roles/groups
            if session_manager:
                # Create a short-lived JWT with the key's specific permissions
                ephemeral_jwt = session_manager.create_jwt_token(
                    user=user,
                    roles=key_roles,
                    groups=key_groups,
                    expiration_days=1,  # Short-lived for API requests
                )
                request.state.jwt_token = ephemeral_jwt
                logger.debug(
                    "Generated ephemeral JWT for API key",
                    key_id=user_info["key_id"],
                    roles=key_roles,
                    groups=key_groups,
                )
            else:
                request.state.jwt_token = None
                logger.warning(
                    "No session_manager provided - JWT not generated for API key"
                )

            return await handler(request)

        return wrapper

    return decorator


def optional_api_key(api_key_service, session_manager=None):
    """
    Decorator to optionally authenticate with API key.
    Sets request.state.user to None if no valid API key is provided.
    
    When a valid API key is provided, generates an ephemeral JWT with
    the key's specific roles and groups.
    """

    def decorator(handler):
        async def wrapper(request: Request):
            # Extract API key from headers
            api_key = _extract_api_key(request)

            if api_key:
                # Validate the key and get RBAC claims
                user_info = await api_key_service.validate_key(api_key)

                if user_info:
                    # Extract RBAC fields from API key
                    key_roles = user_info.get("roles", ["openrag_user"])
                    key_groups = user_info.get("groups", [])

                    # Create a User object with the API key's roles and groups
                    user = User(
                        user_id=user_info["user_id"],
                        email=user_info["user_email"],
                        name=user_info.get("name", "API User"),
                        picture=None,
                        provider="api_key",
                        roles=key_roles,
                        groups=key_groups,
                    )
                    request.state.user = user
                    request.state.api_key_id = user_info["key_id"]

                    # Generate ephemeral JWT with the API key's restricted roles/groups
                    if session_manager:
                        ephemeral_jwt = session_manager.create_jwt_token(
                            user=user,
                            roles=key_roles,
                            groups=key_groups,
                            expiration_days=1,
                        )
                        request.state.jwt_token = ephemeral_jwt
                    else:
                        request.state.jwt_token = None
                else:
                    request.state.user = None
                    request.state.api_key_id = None
                    request.state.jwt_token = None
            else:
                request.state.user = None
                request.state.api_key_id = None
                request.state.jwt_token = None

            return await handler(request)

        return wrapper

    return decorator
