# AGENTS.md — agent context for `bitrix-mcp`

A Python server that puts 50 Bitrix24 operations behind the Model Context Protocol,
so an MCP client can drive a Bitrix24 portal from a conversation. It reaches the
portal over the REST API through `fast-bitrix24`, holds one connection for the life
of the process, and speaks to the client over stdio.

This file is what you need to work on the project without reading all of it. The
repository is small, and the traps below carry most of the cost: each one costs an
hour the first time, and each was checked against the code rather than guessed.

## Run / build / test

```bash
python3.12 -m venv .venv && source .venv/bin/activate   # 3.10 is the floor mcp sets; CI runs 3.12
pip install -r requirements.txt "mcp<2"                  # mcp 2.x removed mcp.server.fastmcp
pip install pytest pytest-asyncio pytest-cov ruff mypy   # the tools CI installs
PYTHONPATH=src pytest tests/unit/ -q                     # 111 unit tests, no network
PYTHONPATH=src pytest tests/integration/ -m integration # 1 live test, skipped without credentials
ruff check src/ tests/                                   # lint
ruff format src/ tests/ --check                         # format check
mypy src/bitrix_mcp --config-file=mypy.ini               # types
PYTHONPATH=src python -m bitrix_mcp.server               # start the server on stdio
python test_real_api.py                                  # a live portal, prints what it finds
```

There is no build step. The package is not installed and there is no
`pyproject.toml`.

## Where things live

| Path | What it holds |
| --- | --- |
| `src/bitrix_mcp/server.py` | The MCPServer: 50 tool functions, the lifespan, the CLI. The only file that imports `mcp`. |
| `src/bitrix_mcp/client.py` | `BitrixClient`, one method per REST call, and `get_bitrix_client`. |
| `src/bitrix_mcp/config.py` | `BitrixConfig` and `MCPConfig`, read from the environment when the module is imported. |
| `src/bitrix_mcp/utils.py` | `parse_json_safe`, `build_success_response`, `build_error_response`. |
| `src/bitrix_mcp/tools/` | Seven tool classes, one per entity. Knows about Bitrix24, not about MCP. |
| `src/bitrix_mcp/client_old.py.bak` | A dead copy of the client from before the pagination rewrite. Nothing imports it. Delete it rather than read it. |
| `tests/unit/` | 111 tests over the tool classes, with a mocked client. |
| `tests/integration/` | One live test, marked `integration`. |
| `test_real_api.py` | A script that walks a live portal: finds a project, creates a task in it, updates it, then lists leads. |
| `.env.example`, `config/example.env` | Two copies of the environment template. |

## Traps

- **The package is not installed, and `src` goes on the path by hand.** There is no
  `pyproject.toml` and no `setup.py`, so `pip install -e .` does not work and
  `pip install -r requirements.txt` does not install `bitrix_mcp`. Three places put
  `src` on the path: `tests/conftest.py` appends it, `__main__.py` inserts it, and CI
  sets `PYTHONPATH=src`. Any command outside pytest needs `PYTHONPATH=src` too.
- **`__main__.py` cannot start the server.** `main()` in `server.py` is a plain
  function, and `__main__.py` calls `asyncio.run(main())`, which raises
  `ValueError: a coroutine was expected, got None`. Use
  `PYTHONPATH=src python -m bitrix_mcp.server`.
- **The network transports are unexercised.** `main()` calls
  `mcp.run(transport=..., port=..., host=...)`. `MCPServer.run()` takes
  `transport` and forwards the rest as keyword arguments, so the `TypeError`
  that mcp 1.x raised for `--port` is gone. Nothing here has started the server
  on `streamable-http` or `sse`, so the transports are untested rather than
  working.
- **The SDK is 2.x, and the import path says so.** `requirements.txt` asks for
  `mcp>=2.3.0,<3`, and the server is a plain `MCPServer` from
  `mcp.server.mcpserver`. The 2.x line kept `request_context` on the `Context`
  a tool receives, which is why the subclass that used to expose it on the
  server is gone. An import of `mcp.server.fastmcp` now fails at collection in
  all seven unit files.
