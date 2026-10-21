# Architecture

How bitrix-mcp is put together.

The server is one Python package with five layers, and the layers only talk
downwards. The tool functions at the top know about the Model Context
Protocol, the tool classes in the middle know about the entities of a
Bitrix24 portal, and the client at the bottom knows about REST calls. A
change to one layer does not reach the other two.

## The shape

| Module | What it is responsible for |
| --- | --- |
| `src/bitrix_mcp/server.py` | The MCPServer, the 50 tool functions, the lifespan and the command line. The only module that imports `mcp`. |
| `src/bitrix_mcp/client.py` | `BitrixClient`, one method per REST call, and `get_bitrix_client`, the async context manager that opens and closes it. |
| `src/bitrix_mcp/config.py` | `BitrixConfig` and `MCPConfig`, both built from the environment when the module is imported. |
| `src/bitrix_mcp/utils.py` | `parse_json_safe`, `build_success_response` and `build_error_response`. The three functions that decide what an answer looks like. |
| `src/bitrix_mcp/tools/leads.py` | `LeadTools`: 5 tools over `crm.lead`. |
| `src/bitrix_mcp/tools/deals.py` | `DealTools`: 5 tools over `crm.deal`. |
| `src/bitrix_mcp/tools/contacts.py` | `ContactTools`: 5 tools over `crm.contact`. |
| `src/bitrix_mcp/tools/companies.py` | `CompanyTools`: 5 tools over `crm.company`. |
| `src/bitrix_mcp/tools/tasks.py` | `TaskTools`: 12 tools over `task`. One of them, the field list, is registered and does not exist. |
| `src/bitrix_mcp/tools/calendar.py` | `CalendarTools`: 9 tools over `calendar.event` and the meeting status. |
| `src/bitrix_mcp/tools/projects.py` | `ProjectTools`: 9 tools over `sonet_group`, the workgroups. |
| `src/bitrix_mcp/tools/__init__.py` | The seven tool classes and nothing else. |
| `__main__.py` | An entry point that puts `src` on the path. It cannot start the server, and `AGENTS.md` says why. |
| `tests/unit/` | 111 tests over the tool classes, with a mocked client. |
| `tests/integration/` | One live test, marked `integration`, skipped when there are no credentials. |
| `test_real_api.py` | A script that walks a live portal and prints what it finds. |
| `.env.example`, `config/example.env` | Two templates for the same fourteen variables. |

## The data flow

The path of one call, from the assistant to the portal and back:

```
MCP client
  -> stdio transport
  -> tool function in server.py
  -> tool class in tools/
  -> BitrixClient
  -> fast_bitrix24 BitrixAsync
  -> Bitrix24 REST API
  -> JSON string back to the assistant
```

The arguments arrive as strings. A tool function parses them, hands the
pieces to the tool class, and the class calls the client. The client
unwraps the portal's answer into a dict or a list. The tool class wraps it
in the success or the error shape, and the tool function hands the JSON
string back.

The context travels with the request. The lifespan builds one `BitrixClient`
and one instance of each of the seven tool classes, and puts them into an
`AppContext`. A tool reaches that context through `context.request_context`.
When the client does not provide one, the server falls back to the context
it keeps on itself.

The list calls have their own shape:

```
get_all() walks every page -> the finished list -> limit slices it -> count and the records
```

`fast_bitrix24.get_all()` does the walking, and it refuses `start`, `limit`
and `order`. The `limit` of a tool therefore slices a list that has already
been fetched, and `ORDER` is absent from the list tools entirely.

## Decisions worth knowing about

### The tool boundary is a JSON string

The MCP schema declares the structured arguments as strings, so the tool
functions parse them with `parse_json_safe` before anything else happens.
The answer travels back the same way.

The cost is that the schema the assistant reads is less precise than the
schema the code uses: every filter is a string that has to be valid JSON.
The benefit is that the schema is the same in both directions, and an
argument that arrives broken produces an error message that names the
field instead of a traceback.

### One connection for the life of the process

`BitrixClient` is opened once, by the MCPServer lifespan, and the same
object serves every call. The rate limit of 2 requests a second and the
pool of 50 connections are set on it when it is built.

The cost is that the server holds a connection to the portal for as long as
the client keeps the pipe open. The benefit is that the limit is a property
of the process rather than of the call, so two tools cannot overrun it
between them.

### The list tools fetch everything and truncate afterwards

`limit=10` on a portal with 5,000 records still moves 5,000 records across
the wire and into memory. The list is walked by `get_all()`, which has to
see the whole result before the first page can be returned.

The reason is `fast_bitrix24.get_all()`: it paginates on its own and
refuses the `start`, `limit` and `order` parameters that a caller would
need for a cheaper query. The cost is a slow call on a large portal, and
the benefit is that a list never misses a record because the caller
guessed the page wrong.

### Two response shapes come out of the same client

The task methods of the portal answer with a dict and the CRM methods with
a list, so `client.py` unwraps them differently: `result if isinstance(
result, dict) else {}` for a task, and `result[0] if result else {}` for a
CRM record. The unit tests mock the client and never see the difference.

### The context falls back to the server

`_get_app_context` first asks the request context for the lifespan
context. When the attribute is missing or the request context carries
nothing, it takes the context the lifespan set on the server object.

The fallback exists because the client does not always provide a request
context. The cost is that a tool can work with a context that belongs to
another request, and the benefit is that the tool does not fail when the
client is quiet.

### The server is not subclassed

`mcp` 2.x keeps `request_context` on the `Context` a tool receives, so the
subclass that existed to expose it on the server has nothing left to do. The
server is a plain `MCPServer`, and `_get_app_context` reads
`context.request_context.lifespan_context` from the argument the framework
passes in.

### The package is not installed

There is no `pyproject.toml` and no `setup.py`, so `src` goes on the path
by hand. Three places do it: `tests/conftest.py` appends it, `__main__.py`
inserts it, and CI sets `PYTHONPATH=src`. Any command outside pytest needs
it too.

### The type check is switched off for the modules with real code

`mypy.ini` sets `ignore_errors = True` for `bitrix_mcp.client`,
`bitrix_mcp.server` and `bitrix_mcp.tools.*`. That is every module with
logic in it, so `mypy` reports "Success: no issues found in 13 source
files". Without those three lines it reports 23 errors.

### The lint job cannot fail the build

Every step of `.github/workflows/code-quality.yml` carries
`continue-on-error: true`, so ruff reports its findings and the workflow
stays green anyway. With ruff 0.17.1, `ruff check src/ tests/` reports 173
findings, 159 of them in `src/`.

## Boundaries

- **`src/bitrix_mcp/tools/` may not import `mcp`.** The tool classes know
  about the entities of a portal and nothing about the protocol that
  carries them.
- **`src/bitrix_mcp/client.py` may not know about the tool classes.** It
  answers REST calls, and it does not know who is asking.
- **`src/bitrix_mcp/server.py` may not call the portal itself.** It goes
  through a tool class, so that the entity knowledge stays in one place.
- **`src/bitrix_mcp/utils.py` owns the shape of an answer.** A new shape
  belongs there, and nowhere else.
- **A tool never raises.** Every failure travels back as
  `{"success": false, "error": "..."}`.
- **The answer is a JSON string, and its keys are a contract.** A new key
  is fine, a renamed one breaks every client that reads it.
