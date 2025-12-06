"""Unit tests for bitrix_mcp.tools.deals.DealTools."""

from __future__ import annotations

import asyncio
import json
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

from bitrix_mcp.tools.deals import DealTools


def _make_deal_tools() -> Tuple[DealTools, MagicMock]:
    """Create a DealTools instance paired with a mocked Bitrix client."""
    client = MagicMock()
    client.get_deals = AsyncMock()
    client.create_deal = AsyncMock()
    client.update_deal = AsyncMock()
    client.get_deal = AsyncMock()
    client.client = MagicMock()
    client.client.call = AsyncMock()
    return DealTools(client), client


def test_get_deals_parses_filters_and_limits() -> None:
    tools, client = _make_deal_tools()
    client.get_deals.return_value = [
        {"id": 1, "title": "First Deal"},
        {"id": 2, "title": "Second Deal"},
    ]

    result_json = asyncio.run(
        tools.get_deals(
            filter_params='{"STAGE_ID": "NEW"}',
            select_fields="ID,TITLE",
            limit=1,
        )
    )

    client.get_deals.assert_awaited_once_with(
        filter_params={"STAGE_ID": "NEW"},
        select_fields=["ID", "TITLE"],
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["deals"] == [{"id": 1, "title": "First Deal"}]


def test_get_deals_returns_error_on_invalid_filter_json() -> None:
    tools, client = _make_deal_tools()

    result_json = asyncio.run(tools.get_deals(filter_params="{bad}"))

    client.get_deals.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]  # error message should be present


def test_get_deals_preserves_results_when_limit_zero() -> None:
    tools, client = _make_deal_tools()
    client.get_deals.return_value = [
        {"id": 1},
        {"id": 2},
    ]

    result_json = asyncio.run(tools.get_deals(limit=0))

    client.get_deals.assert_awaited_once_with(
        filter_params=None,
        select_fields=None,
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["deals"] == [{"id": 1}, {"id": 2}]


def test_create_deal_parses_fields_and_calls_client() -> None:
    tools, client = _make_deal_tools()
    client.create_deal.return_value = {"result": 123}

    result_json = asyncio.run(
        tools.create_deal('{"TITLE": "New Deal", "OPPORTUNITY": 10000}')
    )

    client.create_deal.assert_awaited_once_with(
        {"TITLE": "New Deal", "OPPORTUNITY": 10000}
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["deal_id"] == 123
    assert payload["message"] == "Deal created successfully"


def test_create_deal_returns_error_on_invalid_json() -> None:
    tools, client = _make_deal_tools()

    result_json = asyncio.run(tools.create_deal("{bad}"))

    client.create_deal.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_update_deal_parses_fields_and_calls_client() -> None:
    tools, client = _make_deal_tools()
    client.update_deal.return_value = True

    result_json = asyncio.run(tools.update_deal("123", '{"STAGE_ID": "WON"}'))

    client.update_deal.assert_awaited_once_with("123", {"STAGE_ID": "WON"})

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["deal_id"] == "123"
    assert payload["message"] == "Deal updated successfully"


def test_update_deal_returns_error_on_invalid_json() -> None:
    tools, client = _make_deal_tools()

    result_json = asyncio.run(tools.update_deal("123", "{bad}"))

    client.update_deal.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_get_deal_fields_calls_client_and_returns_result() -> None:
    tools, client = _make_deal_tools()
    client.client.call.return_value = [{"result": {"TITLE": {"type": "string"}}}]

    result_json = asyncio.run(tools.get_deal_fields())

    client.client.call.assert_awaited_once_with("crm.deal.fields")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["fields"] == {"TITLE": {"type": "string"}}


def test_get_deal_fields_returns_error_on_client_error() -> None:
    tools, client = _make_deal_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_deal_fields())

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_deal_calls_client_and_returns_result() -> None:
    tools, client = _make_deal_tools()
    client.get_deal.return_value = {"ID": "456", "TITLE": "Test Deal"}

    result_json = asyncio.run(tools.get_deal("456"))

    client.get_deal.assert_awaited_once_with("456")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["deal"] == {"ID": "456", "TITLE": "Test Deal"}


def test_get_deal_returns_error_when_deal_not_found() -> None:
    tools, client = _make_deal_tools()
    client.get_deal.return_value = None

    result_json = asyncio.run(tools.get_deal("999"))

    client.get_deal.assert_awaited_once_with("999")

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "Deal with ID 999 not found"


def test_get_deal_returns_error_on_client_error() -> None:
    tools, client = _make_deal_tools()
    client.get_deal.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_deal("456"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"
