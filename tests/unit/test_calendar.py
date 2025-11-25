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
