"""Unit tests for bitrix_mcp.tools.companies.CompanyTools."""

from __future__ import annotations

import asyncio
import json
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

from bitrix_mcp.tools.companies import CompanyTools


def _make_company_tools() -> Tuple[CompanyTools, MagicMock]:
    """Create a CompanyTools instance paired with a mocked Bitrix client."""
    client = MagicMock()
    client.get_companies = AsyncMock()
    client.create_company = AsyncMock()
    client.update_company = AsyncMock()
    client.get_company = AsyncMock()
    client.client = MagicMock()
    client.client.call = AsyncMock()
    return CompanyTools(client), client


def test_get_companies_parses_filters_and_limits() -> None:
    tools, client = _make_company_tools()
    client.get_companies.return_value = [
        {"id": 1, "title": "ACME Corp"},
        {"id": 2, "title": "Tech Solutions"},
    ]

    result_json = asyncio.run(
        tools.get_companies(
            filter_params='{"HAS_EMAIL": "Y"}',
            select_fields="ID,TITLE,EMAIL,PHONE",
            limit=1,
        )
    )

    client.get_companies.assert_awaited_once_with(
        filter_params={"HAS_EMAIL": "Y"},
        select_fields=["ID", "TITLE", "EMAIL", "PHONE"],
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["companies"] == [{"id": 1, "title": "ACME Corp"}]


def test_get_companies_returns_error_on_invalid_filter_json() -> None:
    tools, client = _make_company_tools()

    result_json = asyncio.run(tools.get_companies(filter_params="{bad}"))

    client.get_companies.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]  # error message should be present


def test_get_companies_preserves_results_when_limit_zero() -> None:
    tools, client = _make_company_tools()
    client.get_companies.return_value = [
        {"id": 1},
        {"id": 2},
    ]

    result_json = asyncio.run(tools.get_companies(limit=0))

    client.get_companies.assert_awaited_once_with(
        filter_params=None,
        select_fields=None,
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["companies"] == [{"id": 1}, {"id": 2}]


def test_create_company_parses_fields_and_calls_client() -> None:
    tools, client = _make_company_tools()
    client.create_company.return_value = {"result": 123}

    result_json = asyncio.run(
        tools.create_company(
            '{"TITLE": "ACME Corp", "EMAIL": [{"VALUE": "info@acme.com", "VALUE_TYPE": "WORK"}]}'
        )
    )

    client.create_company.assert_awaited_once_with(
        {
            "TITLE": "ACME Corp",
            "EMAIL": [{"VALUE": "info@acme.com", "VALUE_TYPE": "WORK"}],
        }
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["company_id"] == 123
    assert payload["message"] == "Company created successfully"


def test_create_company_returns_error_on_invalid_json() -> None:
    tools, client = _make_company_tools()

    result_json = asyncio.run(tools.create_company("{bad}"))

    client.create_company.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_update_company_parses_fields_and_calls_client() -> None:
    tools, client = _make_company_tools()
    client.update_company.return_value = True

    result_json = asyncio.run(
        tools.update_company(
            "123", '{"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}'
        )
    )

    client.update_company.assert_awaited_once_with(
        "123", {"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["company_id"] == "123"
    assert payload["message"] == "Company updated successfully"


def test_update_company_returns_error_on_invalid_json() -> None:
    tools, client = _make_company_tools()

    result_json = asyncio.run(tools.update_company("123", "{bad}"))

    client.update_company.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_get_company_fields_calls_client_and_returns_result() -> None:
    tools, client = _make_company_tools()
    client.client.call.return_value = [{"result": {"TITLE": {"type": "string"}}}]

    result_json = asyncio.run(tools.get_company_fields())

    client.client.call.assert_awaited_once_with("crm.company.fields")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["fields"] == {"TITLE": {"type": "string"}}


def test_get_company_fields_returns_error_on_client_error() -> None:
    tools, client = _make_company_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_company_fields())

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_company_calls_client_and_returns_result() -> None:
    tools, client = _make_company_tools()
    client.get_company.return_value = {"ID": "101", "TITLE": "Test Company"}

    result_json = asyncio.run(tools.get_company("101"))

    client.get_company.assert_awaited_once_with("101")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["company"] == {"ID": "101", "TITLE": "Test Company"}


def test_get_company_returns_error_when_company_not_found() -> None:
    tools, client = _make_company_tools()
    client.get_company.return_value = None

    result_json = asyncio.run(tools.get_company("999"))

    client.get_company.assert_awaited_once_with("999")

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "Company with ID 999 not found"


def test_get_company_returns_error_on_client_error() -> None:
    tools, client = _make_company_tools()
    client.get_company.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_company("101"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"
