"""Bitrix24 Tasks tools for MCP server."""

import json
import logging
from typing import Any, Optional

from beartype import beartype

from ..client import BitrixClient

logger = logging.getLogger(__name__)


class TaskTools:
    """Tools for managing Bitrix24 tasks."""

    def __init__(self, client: BitrixClient):
        """Initialize task tools with Bitrix client."""
        self.client = client

    @beartype
    async def get_tasks(
        self,
        filter_params: Optional[str] = None,
        select_fields: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Get tasks from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"STATUS": "2"}' for in progress)
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,DESCRIPTION,STATUS,RESPONSIBLE_ID')
            limit: Maximum number of tasks to return (default: 50)

        Returns:
            JSON string with tasks data

        Note:
            ORDER parameter is not supported because the underlying API uses
            automatic pagination which is incompatible with custom ordering.
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else None
            select_list = select_fields.split(",") if select_fields else None

            # Get tasks (using get_tasks from client which uses get_all internally)
            tasks = await self.client.get_tasks(
                filter_params=filter_dict, select_fields=select_list
            )

            # Limit results
            if limit > 0:
                tasks = tasks[:limit]

            result = {"success": True, "count": len(tasks), "tasks": tasks}

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting tasks: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def create_task(self, fields: str) -> str:
        """
        Create a new task in Bitrix24.

        Args:
            fields: JSON string with task fields (e.g., '{"TITLE": "New Task", "DESCRIPTION": "Task description", "RESPONSIBLE_ID": 1}')

        Returns:
            JSON string with creation result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Create task
            result = await self.client.client.call(
                "tasks.task.add", {"fields": fields_dict}
            )

            return json.dumps(
                {
                    "success": True,
                    "task_id": (
                        result[0].get("result", {}).get("task", {}).get("id")
                        if result
                        else None
                    ),
                    "message": "Task created successfully",
                }
            )

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def update_task(self, task_id: str, fields: str) -> str:
        """
        Update an existing task in Bitrix24.

        Args:
            task_id: Task ID to update
            fields: JSON string with fields to update (e.g., '{"STATUS": "5", "MARK": "P"}')

        Returns:
            JSON string with update result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Update task
            result = await self.client.client.call(
                "tasks.task.update", {"taskId": task_id, "fields": fields_dict}
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "message": (
                        "Task updated successfully"
                        if success
                        else "Failed to update task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def complete_task(self, task_id: str) -> str:
        """
        Complete a task in Bitrix24.

        Args:
            task_id: Task ID to complete

        Returns:
            JSON string with completion result
        """
        try:
            # Complete task
            result = await self.client.client.call(
                "tasks.task.complete", {"taskId": task_id}
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "message": (
                        "Task completed successfully"
                        if success
                        else "Failed to complete task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error completing task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_task(self, task_id: str) -> str:
        """
        Get a task by ID from Bitrix24.

        Args:
            task_id: Task ID to retrieve

        Returns:
            JSON string with task data
        """
        try:
            # Get task
            task = self.client.get_task(task_id)

            if task:
                return json.dumps(
                    {"success": True, "task": task}, ensure_ascii=False, indent=2
                )
            else:
                return json.dumps(
                    {"success": False, "error": f"Task with ID {task_id} not found"}
                )

        except Exception as e:
            logger.error(f"Error getting task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def approve_task(self, task_id: str) -> str:
        """
        Approve a task in Bitrix24.

        Args:
            task_id: Task ID to approve

        Returns:
            JSON string with approval result
        """
        try:
            # Approve task
            result = self.client.client.call("tasks.task.approve", {"taskId": task_id})

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "message": (
                        "Task approved successfully"
                        if success
                        else "Failed to approve task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error approving task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def start_task(self, task_id: str) -> str:
        """
        Start a task in Bitrix24.

        Args:
            task_id: Task ID to start

        Returns:
            JSON string with start result
        """
        try:
            # Start task
            result = self.client.client.call("tasks.task.start", {"taskId": task_id})

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "message": (
                        "Task started successfully"
                        if success
                        else "Failed to start task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error starting task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def delegate_task(self, task_id: str, user_id: str) -> str:
        """
        Delegate a task to another user in Bitrix24.

        Args:
            task_id: Task ID to delegate
            user_id: User ID to delegate to

        Returns:
            JSON string with delegation result
        """
        try:
            # Delegate task
            result = self.client.client.call(
                "tasks.task.delegate", {"taskId": task_id, "userId": user_id}
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "user_id": user_id,
                    "message": (
                        "Task delegated successfully"
                        if success
                        else "Failed to delegate task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error delegating task {task_id} to user {user_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def renew_task(self, task_id: str) -> str:
        """
        Renew a task in Bitrix24.

        Args:
            task_id: Task ID to renew

        Returns:
            JSON string with renewal result
        """
        try:
            # Renew task
            result = self.client.client.call("tasks.task.renew", {"taskId": task_id})

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "message": (
                        "Task renewed successfully"
                        if success
                        else "Failed to renew task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error renewing task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def start_watching_task(self, task_id: str) -> str:
        """
        Start watching a task in Bitrix24.

        Args:
            task_id: Task ID to start watching

        Returns:
            JSON string with watch result
        """
        try:
            # Start watching task
            result = self.client.client.call(
                "tasks.task.startwatch", {"taskId": task_id}
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "message": (
                        "Started watching task successfully"
                        if success
                        else "Failed to start watching task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error starting to watch task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def disapprove_task(self, task_id: str) -> str:
        """
        Disapprove a task in Bitrix24.

        Args:
            task_id: Task ID to disapprove

        Returns:
            JSON string with disapproval result
        """
        try:
            # Disapprove task
            result = self.client.client.call(
                "tasks.task.disapprove", {"taskId": task_id}
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "task_id": task_id,
                    "message": (
                        "Task disapproved successfully"
                        if success
                        else "Failed to disapprove task"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error disapproving task {task_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})
