"""Entry point for running the Bitrix24 MCP server as a module."""

import asyncio
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from bitrix_mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())