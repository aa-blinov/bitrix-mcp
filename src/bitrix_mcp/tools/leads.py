"""Bitrix24 Leads tools for MCP server."""

import json
import logging
from typing import Any, Optional

from beartype import beartype

from ..client import BitrixClient

logger = logging.getLogger(__name__)


class LeadTools:
    """Tools for managing Bitrix24 leads."""

    def __init__(self, client: BitrixClient):
        """Initialize lead tools with Bitrix client."""
        self.client = client

    @beartype
    async def get_leads(
        self,
        filter_params: Optional[str] = None,
        select_fields: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Get leads from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"STATUS_ID": "NEW"}')
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,NAME,EMAIL')
            limit: Maximum number of leads to return (default: 50)

        Returns:
            JSON string with leads data

        Note:
            ORDER parameter is not supported because the underlying API uses
            automatic pagination which is incompatible with custom ordering.
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else None
            select_list = select_fields.split(",") if select_fields else None

            # Get leads (using get_all which handles pagination automatically)
            leads = await self.client.get_leads(
                filter_params=filter_dict, select_fields=select_list
            )

            # Limit results
            if limit > 0:
                leads = leads[:limit]

            result = {"success": True, "count": len(leads), "leads": leads}

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting leads: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def create_lead(self, fields: str) -> str:
        """
        Create a new lead in Bitrix24.

        Args:
            fields: JSON string with lead fields (e.g., '{"TITLE": "New Lead", "NAME": "John", "EMAIL": [{"VALUE": "john@example.com", "VALUE_TYPE": "WORK"}]}')

        Returns:
            JSON string with creation result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Create lead
            result = await self.client.create_lead(fields_dict)

            return json.dumps(
                {
                    "success": True,
                    "lead_id": result.get("result"),
                    "message": "Lead created successfully",
                }
            )

        except Exception as e:
            logger.error(f"Error creating lead: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def update_lead(self, lead_id: str, fields: str) -> str:
        """
        Update an existing lead in Bitrix24.

        Args:
            lead_id: Lead ID to update
            fields: JSON string with fields to update (e.g., '{"TITLE": "Updated Lead", "STATUS_ID": "IN_PROCESS"}')

        Returns:
            JSON string with update result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Update lead
            success = await self.client.update_lead(lead_id, fields_dict)

            return json.dumps(
                {
                    "success": success,
                    "lead_id": lead_id,
                    "message": (
                        "Lead updated successfully"
                        if success
                        else "Failed to update lead"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error updating lead {lead_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_lead(self, lead_id: str) -> str:
        """
        Get a lead by ID from Bitrix24.

        Args:
            lead_id: Lead ID to retrieve

        Returns:
            JSON string with lead data
        """
        try:
            # Get lead
            lead = await self.client.get_lead(lead_id)

            if lead:
                return json.dumps(
                    {"success": True, "lead": lead}, ensure_ascii=False, indent=2
                )
            else:
                return json.dumps(
                    {"success": False, "error": f"Lead with ID {lead_id} not found"}
                )

        except Exception as e:
            logger.error(f"Error getting lead {lead_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_lead_fields(self) -> str:
        """
        Get available lead fields from Bitrix24.

        Returns:
            JSON string with field definitions
        """
        try:
            # Get field definitions
            raw_fields = await self.client.client.call("crm.lead.fields")
            payload: Any
            if isinstance(raw_fields, list):
                payload = raw_fields[0] if raw_fields else {}
            else:
                payload = raw_fields or {}
            if isinstance(payload, dict):
                fields = payload.get("result", payload)
            else:
                fields = payload

            return json.dumps(
                {"success": True, "fields": fields}, ensure_ascii=False, indent=2
            )

        except Exception as e:
            logger.error(f"Error getting lead fields: {e}")
            return json.dumps({"success": False, "error": str(e)})
