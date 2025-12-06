"""Unit tests for bitrix_mcp.tools.tasks.TaskTools."""

from __future__ import annotations

import asyncio
import json
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

from bitrix_mcp.tools.tasks import TaskTools


def _make_task_tools() -> Tuple[TaskTools, MagicMock]:
    """Create a TaskTools instance paired with a mocked Bitrix client."""
    client = MagicMock()
    client.get_tasks = AsyncMock()
    client.get_all = AsyncMock()
    client.client = MagicMock()
    return TaskTools(client), client


def test_get_tasks_parses_filters_and_limits() -> None:
    tools, client = _make_task_tools()
    client.get_tasks.return_value = [
        {"id": 1, "title": "First"},
        {"id": 2, "title": "Second"},
    ]

    result_json = asyncio.run(
        tools.get_tasks(
            filter_params='{"STATUS": "2"}',
            select_fields="ID,TITLE",
            limit=1,
        )
    )

    client.get_tasks.assert_awaited_once_with(
        filter_params={"STATUS": "2"},
        select_fields=["ID", "TITLE"],
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["tasks"] == [{"id": 1, "title": "First"}]


def test_get_tasks_returns_error_on_invalid_filter_json() -> None:
    tools, client = _make_task_tools()

    result_json = asyncio.run(tools.get_tasks(filter_params="{bad}"))

    client.get_all.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]  # error message should be present


def test_get_tasks_preserves_results_when_limit_zero() -> None:
    tools, client = _make_task_tools()
    client.get_tasks.return_value = [
        {"id": 1},
        {"id": 2},
    ]

    result_json = asyncio.run(tools.get_tasks(limit=0))

    client.get_tasks.assert_awaited_once_with(
        filter_params=None,
        select_fields=None,
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["tasks"] == [{"id": 1}, {"id": 2}]


def test_get_task_calls_client_and_returns_result() -> None:
    tools, client = _make_task_tools()
    client.get_task.return_value = {"id": 123, "title": "Test Task"}

    result_json = asyncio.run(tools.get_task("123"))

    client.get_task.assert_called_once_with("123")
    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["task"] == {"id": 123, "title": "Test Task"}


def test_get_task_returns_error_on_client_error() -> None:
    tools, client = _make_task_tools()
    client.get_task.side_effect = Exception("API Error")

    result_json = asyncio.run(tools.get_task("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert "API Error" in payload["error"]


def test_approve_task_calls_client_and_returns_result() -> None:
    tools, client = _make_task_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.approve_task("123"))

    client.client.call.assert_called_once_with("tasks.task.approve", {"taskId": "123"})
    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["task_id"] == "123"
    assert "approved successfully" in payload["message"]


def test_approve_task_returns_error_on_client_error() -> None:
    tools, client = _make_task_tools()
    client.client.call.side_effect = Exception("API Error")

    result_json = asyncio.run(tools.approve_task("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert "API Error" in payload["error"]


def test_start_task_calls_client_and_returns_result() -> None:
    tools, client = _make_task_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.start_task("123"))

    client.client.call.assert_called_once_with("tasks.task.start", {"taskId": "123"})
    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["task_id"] == "123"
    assert "started successfully" in payload["message"]


def test_start_task_returns_error_on_client_error() -> None:
    tools, client = _make_task_tools()
    client.client.call.side_effect = Exception("API Error")

    result_json = asyncio.run(tools.start_task("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert "API Error" in payload["error"]


def test_delegate_task_calls_client_and_returns_result() -> None:
    tools, client = _make_task_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.delegate_task("123", "456"))

    client.client.call.assert_called_once_with(
        "tasks.task.delegate", {"taskId": "123", "userId": "456"}
    )
    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["task_id"] == "123"
    assert payload["user_id"] == "456"
    assert "delegated successfully" in payload["message"]


def test_delegate_task_returns_error_on_client_error() -> None:
    tools, client = _make_task_tools()
    client.client.call.side_effect = Exception("API Error")

    result_json = asyncio.run(tools.delegate_task("123", "456"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert "API Error" in payload["error"]


def test_renew_task_calls_client_and_returns_result() -> None:
    tools, client = _make_task_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.renew_task("123"))

    client.client.call.assert_called_once_with("tasks.task.renew", {"taskId": "123"})
    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["task_id"] == "123"
    assert "renewed successfully" in payload["message"]


def test_renew_task_returns_error_on_client_error() -> None:
    tools, client = _make_task_tools()
    client.client.call.side_effect = Exception("API Error")

    result_json = asyncio.run(tools.renew_task("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert "API Error" in payload["error"]


def test_start_watching_task_calls_client_and_returns_result() -> None:
    tools, client = _make_task_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.start_watching_task("123"))

    client.client.call.assert_called_once_with(
        "tasks.task.startwatch", {"taskId": "123"}
    )
    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["task_id"] == "123"
    assert "watching task successfully" in payload["message"]


def test_start_watching_task_returns_error_on_client_error() -> None:
    tools, client = _make_task_tools()
    client.client.call.side_effect = Exception("API Error")

    result_json = asyncio.run(tools.start_watching_task("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert "API Error" in payload["error"]


def test_disapprove_task_calls_client_and_returns_result() -> None:
    tools, client = _make_task_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.disapprove_task("123"))

    client.client.call.assert_called_once_with(
        "tasks.task.disapprove", {"taskId": "123"}
    )
    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["task_id"] == "123"
    assert "disapproved successfully" in payload["message"]


def test_disapprove_task_returns_error_on_client_error() -> None:
    tools, client = _make_task_tools()
    client.client.call.side_effect = Exception("API Error")

    result_json = asyncio.run(tools.disapprove_task("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert "API Error" in payload["error"]
