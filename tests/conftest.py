"""Shared pytest configuration for Bitrix MCP tests."""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.append(str(_SRC_PATH))
