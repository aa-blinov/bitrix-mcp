"""Bitrix24 Deals tools for MCP server."""

import json
import logging
from typing import Optional

from beartype import beartype

from ..client import BitrixClient

logger = logging.getLogger(__name__)


class DealTools:
    """Tools for managing Bitrix24 deals."""

    def __init__(self, client: BitrixClient):
        """Initialize deal tools with Bitrix client."""
        self.client = client

    @beartype
    async def get_deals(
        self,
        filter_params: Optional[str] = None,
        select_fields: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Get deals from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"STAGE_ID": "NEW"}')
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,OPPORTUNITY,STAGE_ID')
            limit: Maximum number of deals to return (default: 50)

        Returns:
            JSON string with deals data

        Note:
            ORDER parameter is not supported because the underlying API uses
            automatic pagination which is incompatible with custom ordering.
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else None
            select_list = select_fields.split(",") if select_fields else None

            # Get deals (using get_all which handles pagination automatically)
            deals = await self.client.get_deals(
                filter_params=filter_dict, select_fields=select_list
            )

            # Limit results
            if limit > 0:
                deals = deals[:limit]

            result = {"success": True, "count": len(deals), "deals": deals}

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def create_deal(self, fields: str) -> str:
        """
        Create a new deal in Bitrix24.

        Args:
            fields: JSON string with deal fields (e.g., '{"TITLE": "New Deal", "OPPORTUNITY": 10000, "CURRENCY_ID": "RUB"}')

        Returns:
            JSON string with creation result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Create deal
            result = await self.client.create_deal(fields_dict)

            return json.dumps(
                {
                    "success": True,
                    "deal_id": result.get("result"),
                    "message": "Deal created successfully",
                }
            )

        except Exception as e:
            logger.error(f"Error creating deal: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def update_deal(self, deal_id: str, fields: str) -> str:
        """
        Update an existing deal in Bitrix24.

        Args:
            deal_id: Deal ID to update
            fields: JSON string with fields to update (e.g., '{"STAGE_ID": "WON", "CLOSEDATE": "2024-01-15"}')

        Returns:
            JSON string with update result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Update deal
            success = await self.client.update_deal(deal_id, fields_dict)

            return json.dumps(
                {
                    "success": success,
                    "deal_id": deal_id,
                    "message": (
                        "Deal updated successfully"
                        if success
                        else "Failed to update deal"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error updating deal {deal_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_deal(self, deal_id: str) -> str:
        """
        Get a deal by ID from Bitrix24.

        Args:
            deal_id: Deal ID to retrieve

        Returns:
            JSON string with deal data
        """
        try:
            # Get deal
            deal = await self.client.get_deal(deal_id)

            if deal:
                return json.dumps(
                    {"success": True, "deal": deal}, ensure_ascii=False, indent=2
                )
            else:
                return json.dumps(
                    {"success": False, "error": f"Deal with ID {deal_id} not found"}
                )

        except Exception as e:
            logger.error(f"Error getting deal {deal_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_deal_fields(self) -> str:
        """
        Get available deal fields from Bitrix24.

        Returns:
            JSON string with field definitions
        """
        try:
            # Get field definitions
            raw_fields = await self.client.client.call("crm.deal.fields")
            payload = (
                raw_fields[0]
                if isinstance(raw_fields, list) and raw_fields
                else raw_fields or {}
            )
            if isinstance(payload, dict):
                fields = payload.get("result", payload)
            else:
                fields = payload

            return json.dumps(
                {"success": True, "fields": fields}, ensure_ascii=False, indent=2
            )

        except Exception as e:
            logger.error(f"Error getting deal fields: {e}")
            return json.dumps({"success": False, "error": str(e)})
