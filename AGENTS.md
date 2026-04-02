# Bitrix24 MCP Server - Development Guide

Компактный справочник для разработки и развертывания Bitrix24 MCP Server.

## Быстрый старт

```bash
git clone https://github.com/your-org/bitrix-mcp.git && cd bitrix-mcp
python -m venv .venv && source .venv/bin/activate  # Win: .venv\Scripts\Activate
pip install -r requirements.txt
cp .env.example .env  # Установите BITRIX24_WEBHOOK
pytest tests/unit/ -q
```

## Структура проекта

```
src/bitrix_mcp/
├── client.py          # Wrapper для fast-bitrix24
├── server.py          # MCP сервер
├── config.py          # Конфигурация
├── utils.py           # JSON validation, response builders
└── tools/             # MCP инструменты
    ├── tasks.py       # TaskTools
    ├── leads.py       # LeadTools
    ├── deals.py       # DealTools
    ├── contacts.py    # ContactTools
    ├── companies.py   # CompanyTools
    ├── projects.py    # ProjectTools
    └── calendar.py    # CalendarTools
tests/unit/  # 111 тестов (17 на каждый модуль)
```

## Разработка

| Задача            | Команда                                                                     |
| ----------------- | --------------------------------------------------------------------------- |
| Запустить тесты   | `pytest tests/unit/ -v`                                                     |
| Проверить lint    | `ruff check src/`                                                           |
| Форматировать код | `ruff format src/`                                                          |
| Type checking     | `mypy src/bitrix_mcp --config-file=mypy.ini`                                |
| Все проверки      | `ruff check . && ruff format . --check && mypy src/bitrix_mcp && pytest -q` |
| Real API тест     | `python test_real_api.py`                                                   |

## Архитектура

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

Все инструменты используют одинаковый паттерн:

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

## Конфигурация

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

### GitHub Actions (автоматические)

| Workflow           | Триггер  | Действие                       |
| ------------------ | -------- | ------------------------------ |
| `tests.yml`        | push, PR | 111 unit тестов на Python 3.12 |
| `code-quality.yml` | push, PR | ruff lint/format + mypy        |

Интеграционные тесты **не** в CI (требуют real API).

## Добавление новой функции

### 1. Новый инструмент

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

### 2. Метод в BitrixClient

```python
# src/bitrix_mcp/client.py
@beartype
async def create_item(self, fields: JSONDict) -> JSONDict:
    """Create item"""
    result = await self.client.call("item.create", fields)
    return result if isinstance(result, dict) else {}
```

### 3. Тесты

```bash
# tests/unit/test_item.py
pytest tests/unit/test_item.py -v
```

## Performance

- **Rate limit**: 2 requests/sec (соблюдается автоматически)
- **Async**: Все операции асинхронные, избегайте `time.sleep()`
- **Connection pool**: 50 connections (fast-bitrix24 по умолчанию)

## Развертывание

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

| Ошибка              | Причина              | Решение                                        |
| ------------------- | -------------------- | ---------------------------------------------- |
| 401 Unauthorized    | Webhook без прав     | Включите методы в настройках Bitrix24          |
| ModuleNotFoundError | Не установлен пакет  | `pip install -e .` или `PYTHONPATH=src pytest` |
| mypy errors         | Type checking        | Проверьте `mypy.ini` конфиг                    |
| Tests fail locally  | Разная версия Python | Используйте Python 3.12+                       |
| Invalid JSON error  | Ошибка в JSON        | Проверьте синтаксис и escaping                 |

## Документация

- [FIXES.md](FIXES.md) - История правок
- [README.md](README.md) - Обзор проекта
- [Bitrix24 REST API](https://dev.1c-bitrix.ru/rest_help/)
- [fast-bitrix24 GitHub](https://github.com/leshchenko1979/fast_bitrix24)
