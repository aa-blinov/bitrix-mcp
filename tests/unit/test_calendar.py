"""Unit tests for bitrix_mcp.tools.calendar.CalendarTools."""

from __future__ import annotations

import asyncio
import json
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

from bitrix_mcp.tools.calendar import CalendarTools


def _make_calendar_tools() -> Tuple[CalendarTools, MagicMock]:
    """Create a CalendarTools instance paired with a mocked Bitrix client."""
    client = MagicMock()
    client.get_calendar_event_by_id = AsyncMock()
    client.get_nearest_calendar_events = AsyncMock()
    client.get_meeting_status = AsyncMock()
    client.set_meeting_status = AsyncMock()
    client.client = MagicMock()
    client.client.call = AsyncMock()
    return CalendarTools(client), client


def test_get_events_parses_filters_and_limits() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.return_value = [
        [
            {"id": 1, "name": "First Event"},
            {"id": 2, "name": "Second Event"},
        ]
    ]

    result_json = asyncio.run(
        tools.get_events(
            filter_params='{"type": "user", "ownerId": 1}',
            date_from="2024-01-01",
            date_to="2024-01-31",
            limit=1,
            sections="[21, 44]",
        )
    )

    client.client.call.assert_awaited_once_with(
        "calendar.event.get",
        {
            "type": "user",
            "ownerId": 1,
            "from": "2024-01-01",
            "to": "2024-01-31",
            "section": [21, 44],
        },
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["events"] == [{"id": 1, "name": "First Event"}]


def test_get_events_returns_error_on_invalid_filter_json() -> None:
    tools, client = _make_calendar_tools()

    result_json = asyncio.run(tools.get_events(filter_params="{bad}"))

    client.client.call.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]  # error message should be present


def test_get_events_preserves_results_when_limit_zero() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.return_value = [
        [
            {"id": 1},
            {"id": 2},
        ]
    ]

    result_json = asyncio.run(tools.get_events(limit=0))

    client.client.call.assert_awaited_once_with("calendar.event.get", {})

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["events"] == [{"id": 1}, {"id": 2}]


def test_create_event_parses_fields_and_calls_client() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.return_value = [123]

    result_json = asyncio.run(
        tools.create_event(
            '{"type": "user", "ownerId": 1, "name": "New Event", "from": "2024-01-15 10:00:00", "to": "2024-01-15 11:00:00", "section": 5}'
        )
    )

    client.client.call.assert_awaited_once_with(
        "calendar.event.add",
        {
            "type": "user",
            "ownerId": 1,
            "name": "New Event",
            "from": "2024-01-15 10:00:00",
            "to": "2024-01-15 11:00:00",
            "section": 5,
        },
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["event_id"] == 123
    assert payload["message"] == "Calendar event created successfully"


def test_create_event_returns_error_on_invalid_json() -> None:
    tools, client = _make_calendar_tools()

    result_json = asyncio.run(tools.create_event("{bad}"))

    client.client.call.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_update_event_parses_fields_and_calls_client() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.update_event("123", '{"name": "Updated Event"}'))

    client.client.call.assert_awaited_once_with(
        "calendar.event.update",
        {
            "id": "123",
            "name": "Updated Event",
        },
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["event_id"] == "123"
    assert payload["message"] == "Calendar event updated successfully"


def test_update_event_returns_error_on_invalid_json() -> None:
    tools, client = _make_calendar_tools()

    result_json = asyncio.run(tools.update_event("123", "{bad}"))

    client.client.call.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_delete_event_calls_client_and_returns_result() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.delete_event("123"))

    client.client.call.assert_awaited_once_with("calendar.event.delete", {"id": "123"})

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["event_id"] == "123"
    assert payload["message"] == "Calendar event deleted successfully"


