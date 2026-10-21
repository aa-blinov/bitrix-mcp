# Bitrix24 MCP server

Point an MCP client at a Bitrix24 portal and the assistant can work the CRM from a
conversation: read leads, deals, contacts and companies, run the task list, book
calendar events, and manage workgroups. The server speaks the Model Context Protocol
over stdio and exposes 50 tools that reach the Bitrix24 REST API through
`fast-bitrix24`.

[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Unit tests](https://github.com/aa-blinov/bitrix-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/aa-blinov/bitrix-mcp/actions/workflows/tests.yml)

---

## Quick start

```bash
git clone https://github.com/aa-blinov/bitrix-mcp.git
cd bitrix-mcp
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`requirements.txt` asks for `mcp>=2.3.0,<3` and carries the whole ceiling: the
2.x line renamed `FastMCP` to `MCPServer` and moved it to `mcp.server.mcpserver`,
and the code imports it from there.

Put the credentials of the portal in `.env`:

```env
BITRIX24_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/1/your_webhook_key/
```

Then start the server:

```bash
PYTHONPATH=src python -m bitrix_mcp.server
```

The package lives in `src/` and is not installed, so `PYTHONPATH=src` is what puts it
on the path.

An MCP client starts the server itself, so point it at the module:

```json
{
  "mcpServers": {
    "bitrix24": {
      "command": "python",
      "args": ["-m", "bitrix_mcp.server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/bitrix-mcp/src",
        "BITRIX24_WEBHOOK_URL": "https://your-portal.bitrix24.ru/rest/1/your_webhook_key/"
      }
    }
  }
}
```

Python 3.10 or newer, which is the floor the `mcp` package sets. CI runs 3.12.

## What it does

- **Leads, deals, contacts and companies.** 20 tools over the four CRM entities:
  list with a filter and a field selection, read one by ID, create, update, and the
  field metadata the portal knows about.
- **Tasks.** 11 working tools: list, read, create, update, complete, start, approve,
  disapprove, renew, hand to another user, and start watching. A twelfth, "Get Task
  Fields", is registered and raises an error when it is called.
- **Calendar.** 9 tools: list events by date range or section, read one, create,
  update, delete, list calendars, find the nearest events, and read or set the
  participation status of a meeting ("Y", "N" or "Q").
- **Workgroups.** 9 tools: list, create and update projects, list the tasks of a
  project, add, list, expel and invite members, and ask to join.
- **Every answer is JSON.** A call that worked answers `{"success": true, ...}`; a
  call that did not answers `{"success": false, "error": "..."}` with the message
  from the portal inside.
- **Two ways in.** An incoming webhook, or an OAuth access token with the portal
  URL.
- **One connection, held open.** The client is built when the server starts and
  lives for the whole process, with a pool of 50 connections and 2 requests a
  second.

## How it works

```
MCP client
  -> stdio transport (MCPServer)
  -> 50 tool functions (src/bitrix_mcp/server.py)
  -> seven tool classes (src/bitrix_mcp/tools/)
  -> BitrixClient (src/bitrix_mcp/client.py)
  -> fast_bitrix24 BitrixAsync
  -> Bitrix24 REST API
```

The tool boundary is a JSON string. The MCP schema declares the fields as strings,
`{"TITLE": "..."}`, and the tool classes parse them with `parse_json_safe`. The
answer travels back the same way, as a JSON string.

The seven tool classes hold the entity knowledge: `LeadTools`, `DealTools`,
`ContactTools`, `CompanyTools`, `TaskTools`, `CalendarTools` and `ProjectTools`.
`BitrixClient` holds the transport knowledge: one method per REST call, with the
response unwrapped into a dict or a list. Nothing under `tools/` knows about MCP,
and nothing above `server.py` knows about Bitrix24.

`BitrixClient` is opened once, by the MCPServer lifespan, and the seven tool objects
are put in an `AppContext`. A tool reaches that context through the request
context; when the client does not provide one, the server keeps the context on
itself and falls back to it.

The list calls go through `fast_bitrix24.get_all()`, which walks the pages itself
and refuses `start`, `limit` and `order`. The `limit` argument of a tool truncates
the finished list afterwards, and the `ORDER` parameter is left out of the list
tools for the same reason.

## Configuration

Everything is read from the environment, and `.env` in the working directory is
loaded when `config.py` is imported.

| Variable | Default | What it does |
| --- | --- | --- |
| `BITRIX24_WEBHOOK_URL` | none | The incoming webhook. Either this or the pair below is required. |
| `BITRIX24_ACCESS_TOKEN` | none | An OAuth token, used together with `BITRIX24_PORTAL_URL`. |
| `BITRIX24_PORTAL_URL` | none | The portal base URL, for example `https://acme.bitrix24.ru`. |
| `BITRIX24_REQUESTS_PER_SECOND` | `2` | The ceiling on the request rate. |
| `BITRIX24_REQUEST_POOL_SIZE` | `50` | The size of the connection pool. |
| `BITRIX24_RESPECT_VELOCITY_POLICY` | `true` | Whether the velocity policy of the portal is obeyed. |
| `BITRIX24_SSL_VERIFY` | `true` | Whether the TLS certificate is checked. |
| `MCP_SERVER_NAME` | `bitrix24-mcp` | The name the server announces. |
| `MCP_SERVER_VERSION` | `1.0.0` | Read into the configuration and then dropped. |
| `MCP_SERVER_DESCRIPTION` | `Model Context Protocol server for Bitrix24 integration` | Read into the configuration and then dropped. |
| `MCP_TRANSPORT` | `stdio` | Read into the configuration and then dropped. |
| `MCP_PORT` | `8000` | Read into the configuration and then dropped. |
| `MCP_HOST` | `localhost` | Read into the configuration and then dropped. |
| `MCP_LOG_LEVEL` | `INFO` | Read into the configuration and then dropped. |

The transport, the port, the host and the log level come from the command line:

```bash
PYTHONPATH=src python -m bitrix_mcp.server --transport stdio --port 8000 --host localhost --log-level INFO
```

Only the stdio transport starts. The two HTTP ones fail against the installed
`mcp`, and [AGENTS.md](AGENTS.md) has the details.

`.env.example` and `config/example.env` hold the same variables. The first names a
`.ru` portal, the second a `.com` one.

## Development

```bash
pip install -r requirements.txt "mcp<2"                  # install
pip install pytest pytest-asyncio pytest-cov ruff mypy   # the tools CI uses
PYTHONPATH=src pytest tests/unit/ -v                     # 111 unit tests
PYTHONPATH=src pytest tests/unit/ --cov=src/bitrix_mcp --cov-report=term-missing
ruff check src/ tests/                                    # lint
ruff format src/ tests/ --check                          # format
mypy src/bitrix_mcp --config-file=mypy.ini                # types
PYTHONPATH=src pytest tests/integration/ -m integration  # one live test
python test_real_api.py                                   # a live portal, prints what it finds
```

| Path | What it holds |
| --- | --- |
| `src/bitrix_mcp/server.py` | The MCPServer, the 50 tool functions, the lifespan, the CLI. |
| `src/bitrix_mcp/client.py` | `BitrixClient`, one method per REST call. |
| `src/bitrix_mcp/config.py` | `BitrixConfig` and `MCPConfig`, read from the environment. |
| `src/bitrix_mcp/utils.py` | JSON parsing and the two response shapes. |
| `src/bitrix_mcp/tools/` | Seven tool classes, one per entity. |
| `tests/unit/` | 111 tests over the tool classes, with a mocked client. |
| `tests/integration/` | One live test, marked `integration`, skipped without credentials. |
| `test_real_api.py` | A script that walks a live portal and prints what it finds. |

The unit tests never touch the network: the client is a `MagicMock` and every tool
is called through `asyncio.run()`. The decisions behind the server are written down
in [PRODUCT.md](PRODUCT.md).

## License

[MIT](LICENSE), © Alexander Blinov.
