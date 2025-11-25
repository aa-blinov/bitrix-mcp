"""Unit tests for bitrix_mcp.tools.contacts.ContactTools."""

from __future__ import annotations

import asyncio
import json
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

from bitrix_mcp.tools.contacts import ContactTools


def _make_contact_tools() -> Tuple[ContactTools, MagicMock]:
    """Create a ContactTools instance paired with a mocked Bitrix client."""
    client = MagicMock()
    client.get_contacts = AsyncMock()
    client.create_contact = AsyncMock()
    client.update_contact = AsyncMock()
    client.get_contact = AsyncMock()
    client.client = MagicMock()
    client.client.call = AsyncMock()
    return ContactTools(client), client


def test_get_contacts_parses_filters_and_limits() -> None:
    tools, client = _make_contact_tools()
    client.get_contacts.return_value = [
        {"id": 1, "name": "John", "last_name": "Doe"},
        {"id": 2, "name": "Jane", "last_name": "Smith"},
    ]

    result_json = asyncio.run(
        tools.get_contacts(
            filter_params='{"HAS_EMAIL": "Y"}',
            select_fields="ID,NAME,LAST_NAME,EMAIL",
            order='{"DATE_CREATE": "DESC"}',
            limit=1,
        )
    )

    client.get_contacts.assert_awaited_once_with(
        filter_params={"HAS_EMAIL": "Y"},
        select_fields=["ID", "NAME", "LAST_NAME", "EMAIL"],
        order={"DATE_CREATE": "DESC"},
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["contacts"] == [{"id": 1, "name": "John", "last_name": "Doe"}]


def test_get_contacts_returns_error_on_invalid_filter_json() -> None:
    tools, client = _make_contact_tools()

    result_json = asyncio.run(tools.get_contacts(filter_params="{bad}"))

    client.get_contacts.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]  # error message should be present


def test_get_contacts_preserves_results_when_limit_zero() -> None:
    tools, client = _make_contact_tools()
    client.get_contacts.return_value = [
        {"id": 1},
        {"id": 2},
    ]

    result_json = asyncio.run(tools.get_contacts(limit=0))

    client.get_contacts.assert_awaited_once_with(
        filter_params=None,
        select_fields=None,
        order=None,
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["contacts"] == [{"id": 1}, {"id": 2}]


def test_create_contact_parses_fields_and_calls_client() -> None:
    tools, client = _make_contact_tools()
    client.create_contact.return_value = {"result": 123}

    result_json = asyncio.run(
        tools.create_contact('{"NAME": "John", "LAST_NAME": "Doe"}')
    )

    client.create_contact.assert_awaited_once_with({"NAME": "John", "LAST_NAME": "Doe"})

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["contact_id"] == 123
    assert payload["message"] == "Contact created successfully"


def test_create_contact_returns_error_on_invalid_json() -> None:
    tools, client = _make_contact_tools()

    result_json = asyncio.run(tools.create_contact("{bad}"))

    client.create_contact.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_update_contact_parses_fields_and_calls_client() -> None:
    tools, client = _make_contact_tools()
    client.update_contact.return_value = True

    result_json = asyncio.run(
        tools.update_contact(
            "123", '{"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}'
        )
    )

    client.update_contact.assert_awaited_once_with(
        "123", {"PHONE": [{"VALUE": "+1234567890", "VALUE_TYPE": "WORK"}]}
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["contact_id"] == "123"
    assert payload["message"] == "Contact updated successfully"


def test_update_contact_returns_error_on_invalid_json() -> None:
    tools, client = _make_contact_tools()

    result_json = asyncio.run(tools.update_contact("123", "{bad}"))

    client.update_contact.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_get_contact_fields_calls_client_and_returns_result() -> None:
    tools, client = _make_contact_tools()
    client.client.call.return_value = [{"result": {"NAME": {"type": "string"}}}]

    result_json = asyncio.run(tools.get_contact_fields())

    client.client.call.assert_awaited_once_with("crm.contact.fields")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["fields"] == {"NAME": {"type": "string"}}


def test_get_contact_fields_returns_error_on_client_error() -> None:
    tools, client = _make_contact_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_contact_fields())

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_contact_calls_client_and_returns_result() -> None:
    tools, client = _make_contact_tools()
    client.get_contact.return_value = {"ID": "789", "NAME": "Test Contact"}

    result_json = asyncio.run(tools.get_contact("789"))

    client.get_contact.assert_awaited_once_with("789")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["contact"] == {"ID": "789", "NAME": "Test Contact"}


def test_get_contact_returns_error_when_contact_not_found() -> None:
    tools, client = _make_contact_tools()
    client.get_contact.return_value = None

    result_json = asyncio.run(tools.get_contact("999"))

    client.get_contact.assert_awaited_once_with("999")

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "Contact with ID 999 not found"


def test_get_contact_returns_error_on_client_error() -> None:
    tools, client = _make_contact_tools()
    client.get_contact.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_contact("789"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"