def test_delete_event_returns_error_on_client_error() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.delete_event("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_calendar_list_parses_params_and_calls_client() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.return_value = [
        [
            {"id": 1, "name": "Personal Calendar"},
            {"id": 2, "name": "Work Calendar"},
        ]
    ]

    result_json = asyncio.run(tools.get_calendar_list('{"type": "user", "ownerId": 1}'))

    client.client.call.assert_awaited_once_with(
        "calendar.section.get",
        {"type": "user", "ownerId": 1},
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["calendars"] == [
        {"id": 1, "name": "Personal Calendar"},
        {"id": 2, "name": "Work Calendar"},
    ]


def test_get_calendar_list_returns_error_on_invalid_json() -> None:
    tools, client = _make_calendar_tools()

    result_json = asyncio.run(tools.get_calendar_list("{bad}"))

    client.client.call.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_get_calendar_list_defaults_to_user_type() -> None:
    tools, client = _make_calendar_tools()
    client.client.call.return_value = [[]]

    result_json = asyncio.run(tools.get_calendar_list())

    client.client.call.assert_awaited_once_with(
        "calendar.section.get", {"type": "user"}
    )

    payload = json.loads(result_json)
    assert payload["success"] is True


def test_get_event_by_id_calls_client_and_returns_result() -> None:
    tools, client = _make_calendar_tools()
    client.get_calendar_event_by_id.return_value = {"ID": "123", "NAME": "Test Event"}

    result_json = asyncio.run(tools.get_event_by_id("123"))

    client.get_calendar_event_by_id.assert_awaited_once_with("123")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["event"] == {"ID": "123", "NAME": "Test Event"}


def test_get_event_by_id_returns_error_when_event_not_found() -> None:
    tools, client = _make_calendar_tools()
    client.get_calendar_event_by_id.return_value = None

    result_json = asyncio.run(tools.get_event_by_id("999"))

    client.get_calendar_event_by_id.assert_awaited_once_with("999")

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "Event with ID 999 not found"


def test_get_event_by_id_returns_error_on_client_error() -> None:
    tools, client = _make_calendar_tools()
    client.get_calendar_event_by_id.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_event_by_id("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_nearest_events_calls_client_and_returns_result() -> None:
    tools, client = _make_calendar_tools()
    client.get_nearest_calendar_events.return_value = [
        {"ID": "123", "NAME": "Meeting 1"},
        {"ID": "456", "NAME": "Meeting 2"},
    ]

    result_json = asyncio.run(tools.get_nearest_events())

    client.get_nearest_calendar_events.assert_awaited_once_with(
        calendar_type="user",
        owner_id=None,
        days=60,
        for_current_user=True,
        max_events_count=None,
        detail_url=None,
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert len(payload["events"]) == 2


def test_get_nearest_events_with_custom_params() -> None:
    tools, client = _make_calendar_tools()
    client.get_nearest_calendar_events.return_value = [{"ID": "123", "NAME": "Event"}]

    result_json = asyncio.run(
        tools.get_nearest_events(
            calendar_type="group",
            owner_id="5",
            days=30,
            for_current_user=False,
            max_events_count=10,
            detail_url="/calendar/",
        )
    )

    client.get_nearest_calendar_events.assert_awaited_once_with(
        calendar_type="group",
        owner_id=5,
        days=30,
        for_current_user=False,
        max_events_count=10,
        detail_url="/calendar/",
    )

    payload = json.loads(result_json)
    assert payload["success"] is True


def test_get_nearest_events_returns_error_on_client_error() -> None:
    tools, client = _make_calendar_tools()
    client.get_nearest_calendar_events.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_nearest_events())

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_meeting_status_calls_client_and_returns_result() -> None:
    tools, client = _make_calendar_tools()
    client.get_meeting_status.return_value = "Y"

    result_json = asyncio.run(tools.get_meeting_status("123"))

    client.get_meeting_status.assert_awaited_once_with("123")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["event_id"] == "123"
    assert payload["status"] == "Y"


def test_get_meeting_status_returns_error_on_failure() -> None:
    tools, client = _make_calendar_tools()
    client.get_meeting_status.return_value = None

    result_json = asyncio.run(tools.get_meeting_status("999"))

    client.get_meeting_status.assert_awaited_once_with("999")

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "Could not get meeting status for event 999"


def test_get_meeting_status_returns_error_on_client_error() -> None:
    tools, client = _make_calendar_tools()
    client.get_meeting_status.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_meeting_status("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_set_meeting_status_calls_client_and_returns_result() -> None:
    tools, client = _make_calendar_tools()
    client.set_meeting_status.return_value = True

    result_json = asyncio.run(tools.set_meeting_status("123", "Y"))

    client.set_meeting_status.assert_awaited_once_with("123", "Y")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["event_id"] == "123"
    assert payload["status"] == "Y"
    assert payload["message"] == "Meeting status updated successfully"


def test_set_meeting_status_with_invalid_status() -> None:
    tools, client = _make_calendar_tools()

    result_json = asyncio.run(tools.set_meeting_status("123", "X"))

    # Client should not be called for invalid status
    client.set_meeting_status.assert_not_called()

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "Invalid status 'X'. Must be 'Y', 'N', or 'Q'"


def test_set_meeting_status_returns_error_on_failure() -> None:
    tools, client = _make_calendar_tools()
    client.set_meeting_status.return_value = False

    result_json = asyncio.run(tools.set_meeting_status("123", "N"))

    client.set_meeting_status.assert_awaited_once_with("123", "N")

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["message"] == "Failed to update meeting status"


def test_set_meeting_status_returns_error_on_client_error() -> None:
    tools, client = _make_calendar_tools()
    client.set_meeting_status.side_effect = Exception("API error")

    result_json = asyncio.run(tools.set_meeting_status("123", "Y"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"
