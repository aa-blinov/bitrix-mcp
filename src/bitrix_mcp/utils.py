"""Utility functions for Bitrix24 MCP tools."""

import json
from typing import Any, Dict, Optional


def parse_json_safe(
    json_str: Optional[str], field_name: str = "field"
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Safely parse JSON string.

    Args:
        json_str: JSON string to parse
        field_name: Name of field for error messages

    Returns:
        Tuple of (parsed_dict, error_message)
        If successful: (dict, None)
        If failed: (None, error_message)
        If empty: (None, None)
    """
    if not json_str:
        return None, None

    try:
        return json.loads(json_str), None
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in {field_name}: {str(e)}"
        return None, error_msg
    except Exception as e:
        error_msg = f"Error parsing {field_name}: {str(e)}"
        return None, error_msg


def build_success_response(data: Dict[str, Any]) -> str:
    """Build successful JSON response."""
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_error_response(error: str) -> str:
    """Build error JSON response."""
    return json.dumps({"success": False, "error": error}, ensure_ascii=False)
