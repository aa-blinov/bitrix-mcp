"""Integration tests for TaskTools using the live Bitrix24 API."""

from __future__ import annotations

import asyncio
import json

import pytest

from bitrix_mcp.client import get_bitrix_client
from bitrix_mcp.config import BitrixConfig
from bitrix_mcp.tools.tasks import TaskTools

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def bitrix_config() -> BitrixConfig:
    """Load Bitrix24 configuration from the environment or skip tests."""
    try:
        return BitrixConfig.from_env()
    except ValueError as exc:
        pytest.skip(f"Bitrix24 credentials are not configured: {exc}")


def test_get_tasks_live_response(bitrix_config: BitrixConfig) -> None:
    """Ensure live API responds with the expected structure."""

    async def _call_live_api() -> dict:
        async with get_bitrix_client(bitrix_config) as client:
            tools = TaskTools(client)
            result_json = await tools.get_tasks(limit=1)
            return json.loads(result_json)

    payload = asyncio.run(_call_live_api())

    assert payload["success"] is True
    assert isinstance(payload.get("tasks"), list)
    assert isinstance(payload.get("count"), int)
    assert payload["count"] <= 1
