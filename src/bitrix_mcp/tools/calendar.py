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
                        items = [
                            item.strip()
                            for item in raw_value.split(",")
                            if item.strip()
                        ]
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
                "count": (
                    len(events[0]) if events and isinstance(events[0], list) else 0
                ),
                "events": events[0] if events else [],
            }

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting calendar events: {e}")
            return json.dumps({"success": False, "error": str(e)})

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

            return json.dumps(
                {
                    "success": True,
                    "event_id": result[0] if result else None,
                    "message": "Calendar event created successfully",
                }
            )

        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return json.dumps({"success": False, "error": str(e)})

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

            return json.dumps(
                {
                    "success": success,
                    "event_id": event_id,
                    "message": (
                        "Calendar event updated successfully"
                        if success
                        else "Failed to update event"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error updating calendar event {event_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

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
            result = await self.client.client.call(
                "calendar.event.delete", {"id": event_id}
            )

            success = bool(result[0]) if result else False

            return json.dumps(
                {
                    "success": success,
                    "event_id": event_id,
                    "message": (
                        "Calendar event deleted successfully"
                        if success
                        else "Failed to delete event"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error deleting calendar event {event_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

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

            return json.dumps(
                {"success": True, "calendars": calendars[0] if calendars else []},
                ensure_ascii=False,
                indent=2,
            )

        except json.JSONDecodeError as exc:
            logger.error(f"Invalid filter_params for calendar list: {exc}")
            return json.dumps(
                {"success": False, "error": f"Invalid filter_params JSON: {exc}"}
            )
        except Exception as e:
            logger.error(f"Error getting calendar list: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_event_by_id(self, event_id: str) -> str:
        """
        Get a calendar event by ID from Bitrix24.

        This method retrieves detailed information about a specific calendar event including
        all its properties, participants, and metadata.

        Args:
            event_id: Event ID to retrieve (required)

        Returns:
            JSON string with event data containing all event fields

        Event fields include:
        - Basic info: ID, NAME, DESCRIPTION, LOCATION
        - Dates: DATE_FROM, DATE_TO, TZ_FROM, TZ_TO, DT_SKIP_TIME
        - Participants: ATTENDEE_LIST, ATTENDEES_CODES, IS_MEETING, MEETING_STATUS
        - Recurrence: RRULE, EXDATE, RECURRENCE_ID
        - Metadata: CREATED_BY, DATE_CREATE, TIMESTAMP_X, PRIVATE_EVENT
        - CRM integration: UF_CRM_CAL_EVENT
        - Files: UF_WEBDAV_CAL_EVENT

        Example:
            {"success": true, "event": {"ID": "123", "NAME": "Meeting", "DATE_FROM": "2024-01-15 10:00:00", ...}}
        """
        try:
            # Get event by ID
            event = await self.client.get_calendar_event_by_id(event_id)

            if event:
                return json.dumps(
                    {"success": True, "event": event}, ensure_ascii=False, indent=2
                )
            else:
                return json.dumps(
                    {"success": False, "error": f"Event with ID {event_id} not found"}
                )

        except Exception as e:
            logger.error(f"Error getting calendar event {event_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_nearest_events(
        self,
        calendar_type: str = "user",
        owner_id: Optional[str] = None,
        days: int = 60,
        for_current_user: bool = True,
        max_events_count: Optional[int] = None,
        detail_url: Optional[str] = None,
    ) -> str:
        """
        Get nearest upcoming calendar events from Bitrix24.

        This method retrieves future calendar events within a specified number of days.
        Useful for displaying upcoming events in dashboards or notifications.

        Args:
            calendar_type: Type of calendar to search in (optional, default: "user")
                         - "user" - user calendar
                         - "group" - group calendar
                         - "company_calendar" - company calendar
            owner_id: Owner ID of the calendar (optional)
                     - For user calendar: user ID
                     - For group calendar: group ID
                     - For company calendar: usually 0 or empty
            days: Number of days to look ahead (optional, default: 60)
            for_current_user: Whether to get events for current user only (optional, default: true)
            max_events_count: Maximum number of events to return (optional)
            detail_url: Calendar detail URL template (optional)

        Returns:
            JSON string with list of upcoming events

        Example:
            {"success": true, "events": [{"ID": "123", "NAME": "Meeting", "DATE_FROM": "2024-01-15 10:00:00"}, ...]}
        """
        try:
            # Parse owner_id if provided
            owner_id_int = int(owner_id) if owner_id else None

            # Get nearest events
            events = await self.client.get_nearest_calendar_events(
                calendar_type=calendar_type,
                owner_id=owner_id_int,
                days=days,
                for_current_user=for_current_user,
                max_events_count=max_events_count,
                detail_url=detail_url,
            )

            result = {"success": True, "count": len(events), "events": events}

            return json.dumps(result, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error getting nearest calendar events: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def get_meeting_status(self, event_id: str) -> str:
        """
        Get the current user's participation status for a meeting event.

        This method retrieves the status of the current user's participation in a calendar meeting.
        Only works for events that are meetings (have participants).

        Args:
            event_id: Event ID to check status for (required)

        Returns:
            JSON string with participation status

        Status values:
        - "Y" - Accepted (согласен)
        - "N" - Declined (отказался)
        - "Q" - Pending (приглашен, но еще не ответил)

        Example:
            {"success": true, "status": "Y", "event_id": "123"}
        """
        try:
            # Get meeting status
            status = await self.client.get_meeting_status(event_id)

            if status is not None:
                return json.dumps(
                    {"success": True, "event_id": event_id, "status": status}
                )
            else:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Could not get meeting status for event {event_id}",
                    }
                )

        except Exception as e:
            logger.error(f"Error getting meeting status for event {event_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @beartype
    async def set_meeting_status(self, event_id: str, status: str) -> str:
        """
        Set the current user's participation status for a meeting event.

        This method allows the current user to accept, decline, or mark as pending
        their participation in a calendar meeting.

        Args:
            event_id: Event ID to set status for (required)
            status: Participation status (required)
                   - "Y" - Accept (принять)
                   - "N" - Decline (отклонить)
                   - "Q" - Mark as pending (отметить как ожидание ответа)

        Returns:
            JSON string with operation result

        Example:
            {"success": true, "event_id": "123", "status": "Y", "message": "Meeting status updated successfully"}
        """
        try:
            # Validate status
            if status not in ["Y", "N", "Q"]:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Invalid status '{status}'. Must be 'Y', 'N', or 'Q'",
                    }
                )

            # Set meeting status
            success = await self.client.set_meeting_status(event_id, status)

            return json.dumps(
                {
                    "success": success,
                    "event_id": event_id,
                    "status": status,
                    "message": (
                        "Meeting status updated successfully"
                        if success
                        else "Failed to update meeting status"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error setting meeting status for event {event_id}: {e}")
            return json.dumps({"success": False, "error": str(e)})
