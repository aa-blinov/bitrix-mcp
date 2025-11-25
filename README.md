# Bitrix24 MCP Server

This repository contains a Model Context Protocol (MCP) server for Bitrix24. It lets LLM assistants work with Bitrix24 CRM data, tasks, calendar events, and project management through natural language commands.

## Features

- **CRM Operations**: Manage leads, deals, contacts, and companies
- **Task Management**: Create, update, and track tasks with full lifecycle management (approve, start, delegate, renew, watch, disapprove)
- **Calendar Integration**: Manage calendar events and schedules with meeting status tracking
- **Project Management**: Handle projects (workgroups) and team collaboration with member management
- **High Performance**: Built on the fast-bitrix24 library for efficient API calls
- **Type Safety**: Full type hints and validation
- **Async Support**: Non-blocking operations using async/await
- **Flexible Authentication**: Support for webhooks and OAuth tokens
- **Multiple Transports**: Support for stdio, HTTP, and Server-Sent Events

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd bitrix-mcp
```

2. Install dependencies (pick one workflow):

   **Using uv (recommended)**

```bash
uv venv
uv pip install -r requirements.txt
```

**Using standard venv + pip**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
pip install -r requirements.txt
```

3. Configure your Bitrix24 credentials:

```bash
cp config/example.env .env
# Edit .env file with your Bitrix24 credentials
```

## Configuration

Create a `.env` file in the project root with your Bitrix24 credentials:

### Option 1: Webhook URL (Recommended for simplicity)

```env
BITRIX24_WEBHOOK_URL=https://your-portal.bitrix24.com/rest/1/your_webhook_key/
```

### Option 2: OAuth Token (Recommended for production)

```env
BITRIX24_ACCESS_TOKEN=your_access_token
BITRIX24_PORTAL_URL=https://your-portal.bitrix24.com
```

### Optional Settings

```env
# Performance settings
BITRIX24_REQUESTS_PER_SECOND=2
BITRIX24_REQUEST_POOL_SIZE=50
BITRIX24_RESPECT_VELOCITY_POLICY=true
BITRIX24_SSL_VERIFY=true

# MCP Server settings
MCP_SERVER_NAME=bitrix24-mcp
MCP_LOG_LEVEL=INFO
```

## Usage

### Running the server

**Using uv (auto-manages the virtual environment):**

```bash
uv run python -m src.bitrix_mcp.server
```

**Using an activated virtual environment:**

```bash
python -m src.bitrix_mcp.server
```

Add transport overrides as needed, for example:

```bash
uv run python -m src.bitrix_mcp.server --transport streamable-http --port 8000
```

Note: legacy helpers `start_server.bat` and `start_server.sh` remain for convenience but offer no additional functionality compared to the commands above.

### Testing

```bash
uv run python test_server.py
```

## Available Tools

### CRM Management

#### Lead Management

- **get_leads**: Retrieve leads with filtering and pagination
- **create_lead**: Create new leads
- **update_lead**: Update existing leads
- **get_lead_fields**: Get available lead fields

#### Deal Management

- **get_deals**: Retrieve deals with filtering
- **create_deal**: Create new deals
- **update_deal**: Update existing deals
- **get_deal_fields**: Get available deal fields

#### Contact Management

- **get_contacts**: Retrieve contacts
- **create_contact**: Create new contacts
- **update_contact**: Update existing contacts
- **get_contact_fields**: Get available contact fields

#### Company Management

- **get_companies**: Retrieve companies
- **create_company**: Create new companies
- **update_company**: Update existing companies
- **get_company_fields**: Get available company fields

### Task Management

- **get_tasks**: Retrieve tasks with filtering and pagination
- **get_task**: Get a specific task by ID
- **create_task**: Create new tasks
- **update_task**: Update existing tasks
- **complete_task**: Mark tasks as completed
- **approve_task**: Approve tasks
- **start_task**: Start task execution
- **delegate_task**: Delegate tasks to other users
- **renew_task**: Renew task deadlines
- **start_watching_task**: Start watching tasks for updates
- **disapprove_task**: Disapprove tasks
- **get_task_fields**: Get available task fields

### Calendar Management

- **get_calendar_events**: Retrieve calendar events with date filtering
- **create_calendar_event**: Create new calendar events
- **update_calendar_event**: Update existing calendar events
- **delete_calendar_event**: Delete calendar events
- **get_calendar_list**: Get list of available calendars
- **get_calendar_event_by_id**: Get detailed calendar event information
- **get_nearest_calendar_events**: Get upcoming calendar events
- **get_meeting_status**: Check meeting participation status
- **set_meeting_status**: Set meeting participation status

