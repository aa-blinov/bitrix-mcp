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
        order: Optional[str] = None,
        limit: int = 50
    ) -> str:
        """
        Get projects (workgroups) from Bitrix24.
        
        Args:
            filter_params: JSON string with filter conditions (e.g., '{"ACTIVE": "Y"}')
            order: JSON string with order conditions (e.g., '{"NAME": "ASC"}')
            limit: Maximum number of projects to return (default: 50)
        
        Returns:
            JSON string with projects data
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else None
            order_dict = json.loads(order) if order else None
            
            params = {}
            if filter_dict:
                params["FILTER"] = filter_dict
            if order_dict:
                params["ORDER"] = order_dict

            # Avoid passing empty dictionaries that fast_bitrix24 rejects
            call_params = params if params else None

            # Get projects (using sonet_group methods for workgroups)
            projects = await self.client.client.call("sonet_group.get", call_params)
            
            # Limit results
            if limit > 0 and projects and isinstance(projects[0], list):
                projects[0] = projects[0][:limit]
            
            result = {
                "success": True,
                "count": len(projects[0]) if projects and isinstance(projects[0], list) else 0,
                "projects": projects[0] if projects else []
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
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
            
            return json.dumps({
                "success": True,
                "project_id": result[0] if result else None,
                "message": "Project created successfully"
            })
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
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
            result = await self.client.client.call("sonet_group.update", {
                "GROUP_ID": project_id,
                **fields_dict
            })
            
            success = bool(result[0]) if result else False
            
            return json.dumps({
                "success": success,
                "project_id": project_id,
                "message": "Project updated successfully" if success else "Failed to update project"
            })
            
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
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
            # Get tasks for project
            tasks = await self.client.client.call("tasks.task.list", {
                "filter": {"GROUP_ID": project_id}
            })
            
            # Limit results
            if limit > 0 and tasks and isinstance(tasks[0], dict) and "tasks" in tasks[0]:
                tasks[0]["tasks"] = tasks[0]["tasks"][:limit]
            
            result = {
                "success": True,
                "project_id": project_id,
                "count": len(tasks[0].get("tasks", [])) if tasks and isinstance(tasks[0], dict) else 0,
                "tasks": tasks[0].get("tasks", []) if tasks and isinstance(tasks[0], dict) else []
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting project tasks for {project_id}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    @beartype
    async def add_project_member(self, project_id: str, user_id: str, role: str = "member") -> str:
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
            result = await self.client.client.call("sonet_group.user.add", {
                "GROUP_ID": project_id,
                "USER_ID": user_id,
                "ROLE": role
            })
            
            success = bool(result[0]) if result else False
            
            return json.dumps({
                "success": success,
                "project_id": project_id,
                "user_id": user_id,
                "role": role,
                "message": "Member added successfully" if success else "Failed to add member"
            })
            
        except Exception as e:
            logger.error(f"Error adding member to project {project_id}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
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
            # Get project members
            members = await self.client.client.call("sonet_group.user.get", {
                "GROUP_ID": project_id
            })
            
            result = {
                "success": True,
                "project_id": project_id,
                "members": members[0] if members else []
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting project members for {project_id}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })