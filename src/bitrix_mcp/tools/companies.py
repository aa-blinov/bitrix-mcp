"""Bitrix24 Companies tools for MCP server."""

import json
import logging
from typing import Optional

from beartype import beartype

from ..client import BitrixClient

logger = logging.getLogger(__name__)


class CompanyTools:
    """Tools for managing Bitrix24 companies."""

    def __init__(self, client: BitrixClient):
        """Initialize company tools with Bitrix client."""
        self.client = client

    @beartype
    async def get_companies(
        self,
        filter_params: Optional[str] = None,
        select_fields: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Get companies from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"HAS_EMAIL": "Y"}')
            select_fields: Comma-separated field names (e.g., 'ID,TITLE,EMAIL,PHONE')
            limit: Maximum number of companies to return (default: 50)

        Returns:
            JSON string with companies data

        Note:
            ORDER parameter is not supported because the underlying API uses
            automatic pagination which is incompatible with custom ordering.
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else None
            select_list = select_fields.split(",") if select_fields else None

            # Get companies (using get_all which handles pagination automatically)
            companies = await self.client.get_companies(
                filter_params=filter_dict, select_fields=select_list
            )

            # Limit results
            if limit > 0:
                companies = companies[:limit]

            result = {"success": True, "count": len(companies), "companies": companies}

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting companies: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def create_company(self, fields: str) -> str:
        """
        Create a new company in Bitrix24.

        Args:
            fields: JSON string with company fields (e.g., '{"TITLE": "ACME Corp", "EMAIL": [{"VALUE": "info@acme.com", "VALUE_TYPE": "WORK"}]}')

        Returns:
            JSON string with creation result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Create company
            result = await self.client.create_company(fields_dict)

            return json.dumps(
                {
                    "success": True,
                    "company_id": result.get("result"),
                    "message": "Company created successfully",
                }
            )

        except Exception as e:
            logger.error(f"Error creating company: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def update_company(self, company_id: str, fields: str) -> str:
        """
        Update an existing company in Bitrix24.

        Args:
            company_id: Company ID to update
            fields: JSON string with fields to update (e.g., '{"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}')

        Returns:
            JSON string with update result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Update company
            success = await self.client.update_company(company_id, fields_dict)

            return json.dumps(
                {
                    "success": success,
                    "company_id": company_id,
                    "message": (
                        "Company updated successfully"
                        if success
                        else "Failed to update company"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error updating company {company_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_company(self, company_id: str) -> str:
        """
        Get a company by ID from Bitrix24.

        Args:
            company_id: Company ID to retrieve

        Returns:
            JSON string with company data
        """
        try:
            # Get company
            company = await self.client.get_company(company_id)

            if company:
                return json.dumps(
                    {"success": True, "company": company}, ensure_ascii=False, indent=2
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Company with ID {company_id} not found",
                    }
                )

        except Exception as e:
            logger.error(f"Error getting company {company_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_company_fields(self) -> str:
        """
        Get available company fields from Bitrix24.

        Returns:
            JSON string with field definitions
        """
        try:
            # Get field definitions
            raw_fields = await self.client.client.call("crm.company.fields")
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
            logger.error(f"Error getting company fields: {e}")
            return json.dumps({"success": False, "error": str(e)})
