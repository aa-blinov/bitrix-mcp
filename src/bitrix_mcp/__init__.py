"""Bitrix24 MCP Server Package."""

__version__ = "1.0.0"
__author__ = "Bitrix24 MCP Team"
__description__ = "Model Context Protocol server for Bitrix24 integration"

from .server import create_server

__all__ = ["create_server"]