"""Unit tests for bitrix_mcp.tools.projects.ProjectTools."""

from __future__ import annotations

import asyncio
import json
from typing import Tuple
from unittest.mock import AsyncMock, MagicMock

from bitrix_mcp.tools.projects import ProjectTools


def _make_project_tools() -> Tuple[ProjectTools, MagicMock]:
    """Create a ProjectTools instance paired with a mocked Bitrix client."""
    client = MagicMock()
    client.client = MagicMock()
    client.client.call = AsyncMock()
    client.expel_project_member = AsyncMock()
    client.request_join_project = AsyncMock()
    client.invite_project_member = AsyncMock()
    return ProjectTools(client), client


def test_get_projects_parses_filters_and_limits() -> None:
    tools, client = _make_project_tools()
    client.client.call.return_value = [
        [
            {"id": 1, "name": "First Project"},
            {"id": 2, "name": "Second Project"},
        ]
    ]

    result_json = asyncio.run(
        tools.get_projects(
            filter_params='{"ACTIVE": "Y"}',
            order='{"NAME": "ASC"}',
            limit=1,
        )
    )

    client.client.call.assert_awaited_once_with(
        "sonet_group.get",
        {
            "FILTER": {"ACTIVE": "Y"},
            "ORDER": {"NAME": "ASC"},
        },
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 1
    assert payload["projects"] == [{"id": 1, "name": "First Project"}]


def test_get_projects_returns_error_on_invalid_filter_json() -> None:
    tools, client = _make_project_tools()

    result_json = asyncio.run(tools.get_projects(filter_params="{bad}"))

    client.client.call.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]  # error message should be present


def test_get_projects_preserves_results_when_limit_zero() -> None:
    tools, client = _make_project_tools()
    client.client.call.return_value = [
        [
            {"id": 1},
            {"id": 2},
        ]
    ]

    result_json = asyncio.run(tools.get_projects(limit=0))

    client.client.call.assert_awaited_once_with("sonet_group.get", None)

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["count"] == 2
    assert payload["projects"] == [{"id": 1}, {"id": 2}]


