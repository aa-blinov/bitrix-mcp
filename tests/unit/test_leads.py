"""Unit tests for bitrix_mcp.tools.leads.LeadTools."""

from __future__ import annotations

import asyncio
import json
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

from bitrix_mcp.tools.leads import LeadTools


def _make_lead_tools() -> Tuple[LeadTools, MagicMock]:
    """Create a LeadTools instance paired with a mocked Bitrix client."""
    client = MagicMock()
    client.get_leads = AsyncMock()
    client.create_lead = AsyncMock()
    client.update_lead = AsyncMock()
    client.get_lead = AsyncMock()
    client.client = MagicMock()
    client.client.call = AsyncMock()
    return LeadTools(client), client


def test_get_leads_parses_filters_and_limits() -> None:
    tools, client = _make_lead_tools()
    client.get_leads.return_value = [
        {"id": 1, "title": "First Lead"},
        {"id": 2, "title": "Second Lead"},
    ]

    result_json = asyncio.run(
        tools.get_leads(
            filter_params='{"STATUS_ID": "NEW"}',
            select_fields="ID,TITLE",
            order='{"DATE_CREATE": "DESC"}',
            limit=1,
        )
    )

    client.get_leads.assert_awaited_once_with(
        filter_params={"STATUS_ID": "NEW"},
        select_fields=["ID", "TITLE"],
        order={"DATE_CREATE": "DESC"},
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["leads"] == [{"id": 1, "title": "First Lead"}]


def test_get_leads_returns_error_on_invalid_filter_json() -> None:
    tools, client = _make_lead_tools()

    result_json = asyncio.run(tools.get_leads(filter_params="{bad}"))

    client.get_leads.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]  # error message should be present


def test_get_leads_preserves_results_when_limit_zero() -> None:
    tools, client = _make_lead_tools()
    client.get_leads.return_value = [
        {"id": 1},
        {"id": 2},
    ]

    result_json = asyncio.run(tools.get_leads(limit=0))

    client.get_leads.assert_awaited_once_with(
        filter_params=None,
        select_fields=None,
        order=None,
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["leads"] == [{"id": 1}, {"id": 2}]


def test_create_lead_parses_fields_and_calls_client() -> None:
    tools, client = _make_lead_tools()
    client.create_lead.return_value = {"result": 123}

    result_json = asyncio.run(
        tools.create_lead('{"TITLE": "New Lead", "NAME": "John"}')
    )

    client.create_lead.assert_awaited_once_with({"TITLE": "New Lead", "NAME": "John"})

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["lead_id"] == 123
    assert payload["message"] == "Lead created successfully"


def test_create_lead_returns_error_on_invalid_json() -> None:
    tools, client = _make_lead_tools()

    result_json = asyncio.run(tools.create_lead("{bad}"))

    client.create_lead.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_update_lead_parses_fields_and_calls_client() -> None:
    tools, client = _make_lead_tools()
    client.update_lead.return_value = True

    result_json = asyncio.run(tools.update_lead("123", '{"STATUS_ID": "IN_PROCESS"}'))

    client.update_lead.assert_awaited_once_with("123", {"STATUS_ID": "IN_PROCESS"})

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["lead_id"] == "123"
    assert payload["message"] == "Lead updated successfully"


def test_update_lead_returns_error_on_invalid_json() -> None:
    tools, client = _make_lead_tools()

    result_json = asyncio.run(tools.update_lead("123", "{bad}"))

    client.update_lead.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_get_lead_fields_calls_client_and_returns_result() -> None:
    tools, client = _make_lead_tools()
    client.client.call.return_value = [{"result": {"TITLE": {"type": "string"}}}]

    result_json = asyncio.run(tools.get_lead_fields())

    client.client.call.assert_awaited_once_with("crm.lead.fields")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["fields"] == {"TITLE": {"type": "string"}}


def test_get_lead_fields_returns_error_on_client_error() -> None:
    tools, client = _make_lead_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_lead_fields())

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_lead_calls_client_and_returns_result() -> None:
    tools, client = _make_lead_tools()
    client.get_lead.return_value = {"ID": "123", "TITLE": "Test Lead"}

    result_json = asyncio.run(tools.get_lead("123"))

    client.get_lead.assert_awaited_once_with("123")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["lead"] == {"ID": "123", "TITLE": "Test Lead"}


def test_get_lead_returns_error_when_lead_not_found() -> None:
    tools, client = _make_lead_tools()
    client.get_lead.return_value = None

    result_json = asyncio.run(tools.get_lead("999"))

    client.get_lead.assert_awaited_once_with("999")

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "Lead with ID 999 not found"


def test_get_lead_returns_error_on_client_error() -> None:
    tools, client = _make_lead_tools()
    client.get_lead.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_lead("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"
