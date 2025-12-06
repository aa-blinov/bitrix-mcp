"""Bitrix24 Projects (Workgroups) tools for MCP server."""

import json
import logging
from typing import Optional

from beartype import beartype

from ..client import BitrixClient

logger = logging.getLogger(__name__)


class ProjectTools:
    """Tools for managing Bitrix24 projects (workgroups)."""

    def __init__(self, client: BitrixClient):
        """Initialize project tools with Bitrix client."""
        self.client = client

    @beartype
    async def get_projects(
        self,
        filter_params: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Get projects (workgroups) from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"ACTIVE": "Y"}')
            limit: Maximum number of projects to return (default: 50)

        Returns:
            JSON string with projects data

        Note:
            ORDER parameter is not supported because the underlying API uses
            automatic pagination which is incompatible with custom ordering.
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else {}

            params = {}
            if filter_dict:
                params["FILTER"] = filter_dict

            # Use get_all for automatic pagination
            projects = await self.client.client.get_all(
                "sonet_group.get", params if params else {}
            )

            # Limit results
            if limit > 0 and projects:
                projects = projects[:limit]

            # Add total count
            total = len(projects) if projects else 0

            result = {
                "success": True,
                "total": total,
                "count": total,
                "projects": projects if projects else [],
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def create_project(self, fields: str) -> str:
        """
        Create a new project (workgroup) in Bitrix24.

        Args:
            fields: JSON string with project fields (e.g., '{"NAME": "New Project", "DESCRIPTION": "Project description"}')

        Returns:
            JSON string with creation result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Create project
            result = await self.client.client.call("sonet_group.create", fields_dict)

            return json.dumps(
                {
                    "success": True,
                    "project_id": result[0] if result else None,
                    "message": "Project created successfully",
                }
            )

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def update_project(self, project_id: str, fields: str) -> str:
        """
        Update an existing project in Bitrix24.

        Args:
            project_id: Project ID to update
            fields: JSON string with fields to update

        Returns:
            JSON string with update result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Update project
            result = await self.client.client.call(
                "sonet_group.update", {"GROUP_ID": project_id, **fields_dict}
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "project_id": project_id,
                    "message": (
                        "Project updated successfully"
                        if success
                        else "Failed to update project"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_project_tasks(self, project_id: str, limit: int = 50) -> str:
        """
        Get tasks for a specific project.

        Args:
            project_id: Project ID
            limit: Maximum number of tasks to return

        Returns:
            JSON string with project tasks
        """
        try:
            # Get tasks for project using get_all for proper pagination
            tasks_list = await self.client.client.get_all(
                "tasks.task.list", {"filter": {"GROUP_ID": project_id}}
            )

            # Limit results
            if limit > 0 and tasks_list:
                tasks_list = tasks_list[:limit]

            result = {
                "success": True,
                "project_id": project_id,
                "count": len(tasks_list) if tasks_list else 0,
                "tasks": tasks_list if tasks_list else [],
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting project tasks for {project_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def add_project_member(
        self, project_id: str, user_id: str, role: str = "member"
    ) -> str:
        """
        Add a member to a project.

        Args:
            project_id: Project ID
            user_id: User ID to add
            role: Role for the user (member, moderator, etc.)

        Returns:
            JSON string with result
        """
        try:
            # Add member to project
            result = await self.client.client.call(
                "sonet_group.user.add",
                {"GROUP_ID": project_id, "USER_ID": user_id, "ROLE": role},
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "project_id": project_id,
                    "user_id": user_id,
                    "role": role,
                    "message": (
                        "Member added successfully"
                        if success
                        else "Failed to add member"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error adding member to project {project_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_project_members(self, project_id: str) -> str:
        """
        Get members of a project.

        Args:
            project_id: Project ID

        Returns:
            JSON string with project members
        """
        try:
            # Get project members using get_all
            members_list = await self.client.client.get_all(
                "sonet_group.user.get", {"ID": project_id}
            )

            result = {
                "success": True,
                "project_id": project_id,
                "count": len(members_list) if members_list else 0,
                "members": members_list if members_list else [],
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting project members for {project_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def expel_project_member(self, project_id: str, user_id: str) -> str:
        """
        Remove a member from a Bitrix24 project (workgroup).

        This method removes a user from a project. The current user must have sufficient
        permissions to expel members from the project.

        Args:
            project_id: Project ID from which to remove the member (required)
            user_id: User ID to remove from the project (required)

        Returns:
            JSON string with operation result

        Example:
            expel_project_member("123", "456")
            # Returns: {"success": true, "project_id": "123", "user_id": "456", "message": "Member expelled successfully"}
        """
        try:
            # Expel member from project
            result = await self.client.expel_project_member(project_id, user_id)

            return json.dumps(
                {
                    "success": result,
                    "project_id": project_id,
                    "user_id": user_id,
                    "message": (
                        "Member expelled successfully"
                        if result
                        else "Failed to expel member"
                    ),
                }
            )

        except Exception as e:
            logger.error(
                f"Error expelling member {user_id} from project {project_id}: {e}"
            )
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def request_join_project(
        self, project_id: str, message: Optional[str] = None
    ) -> str:
        """
        Send a request to join a Bitrix24 project (workgroup).

        This method allows the current user to request membership in a project.
        The project owner or moderators will receive the request and can approve or deny it.

        Args:
            project_id: Project ID to request joining (required)
            message: Optional message to include with the request (optional)

        Returns:
            JSON string with operation result

        Example:
            request_join_project("123", "Please add me to the project")
            # Returns: {"success": true, "project_id": "123", "message": "Join request sent successfully"}
        """
        try:
            # Send join request
            result = await self.client.request_join_project(project_id, message)

            return json.dumps(
                {
                    "success": result,
                    "project_id": project_id,
                    "request_message": message,
                    "message": (
                        "Join request sent successfully"
                        if result
                        else "Failed to send join request"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error sending join request for project {project_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def invite_project_member(
        self, project_id: str, user_id: str, message: Optional[str] = None
    ) -> str:
        """
        Invite a user to join a Bitrix24 project (workgroup).

        This method sends an invitation to a user to join a project. The invited user will
        receive a notification and can accept or decline the invitation. This differs from
        'add_project_member' which directly adds a user without their consent.

        Args:
            project_id: Project ID to invite the user to (required)
            user_id: User ID to invite to the project (required)
            message: Optional personal message to include with the invitation (optional)

        Returns:
            JSON string with operation result

        Example:
            invite_project_member("123", "456", "We'd like you to join our project")
            # Returns: {"success": true, "project_id": "123", "user_id": "456", "message": "Invitation sent successfully"}
        """
        try:
            # Send invitation
            result = await self.client.invite_project_member(
                project_id, user_id, message
            )

            return json.dumps(
                {
                    "success": result,
                    "project_id": project_id,
                    "user_id": user_id,
                    "invitation_message": message,
                    "message": (
                        "Invitation sent successfully"
                        if result
                        else "Failed to send invitation"
                    ),
                }
            )

        except Exception as e:
            logger.error(
                f"Error sending invitation to user {user_id} for project {project_id}: {e}"
            )
            return json.dumps({"success": False, "error": str(e)})
