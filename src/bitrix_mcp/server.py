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
from .tools import CompanyTools, ContactTools, DealTools, LeadTools, TaskTools, CalendarTools, ProjectTools

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
            project_tools=project_tools
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
    mcp = BitrixFastMCP(
        name=mcp_config.server_name,
        lifespan=app_lifespan
    )

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
                    type(context)
                )
        app_ctx = getattr(mcp, "_app_context", None)
        if app_ctx is None:
            raise RuntimeError("Bitrix24 application context is not initialized")
        return cast(AppContext, app_ctx)
    
    # Lead tools
    @register_tool(
        "Get Leads",
        "List Bitrix24 leads filtered, ordered, and limited via optional parameters."
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
            filter_params or None,
            select_fields or None,
            order or None,
            limit
        )
    
    @register_tool(
        "Create Lead",
        "Create a Bitrix24 lead using a JSON payload with field values."
    )
    async def create_lead(fields: str, *, context: Context) -> str:
        """
        Create a new lead in Bitrix24.
        
        Args:
            fields: JSON string with lead fields (e.g., '{"TITLE": "New Lead", "NAME": "John", "EMAIL": [{"VALUE": "john@example.com", "VALUE_TYPE": "WORK"}]}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.create_lead(fields)
    
    @register_tool(
        "Update Lead",
        "Update fields of an existing Bitrix24 lead."
    )
    async def update_lead(lead_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing lead in Bitrix24.
        
        Args:
            lead_id: Lead ID to update
            fields: JSON string with fields to update (e.g., '{"TITLE": "Updated Lead", "STATUS_ID": "IN_PROCESS"}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.update_lead(lead_id, fields)
    
    @register_tool(
        "Get Lead Fields",
        "Retrieve metadata about available Bitrix24 lead fields."
    )
    async def get_lead_fields(*, context: Context) -> str:
        """Get available lead fields from Bitrix24."""
        app_ctx = _get_app_context(context)
        return await app_ctx.lead_tools.get_lead_fields()
    
    # Deal tools
    @register_tool(
        "Get Deals",
        "List Bitrix24 deals with optional filters, selection, ordering, and limits."
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
            filter_params or None,
            select_fields or None,
            order or None,
            limit
        )
    
    @register_tool(
        "Create Deal",
        "Create a Bitrix24 deal from the provided JSON field map."
    )
    async def create_deal(fields: str, *, context: Context) -> str:
        """
        Create a new deal in Bitrix24.
        
        Args:
            fields: JSON string with deal fields (e.g., '{"TITLE": "New Deal", "OPPORTUNITY": 10000, "CURRENCY_ID": "RUB"}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.create_deal(fields)
    
    @register_tool(
        "Update Deal",
        "Update fields on an existing Bitrix24 deal."
    )
    async def update_deal(deal_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing deal in Bitrix24.
        
        Args:
            deal_id: Deal ID to update
            fields: JSON string with fields to update (e.g., '{"STAGE_ID": "WON", "CLOSEDATE": "2024-01-15"}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.update_deal(deal_id, fields)
    
    @register_tool(
        "Get Deal Fields",
        "Retrieve metadata describing Bitrix24 deal fields."
    )
    async def get_deal_fields(*, context: Context) -> str:
        """Get available deal fields from Bitrix24."""
        app_ctx = _get_app_context(context)
        return await app_ctx.deal_tools.get_deal_fields()
    
    # Contact tools
    @register_tool(
        "Get Contacts",
        "List Bitrix24 contacts using optional filters, selected fields, and ordering."
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
            filter_params or None,
            select_fields or None,
            order or None,
            limit
        )
    
    @register_tool(
        "Create Contact",
        "Create a Bitrix24 contact from the supplied JSON field map."
    )
    async def create_contact(fields: str, *, context: Context) -> str:
        """
        Create a new contact in Bitrix24.
        
        Args:
            fields: JSON string with contact fields (e.g., '{"NAME": "John", "LAST_NAME": "Doe", "EMAIL": [{"VALUE": "john@example.com", "VALUE_TYPE": "WORK"}]}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.create_contact(fields)
    
    @register_tool(
        "Update Contact",
        "Update fields for an existing Bitrix24 contact."
    )
    async def update_contact(contact_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing contact in Bitrix24.
        
        Args:
            contact_id: Contact ID to update
            fields: JSON string with fields to update (e.g., '{"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.update_contact(contact_id, fields)
    
    @register_tool(
        "Get Contact Fields",
        "Retrieve metadata about Bitrix24 contact fields."
    )
    async def get_contact_fields(*, context: Context) -> str:
        """Get available contact fields from Bitrix24."""
        app_ctx = _get_app_context(context)
        return await app_ctx.contact_tools.get_contact_fields()
    
    # Company tools
    @register_tool(
        "Get Companies",
        "List Bitrix24 companies with optional filters, selected fields, and ordering."
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
            filter_params or None,
            select_fields or None,
            order or None,
            limit
        )
    
    @register_tool(
        "Create Company",
        "Create a Bitrix24 company record from JSON field values."
    )
    async def create_company(fields: str, *, context: Context) -> str:
        """
        Create a new company in Bitrix24.
        
        Args:
            fields: JSON string with company fields (e.g., '{"TITLE": "ACME Corp", "EMAIL": [{"VALUE": "info@acme.com", "VALUE_TYPE": "WORK"}]}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.create_company(fields)
    
    @register_tool(
        "Update Company",
        "Update fields of an existing Bitrix24 company."
    )
    async def update_company(company_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing company in Bitrix24.
        
        Args:
            company_id: Company ID to update
            fields: JSON string with fields to update (e.g., '{"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.update_company(company_id, fields)
    
    @register_tool(
        "Get Company Fields",
        "Retrieve metadata for Bitrix24 company fields."
    )
    async def get_company_fields(*, context: Context) -> str:
        """Get available company fields from Bitrix24."""
        app_ctx = _get_app_context(context)
        return await app_ctx.company_tools.get_company_fields()
    
    # Task tools
    @register_tool(
        "Get Tasks",
        "List Bitrix24 tasks using optional filters, selected fields, ordering, and limits."
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
            filter_params or None,
            select_fields or None,
            order or None,
            limit
        )
    
    @register_tool(
        "Create Task",
        "Create a Bitrix24 task from a JSON payload."
    )
    async def create_task(fields: str, *, context: Context) -> str:
        """
        Create a new task in Bitrix24.
        
        Args:
            fields: JSON string with task fields (e.g., '{"TITLE": "New Task", "DESCRIPTION": "Task description", "RESPONSIBLE_ID": 1}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.create_task(fields)
    
    @register_tool(
        "Update Task",
        "Update fields on an existing Bitrix24 task."
    )
    async def update_task(task_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing task in Bitrix24.
        
        Args:
            task_id: Task ID to update
            fields: JSON string with fields to update (e.g., '{"STATUS": "5", "MARK": "P"}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.update_task(task_id, fields)
    
    @register_tool(
        "Complete Task",
        "Mark a Bitrix24 task as completed."
    )
    async def complete_task(task_id: str, *, context: Context) -> str:
        """
        Complete a task in Bitrix24.
        
        Args:
            task_id: Task ID to complete
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.complete_task(task_id)
    
    @register_tool(
        "Get Task Fields",
        "Retrieve metadata about Bitrix24 task fields."
    )
    async def get_task_fields(*, context: Context) -> str:
        """Get available task fields from Bitrix24."""
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.get_task_fields()
    
    # Calendar tools
    @register_tool(
        "Get Calendar Events",
        "List Bitrix24 calendar events with optional filters and date boundaries."
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
            filter_params: JSON string with filter conditions
            date_from: Start date for events (YYYY-MM-DD format)
            date_to: End date for events (YYYY-MM-DD format)
            limit: Maximum number of events to return (default: 50)
            sections: JSON string or comma-separated list of calendar section IDs
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
        "Create a Bitrix24 calendar event from JSON fields."
    )
    async def create_calendar_event(fields: str, *, context: Context) -> str:
        """
        Create a new calendar event in Bitrix24.
        
        Args:
            fields: JSON string with event fields (e.g., '{"NAME": "Meeting", "DATE_FROM": "2024-01-15 10:00:00", "DATE_TO": "2024-01-15 11:00:00"}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.create_event(fields)
    
    @register_tool(
        "Update Calendar Event",
        "Update fields on an existing Bitrix24 calendar event."
    )
    async def update_calendar_event(event_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing calendar event in Bitrix24.
        
        Args:
            event_id: Event ID to update
            fields: JSON string with fields to update
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.update_event(event_id, fields)
    
    @register_tool(
        "Delete Calendar Event",
        "Delete a Bitrix24 calendar event by its identifier."
    )
    async def delete_calendar_event(event_id: str, *, context: Context) -> str:
        """
        Delete a calendar event in Bitrix24.
        
        Args:
            event_id: Event ID to delete
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.delete_event(event_id)
    
    @register_tool(
        "Get Calendar List",
        "Retrieve the list of Bitrix24 calendars available to the integration."
    )
    async def get_calendar_list(
        filter_params: str = "",
        *,
        context: Context,
    ) -> str:
        """Get available calendars from Bitrix24."""
        app_ctx = _get_app_context(context)
        return await app_ctx.calendar_tools.get_calendar_list(filter_params or None)
    
    # Project tools
    @register_tool(
        "Get Projects",
        "List Bitrix24 projects (workgroups) with optional filtering, ordering, and limits."
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
            filter_params: JSON string with filter conditions (e.g., '{"ACTIVE": "Y"}')
            order: JSON string with order conditions (e.g., '{"NAME": "ASC"}')
            limit: Maximum number of projects to return (default: 50)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.get_projects(
            filter_params or None,
            order or None,
            limit
        )
    
    @register_tool(
        "Create Project",
        "Create a Bitrix24 project (workgroup) using JSON field data."
    )
    async def create_project(fields: str, *, context: Context) -> str:
        """
        Create a new project (workgroup) in Bitrix24.
        
        Args:
            fields: JSON string with project fields (e.g., '{"NAME": "New Project", "DESCRIPTION": "Project description"}')
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.create_project(fields)
    
    @register_tool(
        "Update Project",
        "Update fields for an existing Bitrix24 project."
    )
    async def update_project(project_id: str, fields: str, *, context: Context) -> str:
        """
        Update an existing project in Bitrix24.
        
        Args:
            project_id: Project ID to update
            fields: JSON string with fields to update
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.update_project(project_id, fields)
    
    @register_tool(
        "Get Project Tasks",
        "List tasks associated with a Bitrix24 project."
    )
    async def get_project_tasks(project_id: str, limit: int = 50, *, context: Context) -> str:
        """
        Get tasks for a specific project.
        
        Args:
            project_id: Project ID
            limit: Maximum number of tasks to return
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.get_project_tasks(project_id, limit)
    
    @register_tool(
        "Add Project Member",
        "Add a user to a Bitrix24 project with an optional role."
    )
    async def add_project_member(project_id: str, user_id: str, role: str = "member", *, context: Context) -> str:
        """
        Add a member to a project.
        
        Args:
            project_id: Project ID
            user_id: User ID to add
            role: Role for the user (member, moderator, etc.)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.add_project_member(project_id, user_id, role)
    
    @register_tool(
        "Get Project Members",
        "Retrieve members of a Bitrix24 project."
    )
    async def get_project_members(project_id: str, *, context: Context) -> str:
        """
        Get members of a project.
        
        Args:
            project_id: Project ID
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.get_project_members(project_id)
    
    return mcp


def main() -> None:
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="Bitrix24 MCP Server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
    
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