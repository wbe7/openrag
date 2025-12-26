"""
User Groups management endpoints.

These endpoints allow managing user groups for RBAC.
"""
from starlette.requests import Request
from starlette.responses import JSONResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


async def list_groups_endpoint(request: Request, group_service):
    """
    List all user groups.

    GET /groups

    Response:
        {
            "success": true,
            "groups": [
                {
                    "group_id": "...",
                    "name": "finance",
                    "description": "Finance team",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
        }
    """
    result = await group_service.list_groups()
    return JSONResponse(result)


async def create_group_endpoint(request: Request, group_service):
    """
    Create a new user group.

    POST /groups
    Body: {"name": "finance", "description": "Finance team"}

    Response:
        {
            "success": true,
            "group_id": "...",
            "name": "finance",
            "description": "Finance team",
            "created_at": "2024-01-01T00:00:00"
        }
    """
    try:
        data = await request.json()
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()

        if not name:
            return JSONResponse(
                {"success": False, "error": "Name is required"},
                status_code=400,
            )

        if len(name) > 100:
            return JSONResponse(
                {"success": False, "error": "Name must be 100 characters or less"},
                status_code=400,
            )

        result = await group_service.create_group(
            name=name,
            description=description,
        )

        if result.get("success"):
            return JSONResponse(result)
        elif "already exists" in result.get("error", ""):
            return JSONResponse(result, status_code=409)
        else:
            return JSONResponse(result, status_code=500)

    except Exception as e:
        logger.error(f"Failed to create group: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500,
        )


async def delete_group_endpoint(request: Request, group_service):
    """
    Delete a user group.

    DELETE /groups/{group_id}

    Response:
        {"success": true}
    """
    group_id = request.path_params.get("group_id")

    if not group_id:
        return JSONResponse(
            {"success": False, "error": "Group ID is required"},
            status_code=400,
        )

    result = await group_service.delete_group(group_id=group_id)

    if result.get("success"):
        return JSONResponse(result)
    elif result.get("error") == "Group not found":
        return JSONResponse(result, status_code=404)
    else:
        return JSONResponse(result, status_code=500)