### Project Management

- **get_projects**: Retrieve projects (workgroups) with filtering
- **create_project**: Create new projects
- **update_project**: Update existing projects
- **get_project_tasks**: Get tasks for a specific project
- **add_project_member**: Add members to projects
- **get_project_members**: Get project member list
- **expel_project_member**: Remove members from projects
- **request_join_project**: Send requests to join projects
- **invite_project_member**: Invite users to join projects

## Usage Examples

### CRM Operations

#### Getting Leads

```json
{
  "tool": "get_leads",
  "arguments": {
    "filter_params": "{\"STATUS_ID\": \"NEW\"}",
    "select_fields": "ID,TITLE,NAME,EMAIL",
    "limit": 10
  }
}
```

#### Creating a Lead

```json
{
  "tool": "create_lead",
  "arguments": {
    "fields": "{\"TITLE\": \"New Lead\", \"NAME\": \"John\", \"EMAIL\": [{\"VALUE\": \"john@example.com\", \"VALUE_TYPE\": \"WORK\"}]}"
  }
}
```

#### Getting Deals with Filtering

```json
{
  "tool": "get_deals",
  "arguments": {
    "filter_params": "{\"STAGE_ID\": \"NEW\"}",
    "select_fields": "ID,TITLE,OPPORTUNITY,STAGE_ID",
    "order": "{\"DATE_CREATE\": \"DESC\"}",
    "limit": 20
  }
}
```

### Task Management

#### Getting Tasks

```json
{
  "tool": "get_tasks",
  "arguments": {
    "filter_params": "{\"STATUS\": \"2\"}",
    "select_fields": "ID,TITLE,DESCRIPTION,STATUS,RESPONSIBLE_ID",
    "limit": 15
  }
}
```

#### Creating a Task

```json
{
  "tool": "create_task",
  "arguments": {
    "fields": "{\"TITLE\": \"Complete project documentation\", \"DESCRIPTION\": \"Write comprehensive docs for the project\", \"RESPONSIBLE_ID\": 1, \"DEADLINE\": \"2024-02-01\"}"
  }
}
```

#### Completing a Task

```json
{
  "tool": "complete_task",
  "arguments": {
    "task_id": "123"
  }
}
```

#### Getting a Task by ID

```json
{
  "tool": "get_task_by_id",
  "arguments": {
    "task_id": "123"
  }
}
```

#### Approving a Task

```json
{
  "tool": "approve_task",
  "arguments": {
    "task_id": "123"
  }
}
```

#### Starting a Task

```json
{
  "tool": "start_task",
  "arguments": {
    "task_id": "123"
  }
}
```

#### Delegating a Task

```json
{
  "tool": "delegate_task",
  "arguments": {
    "task_id": "123",
    "user_id": "456"
  }
}
```

#### Renewing a Task

```json
{
  "tool": "renew_task",
  "arguments": {
    "task_id": "123"
  }
}
```

#### Starting to Watch a Task

```json
{
  "tool": "start_watching_task",
  "arguments": {
    "task_id": "123"
  }
}
```

#### Disapproving a Task

```json
{
  "tool": "disapprove_task",
  "arguments": {
    "task_id": "123"
  }
}
```

### Calendar Management

#### Getting Calendar Events

```json
{
  "tool": "get_calendar_events",
  "arguments": {
    "date_from": "2024-01-01",
    "date_to": "2024-01-31",
    "limit": 20
  }
}
```

#### Creating a Calendar Event

```json
{
  "tool": "create_calendar_event",
  "arguments": {
    "fields": "{\"NAME\": \"Team Meeting\", \"DATE_FROM\": \"2024-01-15 10:00:00\", \"DATE_TO\": \"2024-01-15 11:00:00\", \"DESCRIPTION\": \"Weekly team sync\"}"
  }
}
```

#### Getting Calendar Event by ID

```json
{
  "tool": "get_calendar_event_by_id",
  "arguments": {
    "event_id": "123"
  }
}
```

#### Getting Nearest Calendar Events

```json
{
  "tool": "get_nearest_calendar_events",
  "arguments": {
    "days": 30,
    "max_events_count": 10
  }
}
```

#### Getting Meeting Status

```json
{
  "tool": "get_meeting_status",
  "arguments": {
    "event_id": "123"
  }
}
```

#### Setting Meeting Status