- **The MCP environment variables do nothing.** `config.py` reads `MCP_TRANSPORT`,
  `MCP_PORT`, `MCP_HOST` and `MCP_LOG_LEVEL` into `MCPConfig`; `main()` takes the
  transport, the port, the host and the log level from argparse and never looks at
  them. `MCP_SERVER_VERSION` and `MCP_SERVER_DESCRIPTION` are read and then dropped,
  because `create_server()` hands `MCPServer` only the name. A server started with
  `MCP_TRANSPORT=sse` still speaks stdio. Once the HTTP transports work, `MCPServer`
  reads `FASTMCP_HOST` and `FASTMCP_PORT` from its own settings, not from `MCP_HOST`
  and `MCP_PORT`.
- **`Get Task Fields` is registered and does not exist.** `server.py` calls
  `app_ctx.task_tools.get_task_fields()`, and `TaskTools` has no such method, so the
  call raises `AttributeError: 'TaskTools' object has no attribute
  'get_task_fields'`. The lead, deal, contact and company field tools are real; only
  the task one is missing.
- **`limit` truncates after the fetch, it does not limit the request.** The list
  tools call `get_all()`, which walks every page, and slice the finished list.
  `limit=10` on a portal with 5,000 records still moves 5,000 records.
- **`ORDER` is absent from the list tools on purpose.**
  `fast_bitrix24.get_all()` paginates itself and refuses `start`, `limit` and
  `order`. Every "the ORDER parameter is not supported" note in a tool description
  comes from that.
- **Two response shapes come out of the same client.** The task methods return a
  dict and the CRM methods a list, so `client.py` unwraps them differently:
  `result if isinstance(result, dict) else {}` for tasks, `result[0] if result else
  {}` for CRM. The unit tests mock the client and never see the difference.
- **The task id is read under two different keys.** `TaskTools.create_task` reads
  `result.get("result")` and `test_real_api.py` reads `result.get("id")` from the
  same value. One of them is wrong, and the mocked tests do not catch it.
- **The tool boundary is a JSON string.** The MCP schema declares the fields as
  strings, so `parse_json_safe` returns `(None, None)` for an empty string and
  `(None, "Invalid JSON in ...")` for a broken one. The tools check the error, not
  the value.
- **The calendar creation example contradicts its own requirement.** The
  description of `create_calendar_event` says the fields must include `NAME` and
  `DATE_FROM`, and the example next to it uses `name`, `from` and `to`.
  `CalendarTools.create_event` passes the parsed dict straight to
  `calendar.event.add`, so the keys the caller picks are the keys the portal
  receives.
- **The type check is hollow.** `mypy.ini` sets `ignore_errors = True` for
  `bitrix_mcp.client`, `bitrix_mcp.server` and `bitrix_mcp.tools.*`, which is every
  module with real code in it. `mypy src/bitrix_mcp --config-file=mypy.ini` reports
  "Success: no issues found in 13 source files"; without those three lines it
  reports 23 errors, among them the missing `get_task_fields` and the
  `run(port=..., host=...)` call.
- **The lint job cannot fail the build.** Every step of
  `.github/workflows/code-quality.yml` carries `continue-on-error: true`. With ruff
  0.17.1, `ruff check src/ tests/` reports 173 findings, 159 of them in `src/`;
  `ruff format src/ tests/ --check` passes.

## Style / safety rails

- **Every tool answers with a JSON string**, in one of two shapes:
  `{"success": true, ...}` or `{"success": false, "error": "..."}`. The caller is an
  assistant that cannot read a traceback, so a tool must never raise.
- **Comments explain why, never what.**
- **No emoji, in any file.**
- **Do not add a dependency to `requirements.txt` without writing down why.** The
  list is short on purpose, and the ceiling on `mcp` matters.
- **The two environment templates have drifted.** `.env.example` names a `.ru` portal
  and `config/example.env` names a `.com` one. Change both, or delete one.
- **Lower the rate limit rather than raise it.** Two requests a second is the
  default, and the velocity policy of the portal is obeyed on top of it.
- **Do not change the shape of a tool answer.** An assistant parses it. A new key
  is fine, a renamed one is a breaking change.
- **The unit tests never reach the network.** The client is a `MagicMock` with
  `AsyncMock` methods, and each test calls the tool through `asyncio.run()`. Without
  `pytest-asyncio` pytest warns about two unknown options in `pytest.ini` and the
  111 tests still pass.

## Where the product truth lives

`PRODUCT.md` holds it. Read it before changing the behaviour of the server, and
write the change there when the behaviour changes.
