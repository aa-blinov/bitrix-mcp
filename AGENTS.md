# Bitrix24 MCP Server - Development Guide

Quick reference for developing and deploying the Bitrix24 MCP Server.

## Quick Start

```bash
git clone https://github.com/your-org/bitrix-mcp.git && cd bitrix-mcp
python -m venv .venv && source .venv/bin/activate  # Win: .venv\Scripts\Activate
pip install -r requirements.txt
cp .env.example .env  # Set BITRIX24_WEBHOOK
pytest tests/unit/ -q
```

## Project Structure

```
src/bitrix_mcp/
├── client.py          # Wrapper for fast-bitrix24
├── server.py          # MCP server
├── config.py          # Configuration
├── utils.py           # JSON validation, response builders
└── tools/             # MCP tools
    ├── tasks.py       # TaskTools
    ├── leads.py       # LeadTools
    ├── deals.py       # DealTools
    ├── contacts.py    # ContactTools
    ├── companies.py   # CompanyTools
    ├── projects.py    # ProjectTools
    └── calendar.py    # CalendarTools
tests/unit/  # 111 tests (17 per module)
```

## Development

| Task | Command |
|------|---------|
| Run tests | `pytest tests/unit/ -v` |
| Check lint | `ruff check src/` |
| Format code | `ruff format src/` |
| Type checking | `mypy src/bitrix_mcp --config-file=mypy.ini` |
| All checks | `ruff check . && ruff format . --check && mypy src/bitrix_mcp && pytest -q` |
| Real API test | `python test_real_api.py` |

## Architecture

### BitrixClient API

```python
async with get_bitrix_client(config) as client:
    # Tasks
    task = await client.create_task({"TITLE": "..."})
    task = await client.get_task(id)
    await client.update_task(id, fields)
    await client.complete_task(id)
    
    # CRM (leads, deals, contacts, companies)
    leads = await client.get_leads(filter)
    deal = await client.create_deal(fields)
```

### MCP Tools Pattern

All tools follow the same pattern:

```python
@beartype
async def method(self, param: str) -> str:
    parsed, error = parse_json_safe(param, "field_name")
    if error:
        return build_error_response(error)
    result = await self.client.method(parsed)
    return build_success_response(result)
```

### Response format

```json
// Success
{"success": true, "data": {...}}

// Error
{"success": false, "error": "Description"}
```

## Configuration

### .env

```env
BITRIX24_WEBHOOK=https://instance.bitrix24.ru/rest/ID/TOKEN/
MCP_HOST=localhost
MCP_PORT=3000
```

### mypy.ini (type checking)
```ini
[mypy]
python_version = 3.12
ignore_missing_imports = True
```

### pytest.ini
```ini
[pytest]
markers = integration: marks integration tests
```

## CI/CD

### GitHub Actions (automatic)

| Workflow | Trigger | Action |
|----------|---------|--------|
| `tests.yml` | push, PR | 111 unit tests on Python 3.12 |
| `code-quality.yml` | push, PR | ruff lint/format + mypy |

Integration tests **not in CI** (require real API).

## Adding New Features

### 1. New Tool

```python
# src/bitrix_mcp/tools/item.py
from beartype import beartype
from ..client import BitrixClient
from ..utils import parse_json_safe, build_success_response, build_error_response

class ItemTools:
    def __init__(self, client: BitrixClient):
        self.client = client
    
    @beartype
    async def create_item(self, fields: str) -> str:
        parsed, error = parse_json_safe(fields, "fields")
        if error:
            return build_error_response(error)
        result = await self.client.create_item(parsed)
        return build_success_response(result)
```

### 2. Client Method

```python
# src/bitrix_mcp/client.py
@beartype
async def create_item(self, fields: JSONDict) -> JSONDict:
    """Create item"""
    result = await self.client.call("item.create", fields)
    return result if isinstance(result, dict) else {}
```

### 3. Tests

```bash
# tests/unit/test_item.py
pytest tests/unit/test_item.py -v
```

## Performance

- **Rate limit**: 2 requests/sec (automatic)
- **Async**: All operations async, avoid `time.sleep()`
- **Connection pool**: 50 connections (fast-bitrix24 default)

## Deployment

### Docker

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "bitrix_mcp.server"]
```

```bash
docker build -t bitrix-mcp .
docker run -e BITRIX24_WEBHOOK=YOUR_WEBHOOK bitrix-mcp
```

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Webhook no permissions | Enable methods in Bitrix24 settings |
| ModuleNotFoundError | Package not installed | `pip install -e .` or `PYTHONPATH=src pytest` |
| mypy errors | Type checking | Check `mypy.ini` config |
| Tests fail locally | Different Python version | Use Python 3.12+ |
| Invalid JSON error | JSON error | Check syntax and escaping |

## Documentation

- [README.md](README.md) - Project overview
- [Bitrix24 REST API](https://dev.1c-bitrix.ru/rest_help/)
- [fast-bitrix24](https://github.com/yegorg/fast-bitrix24)
- [MCP Spec](https://modelcontextprotocol.io/)

---

**Version**: 3.12+ | **MCP**: 1.0.0+ | **Updated**: 03.04.2026
