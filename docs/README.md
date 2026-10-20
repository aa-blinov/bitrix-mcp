# Documentation

The documents for the Bitrix24 MCP server. The server is a Python process
that speaks the Model Context Protocol over stdio and calls the Bitrix24
REST API, so there is no interface to describe and no picture to show.

| Document | What it covers |
| --- | --- |
| [architecture.md](architecture.md) | The five layers, the path of one call, the decisions behind them and the boundaries. |
| [screenshots/README.md](screenshots/README.md) | Why there are no images, and what would be worth photographing if there were. |
| [../README.md](../README.md) | The front door: the 50 tools, the environment variables and the commands. |
| [../AGENTS.md](../AGENTS.md) | The commands, the layout of the tree, and the fourteen traps that cost a rebuild to learn. |
| [../PRODUCT.md](../PRODUCT.md) | Who the server is for, what it must not turn into, and the parts the code cannot answer. |
| [../DESIGN.md](../DESIGN.md) | The contract the assistant reads: the tool titles, the description shape and the two answers. |

## Reading order

New here: [../README.md](../README.md), then
[architecture.md](architecture.md) for how a call travels.

Changing the code: [architecture.md](architecture.md), then
[../AGENTS.md](../AGENTS.md) for the traps. The traps are the ones the code
does not show: the package that is not installed, the transport that only
works on stdio, the `mcp` ceiling, and the list tools that fetch every
page before they truncate.

Changing what the assistant sees: [../DESIGN.md](../DESIGN.md). It holds
the four labels every tool description uses, the naming of the arguments,
and the two shapes of an answer.

## What is not here

There is no guide to the portal itself. The field names, the permissions
and the limits belong to the Bitrix24 documentation, and the server passes
them through without changing them.

There is no deployment guide either. The server is a child process of the
MCP client: the client starts it, the client closes the pipe, and the
server goes away with it.
