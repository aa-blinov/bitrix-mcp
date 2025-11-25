"""Bitrix24 Contacts tools for MCP server."""

import json
import logging
from typing import Optional

from beartype import beartype

from ..client import BitrixClient

logger = logging.getLogger(__name__)


class ContactTools:
    """Tools for managing Bitrix24 contacts."""

    def __init__(self, client: BitrixClient):
        """Initialize contact tools with Bitrix client."""
        self.client = client

    @beartype
    async def get_contacts(
        self,
        filter_params: Optional[str] = None,
        select_fields: Optional[str] = None,
        order: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Get contacts from Bitrix24.

        Args:
            filter_params: JSON string with filter conditions (e.g., '{"HAS_EMAIL": "Y"}')
            select_fields: Comma-separated field names (e.g., 'ID,NAME,LAST_NAME,EMAIL,PHONE')
            order: JSON string with order conditions (e.g., '{"DATE_CREATE": "DESC"}')
            limit: Maximum number of contacts to return (default: 50)

        Returns:
            JSON string with contacts data
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else None
            select_list = select_fields.split(",") if select_fields else None
            order_dict = json.loads(order) if order else None

            # Get contacts
            contacts = await self.client.get_contacts(
                filter_params=filter_dict, select_fields=select_list, order=order_dict
            )

            # Limit results
            if limit > 0:
                contacts = contacts[:limit]

            result = {"success": True, "count": len(contacts), "contacts": contacts}

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def create_contact(self, fields: str) -> str:
        """
        Create a new contact in Bitrix24.

        Args:
            fields: JSON string with contact fields (e.g., '{"NAME": "John", "LAST_NAME": "Doe", "EMAIL": [{"VALUE": "john@example.com", "VALUE_TYPE": "WORK"}]}')

        Returns:
            JSON string with creation result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Create contact
            result = await self.client.create_contact(fields_dict)

            return json.dumps(
                {
                    "success": True,
                    "contact_id": result.get("result"),
                    "message": "Contact created successfully",
                }
            )

        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def update_contact(self, contact_id: str, fields: str) -> str:
        """
        Update an existing contact in Bitrix24.

        Args:
            contact_id: Contact ID to update
            fields: JSON string with fields to update (e.g., '{"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}')

        Returns:
            JSON string with update result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)

            # Update contact
            success = await self.client.update_contact(contact_id, fields_dict)

            return json.dumps(
                {
                    "success": success,
                    "contact_id": contact_id,
                    "message": (
                        "Contact updated successfully"
                        if success
                        else "Failed to update contact"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_contact(self, contact_id: str) -> str:
        """
        Get a contact by ID from Bitrix24.

        Args:
            contact_id: Contact ID to retrieve

        Returns:
            JSON string with contact data
        """
        try:
            # Get contact
            contact = await self.client.get_contact(contact_id)

            if contact:
                return json.dumps(
                    {"success": True, "contact": contact}, ensure_ascii=False, indent=2
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Contact with ID {contact_id} not found",
                    }
                )

        except Exception as e:
            logger.error(f"Error getting contact {contact_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_contact_fields(self) -> str:
        """
        Get available contact fields from Bitrix24.

        Returns:
            JSON string with field definitions
        """
        try:
            # Get field definitions
            raw_fields = await self.client.client.call("crm.contact.fields")
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
            logger.error(f"Error getting contact fields: {e}")
            return json.dumps({"success": False, "error": str(e)})