def test_create_project_parses_fields_and_calls_client() -> None:
    tools, client = _make_project_tools()
    client.client.call.return_value = [123]

    result_json = asyncio.run(
        tools.create_project(
            '{"NAME": "New Project", "DESCRIPTION": "Project description"}'
        )
    )

    client.client.call.assert_awaited_once_with(
        "sonet_group.create",
        {
            "NAME": "New Project",
            "DESCRIPTION": "Project description",
        },
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == 123
    assert payload["message"] == "Project created successfully"


def test_create_project_returns_error_on_invalid_json() -> None:
    tools, client = _make_project_tools()

    result_json = asyncio.run(tools.create_project("{bad}"))

    client.client.call.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_update_project_parses_fields_and_calls_client() -> None:
    tools, client = _make_project_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(
        tools.update_project("123", '{"NAME": "Updated Project"}')
    )

    client.client.call.assert_awaited_once_with(
        "sonet_group.update",
        {
            "GROUP_ID": "123",
            "NAME": "Updated Project",
        },
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["message"] == "Project updated successfully"


def test_update_project_returns_error_on_invalid_json() -> None:
    tools, client = _make_project_tools()

    result_json = asyncio.run(tools.update_project("123", "{bad}"))

    client.client.call.assert_not_called()
    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"]


def test_get_project_tasks_calls_client_and_returns_result() -> None:
    tools, client = _make_project_tools()
    client.client.call.return_value = [
        {
            "tasks": [
                {"id": 1, "title": "Task 1"},
                {"id": 2, "title": "Task 2"},
            ]
        }
    ]

    result_json = asyncio.run(tools.get_project_tasks("123", limit=1))

    client.client.call.assert_awaited_once_with(
        "tasks.task.list",
        {"filter": {"GROUP_ID": "123"}},
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["count"] == 1
    assert payload["tasks"] == [{"id": 1, "title": "Task 1"}]


def test_get_project_tasks_returns_error_on_client_error() -> None:
    tools, client = _make_project_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_project_tasks("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_add_project_member_calls_client_and_returns_result() -> None:
    tools, client = _make_project_tools()
    client.client.call.return_value = [True]

    result_json = asyncio.run(tools.add_project_member("123", "456", "member"))

    client.client.call.assert_awaited_once_with(
        "sonet_group.user.add",
        {
            "GROUP_ID": "123",
            "USER_ID": "456",
            "ROLE": "member",
        },
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["user_id"] == "456"
    assert payload["role"] == "member"
    assert payload["message"] == "Member added successfully"


def test_add_project_member_returns_error_on_client_error() -> None:
    tools, client = _make_project_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.add_project_member("123", "456"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_get_project_members_calls_client_and_returns_result() -> None:
    tools, client = _make_project_tools()
    client.client.call.return_value = [
        [
            {"USER_ID": "1", "ROLE": "A"},
            {"USER_ID": "2", "ROLE": "K"},
        ]
    ]

    result_json = asyncio.run(tools.get_project_members("123"))

    client.client.call.assert_awaited_once_with(
        "sonet_group.user.get",
        {"ID": "123"},
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["members"] == [
        {"USER_ID": "1", "ROLE": "A"},
        {"USER_ID": "2", "ROLE": "K"},
    ]


def test_get_project_members_returns_error_on_client_error() -> None:
    tools, client = _make_project_tools()
    client.client.call.side_effect = Exception("API error")

    result_json = asyncio.run(tools.get_project_members("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_expel_project_member_calls_client_and_returns_result() -> None:
    tools, client = _make_project_tools()
    client.expel_project_member = AsyncMock(return_value=True)

    result_json = asyncio.run(tools.expel_project_member("123", "456"))

    client.expel_project_member.assert_awaited_once_with("123", "456")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["user_id"] == "456"
    assert payload["message"] == "Member expelled successfully"


def test_expel_project_member_returns_error_on_client_error() -> None:
    tools, client = _make_project_tools()
    client.expel_project_member = AsyncMock(side_effect=Exception("API error"))

    result_json = asyncio.run(tools.expel_project_member("123", "456"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_request_join_project_calls_client_and_returns_result() -> None:
    tools, client = _make_project_tools()
    client.request_join_project = AsyncMock(return_value=True)

    result_json = asyncio.run(tools.request_join_project("123", "Please add me"))

    client.request_join_project.assert_awaited_once_with("123", "Please add me")

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["request_message"] == "Please add me"
    assert payload["message"] == "Join request sent successfully"


def test_request_join_project_without_message_calls_client() -> None:
    tools, client = _make_project_tools()
    client.request_join_project = AsyncMock(return_value=True)

    result_json = asyncio.run(tools.request_join_project("123"))

    client.request_join_project.assert_awaited_once_with("123", None)

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["request_message"] is None


def test_request_join_project_returns_error_on_client_error() -> None:
    tools, client = _make_project_tools()
    client.request_join_project = AsyncMock(side_effect=Exception("API error"))

    result_json = asyncio.run(tools.request_join_project("123"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"


def test_invite_project_member_calls_client_and_returns_result() -> None:
    tools, client = _make_project_tools()
    client.invite_project_member = AsyncMock(return_value=True)

    result_json = asyncio.run(
        tools.invite_project_member("123", "456", "Join our project")
    )

    client.invite_project_member.assert_awaited_once_with(
        "123", "456", "Join our project"
    )

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["user_id"] == "456"
    assert payload["invitation_message"] == "Join our project"
    assert payload["message"] == "Invitation sent successfully"


def test_invite_project_member_without_message_calls_client() -> None:
    tools, client = _make_project_tools()
    client.invite_project_member = AsyncMock(return_value=True)

    result_json = asyncio.run(tools.invite_project_member("123", "456"))

    client.invite_project_member.assert_awaited_once_with("123", "456", None)

    payload = json.loads(result_json)
    assert payload["success"] is True
    assert payload["project_id"] == "123"
    assert payload["user_id"] == "456"
    assert payload["invitation_message"] is None


def test_invite_project_member_returns_error_on_client_error() -> None:
    tools, client = _make_project_tools()
    client.invite_project_member = AsyncMock(side_effect=Exception("API error"))

    result_json = asyncio.run(tools.invite_project_member("123", "456"))

    payload = json.loads(result_json)
    assert payload["success"] is False
    assert payload["error"] == "API error"
