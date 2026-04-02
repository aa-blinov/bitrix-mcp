# Bitrix24 MCP Server

A Model Context Protocol (MCP) server that enables LLM assistants to interact with Bitrix24 CRM through natural language. Manage tasks, deals, contacts, projects, and calendar events seamlessly.

## Features

- **CRM Management** - Leads, deals, contacts, companies
- **Task Management** - Full lifecycle control with approval, delegation, tracking
- **Calendar Integration** - Events and meeting management
- **Project Management** - Workgroups and team collaboration
- **Async/Await** - Non-blocking operations
- **Type Safety** - Full type hints and validation
- **High Performance** - Built on fast-bitrix24

## Quick Start

```bash
git clone https://github.com/your-org/bitrix-mcp.git && cd bitrix-mcp
python -m venv .venv && source .venv/bin/activate  # Win: .venv\Scripts\Activate
pip install -r requirements.txt
cp .env.example .env
pytest tests/unit/ -q
```

## Configuration

Set your Bitrix24 webhook in `.env`:

```env
BITRIX24_WEBHOOK=https://instance.bitrix24.ru/rest/ID/TOKEN/
```

## Usage

Run the server:

```bash
python -m bitrix_mcp.server
```

Run tests:

```bash
pytest tests/unit/ -v
```

## Tools

The server provides tools for:

- **TaskTools** - Tasks
- **LeadTools** - CRM Leads
- **DealTools** - CRM Deals
- **ContactTools** - CRM Contacts
- **CompanyTools** - CRM Companies
- **ProjectTools** - Projects
- **CalendarTools** - Calendar Events

See [AGENTS.md](AGENTS.md) for complete tool documentation.

## Documentation

- [AGENTS.md](AGENTS.md) - Development guide and architecture
- [Bitrix24 REST API](https://dev.1c-bitrix.ru/rest_help/)
- [fast-bitrix24](https://github.com/yegorg/fast-bitrix24)
