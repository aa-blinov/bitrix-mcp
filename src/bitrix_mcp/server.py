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
    mcp = BitrixFastMCP(
        name=mcp_config.server_name,
        host=mcp_config.host,
        port=mcp_config.port,
        lifespan=app_lifespan,
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
                    type(context),
                )
        app_ctx = getattr(mcp, "_app_context", None)
        if app_ctx is None:
            raise RuntimeError("Bitrix24 application context is not initialized")
        return cast(AppContext, app_ctx)

    # Lead tools
    @register_tool(
        "Get Leads",
        'Retrieve Bitrix24 leads with optional filters.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter conditions (e.g., \'{"STATUS_ID": "NEW"}\')\n- select_fields: Comma-separated field names (e.g., \'ID,TITLE,NAME,EMAIL\')\n- order: JSON string with order conditions (e.g., \'{"DATE_CREATE": "DESC"}\')\n- limit: Maximum number of leads to return (default: 50)\n\n**Example request:** get_leads(filter_params=\'{"STATUS_ID": "NEW"}\', select_fields=\'ID,TITLE,NAME\', limit=10)\n\n**Returns:** JSON with leads data.',
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
        'Create a new Bitrix24 lead.\n\n**Required attributes:**\n- fields: JSON string with lead data (must include TITLE)\n\n**Optional attributes:** None\n\n**Example request:** create_lead(fields=\'{"TITLE": "ИП Титов", "NAME": "Глеб", "STATUS_ID": "NEW"}\')\n\n**Returns:** JSON with creation result including lead ID.',
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
        'Update an existing Bitrix24 lead.\n\n**Required attributes:**\n- lead_id: Lead ID to update\n- fields: JSON string with fields to update\n\n**Optional attributes:** None\n\n**Example request:** update_lead(lead_id="123", fields=\'{"STATUS_ID": "IN_PROCESS", "OPPORTUNITY": 15000}\')\n\n**Returns:** JSON with update result.',
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
        "Get Lead Fields",
        "Retrieve metadata about available Bitrix24 lead fields.\n\n**Required attributes:** None\n\n**Optional attributes:** None\n\n**Example request:** get_lead_fields()\n\n**Returns:** JSON with field metadata.",
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
        'Retrieve a single Bitrix24 lead by ID.\n\n**Required attributes:**\n- lead_id: Lead ID to retrieve\n\n**Optional attributes:** None\n\n**Example request:** get_lead(lead_id="123")\n\n**Returns:** JSON with lead data.',
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
        'List Bitrix24 deals with optional filters.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter conditions (e.g., \'{"STAGE_ID": "NEW"}\')\n- select_fields: Comma-separated field names (e.g., \'ID,TITLE,OPPORTUNITY,STAGE_ID\')\n- order: JSON string with order conditions (e.g., \'{"DATE_CREATE": "DESC"}\')\n- limit: Maximum number of deals to return (default: 50)\n\n**Example request:** get_deals(filter_params=\'{"STAGE_ID": "NEW"}\', select_fields=\'ID,TITLE,OPPORTUNITY\', limit=10)\n\n**Returns:** JSON with deals data.',
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
        'Create a new Bitrix24 deal.\n\n**Required attributes:**\n- fields: JSON string with deal data\n\n**Optional attributes:** None\n\n**Example request:** create_deal(fields=\'{"TITLE": "Новая сделка", "STAGE_ID": "PREPARATION", "OPPORTUNITY": 100000}\')\n\n**Returns:** JSON with creation result including deal ID.',
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
        'Update an existing Bitrix24 deal.\n\n**Required attributes:**\n- deal_id: Deal ID to update\n- fields: JSON string with fields to update\n\n**Optional attributes:** None\n\n**Example request:** update_deal(deal_id="123", fields=\'{"STAGE_ID": "WON", "CLOSEDATE": "2024-01-15"}\')\n\n**Returns:** JSON with update result.',
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
        "Get Deal Fields",
        "Retrieve metadata about available Bitrix24 deal fields.\n\n**Required attributes:** None\n\n**Optional attributes:** None\n\n**Example request:** get_deal_fields()\n\n**Returns:** JSON with field metadata.",
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
        'Retrieve a single Bitrix24 deal by ID.\n\n**Required attributes:**\n- deal_id: Deal ID to retrieve\n\n**Optional attributes:** None\n\n**Example request:** get_deal(deal_id="123")\n\n**Returns:** JSON with deal data.',
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
        'List Bitrix24 contacts with optional filters.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter conditions (e.g., \'{"HAS_EMAIL": "Y"}\')\n- select_fields: Comma-separated field names (e.g., \'ID,NAME,LAST_NAME,EMAIL,PHONE\')\n- order: JSON string with order conditions (e.g., \'{"DATE_CREATE": "DESC"}\')\n- limit: Maximum number of contacts to return (default: 50)\n\n**Example request:** get_contacts(filter_params=\'{"HAS_EMAIL": "Y"}\', select_fields=\'ID,NAME,EMAIL\', limit=10)\n\n**Returns:** JSON with contacts data.',
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
        'Create a new Bitrix24 contact.\n\n**Required attributes:**\n- fields: JSON string with contact data\n\n**Optional attributes:** None\n\n**Example request:** create_contact(fields=\'{"NAME": "Иван", "LAST_NAME": "Иванов", "EMAIL": [{"VALUE": "ivan@example.com", "VALUE_TYPE": "WORK"}]}\')\n\n**Returns:** JSON with creation result including contact ID.',
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
        'Update an existing Bitrix24 contact.\n\n**Required attributes:**\n- contact_id: Contact ID to update\n- fields: JSON string with fields to update\n\n**Optional attributes:** None\n\n**Example request:** update_contact(contact_id="123", fields=\'{"PHONE": [{"VALUE": "+35599888666", "VALUE_TYPE": "HOME"}]}\')\n\n**Returns:** JSON with update result.',
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
        "Get Contact Fields",
        "Retrieve metadata about available Bitrix24 contact fields.\n\n**Required attributes:** None\n\n**Optional attributes:** None\n\n**Example request:** get_contact_fields()\n\n**Returns:** JSON with field metadata.",
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
        'Retrieve a single Bitrix24 contact by ID.\n\n**Required attributes:**\n- contact_id: Contact ID to retrieve\n\n**Optional attributes:** None\n\n**Example request:** get_contact(contact_id="123")\n\n**Returns:** JSON with contact data.',
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
        'List Bitrix24 companies with optional filters.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter conditions (e.g., \'{"HAS_EMAIL": "Y"}\')\n- select_fields: Comma-separated field names (e.g., \'ID,TITLE,EMAIL,PHONE\')\n- order: JSON string with order conditions (e.g., \'{"DATE_CREATE": "DESC"}\')\n- limit: Maximum number of companies to return (default: 50)\n\n**Example request:** get_companies(filter_params=\'{"HAS_EMAIL": "Y"}\', select_fields=\'ID,TITLE,EMAIL\', limit=10)\n\n**Returns:** JSON with companies data.',
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
        'Create a new Bitrix24 company.\n\n**Required attributes:**\n- fields: JSON string with company data (must include TITLE)\n\n**Optional attributes:** None\n\n**Example request:** create_company(fields=\'{"TITLE": "ИП Титов", "COMPANY_TYPE": "CUSTOMER", "EMAIL": [{"VALUE": "info@company.com", "VALUE_TYPE": "WORK"}]}\')\n\n**Returns:** JSON with creation result including company ID.',
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
        'Update an existing Bitrix24 company.\n\n**Required attributes:**\n- company_id: Company ID to update\n- fields: JSON string with fields to update\n\n**Optional attributes:** None\n\n**Example request:** update_company(company_id="123", fields=\'{"PHONE": [{"VALUE": "555999", "VALUE_TYPE": "WORK"}]}\')\n\n**Returns:** JSON with update result.',
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
        "Get Company Fields",
        "Retrieve metadata about available Bitrix24 company fields.\n\n**Required attributes:** None\n\n**Optional attributes:** None\n\n**Example request:** get_company_fields()\n\n**Returns:** JSON with field metadata.",
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
        'Retrieve a single Bitrix24 company by ID.\n\n**Required attributes:**\n- company_id: Company ID to retrieve\n\n**Optional attributes:** None\n\n**Example request:** get_company(company_id="123")\n\n**Returns:** JSON with company data.',
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
        'List Bitrix24 tasks with optional filters.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter conditions (e.g., \'{"STATUS": "2"}\')\n- select_fields: Comma-separated field names (e.g., \'ID,TITLE,DESCRIPTION,STATUS,RESPONSIBLE_ID\')\n- order: JSON string with order conditions (e.g., \'{"CREATED_DATE": "DESC"}\')\n- limit: Maximum number of tasks to return (default: 50)\n\n**Example request:** get_tasks(filter_params=\'{"STATUS": "2"}\', select_fields=\'ID,TITLE,RESPONSIBLE_ID\', limit=10)\n\n**Returns:** JSON with tasks data.',
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
        'Create a new Bitrix24 task.\n\n**Required attributes:**\n- fields: JSON string with task data (must include TITLE and RESPONSIBLE_ID)\n\n**Optional attributes:** None\n\n**Example request:** create_task(fields=\'{"TITLE": "Подготовить отчет", "RESPONSIBLE_ID": 1, "DESCRIPTION": "Отчет по продажам", "DEADLINE": "2024-12-31T23:59:59"}\')\n\n**Returns:** JSON with creation result including task ID.',
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
        'Update an existing Bitrix24 task.\n\n**Required attributes:**\n- task_id: Task ID to update\n- fields: JSON string with fields to update\n\n**Optional attributes:** None\n\n**Example request:** update_task(task_id="123", fields=\'{"STATUS": "5", "MARK": "P"}\')\n\n**Returns:** JSON with update result.',
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

    @register_tool(
        "Complete Task",
        'Mark a Bitrix24 task as completed.\n\n**Required attributes:**\n- task_id: Task ID to complete\n\n**Optional attributes:** None\n\n**Example request:** complete_task(task_id="123")\n\n**Returns:** JSON with completion result.',
    )
    async def complete_task(task_id: str, *, context: Context) -> str:
        """
        Complete a task in Bitrix24.

        Args:
            task_id: Task ID to complete (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.complete_task(task_id)

    @register_tool(
        "Get Task Fields",
        "Retrieve metadata about available Bitrix24 task fields.\n\n**Required attributes:** None\n\n**Optional attributes:** None\n\n**Example request:** get_task_fields()\n\n**Returns:** JSON with field metadata.",
    )
    async def get_task_fields(*, context: Context) -> str:
        """
        Get available task fields from Bitrix24.

        Returns:
            JSON string with field metadata (field types, requirements, etc.)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.get_task_fields()

    @register_tool(
        "Get Task by ID",
        'Retrieve detailed information about a specific Bitrix24 task by ID.\n\n**Required attributes:**\n- task_id: Task ID to retrieve\n\n**Optional attributes:** None\n\n**Example request:** get_task_by_id(task_id="123")\n\n**Returns:** JSON with complete task data including title, description, status, responsible user, deadlines, and metadata.',
    )
    async def get_task_by_id(task_id: str, *, context: Context) -> str:
        """
        Get a task by ID from Bitrix24.

        This method retrieves complete task information including all fields and metadata.

        Args:
            task_id: Task ID to retrieve (required)

        Returns:
            JSON string with complete task data including:
            - Basic info: ID, TITLE, DESCRIPTION, STATUS, RESPONSIBLE_ID
            - Dates: CREATED_DATE, DEADLINE, START_DATE_PLAN, END_DATE_PLAN
            - Participants: CREATED_BY, RESPONSIBLE_ID, ACCOMPLICES, AUDITORS
            - Metadata: PRIORITY, MARK, GROUP_ID, PARENT_ID
            - Additional fields: UF_CRM_TASK, UF_TASK_WEBDAV_FILES
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.get_task(task_id)

    @register_tool(
        "Approve Task",
        'Approve a Bitrix24 task.\n\n**Required attributes:**\n- task_id: Task ID to approve\n\n**Optional attributes:** None\n\n**Example request:** approve_task(task_id="123")\n\n**Returns:** JSON with approval result.',
    )
    async def approve_task(task_id: str, *, context: Context) -> str:
        """
        Approve a task in Bitrix24.

        Args:
            task_id: Task ID to approve (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.approve_task(task_id)

    @register_tool(
        "Start Task",
        'Start a Bitrix24 task.\n\n**Required attributes:**\n- task_id: Task ID to start\n\n**Optional attributes:** None\n\n**Example request:** start_task(task_id="123")\n\n**Returns:** JSON with start result.',
    )
    async def start_task(task_id: str, *, context: Context) -> str:
        """
        Start a task in Bitrix24.

        Args:
            task_id: Task ID to start (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.start_task(task_id)

    @register_tool(
        "Delegate Task",
        'Delegate a Bitrix24 task to another user.\n\n**Required attributes:**\n- task_id: Task ID to delegate\n- user_id: User ID to delegate to\n\n**Optional attributes:** None\n\n**Example request:** delegate_task(task_id="123", user_id="456")\n\n**Returns:** JSON with delegation result.',
    )
    async def delegate_task(task_id: str, user_id: str, *, context: Context) -> str:
        """
        Delegate a task to another user in Bitrix24.

        Args:
            task_id: Task ID to delegate (required)
            user_id: User ID to delegate to (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.delegate_task(task_id, user_id)

    @register_tool(
        "Renew Task",
        'Renew a Bitrix24 task.\n\n**Required attributes:**\n- task_id: Task ID to renew\n\n**Optional attributes:** None\n\n**Example request:** renew_task(task_id="123")\n\n**Returns:** JSON with renewal result.',
    )
    async def renew_task(task_id: str, *, context: Context) -> str:
        """
        Renew a task in Bitrix24.

        Args:
            task_id: Task ID to renew (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.renew_task(task_id)

    @register_tool(
        "Start Watching Task",
        'Start watching a Bitrix24 task.\n\n**Required attributes:**\n- task_id: Task ID to start watching\n\n**Optional attributes:** None\n\n**Example request:** start_watching_task(task_id="123")\n\n**Returns:** JSON with watch result.',
    )
    async def start_watching_task(task_id: str, *, context: Context) -> str:
        """
        Start watching a task in Bitrix24.

        Args:
            task_id: Task ID to start watching (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.start_watching_task(task_id)

    @register_tool(
        "Disapprove Task",
        'Disapprove a Bitrix24 task.\n\n**Required attributes:**\n- task_id: Task ID to disapprove\n\n**Optional attributes:** None\n\n**Example request:** disapprove_task(task_id="123")\n\n**Returns:** JSON with disapproval result.',
    )
    async def disapprove_task(task_id: str, *, context: Context) -> str:
        """
        Disapprove a task in Bitrix24.

        Args:
            task_id: Task ID to disapprove (required)
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.task_tools.disapprove_task(task_id)

    # Calendar tools
    @register_tool(
        "Get Calendar Events",
        'List Bitrix24 calendar events with optional filters.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter conditions\n- date_from: Start date for events (YYYY-MM-DD format)\n- date_to: End date for events (YYYY-MM-DD format)\n- limit: Maximum number of events to return (default: 50)\n- sections: JSON string or comma-separated list of calendar section IDs\n\n**Example request:** get_calendar_events(date_from="2024-01-01", date_to="2024-01-31", limit=10)\n\n**Returns:** JSON with calendar events data.',
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
        'Create a new Bitrix24 calendar event.\n\n**Required attributes:**\n- fields: JSON string with event data (must include NAME and DATE_FROM)\n\n**Optional attributes:** None\n\n**Example request:** create_calendar_event(fields=\'{"type": "user", "ownerId": 2, "name": "New Event", "from": "2024-06-14", "to": "2024-06-14", "section": 5}\')\n\n**Returns:** JSON with creation result including event ID.',
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
        'Update an existing Bitrix24 calendar event.\n\n**Required attributes:**\n- event_id: Event ID to update\n- fields: JSON string with fields to update\n\n**Optional attributes:** None\n\n**Example request:** update_calendar_event(event_id="123", fields=\'{"name": "Updated Event", "description": "Updated description"}\')\n\n**Returns:** JSON with update result.',
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
        "Delete Calendar Event",
        'Delete a Bitrix24 calendar event by ID.\n\n**Required attributes:**\n- event_id: Event ID to delete\n\n**Optional attributes:** None\n\n**Example request:** delete_calendar_event(event_id="123")\n\n**Returns:** JSON with deletion result.',
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
        'Retrieve the list of Bitrix24 calendars.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter parameters (e.g., \'{"type": "user", "ownerId": 1}\')\n\n**Example request:** get_calendar_list(filter_params=\'{"type": "user", "ownerId": 1}\')\n\n**Returns:** JSON with list of calendars.',
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
        'Retrieve detailed information about a specific Bitrix24 calendar event by ID.\n\n**Required attributes:**\n- event_id: Event ID to retrieve\n\n**Optional attributes:** None\n\n**Example request:** get_calendar_event_by_id(event_id="123")\n\n**Returns:** JSON with complete event data including participants, recurrence rules, and metadata.',
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
        'Retrieve upcoming Bitrix24 calendar events within a specified number of days.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- calendar_type: Type of calendar to search (default: "user")\n- owner_id: Owner ID of the calendar\n- days: Number of days to look ahead (default: 60)\n- for_current_user: Get events for current user only (default: true)\n- max_events_count: Maximum events to return\n- detail_url: Calendar detail URL template\n\n**Example request:** get_nearest_calendar_events(calendar_type="user", days=30, max_events_count=10)\n\n**Returns:** JSON with list of upcoming events.',
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
        'Check the current user\'s participation status for a Bitrix24 calendar meeting event.\n\n**Required attributes:**\n- event_id: Event ID to check status for\n\n**Optional attributes:** None\n\n**Example request:** get_meeting_status(event_id="123")\n\n**Returns:** JSON with participation status ("Y", "N", or "Q").',
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
        'Set the current user\'s participation status for a Bitrix24 calendar meeting event.\n\n**Required attributes:**\n- event_id: Event ID to set status for\n- status: Participation status ("Y", "N", or "Q")\n\n**Optional attributes:** None\n\n**Example request:** set_meeting_status(event_id="123", status="Y")\n\n**Returns:** JSON with operation result.',
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
        'List Bitrix24 projects (workgroups) with optional filters.\n\n**Required attributes:** None\n\n**Optional attributes:**\n- filter_params: JSON string with filter conditions (e.g., \'{"ACTIVE": "Y"}\')\n- order: JSON string with order conditions (e.g., \'{"NAME": "ASC"}\')\n- limit: Maximum number of projects to return (default: 50)\n\n**Example request:** get_projects(filter_params=\'{"ACTIVE": "Y"}\', limit=10)\n\n**Returns:** JSON with projects data.',
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
        'Create a new Bitrix24 project (workgroup).\n\n**Required attributes:**\n- fields: JSON string with project data (must include NAME)\n\n**Optional attributes:** None\n\n**Example request:** create_project(fields=\'{"NAME": "Test Project", "VISIBLE": "Y", "DESCRIPTION": "Project description"}\')\n\n**Returns:** JSON with creation result including project ID.',
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
        'Update an existing Bitrix24 project.\n\n**Required attributes:**\n- project_id: Project ID to update\n- fields: JSON string with fields to update\n\n**Optional attributes:** None\n\n**Example request:** update_project(project_id="123", fields=\'{"NAME": "Updated Project Name"}\')\n\n**Returns:** JSON with update result.',
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
        'List tasks associated with a Bitrix24 project.\n\n**Required attributes:**\n- project_id: Project ID\n\n**Optional attributes:**\n- limit: Maximum number of tasks to return (default: 50)\n\n**Example request:** get_project_tasks(project_id="123", limit=10)\n\n**Returns:** JSON with project tasks data.',
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
        'Add a user to a Bitrix24 project.\n\n**Required attributes:**\n- project_id: Project ID\n- user_id: User ID to add\n\n**Optional attributes:**\n- role: Role for the user (default: "member")\n\n**Example request:** add_project_member(project_id="123", user_id="456", role="moderator")\n\n**Returns:** JSON with operation result.',
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
        'Retrieve members of a Bitrix24 project by ID.\n\n**Required attributes:**\n- project_id: Project ID\n\n**Optional attributes:** None\n\n**Example request:** get_project_members(project_id="123")\n\n**Returns:** JSON with list of project members and their roles.',
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

    @register_tool(
        "Expel Project Member",
        'Remove a user from a Bitrix24 project (workgroup).\n\n**Required attributes:**\n- project_id: Project ID from which to remove the member\n- user_id: User ID to remove from the project\n\n**Optional attributes:** None\n\n**Example request:** expel_project_member(project_id="123", user_id="456")\n\n**Returns:** JSON with success status, project_id, user_id, and confirmation message.',
    )
    async def expel_project_member(
        project_id: str, user_id: str, *, context: Context
    ) -> str:
        """
        Remove a member from a Bitrix24 project (workgroup).

        Args:
            project_id: Project ID from which to remove the member (required)
            user_id: User ID to remove from the project (required)

        Returns:
            JSON string with operation result

        Example:
            expel_project_member("123", "456")
            # Returns: {"success": true, "project_id": "123", "user_id": "456", "message": "Member expelled successfully"}
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.expel_project_member(project_id, user_id)

    @register_tool(
        "Request to Join Project",
        'Send a request to join a Bitrix24 project (workgroup).\n\n**Required attributes:**\n- project_id: Project ID to request joining\n\n**Optional attributes:**\n- message: Personal message to include with the request\n\n**Example request:** request_join_project(project_id="123", message="Please add me to the project")\n\n**Returns:** JSON with success status, project_id, request_message, and confirmation message.',
    )
    async def request_join_project(
        project_id: str, message: Optional[str] = None, *, context: Context
    ) -> str:
        """
        Send a request to join a Bitrix24 project (workgroup).

        Args:
            project_id: Project ID to request joining (required)
            message: Optional message to include with the request (optional)

        Returns:
            JSON string with operation result

        Example:
            request_join_project("123", "Please add me to the project")
            # Returns: {"success": true, "project_id": "123", "request_message": "Please add me to the project", "message": "Join request sent successfully"}
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.request_join_project(project_id, message)

    @register_tool(
        "Invite Project Member",
        'Invite a user to join a Bitrix24 project (workgroup).\n\n**Required attributes:**\n- project_id: Project ID to invite the user to\n- user_id: User ID to invite to the project\n\n**Optional attributes:**\n- message: Personal message to include with the invitation\n\n**Example request:** invite_project_member(project_id="123", user_id="456", message="We\'d like you to join our project")\n\n**Returns:** JSON with success status, project_id, user_id, invitation_message, and confirmation message.',
    )
    async def invite_project_member(
        project_id: str,
        user_id: str,
        message: Optional[str] = None,
        *,
        context: Context,
    ) -> str:
        """
        Invite a user to join a Bitrix24 project (workgroup).

        Args:
            project_id: Project ID to invite the user to (required)
            user_id: User ID to invite to the project (required)
            message: Optional personal message to include with the invitation (optional)

        Returns:
            JSON string with operation result

        Example:
            invite_project_member("123", "456", "We'd like you to join our project")
            # Returns: {"success": true, "project_id": "123", "user_id": "456", "invitation_message": "We'd like you to join our project", "message": "Invitation sent successfully"}
        """
        app_ctx = _get_app_context(context)
        return await app_ctx.project_tools.invite_project_member(
            project_id, user_id, message
        )

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
        mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
