# Bitrix24 MCP Server Project

This project implements a Model Context Protocol (MCP) server for Bitrix24 integration, enabling LLM assistants to interact with Bitrix24 CRM data through natural language.

## Project Structure
- `src/bitrix_mcp/` - Main MCP server implementation
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation
- `config/` - Configuration files and examples

## Key Components
- **Bitrix24 Tools**: CRM operations (leads, deals, contacts, companies)
- **MCP Integration**: Standard MCP protocol implementation
- **fast-bitrix24**: High-performance Bitrix24 API client
- **Authentication**: Webhook and OAuth token support

## Development Guidelines
- Use type hints and proper error handling
- Follow MCP protocol specifications
- Implement comprehensive logging
- Add docstrings for all public methods
- Use async/await for API operations