```json
{
  "tool": "set_meeting_status",
  "arguments": {
    "event_id": "123",
    "status": "Y"
  }
}
```

### Project Management

#### Getting Projects

```json
{
  "tool": "get_projects",
  "arguments": {
    "filter_params": "{\"ACTIVE\": \"Y\"}",
    "order": "{\"NAME\": \"ASC\"}",
    "limit": 10
  }
}
```

#### Creating a Project

```json
{
  "tool": "create_project",
  "arguments": {
    "fields": "{\"NAME\": \"Mobile App Development\", \"DESCRIPTION\": \"New mobile application project\", \"VISIBLE\": \"Y\"}"
  }
}
```

#### Getting Project Tasks

```json
{
  "tool": "get_project_tasks",
  "arguments": {
    "project_id": "5",
    "limit": 25
  }
}
```

#### Adding Project Member

```json
{
  "tool": "add_project_member",
  "arguments": {
    "project_id": "5",
    "user_id": "3",
    "role": "member"
  }
}
```

#### Expelling a Project Member

```json
{
  "tool": "expel_project_member",
  "arguments": {
    "project_id": "5",
    "user_id": "3"
  }
}
```

#### Requesting to Join a Project

```json
{
  "tool": "request_join_project",
  "arguments": {
    "project_id": "5",
    "message": "Please add me to the project"
  }
}
```

#### Inviting a User to Join a Project

```json
{
  "tool": "invite_project_member",
  "arguments": {
    "project_id": "5",
    "user_id": "3",
    "message": "We'd like you to join our project"
  }
}
```

## Project Structure

```
bitrix-mcp/
├── src/
│   └── bitrix_mcp/
│       ├── __init__.py
│       ├── server.py          # Main MCP server
│       ├── client.py          # Bitrix24 client wrapper
│       ├── config.py          # Configuration management
│       └── tools/             # MCP tools implementation
│           ├── __init__.py
│           ├── leads.py       # CRM Lead management
│           ├── deals.py       # CRM Deal management
│           ├── contacts.py    # CRM Contact management
│           ├── companies.py   # CRM Company management
│           ├── tasks.py       # Task management
│           ├── calendar.py    # Calendar event management
│           └── projects.py    # Project (workgroup) management
├── config/
│   └── example.env           # Example configuration
├── tests/
│   ├── conftest.py           # Test configuration
│   ├── integration/          # Integration tests
│   │   └── test_tasks_integration.py
│   └── unit/                 # Unit tests
│       ├── test_calendar.py  # Calendar tool tests
│       ├── test_companies.py # Company tool tests
│       ├── test_contacts.py  # Contact tool tests
│       ├── test_deals.py     # Deal tool tests
│       ├── test_leads.py     # Lead tool tests
│       ├── test_projects.py  # Project tool tests
│       └── test_tasks.py     # Task tool tests
├── requirements.txt
├── README.md
├── test_server.py           # Test script
├── start_server.bat         # Optional Windows wrapper
├── start_server.sh          # Optional Linux/Mac wrapper
└── .github/
    └── copilot-instructions.md
```

## Development

### Installing Development Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov black flake8 mypy
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/ tests/
```

### Linting

```bash
flake8 src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Integration with LLM Clients

This MCP server can be integrated with various LLM clients that support the Model Context Protocol:

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bitrix24": {
      "command": "python",
      "args": ["-m", "src.bitrix_mcp.server"],
      "cwd": "/path/to/bitrix-mcp"
    }
  }
}
```

### Generic MCP Client

```python
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def connect_to_bitrix():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.bitrix_mcp.server"],
        cwd="/path/to/bitrix-mcp"
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Call a tool
            result = await session.call_tool("get_leads", {
                "limit": 5
            })
            print(result)
```

## Security Notes

- Store your Bitrix24 credentials securely in the `.env` file
- Never commit credentials to version control
- Use webhook URLs for development, OAuth tokens for production
- Consider IP restrictions on your Bitrix24 webhooks
- Enable SSL verification in production environments

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

1. **Connection errors**: Check your webhook URL or OAuth credentials
2. **Rate limiting**: Adjust `BITRIX24_REQUESTS_PER_SECOND` in `.env`
3. **SSL errors**: Set `BITRIX24_SSL_VERIFY=false` for testing (not recommended for production)
4. **Import errors**: Ensure virtual environment is activated and dependencies are installed

### Getting Help

- Check the Bitrix24 REST API documentation
- Review the fast-bitrix24 library documentation
- Open an issue on GitHub for bugs or feature requests
