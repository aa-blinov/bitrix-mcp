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
    client.get_all = AsyncMock()
    client.client = MagicMock()
    return TaskTools(client), client


def test_get_tasks_parses_filters_and_limits() -> None:
    tools, client = _make_task_tools()
    client.get_all.return_value = [
        {"id": 1, "title": "First"},
        {"id": 2, "title": "Second"},
    ]

    result_json = asyncio.run(
        tools.get_tasks(
            filter_params='{"STATUS": "2"}',
            select_fields="ID,TITLE",
            order='{"CREATED_DATE": "DESC"}',
            limit=1,
        )
    )

    client.get_all.assert_awaited_once_with(
        "tasks.task.list",
        params={
            "filter": {"STATUS": "2"},
            "select": ["ID", "TITLE"],
            "order": {"CREATED_DATE": "DESC"},
        },
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
    client.get_all.return_value = [
        {"id": 1},
        {"id": 2},
    ]

    result_json = asyncio.run(tools.get_tasks(limit=0))

    client.get_all.assert_awaited_once_with("tasks.task.list", params=None)

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["tasks"] == [{"id": 1}, {"id": 2}]
