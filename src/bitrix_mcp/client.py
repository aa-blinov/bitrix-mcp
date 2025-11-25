"""Bitrix24 client wrapper for MCP server."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, Union

from beartype import beartype
from fast_bitrix24 import BitrixAsync

from .config import BitrixConfig

logger = logging.getLogger(__name__)

JSONDict = dict[str, Any]
JSONList = list[JSONDict]


class BitrixClient:
    """Wrapper around fast_bitrix24 client with MCP-specific functionality."""

    def __init__(self, config: BitrixConfig):
        """Initialize the Bitrix24 client."""
        self.config = config
        self._client: Optional[BitrixAsync] = None

    async def __aenter__(self) -> "BitrixClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self):
        """Initialize connection to Bitrix24."""
        try:
            if self.config.webhook_url:
                # Use webhook URL
                self._client = BitrixAsync(
                    webhook=self.config.webhook_url,
                    respect_velocity_policy=self.config.respect_velocity_policy,
                    requests_per_second=self.config.requests_per_second,
                    request_pool_size=self.config.request_pool_size,
                    ssl=self.config.ssl_verify,
                )
            elif self.config.access_token and self.config.portal_url:
                # Use OAuth token via static token provider
                async def _static_token() -> str:
                    return self.config.access_token

                portal_base = self.config.portal_url.rstrip("/") + "/rest/"

                self._client = BitrixAsync(
                    webhook=portal_base,
                    token_func=_static_token,
                    respect_velocity_policy=self.config.respect_velocity_policy,
                    requests_per_second=self.config.requests_per_second,
                    request_pool_size=self.config.request_pool_size,
                    ssl=self.config.ssl_verify,
                )
            else:
                raise ValueError("Invalid Bitrix24 configuration")

            logger.info("Connected to Bitrix24")

        except Exception as e:
            logger.error(f"Failed to connect to Bitrix24: {e}")
            raise

    async def disconnect(self):
        """Clean up connection."""
        if self._client:
            # Note: fast_bitrix24 doesn't have explicit disconnect method
            # The session will be cleaned up automatically
            self._client = None
            logger.info("Disconnected from Bitrix24")

    @property
    def client(self) -> BitrixAsync:
        """Get the underlying Bitrix24 client."""
        if not self._client:
            raise RuntimeError(
                "Client not connected. Use 'async with' or call connect() first."
            )
        return self._client

    # Generic method for any API call
    @beartype
    async def get_all(self, method: str, params: Optional[JSONDict] = None) -> JSONList:
        """Generic method to get all items from any Bitrix24 API method."""
        return await self.client.get_all(method, params=params or {})

    # CRM Methods

    @beartype
    async def get_leads(
        self,
        filter_params: Optional[JSONDict] = None,
        select_fields: Optional[list[str]] = None,
        order: Optional[JSONDict] = None,
        start: int = 0,
    ) -> JSONList:
        """Get leads from Bitrix24."""
        params = {
            "start": start,
        }

        if filter_params:
            params["filter"] = filter_params
        if select_fields:
            params["select"] = select_fields
        if order:
            params["order"] = order

        return await self.client.get_all("crm.lead.list", params=params)

    @beartype
    async def create_lead(self, fields: JSONDict) -> JSONDict:
        """Create a new lead."""
        result = await self.client.call("crm.lead.add", {"fields": fields})
        return result[0] if result else {}

    @beartype
    async def update_lead(self, lead_id: Union[str, int], fields: JSONDict) -> bool:
        """Update an existing lead."""
        result = await self.client.call(
            "crm.lead.update", {"id": lead_id, "fields": fields}
        )
        return bool(result[0]) if result else False

    @beartype
    async def get_lead(self, lead_id: Union[str, int]) -> Optional[JSONDict]:
        """Get a lead by ID."""
        result = await self.client.call("crm.lead.get", {"id": lead_id})
        return result[0] if result else None

    @beartype
    async def get_deals(
        self,
        filter_params: Optional[JSONDict] = None,
        select_fields: Optional[list[str]] = None,
        order: Optional[JSONDict] = None,
        start: int = 0,
    ) -> JSONList:
        """Get deals from Bitrix24."""
        params = {
            "start": start,
        }

        if filter_params:
            params["filter"] = filter_params
        if select_fields:
            params["select"] = select_fields
        if order:
            params["order"] = order

        return await self.client.get_all("crm.deal.list", params=params)

    @beartype
    async def create_deal(self, fields: JSONDict) -> JSONDict:
        """Create a new deal."""
        result = await self.client.call("crm.deal.add", {"fields": fields})
        return result[0] if result else {}

    @beartype
    async def update_deal(self, deal_id: Union[str, int], fields: JSONDict) -> bool:
        """Update an existing deal."""
        result = await self.client.call(
            "crm.deal.update", {"id": deal_id, "fields": fields}
        )
        return bool(result[0]) if result else False

    @beartype
    async def get_deal(self, deal_id: Union[str, int]) -> Optional[JSONDict]:
        """Get a deal by ID."""
        result = await self.client.call("crm.deal.get", {"id": deal_id})
        return result[0] if result else None

    @beartype
    async def get_contacts(
        self,
        filter_params: Optional[JSONDict] = None,
        select_fields: Optional[list[str]] = None,
        order: Optional[JSONDict] = None,
        start: int = 0,
    ) -> JSONList:
        """Get contacts from Bitrix24."""
        params = {
            "start": start,
        }

        if filter_params:
            params["filter"] = filter_params
        if select_fields:
            params["select"] = select_fields
        if order:
            params["order"] = order

        return await self.client.get_all("crm.contact.list", params=params)

    @beartype
    async def create_contact(self, fields: JSONDict) -> JSONDict:
        """Create a new contact."""
        result = await self.client.call("crm.contact.add", {"fields": fields})
        return result[0] if result else {}

    @beartype
    async def update_contact(
        self, contact_id: Union[str, int], fields: JSONDict
    ) -> bool:
        """Update an existing contact."""
        result = await self.client.call(
            "crm.contact.update", {"id": contact_id, "fields": fields}
        )
        return bool(result[0]) if result else False

    @beartype
    async def get_contact(self, contact_id: Union[str, int]) -> Optional[JSONDict]:
        """Get a contact by ID."""
        result = await self.client.call("crm.contact.get", {"id": contact_id})
        return result[0] if result else None

    @beartype
    async def get_companies(
        self,
        filter_params: Optional[JSONDict] = None,
        select_fields: Optional[list[str]] = None,
        order: Optional[JSONDict] = None,
        start: int = 0,
    ) -> JSONList:
        """Get companies from Bitrix24."""
        params = {
            "start": start,
        }

        if filter_params:
            params["filter"] = filter_params
        if select_fields:
            params["select"] = select_fields
        if order:
            params["order"] = order

        return await self.client.get_all("crm.company.list", params=params)

    @beartype
    async def create_company(self, fields: JSONDict) -> JSONDict:
        """Create a new company."""
        result = await self.client.call("crm.company.add", {"fields": fields})
        return result[0] if result else {}

    @beartype
    async def update_company(
        self, company_id: Union[str, int], fields: JSONDict
    ) -> bool:
        """Update an existing company."""
        result = await self.client.call(
            "crm.company.update", {"id": company_id, "fields": fields}
        )
        return bool(result[0]) if result else False

    @beartype
    async def get_company(self, company_id: Union[str, int]) -> Optional[JSONDict]:
        """Get a company by ID."""
        result = await self.client.call("crm.company.get", {"id": company_id})
        return result[0] if result else None

    # Task Methods

    @beartype
    async def get_tasks(
        self,
        filter_params: Optional[JSONDict] = None,
        select_fields: Optional[list[str]] = None,
        order: Optional[JSONDict] = None,
        start: int = 0,
    ) -> JSONList:
        """Get tasks from Bitrix24."""
        params = {
            "start": start,
        }

        if filter_params:
            params["filter"] = filter_params
        if select_fields:
            params["select"] = select_fields
        if order:
            params["order"] = order

        return await self.client.get_all("tasks.task.list", params=params)

    @beartype
    async def create_task(self, fields: JSONDict) -> JSONDict:
        """Create a new task."""
        result = await self.client.call("tasks.task.add", {"fields": fields})
        return result[0] if result else {}

    @beartype
    async def update_task(self, task_id: Union[str, int], fields: JSONDict) -> bool:
        """Update an existing task."""
        result = await self.client.call(
            "tasks.task.update", {"taskId": task_id, "fields": fields}
        )
        return bool(result[0]) if result else False

    @beartype
    async def complete_task(self, task_id: Union[str, int]) -> bool:
        """Complete a task."""
        result = await self.client.call("tasks.task.complete", {"taskId": task_id})
        return bool(result[0]) if result else False

    @beartype
    async def get_task(self, task_id: Union[str, int]) -> Optional[JSONDict]:
        """Get a task by ID."""
        result = await self.client.call("tasks.task.get", {"taskId": task_id})
        return result[0] if result else None

    @beartype
    async def approve_task(self, task_id: Union[str, int]) -> bool:
        """Approve a task."""
        result = await self.client.call("tasks.task.approve", {"taskId": task_id})
        return bool(result[0]) if result else False

    @beartype
    async def start_task(self, task_id: Union[str, int]) -> bool:
        """Start a task."""
        result = await self.client.call("tasks.task.start", {"taskId": task_id})
        return bool(result[0]) if result else False

    @beartype
    async def delegate_task(
        self, task_id: Union[str, int], user_id: Union[str, int]
    ) -> bool:
        """Delegate a task to another user."""
        result = await self.client.call(
            "tasks.task.delegate", {"taskId": task_id, "userId": user_id}
        )
        return bool(result[0]) if result else False

    @beartype
    async def renew_task(self, task_id: Union[str, int]) -> bool:
        """Renew a task."""
        result = await self.client.call("tasks.task.renew", {"taskId": task_id})
        return bool(result[0]) if result else False

    @beartype
    async def start_watching_task(self, task_id: Union[str, int]) -> bool:
        """Start watching a task."""
        result = await self.client.call("tasks.task.startwatch", {"taskId": task_id})
        return bool(result[0]) if result else False

    @beartype
    async def disapprove_task(self, task_id: Union[str, int]) -> bool:
        """Disapprove a task."""
        result = await self.client.call("tasks.task.disapprove", {"taskId": task_id})
        return bool(result[0]) if result else False

    # Calendar Methods

    @beartype
    async def get_calendar_events(
        self,
        filter_params: Optional[JSONDict] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> JSONList:
        """Get calendar events from Bitrix24."""
        params = filter_params or {}

        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to

        result = await self.client.call("calendar.event.get", params)
        return result[0] if result and isinstance(result[0], list) else []

    @beartype
    async def create_calendar_event(self, fields: JSONDict) -> JSONDict:
        """Create a new calendar event."""
        result = await self.client.call("calendar.event.add", fields)
        return result[0] if result else {}

    @beartype
    async def update_calendar_event(
        self, event_id: Union[str, int], fields: JSONDict
    ) -> bool:
        """Update an existing calendar event."""
        fields["id"] = event_id
        result = await self.client.call("calendar.event.update", fields)
        return bool(result[0]) if result else False

    @beartype
    async def delete_calendar_event(self, event_id: Union[str, int]) -> bool:
        """Delete a calendar event."""
        result = await self.client.call("calendar.event.delete", {"id": event_id})
        return bool(result[0]) if result else False

    @beartype
    async def get_calendar_event_by_id(
        self, event_id: Union[str, int]
    ) -> Optional[JSONDict]:
        """Get a calendar event by ID."""
        result = await self.client.call("calendar.event.getbyid", {"id": event_id})
        return result[0] if result else None

    @beartype
    async def get_nearest_calendar_events(
        self,
        calendar_type: Optional[str] = None,
        owner_id: Optional[Union[str, int]] = None,
        days: int = 60,
        for_current_user: bool = True,
        max_events_count: Optional[int] = None,
        detail_url: Optional[str] = None,
    ) -> JSONList:
        """Get nearest calendar events from Bitrix24."""
        params = {}

        if calendar_type:
            params["type"] = calendar_type
        if owner_id is not None:
            params["ownerId"] = owner_id
        if days != 60:
            params["days"] = days
        if not for_current_user:
            params["forCurrentUser"] = for_current_user
        if max_events_count:
            params["maxEventsCount"] = max_events_count
        if detail_url:
            params["detailUrl"] = detail_url

        result = await self.client.call("calendar.event.get.nearest", params)
        return result[0] if result and isinstance(result[0], list) else []

    @beartype
    async def get_meeting_status(self, event_id: Union[str, int]) -> Optional[str]:
        """Get meeting participation status for current user."""
        result = await self.client.call(
            "calendar.meeting.status.get", {"eventId": event_id}
        )
        return result[0] if result else None

    @beartype
    async def set_meeting_status(self, event_id: Union[str, int], status: str) -> bool:
        """Set meeting participation status for current user."""
        result = await self.client.call(
            "calendar.meeting.status.set", {"eventId": event_id, "status": status}
        )
        return bool(result[0]) if result else False

    # Project (Workgroup) Methods

    @beartype
    async def get_projects(
        self, filter_params: Optional[JSONDict] = None, order: Optional[JSONDict] = None
    ) -> JSONList:
        """Get projects (workgroups) from Bitrix24."""
        params = {}

        if filter_params:
            params["filter"] = filter_params
        if order:
            params["order"] = order

        result = await self.client.call("sonet_group.get", params)
        return result[0] if result and isinstance(result[0], list) else []

    @beartype
    async def create_project(self, fields: JSONDict) -> JSONDict:
        """Create a new project (workgroup)."""
        result = await self.client.call("sonet_group.create", fields)
        return result[0] if result else {}

    @beartype
    async def update_project(
        self, project_id: Union[str, int], fields: JSONDict
    ) -> bool:
        """Update an existing project."""
        params = {"GROUP_ID": project_id, **fields}
        result = await self.client.call("sonet_group.update", params)
        return bool(result[0]) if result else False

    @beartype
    async def expel_project_member(
        self, project_id: Union[str, int], user_id: Union[str, int]
    ) -> bool:
        """Remove a member from a project (workgroup)."""
        params = {"GROUP_ID": project_id, "USER_ID": user_id}
        result = await self.client.call("sonet_group.user.expel", params)
        return bool(result[0]) if result else False

    @beartype
    async def request_join_project(
        self, project_id: Union[str, int], message: Optional[str] = None
    ) -> bool:
        """Send a request to join a project (workgroup)."""
        params = {"GROUP_ID": project_id}
        if message:
            params["MESSAGE"] = message
        result = await self.client.call("sonet_group.user.request", params)
        return bool(result[0]) if result else False

    @beartype
    async def invite_project_member(
        self,
        project_id: Union[str, int],
        user_id: Union[str, int],
        message: Optional[str] = None,
    ) -> bool:
        """Invite a user to join a project (workgroup)."""
        params = {"GROUP_ID": project_id, "USER_ID": user_id}
        if message:
            params["MESSAGE"] = message
        result = await self.client.call("sonet_group.user.invite", params)
        return bool(result[0]) if result else False


@asynccontextmanager
async def get_bitrix_client(config: BitrixConfig) -> AsyncIterator[BitrixClient]:
    """Get a connected Bitrix24 client as an async context manager."""
    client = BitrixClient(config)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()
