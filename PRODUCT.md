# Product

<!-- impeccable:product-schema 1 -->

## Platform

server

The product is a Python process, not an application with a screen. It speaks the
Model Context Protocol to an MCP client over stdio, and calls the Bitrix24 REST API
through `fast-bitrix24`. Python 3.10 or newer; CI runs 3.12. The user never sees
this process: they see the tools inside their assistant.

## Users

The code says what the user is doing and nothing about who they are. The old README
described the product as "a Model Context Protocol (MCP) server that enables LLM
assistants to interact with Bitrix24 CRM through natural language".

So the user is someone who runs an MCP client, already has a Bitrix24 portal, and
wants the assistant to work the CRM instead of a browser tab. Two roles follow from
that: a person who asks for the list of new leads, and the assistant that has to
pick the right tool for it.

The GitHub description of the repository is empty, there is one open issue, and
nothing in the code or in the twelve commit messages names a company, a team or a
person. That part is open.

## Product Purpose

The product puts 50 Bitrix24 operations behind the Model Context Protocol, 49 of
which work. The assistant decides which one to call, the server makes the call, and
the answer comes back as JSON.

Success for the user: the assistant answers "what is on my plate this week" by
calling `get_tasks` and `get_calendar_events`, and the answer arrives without the
person opening the portal.

Success for the product: a Bitrix24 portal becomes reachable from whatever
assistant the person already uses. There is no figure to report for that. The
repository has 0 stars, 0 forks and 0 watchers, and the server has no telemetry.

## Positioning

A judgement, read out of the code.

The 50 tool descriptions are the product. Each one names the required attributes,
names the optional ones, gives an example request and says what comes back, in the
same four-part shape. The assistant reads that text when it picks a tool, and the
shape is what makes the choice reliable.

Every answer is a JSON string with a `success` flag, so a refusal and an empty
result are two different values. The assistant can say "there are none" and "that
was refused" in the same conversation.

The list tools have no `ORDER`. `fast_bitrix24.get_all()` paginates itself and
refuses `start`, `limit` and `order`, so ordering was given up rather than faked. A
neighbour that exposes ordering has to settle that conflict some other way.

No comparison with another product was checked, and none should be written from
memory.

## Operating Context

The server runs as a child of the MCP client, on stdio, and lives as long as the
client keeps the pipe open. It is started once per assistant session and holds a
single Bitrix24 connection the whole time.

Credentials come from the environment. The `.env` file in the working directory is
loaded when `config.py` is imported, and a webhook or an OAuth token has to be there
before the process starts. The server refuses to start without one.

The portal answers at its own pace. The client asks for 2 requests a second, with a
pool of 50 connections, and obeys the velocity policy of the portal on top of that.

A list call is expensive by design: it fetches every page and then truncates. On a
portal with a long task history, one `get_tasks` moves the whole history across the
wire.

## Capabilities and Constraints

Confirmed by the code:

- 50 tools over seven entity groups: 5 each for leads, deals, contacts and
  companies, 12 for tasks, 9 for the calendar, 9 for workgroups.
- Two authentication routes: an incoming webhook, or an OAuth access token with the
  portal URL.
- One connection for the life of the process, opened by the FastMCP lifespan.
- 2 requests a second, a pool of 50, the velocity policy respected, all three
  configurable.
- Every tool answers with a JSON string: `{"success": true, ...}` or
  `{"success": false, "error": "..."}`.
- The list tools fetch every page and truncate afterwards. `limit` defaults to 50,
  and 0 means no truncation.
- The participation status of a meeting is read and set with "Y", "N" or "Q".
- 111 unit tests that never touch the network, and one live integration test that
  skips itself when there are no credentials.

Deliberately not true, and worth knowing before a change:

- Only the stdio transport starts. The two HTTP transports raise `TypeError`.
- `get_task_fields` is registered and raises `AttributeError` when called.
- The environment variables for transport, port, host and log level are read and
  ignored.
- The type check is switched off for every module with real code in it.
- The lint job cannot fail the build.
- There is no `ORDER` on any list tool, and no pagination control for the caller.

Open, for the owner to answer:

- Whether the OAuth route works. The code path is there and nothing in the tests
  reaches it.
- Whether the HTTP transports are meant to work, or whether the command line and
  the environment template advertise something that was never finished.
- Which key the answer of a task creation really carries. The tool reads `result`,
  the live script reads `id`.
- Which portal the server was last pointed at, and whether the twelve commits were
  driven by a real deployment.

## Brand Commitments

**Name:** bitrix-mcp. It appears in three spellings: the repository is `bitrix-mcp`,
the package is `bitrix_mcp`, and the name the server announces is `bitrix24-mcp`.
Pick one for new text, and say which.

**Voice:** the tool descriptions are written for a reader that has to choose. They
name the attributes, give an example, and say what comes back, with no adjectives.
The answers are short and factual: "Task created successfully", "Member expelled
successfully".

**Assets:** none. No logo, no screenshots, no landing page, no theme.

## Evidence on Hand

- The code: 13 modules under `src/bitrix_mcp/`, 50 registered tools, and 111 unit
  tests that pass on Python 3.12 with mcp 1.30.0.
- `.env.example` and `config/example.env`, two templates for the same fourteen
  variables, with a `.ru` portal in one and a `.com` portal in the other.
- `test_real_api.py`, a script that finds a project, creates a task in it, updates
  it, and lists leads. It prints what it finds and reports a 401 or a 403 as a
  permission problem rather than a bug.
- `tests/integration/test_tasks_integration.py`, one live test that skips itself
  when the credentials are missing.

Absent, and not to be invented:

- No licence of its own: the repository carried none, and the house standard
  brings MIT.
- No release, no tag, no changelog. The package says 1.0.0 and the default server
  version says 1.0.0.
- No usage numbers: 0 stars, 0 forks, 0 watchers, one open issue, and no telemetry
  in the server.
- No repository description on GitHub.
- No screenshot, no demo, no landing page.
- No measurement of any kind. The old README called the server "high performance",
  and nothing in the repository measures that.

## Product Principles

1. **The tool description is the interface.** The assistant chooses from the text of
   the description, so the description names the required attributes, gives an
   example and says what comes back. A description that drifts from the behaviour
   of its tool is a defect.
2. **Every answer is JSON with a success flag.** A refusal, an empty result and a
   value are three different answers, and the assistant can tell them apart.
3. **A tool never raises.** The caller cannot read a traceback, so an exception
   inside a tool is a lost error message. Errors travel back as
   `{"success": false, "error": "..."}`.
4. **The portal sets the pace.** Two requests a second, the velocity policy obeyed,
   and the full list fetched before it is truncated.
5. **One connection for the life of the process.** The client is built at startup
   and shared by every tool, so the pool and the rate limit hold for every call.

## Accessibility & Inclusion

The product has no interface of its own. The interface is the assistant's, and the
portal's.

- The tool descriptions are the only documentation the assistant gets. They are in
  English, while most of the example values are Russian, "ИП Титов" and "Подготовить
  отчет", so an assistant that copies an example literally writes Russian records
  into an English portal. That inconsistency is open and belongs to the owner.
- The answers are read by a machine, not by a screen reader, and the portal renders
  whatever the tools create.
- No standard has been set for the accessibility of what the tools create: an
  event, a task, a deal. The Bitrix24 portal governs that, and the server has no
  say in it.
- The rate limit means a long list is slow for everyone who shares the portal.
