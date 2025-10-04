"""Bitrix24 Calendar tools for MCP server."""

import json
import logging
from typing import Optional

from beartype import beartype

from ..client import BitrixClient

logger = logging.getLogger(__name__)


class CalendarTools:
    """Tools for managing Bitrix24 calendar events."""
    
    def __init__(self, client: BitrixClient):
        """Initialize calendar tools with Bitrix client."""
        self.client = client
    
    @beartype
    async def get_events(
        self,
        filter_params: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 50,
        sections: Optional[str] = None,
    ) -> str:
        """
        Get calendar events from Bitrix24.
        
        Args:
            filter_params: JSON string with filter conditions
            date_from: Start date for events (YYYY-MM-DD format)
            date_to: End date for events (YYYY-MM-DD format)
            limit: Maximum number of events to return (default: 50)
            sections: JSON string or comma-separated list of calendar section IDs
        
        Returns:
            JSON string with events data
        """
        try:
            # Parse parameters
            filter_dict = json.loads(filter_params) if filter_params else {}

            def _normalize_sections(raw_value):
                if raw_value is None:
                    return []
                if isinstance(raw_value, list):
                    return raw_value
                if isinstance(raw_value, (int, float)):
                    return [int(raw_value)]
                if isinstance(raw_value, str):
                    try:
                        parsed_value = json.loads(raw_value)
                        if isinstance(parsed_value, list):
                            return parsed_value
                        return [parsed_value]
                    except json.JSONDecodeError:
                        items = [item.strip() for item in raw_value.split(",") if item.strip()]
                        normalized_items = []
                        for item in items:
                            if item.isdigit():
                                normalized_items.append(int(item))
                            else:
                                normalized_items.append(item)
                        return normalized_items
                return []

            # Merge section filters from filter_params and explicit sections argument
            section_values = []
            if "section" in filter_dict:
                section_values.extend(_normalize_sections(filter_dict["section"]))
            if sections:
                section_values.extend(_normalize_sections(sections))
            if section_values:
                # Deduplicate while preserving order
                seen = set()
                normalized_sections = []
                for section in section_values:
                    key = str(section)
                    if key not in seen:
                        seen.add(key)
                        normalized_sections.append(section)
                filter_dict["section"] = normalized_sections
            elif "section" in filter_dict:
                # Remove invalid section payload to avoid API errors
                filter_dict.pop("section")
            
            # Add date filters if provided
            if date_from:
                filter_dict["from"] = date_from
            if date_to:
                filter_dict["to"] = date_to
            
            # Get events
            events = await self.client.client.call("calendar.event.get", filter_dict)
            
            # Limit results
            if limit > 0 and events and isinstance(events[0], list):
                events[0] = events[0][:limit]
            
            result = {
                "success": True,
                "count": len(events[0]) if events and isinstance(events[0], list) else 0,
                "events": events[0] if events else []
            }
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting calendar events: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    @beartype
    async def create_event(self, fields: str) -> str:
        """
        Create a new calendar event in Bitrix24.
        
        Args:
            fields: JSON string with event fields (e.g., '{"NAME": "Meeting", "DATE_FROM": "2024-01-15 10:00:00", "DATE_TO": "2024-01-15 11:00:00"}')
        
        Returns:
            JSON string with creation result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)
            
            # Create event
            result = await self.client.client.call("calendar.event.add", fields_dict)
            
            return json.dumps({
                "success": True,
                "event_id": result[0] if result else None,
                "message": "Calendar event created successfully"
            })
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    @beartype
    async def update_event(self, event_id: str, fields: str) -> str:
        """
        Update an existing calendar event in Bitrix24.
        
        Args:
            event_id: Event ID to update
            fields: JSON string with fields to update
        
        Returns:
            JSON string with update result
        """
        try:
            # Parse fields
            fields_dict = json.loads(fields)
            fields_dict["id"] = event_id
            
            # Update event
            result = await self.client.client.call("calendar.event.update", fields_dict)
            
            success = bool(result[0]) if result else False
            
            return json.dumps({
                "success": success,
                "event_id": event_id,
                "message": "Calendar event updated successfully" if success else "Failed to update event"
            })
            
        except Exception as e:
            logger.error(f"Error updating calendar event {event_id}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    @beartype
    async def delete_event(self, event_id: str) -> str:
        """
        Delete a calendar event in Bitrix24.
        
        Args:
            event_id: Event ID to delete
        
        Returns:
            JSON string with deletion result
        """
        try:
            # Delete event
            result = await self.client.client.call("calendar.event.delete", {"id": event_id})
            
            success = bool(result[0]) if result else False
            
            return json.dumps({
                "success": success,
                "event_id": event_id,
                "message": "Calendar event deleted successfully" if success else "Failed to delete event"
            })
            
        except Exception as e:
            logger.error(f"Error deleting calendar event {event_id}: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    @beartype
    async def get_calendar_list(self, filter_params: Optional[str] = None) -> str:
        """
        Get list of available calendars in Bitrix24.

        Args:
            filter_params: JSON string with request parameters (e.g., '{"type": "user", "ownerId": 9}')

        Returns:
            JSON string with calendars list
        """
        try:
            params = json.loads(filter_params) if filter_params else {}

            if "TYPE" in params and "type" not in params:
                params["type"] = params.pop("TYPE")

            if "OWNER_ID" in params and "ownerId" not in params:
                params["ownerId"] = params.pop("OWNER_ID")
            elif "owner_id" in params and "ownerId" not in params:
                params["ownerId"] = params.pop("owner_id")

            if "type" not in params:
                params["type"] = "user"

            if "ownerId" in params:
                try:
                    params["ownerId"] = int(params["ownerId"])
                except (TypeError, ValueError):
                    pass

            calendars = await self.client.client.call("calendar.section.get", params)

            return json.dumps({
                "success": True,
                "calendars": calendars[0] if calendars else []
            }, ensure_ascii=False, indent=2)

        except json.JSONDecodeError as exc:
            logger.error(f"Invalid filter_params for calendar list: {exc}")
            return json.dumps({
                "success": False,
                "error": f"Invalid filter_params JSON: {exc}"
            })
        except Exception as e:
            logger.error(f"Error getting calendar list: {e}")
            return json.dumps({
                "success": False,
                "error": str(e)
            })