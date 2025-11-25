"""Main MCP server for Bitrix24 integration."""

import argparse
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Optional, cast

from mcp.server.fastmcp import Context, FastMCP


if not hasattr(FastMCP, "request_context"):

    def _legacy_request_context(self: FastMCP):
        context = self.get_context()
        return context.request_context

    FastMCP.request_context = property(_legacy_request_context)  # type: ignore[attr-defined]

from .client import BitrixClient, get_bitrix_client
from .config import get_config
from .tools import (
    CompanyTools,
    ContactTools,
    DealTools,
    LeadTools,
    TaskTools,
    CalendarTools,
    ProjectTools,
)

# Module-level logger; configured in main()
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    """Application context with Bitrix client and tools."""

    client: BitrixClient
    lead_tools: LeadTools
    deal_tools: DealTools
    contact_tools: ContactTools
    company_tools: CompanyTools
    task_tools: TaskTools
    calendar_tools: CalendarTools
    project_tools: ProjectTools


class BitrixFastMCP(FastMCP):
    """FastMCP subclass exposing legacy request_context attribute for compatibility."""

    @property
    def request_context(self):  # type: ignore[override]
        context = super().get_context()
        return context.request_context


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with Bitrix24 client."""
    # Load configuration
    bitrix_config, mcp_config = get_config()

    # Initialize Bitrix client
    async with get_bitrix_client(bitrix_config) as client:
        logger.info("Bitrix24 client connected")

        # Initialize tools
        lead_tools = LeadTools(client)
        deal_tools = DealTools(client)
        contact_tools = ContactTools(client)
        company_tools = CompanyTools(client)
        task_tools = TaskTools(client)
        calendar_tools = CalendarTools(client)
        project_tools = ProjectTools(client)

        # Create application context
        app_context = AppContext(
            client=client,
            lead_tools=lead_tools,
            deal_tools=deal_tools,
            contact_tools=contact_tools,
            company_tools=company_tools,
            task_tools=task_tools,
            calendar_tools=calendar_tools,
            project_tools=project_tools,
        )
        # expose application context on server for tool access when request context is unavailable
        setattr(server, "_app_context", app_context)

        try:
            yield app_context
        finally:
            if hasattr(server, "_app_context"):
                delattr(server, "_app_context")
            logger.info("Shutting down Bitrix24 MCP server")


def create_server() -> FastMCP:
    """Create and configure the MCP server."""
    # Load configuration
    _, mcp_config = get_config()

    # Create FastMCP server
    mcp = BitrixFastMCP(name=mcp_config.server_name, lifespan=app_lifespan)

    def register_tool(title: str, description: str):
        """Wrap FastMCP.tool with consistent title/description metadata."""
        return mcp.tool(title=title, description=description)

    def _get_app_context(context: Optional[Context] = None) -> AppContext:
        """Safely resolve the Bitrix24 application context for a tool call."""
        if context is not None:
            try:
                return cast(AppContext, context.request_context.lifespan_context)
            except (AttributeError, ValueError):
                # Fall back to the server-level context if request-scoped context is unavailable
                logger.debug(
                    "Falling back to server app context; request context unavailable (received %s)",
                    type(context),
                )
        app_ctx = getattr(mcp, "_app_context", None)
        if app_ctx is None:
            raise RuntimeError("Bitrix24 application context is not initialized")
        return cast(AppContext, app_ctx)

    # Lead tools
    @register_tool(
        "Get Leads",
        "Retrieve Bitrix24 leads with optional JSON filters (e.g., status, date), comma-separated field selection, JSON ordering, and result limit.",
    )
    async def get_leads(
        filter_params: str = "",
        select_fields: str = "",
        order: str = "",
        limit: int = 50,
        *,
        context: Context,
    ) -> str:
        """
        Get leads from Bitrix24 CRM.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"STATUS_ID": "NEW"}')
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,NAME,EMAIL')
            order: JSON string with order conditions (e.g., '{"DATE_CREATE": "DESC"}')
            limit: Maximum number of leads to return (default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.get_leads(
            filter_params or None, select_fields or None, order or None, limit
        )

    @register_tool(
        "Create Lead",
        'Create a Bitrix24 lead using a JSON payload with field values. Required: TITLE. Optional: NAME, LAST_NAME, STATUS_ID, ASSIGNED_BY_ID, CURRENCY_ID, OPPORTUNITY, PHONE array, EMAIL array, etc. Example: \'{"TITLE": "ИП Титов", "NAME": "Глеб", "LAST_NAME": "Титов", "STATUS_ID": "NEW", "ASSIGNED_BY_ID": 1, "CURRENCY_ID": "USD", "OPPORTUNITY": 12500, "PHONE": [{"VALUE": "555888", "VALUE_TYPE": "WORK"}], "EMAIL": [{"VALUE": "gleb@example.com", "VALUE_TYPE": "WORK"}]}\'',
    )
    async def create_lead(fields: str, *, context: Context) -> str:
        """
        Create a new lead in Bitrix24.

        Args:
            fields: JSON string with lead fields (required: TITLE; optional: NAME, LAST_NAME, STATUS_ID, ASSIGNED_BY_ID, CURRENCY_ID, OPPORTUNITY, PHONE array, EMAIL array, etc.). Example: '{"TITLE": "ИП Титов", "NAME": "Глеб", "LAST_NAME": "Титов", "STATUS_ID": "NEW", "ASSIGNED_BY_ID": 1, "CURRENCY_ID": "USD", "OPPORTUNITY": 12500, "PHONE": [{"VALUE": "555888", "VALUE_TYPE": "WORK"}], "EMAIL": [{"VALUE": "gleb@example.com", "VALUE_TYPE": "WORK"}]}'

        Returns:
            JSON string with creation result including lead ID
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.create_lead(fields)

    @register_tool(
        "Update Lead",
        "Update fields of an existing Bitrix24 lead by ID with JSON field values.",
    )
    async def update_lead(lead_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing lead in Bitrix24.

        Args:
            lead_id: Lead ID to update (required)
            fields: JSON string with fields to update (optional: TITLE, NAME, LAST_NAME, STATUS_ID, ASSIGNED_BY_ID, CURRENCY_ID, OPPORTUNITY, PHONE array, EMAIL array, etc.). Example: '{"STATUS_ID": "IN_PROCESS", "OPPORTUNITY": 15000}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.update_lead(lead_id, fields)

    @register_tool(
        "Get Lead Fields", "Retrieve metadata about available Bitrix24 lead fields."
    )
    async def get_lead_fields(*, context: Context) -> str:
        """
        Get available lead fields from Bitrix24.

        Returns:
            JSON string with field metadata (field types, requirements, etc.)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.get_lead_fields()

    @register_tool(
        "Get Lead",
        "Retrieve a single Bitrix24 lead by its ID.",
    )
    async def get_lead(lead_id: str, *, context: Context) -> str:
        """
        Get a lead by ID from Bitrix24.

        Args:
            lead_id: Lead ID to retrieve (required)

        Returns:
            JSON string with lead data
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.get_lead(lead_id)

    # Deal tools
    @register_tool(
        "Get Deals",
        "List Bitrix24 deals with optional JSON filters (e.g., stage, opportunity), comma-separated field selection, JSON ordering, and result limit.",
    )
    async def get_deals(
        filter_params: str = "",
        select_fields: str = "",
        order: str = "",
        limit: int = 50,
        *,
        context: Context,
    ) -> str:
        """
        Get deals from Bitrix24 CRM.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"STAGE_ID": "NEW"}')
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,OPPORTUNITY,STAGE_ID')
            order: JSON string with order conditions (e.g., '{"DATE_CREATE": "DESC"}')
            limit: Maximum number of deals to return (default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.get_deals(
            filter_params or None, select_fields or None, order or None, limit
        )

    @register_tool(
        "Create Deal",
        'Create a Bitrix24 deal from JSON field map. Optional: TITLE, TYPE_ID, CATEGORY_ID, STAGE_ID, CURRENCY_ID, OPPORTUNITY, COMPANY_ID, CONTACT_IDS array, etc. Example: \'{"TITLE": "Новая сделка #1", "TYPE_ID": "COMPLEX", "CATEGORY_ID": 0, "STAGE_ID": "PREPARATION", "CURRENCY_ID": "EUR", "OPPORTUNITY": 1000000, "COMPANY_ID": 9, "CONTACT_IDS": [84, 83]}\'',
    )
    async def create_deal(fields: str, *, context: Context) -> str:
        """
        Create a new deal in Bitrix24.

        Args:
            fields: JSON string with deal fields (optional: TITLE, TYPE_ID, CATEGORY_ID, STAGE_ID, CURRENCY_ID, OPPORTUNITY, COMPANY_ID, CONTACT_IDS array, etc.). Example: '{"TITLE": "Новая сделка #1", "TYPE_ID": "COMPLEX", "CATEGORY_ID": 0, "STAGE_ID": "PREPARATION", "CURRENCY_ID": "EUR", "OPPORTUNITY": 1000000, "COMPANY_ID": 9, "CONTACT_IDS": [84, 83]}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.create_deal(fields)

    @register_tool(
        "Update Deal",
        "Update fields on an existing Bitrix24 deal by ID with JSON field values.",
    )
    async def update_deal(deal_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing deal in Bitrix24.

        Args:
            deal_id: Deal ID to update (required)
            fields: JSON string with fields to update (optional: TITLE, TYPE_ID, CATEGORY_ID, STAGE_ID, CURRENCY_ID, OPPORTUNITY, COMPANY_ID, CONTACT_IDS array, etc.). Example: '{"STAGE_ID": "WON", "CLOSEDATE": "2024-01-15"}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.update_deal(deal_id, fields)

    @register_tool(
        "Get Deal Fields", "Retrieve metadata describing Bitrix24 deal fields."
    )
    async def get_deal_fields(*, context: Context) -> str:
        """
        Get available deal fields from Bitrix24.

        Returns:
            JSON string with field metadata (field types, requirements, etc.)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.get_deal_fields()

    @register_tool(
        "Get Deal",
        "Retrieve a single Bitrix24 deal by its ID.",
    )
    async def get_deal(deal_id: str, *, context: Context) -> str:
        """
        Get a deal by ID from Bitrix24.

        Args:
            deal_id: Deal ID to retrieve (required)

        Returns:
            JSON string with deal data
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.get_deal(deal_id)

    # Contact tools
    @register_tool(
        "Get Contacts",
        "List Bitrix24 contacts with optional JSON filters (e.g., has email), comma-separated field selection, JSON ordering, and result limit.",
    )
    async def get_contacts(
        filter_params: str = "",
        select_fields: str = "",
        order: str = "",
        limit: int = 50,
        *,
        context: Context,
    ) -> str:
        """
        Get contacts from Bitrix24 CRM.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"HAS_EMAIL": "Y"}')
            select_fields: Comma-separated field names (e.g., 'ID,NAME,LAST_NAME,EMAIL,PHONE')
            order: JSON string with order conditions (e.g., '{"DATE_CREATE": "DESC"}')
            limit: Maximum number of contacts to return (default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.get_contacts(
            filter_params or None, select_fields or None, order or None, limit
        )

    @register_tool(
        "Create Contact",
        'Create a Bitrix24 contact from JSON field map. Optional: NAME, LAST_NAME, HONORIFIC, TYPE_ID, SOURCE_ID, POST, PHONE array, EMAIL array, COMPANY_ID, etc. Example: \'{"NAME": "Иван", "LAST_NAME": "Иванов", "HONORIFIC": "HNR_RU_1", "TYPE_ID": "PARTNER", "SOURCE_ID": "WEB", "POST": "Администратор", "PHONE": [{"VALUE": "+7333333555", "VALUE_TYPE": "WORK"}], "EMAIL": [{"VALUE": "ivanov@example.work", "VALUE_TYPE": "WORK"}], "COMPANY_ID": 12}\'',
    )
    async def create_contact(fields: str, *, context: Context) -> str:
        """
        Create a new contact in Bitrix24.

        Args:
            fields: JSON string with contact fields (optional: NAME, LAST_NAME, HONORIFIC, TYPE_ID, SOURCE_ID, POST, PHONE array, EMAIL array, COMPANY_ID, etc.). Example: '{"NAME": "Иван", "LAST_NAME": "Иванов", "HONORIFIC": "HNR_RU_1", "TYPE_ID": "PARTNER", "SOURCE_ID": "WEB", "POST": "Администратор", "PHONE": [{"VALUE": "+7333333555", "VALUE_TYPE": "WORK"}], "EMAIL": [{"VALUE": "ivanov@example.work", "VALUE_TYPE": "WORK"}], "COMPANY_ID": 12}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.create_contact(fields)

    @register_tool(
        "Update Contact",
        "Update fields for an existing Bitrix24 contact by ID with JSON field values.",
    )
    async def update_contact(contact_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing contact in Bitrix24.

        Args:
            contact_id: Contact ID to update (required)
            fields: JSON string with fields to update (required: at least one field; optional: NAME, LAST_NAME, HONORIFIC, TYPE_ID, SOURCE_ID, POST, PHONE array, EMAIL array, COMPANY_ID, etc.). Example: '{"PHONE": [{"VALUE": "+35599888666", "VALUE_TYPE": "HOME"}]}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.update_contact(contact_id, fields)

    @register_tool(
        "Get Contact Fields", "Retrieve metadata about Bitrix24 contact fields."
    )
    async def get_contact_fields(*, context: Context) -> str:
        """
        Get available contact fields from Bitrix24.

        Returns:
            JSON string with field metadata (field types, requirements, etc.)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.get_contact_fields()

    @register_tool(
        "Get Contact",
        "Retrieve a single Bitrix24 contact by its ID.",
    )
    async def get_contact(contact_id: str, *, context: Context) -> str:
        """
        Get a contact by ID from Bitrix24.

        Args:
            contact_id: Contact ID to retrieve (required)

        Returns:
            JSON string with contact data
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.get_contact(contact_id)

    # Company tools
    @register_tool(
        "Get Companies",
        "List Bitrix24 companies with optional JSON filters (e.g., has email), comma-separated field selection, JSON ordering, and result limit.",
    )
    async def get_companies(
        filter_params: str = "",
        select_fields: str = "",
        order: str = "",
        limit: int = 50,
        *,
        context: Context,
    ) -> str:
        """
        Get companies from Bitrix24 CRM.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"HAS_EMAIL": "Y"}')
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,EMAIL,PHONE')
            order: JSON string with order conditions (e.g., '{"DATE_CREATE": "DESC"}')
            limit: Maximum number of companies to return (default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.get_companies(
            filter_params or None, select_fields or None, order or None, limit
        )

    @register_tool(
        "Create Company",
        'Create a Bitrix24 company record from JSON field values. Required: TITLE. Optional: COMPANY_TYPE, INDUSTRY, EMPLOYEES, CURRENCY_ID, REVENUE, PHONE array, EMAIL array, etc. Example: \'{"TITLE": "ИП Титов", "COMPANY_TYPE": "CUSTOMER", "INDUSTRY": "MANUFACTURING", "EMPLOYEES": "EMPLOYEES_2", "CURRENCY_ID": "RUB", "REVENUE": 3000000, "PHONE": [{"VALUE": "555888", "VALUE_TYPE": "WORK"}]}\'',
    )
    async def create_company(fields: str, *, context: Context) -> str:
        """
        Create a new company in Bitrix24.

        Args:
            fields: JSON string with company fields (required: TITLE; optional: COMPANY_TYPE, INDUSTRY, EMPLOYEES, CURRENCY_ID, REVENUE, PHONE array, EMAIL array, etc.). Example: '{"TITLE": "ИП Титов", "COMPANY_TYPE": "CUSTOMER", "INDUSTRY": "MANUFACTURING", "EMPLOYEES": "EMPLOYEES_2", "CURRENCY_ID": "RUB", "REVENUE": 3000000, "PHONE": [{"VALUE": "555888", "VALUE_TYPE": "WORK"}]}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.create_company(fields)

    @register_tool(
        "Update Company",
        "Update fields of an existing Bitrix24 company by ID with JSON field values.",
    )
    async def update_company(company_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing company in Bitrix24.

        Args:
            company_id: Company ID to update (required)
            fields: JSON string with fields to update (required: at least one field; optional: TITLE, COMPANY_TYPE, INDUSTRY, EMPLOYEES, CURRENCY_ID, REVENUE, PHONE array, EMAIL array, etc.). Example: '{"PHONE": [{"VALUE": "555999", "VALUE_TYPE": "WORK"}]}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.update_company(company_id, fields)

    @register_tool(
        "Get Company Fields", "Retrieve metadata for Bitrix24 company fields."
    )
    async def get_company_fields(*, context: Context) -> str:
        """
        Get available company fields from Bitrix24.

        Returns:
            JSON string with field metadata (field types, requirements, etc.)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.get_company_fields()

    @register_tool(
        "Get Company",
        "Retrieve a single Bitrix24 company by its ID.",
    )
    async def get_company(company_id: str, *, context: Context) -> str:
        """
        Get a company by ID from Bitrix24.

        Args:
            company_id: Company ID to retrieve (required)

        Returns:
            JSON string with company data
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.get_company(company_id)

    # Task tools
    @register_tool(
        "Get Tasks",
        "List Bitrix24 tasks with optional JSON filters (e.g., status, responsible), comma-separated field selection, JSON ordering, and result limit.",
    )
    async def get_tasks(
        filter_params: str = "",
        select_fields: str = "",
        order: str = "",
        limit: int = 50,
        *,
        context: Context,
    ) -> str:
        """
        Get tasks from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"STATUS": "2"}' for in progress)
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,DESCRIPTION,STATUS,RESPONSIBLE_ID')
            order: JSON string with order conditions (e.g., '{"CREATED_DATE": "DESC"}')
            limit: Maximum number of tasks to return (default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.get_tasks(
            filter_params or None, select_fields or None, order or None, limit
        )

    @register_tool(
        "Create Task",
        'Create a Bitrix24 task from JSON payload. Required: TITLE, RESPONSIBLE_ID. Optional: DESCRIPTION, DEADLINE, PRIORITY, etc. Example: \'{"TITLE": "Подготовить отчет", "RESPONSIBLE_ID": 1, "DESCRIPTION": "Отчет по продажам за квартал", "DEADLINE": "2024-12-31T23:59:59", "PRIORITY": "2"}\'',
    )
    async def create_task(fields: str, *, context: Context) -> str:
        """
        Create a new task in Bitrix24.

        Args:
            fields: JSON string with task fields (required: TITLE, RESPONSIBLE_ID; optional: DESCRIPTION, DEADLINE, PRIORITY, etc.). Example: '{"TITLE": "Подготовить отчет", "RESPONSIBLE_ID": 1, "DESCRIPTION": "Отчет по продажам за квартал", "DEADLINE": "2024-12-31T23:59:59", "PRIORITY": "2"}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.create_task(fields)

    @register_tool(
        "Update Task",
        "Update fields on an existing Bitrix24 task by ID with JSON field values like STATUS, MARK, DEADLINE, etc.",
    )
    async def update_task(task_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing task in Bitrix24.

        Args:
            task_id: Task ID to update (required)
            fields: JSON string with fields to update (required: at least one field; optional: TITLE, DESCRIPTION, RESPONSIBLE_ID, DEADLINE, PRIORITY, STATUS, etc.). Example: '{"STATUS": "5", "MARK": "P"}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.update_task(task_id, fields)

    @register_tool("Complete Task", "Mark a Bitrix24 task as completed.")
    async def complete_task(task_id: str, *, context: Context) -> str:
        """
        Complete a task in Bitrix24.

        Args:
            task_id: Task ID to complete (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.complete_task(task_id)

    @register_tool("Get Task Fields", "Retrieve metadata about Bitrix24 task fields.")
    async def get_task_fields(*, context: Context) -> str:
        """
        Get available task fields from Bitrix24.

        Returns:
            JSON string with field metadata (field types, requirements, etc.)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.get_task_fields()

    # Calendar tools
    @register_tool(
        "Get Calendar Events",
        "List Bitrix24 calendar events with optional JSON filters, date ranges (YYYY-MM-DD), calendar section IDs, and result limit.",
    )
    async def get_calendar_events(
        filter_params: str = "",
        date_from: str = "",
        date_to: str = "",
        limit: int = 50,
        sections: str = "",
        *,
        context: Context,
    ) -> str:
        """
        Get calendar events from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (optional)
            date_from: Start date for events (YYYY-MM-DD format, optional)
            date_to: End date for events (YYYY-MM-DD format, optional)
            limit: Maximum number of events to return (default: 50)
            sections: JSON string or comma-separated list of calendar section IDs (optional)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.get_events(
            filter_params or None,
            date_from or None,
            date_to or None,
            limit=limit,
            sections=sections or None,
        )

    @register_tool(
        "Create Calendar Event",
        'Create a Bitrix24 calendar event from JSON fields. Required: NAME, DATE_FROM. Optional: DATE_TO, SECTION, DESCRIPTION, etc. Example: \'{"type": "user", "ownerId": 2, "name": "New Event Name", "from": "2024-06-14", "to": "2024-06-14", "section": 5, "description": "Meeting description"}\'',
    )
    async def create_calendar_event(fields: str, *, context: Context) -> str:
        """
        Create a new calendar event in Bitrix24.

        Args:
            fields: JSON string with event fields (required: NAME, DATE_FROM; optional: DATE_TO, SECTION, DESCRIPTION, etc.). Example: '{"type": "user", "ownerId": 2, "name": "New Event Name", "from": "2024-06-14", "to": "2024-06-14", "section": 5, "description": "Meeting description"}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.create_event(fields)

    @register_tool(
        "Update Calendar Event",
        "Update fields on an existing Bitrix24 calendar event by ID with JSON field values.",
    )
    async def update_calendar_event(
        event_id: str, fields: str, *, context: Context
    ) -> str:
        """
        Update an existing calendar event in Bitrix24.

        Args:
            event_id: Event ID to update (required)
            fields: JSON string with fields to update (optional: NAME, DATE_FROM, DATE_TO, SECTION, DESCRIPTION, etc.). Example: '{"name": "Updated Event", "description": "Updated description"}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.update_event(event_id, fields)

    @register_tool(
        "Delete Calendar Event", "Delete a Bitrix24 calendar event by its identifier."
    )
    async def delete_calendar_event(event_id: str, *, context: Context) -> str:
        """
        Delete a calendar event in Bitrix24.

        Args:
            event_id: Event ID to delete (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.delete_event(event_id)

    @register_tool(
        "Get Calendar List",
        "Retrieve the list of Bitrix24 calendars with optional JSON filters (e.g., type: user/group, ownerId).",
    )
    async def get_calendar_list(
        filter_params: str = "",
        *,
        context: Context,
    ) -> str:
        """
        Get available calendars from Bitrix24.

        Args:
            filter_params: JSON string with filter parameters (optional, e.g., '{"type": "user", "ownerId": 1}')

        Returns:
            JSON string with list of calendars
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.get_calendar_list(filter_params or None)

    @register_tool(
        "Get Calendar Event by ID",
        "Retrieve detailed information about a specific Bitrix24 calendar event by its ID, including all properties, participants, and metadata.",
    )
    async def get_calendar_event_by_id(event_id: str, *, context: Context) -> str:
        """
        Get a calendar event by ID from Bitrix24.

        This method retrieves complete event information including participants, recurrence rules,
        CRM links, and file attachments.

        Args:
            event_id: Event ID to retrieve (required)

        Returns:
            JSON string with complete event data including:
            - Basic info: ID, NAME, DESCRIPTION, LOCATION
            - Dates: DATE_FROM, DATE_TO, TZ_FROM, TZ_TO, DT_SKIP_TIME
            - Participants: ATTENDEE_LIST, ATTENDEES_CODES, IS_MEETING, MEETING_STATUS
            - Recurrence: RRULE, EXDATE, RECURRENCE_ID
            - Metadata: CREATED_BY, DATE_CREATE, TIMESTAMP_X, PRIVATE_EVENT
            - CRM integration: UF_CRM_CAL_EVENT
            - Files: UF_WEBDAV_CAL_EVENT
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.get_event_by_id(event_id)

    @register_tool(
        "Get Nearest Calendar Events",
        "Retrieve upcoming Bitrix24 calendar events within a specified number of days for dashboards, notifications, or planning.",
    )
    async def get_nearest_calendar_events(
        calendar_type: str = "user",
        owner_id: str = "",
        days: int = 60,
        for_current_user: bool = True,
        max_events_count: int = 0,
        detail_url: str = "",
        *,
        context: Context,
    ) -> str:
        """
        Get nearest upcoming calendar events from Bitrix24.

        Useful for displaying upcoming events in dashboards or sending notifications.

        Args:
            calendar_type: Type of calendar to search (optional, default: "user")
                         - "user" - user calendar
                         - "group" - group calendar
                         - "company_calendar" - company calendar
            owner_id: Owner ID of the calendar (optional)
                     - For user calendar: user ID
                     - For group calendar: group ID
                     - For company calendar: usually 0 or empty
            days: Number of days to look ahead (optional, default: 60)
            for_current_user: Get events for current user only (optional, default: true)
            max_events_count: Maximum events to return (optional, 0 = no limit)
            detail_url: Calendar detail URL template (optional)

        Returns:
            JSON string with list of upcoming events
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.get_nearest_events(
            calendar_type=calendar_type,
            owner_id=owner_id or None,
            days=days,
            for_current_user=for_current_user,
            max_events_count=max_events_count if max_events_count > 0 else None,
            detail_url=detail_url or None,
        )

    @register_tool(
        "Get Meeting Status",
        "Check the current user's participation status for a Bitrix24 calendar meeting event.",
    )
    async def get_meeting_status(event_id: str, *, context: Context) -> str:
        """
        Get the current user's participation status for a meeting event.

        Only works for events that are meetings (have participants).

        Args:
            event_id: Event ID to check status for (required)

        Returns:
            JSON string with participation status:
            - "Y" - Accepted (согласен)
            - "N" - Declined (отказался)
            - "Q" - Pending (приглашен, но еще не ответил)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.get_meeting_status(event_id)

    @register_tool(
        "Set Meeting Status",
        "Set the current user's participation status for a Bitrix24 calendar meeting event (accept, decline, or mark as pending).",
    )
    async def set_meeting_status(
        event_id: str, status: str, *, context: Context
    ) -> str:
        """
        Set the current user's participation status for a meeting event.

        Allows accepting, declining, or marking as pending participation in calendar meetings.

        Args:
            event_id: Event ID to set status for (required)
            status: Participation status (required):
                   - "Y" - Accept (принять)
                   - "N" - Decline (отклонить)
                   - "Q" - Mark as pending (отметить как ожидание ответа)

        Returns:
            JSON string with operation result
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.set_meeting_status(event_id, status)

    # Project tools
    @register_tool(
        "Get Projects",
        "List Bitrix24 projects (workgroups) with optional JSON filters (e.g., ACTIVE), JSON ordering, and result limit.",
    )
    async def get_projects(
        filter_params: str = "",
        order: str = "",
        limit: int = 50,
        *,
        context: Context,
    ) -> str:
        """
        Get projects (workgroups) from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (optional, e.g., '{"ACTIVE": "Y"}')
            order: JSON string with order conditions (optional, e.g., '{"NAME": "ASC"}')
            limit: Maximum number of projects to return (default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.get_projects(
            filter_params or None, order or None, limit
        )

    @register_tool(
        "Create Project",
        'Create a Bitrix24 project (workgroup) using JSON field data. Required: NAME. Optional: VISIBLE, OPENED, INITIATE_PERMS, DESCRIPTION, etc. Example: \'{"NAME": "Test sonet group", "VISIBLE": "Y", "OPENED": "N", "INITIATE_PERMS": "K", "DESCRIPTION": "Project description"}\'',
    )
    async def create_project(fields: str, *, context: Context) -> str:
        """
        Create a new project (workgroup) in Bitrix24.

        Args:
            fields: JSON string with project fields (required: NAME; optional: VISIBLE, OPENED, INITIATE_PERMS, DESCRIPTION, etc.). Example: '{"NAME": "Test sonet group", "VISIBLE": "Y", "OPENED": "N", "INITIATE_PERMS": "K", "DESCRIPTION": "Project description"}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.create_project(fields)

    @register_tool(
        "Update Project",
        "Update fields for an existing Bitrix24 project by ID with JSON field values.",
    )
    async def update_project(project_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing project in Bitrix24.

        Args:
            project_id: Project ID to update (required)
            fields: JSON string with fields to update (required: at least one field; optional: NAME, VISIBLE, OPENED, INITIATE_PERMS, DESCRIPTION, etc.). Example: '{"NAME": "Updated Project Name"}'
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.update_project(project_id, fields)

    @register_tool(
        "Get Project Tasks",
        "List tasks associated with a Bitrix24 project by project ID with optional result limit.",
    )
    async def get_project_tasks(
        project_id: str, limit: int = 50, *, context: Context
    ) -> str:
        """
        Get tasks for a specific project.

        Args:
            project_id: Project ID (required)
            limit: Maximum number of tasks to return (optional, default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.get_project_tasks(project_id, limit)

    @register_tool(
        "Add Project Member",
        "Add a user to a Bitrix24 project by project ID and user ID with optional role (member/moderator/etc.).",
    )
    async def add_project_member(
        project_id: str, user_id: str, role: str = "member", *, context: Context
    ) -> str:
        """
        Add a member to a project.

        Args:
            project_id: Project ID (required)
            user_id: User ID to add (required)
            role: Role for the user (optional, member/moderator/etc., default: member)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.add_project_member(project_id, user_id, role)

    @register_tool(
        "Get Project Members",
        "Retrieve members of a Bitrix24 project by project ID with their roles.",
    )
    async def get_project_members(project_id: str, *, context: Context) -> str:
        """
        Get members of a project.

        Args:
            project_id: Project ID (required)

        Returns:
            JSON string with list of project members and their roles
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.get_project_members(project_id)

    return mcp


def main() -> None:
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="Bitrix24 MCP Server")
    parser.add_argument(
        "--transport", choices=["stdio", "streamable-http", "sse"], default="stdio"
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="localhost")
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO"
    )

    args = parser.parse_args()

    # Configure logging respecting existing handlers
    log_level = getattr(logging, args.log_level)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=log_level)
    else:
        root_logger.setLevel(log_level)
        for handler in root_logger.handlers:
            handler.setLevel(log_level)
    logger.setLevel(log_level)

    # Create server
    mcp = create_server()

    if args.transport == "stdio":
        # Run with stdio transport
        mcp.run()
    elif args.transport in ["streamable-http", "sse"]:
        # Run with HTTP transport
        mcp.run(transport=args.transport, port=args.port, host=args.host)


if __name__ == "__main__":
    main()
