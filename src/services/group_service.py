"""
Group Service for managing user groups for RBAC.
"""
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import GROUPS_INDEX_NAME
from utils.logging_config import get_logger

logger = get_logger(__name__)


class GroupService:
    """Service for managing user groups for RBAC."""

    def __init__(self, session_manager=None):
        self.session_manager = session_manager

    async def _ensure_index_exists(self, opensearch_client) -> None:
        """Ensure the groups index exists."""
        from config.settings import GROUPS_INDEX_BODY

        try:
            exists = await opensearch_client.indices.exists(index=GROUPS_INDEX_NAME)
            if not exists:
                await opensearch_client.indices.create(
                    index=GROUPS_INDEX_NAME,
                    body=GROUPS_INDEX_BODY,
                )
                logger.info(f"Created groups index: {GROUPS_INDEX_NAME}")
        except Exception as e:
            # Index might already exist from concurrent creation
            if "resource_already_exists_exception" not in str(e):
                logger.error(f"Failed to create groups index: {e}")
                raise

    async def create_group(
        self,
        name: str,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a new user group.

        Args:
            name: The group name (must be unique)
            description: Optional description of the group

        Returns:
            Dict with success status and group info
        """
        try:
            # Get OpenSearch client
            from config.settings import clients

            opensearch_client = clients.opensearch

            # Ensure index exists
            await self._ensure_index_exists(opensearch_client)

            # Check if group with this name already exists
            search_body = {
                "query": {"term": {"name": name}},
                "size": 1,
            }

            result = await opensearch_client.search(
                index=GROUPS_INDEX_NAME,
                body=search_body,
            )

            if result.get("hits", {}).get("hits", []):
                return {"success": False, "error": f"Group '{name}' already exists"}

            # Create a unique group_id
            group_id = secrets.token_urlsafe(16)
            now = datetime.utcnow().isoformat()

            # Create the document to store
            group_doc = {
                "group_id": group_id,
                "name": name,
                "description": description,
                "created_at": now,
            }

            # Index the group document
            result = await opensearch_client.index(
                index=GROUPS_INDEX_NAME,
                id=group_id,
                body=group_doc,
                refresh="wait_for",
            )

            if result.get("result") in ("created", "updated"):
                logger.info(f"Created group: {name} (id: {group_id})")
                return {
                    "success": True,
                    "group_id": group_id,
                    "name": name,
                    "description": description,
                    "created_at": now,
                }
            else:
                return {"success": False, "error": "Failed to create group"}

        except Exception as e:
            logger.error(f"Failed to create group: {e}")
            return {"success": False, "error": str(e)}

    async def list_groups(self) -> Dict[str, Any]:
        """
        List all user groups.

        Returns:
            Dict with list of groups
        """
        try:
            # Get OpenSearch client
            from config.settings import clients

            opensearch_client = clients.opensearch

            # Ensure index exists
            await self._ensure_index_exists(opensearch_client)

            # Search for all groups
            search_body = {
                "query": {"match_all": {}},
                "sort": [{"name": {"order": "asc"}}],
                "_source": ["group_id", "name", "description", "created_at"],
                "size": 1000,
            }

            result = await opensearch_client.search(
                index=GROUPS_INDEX_NAME,
                body=search_body,
            )

            groups = []
            for hit in result.get("hits", {}).get("hits", []):
                groups.append(hit["_source"])

            return {"success": True, "groups": groups}

        except Exception as e:
            logger.error(f"Failed to list groups: {e}")
            return {"success": False, "error": str(e), "groups": []}

    async def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a group by ID.

        Args:
            group_id: The group ID

        Returns:
            Group info if found, None otherwise
        """
        try:
            # Get OpenSearch client
            from config.settings import clients

            opensearch_client = clients.opensearch

            doc = await opensearch_client.get(
                index=GROUPS_INDEX_NAME,
                id=group_id,
            )

            return doc["_source"]

        except Exception:
            return None

    async def delete_group(self, group_id: str) -> Dict[str, Any]:
        """
        Delete a user group.

        Args:
            group_id: The group ID to delete

        Returns:
            Dict with success status
        """
        try:
            # Get OpenSearch client
            from config.settings import clients

            opensearch_client = clients.opensearch

            # Verify the group exists
            try:
                doc = await opensearch_client.get(
                    index=GROUPS_INDEX_NAME,
                    id=group_id,
                )
                group_name = doc["_source"].get("name", "unknown")
            except Exception:
                return {"success": False, "error": "Group not found"}

            # Delete the group
            result = await opensearch_client.delete(
                index=GROUPS_INDEX_NAME,
                id=group_id,
                refresh="wait_for",
            )

            if result.get("result") == "deleted":
                logger.info(f"Deleted group: {group_name} (id: {group_id})")
                return {"success": True}
            else:
                return {"success": False, "error": "Failed to delete group"}

        except Exception as e:
            logger.error(f"Failed to delete group: {e}")
            return {"success": False, "error": str(e)}

