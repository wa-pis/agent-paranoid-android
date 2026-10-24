# Подключить MCP-клиент

[English](../../how-to/mcp.md) · Русский

Для подключения Trino по логину и паролю используйте
[готовый пример настройки MCP](trino.md#trino-mcp-basic).

## Для чего это нужно

MCP позволяет клиенту вызывать генератор и получать сводки и пути к артефактам. Разделяйте процесс генерации с файловым workspace и процесс чтения Trino.

## Что получится в результате

Клиент видит инструменты generator; профиль и spec остаются внутри заданной папки.

## Предварительные требования

Установлен extra mcp; для Trino также trino. Нужен MCP-клиент с поддержкой stdio (обмена сообщениями через стандартные потоки). Конкретный интерфейс клиента не проверен выполнением. Проверка SDK и регистрации выполняется локальными тестами.

## Пошаговое выполнение

### Шаг 1. Создайте отдельную рабочую папку

**Что сделать:** Создайте out/ru-mcp из корня проекта и узнайте её абсолютный путь.

**Где выполнить:** Терминал, корень checkout.

**Команда или пример:**

```bash
python -c "from pathlib import Path; p=Path('out/ru-mcp'); p.mkdir(parents=True, exist_ok=False); print(p.resolve())"
```

**Что должно произойти:** Напечатан абсолютный путь.

**Как проверить:** Это обычная новая папка; не домашняя папка целиком и не корень диска.

**Если не получилось:** Если папка есть, выберите новое имя. Не используйте широкую область доступа.

### Шаг 2. Добавьте сервер в клиент

**Что сделать:** В конфигурации своего клиента замените оба placeholder на полученные реальные абсолютные пути. Путь command — исполняемый файл из вашего окружения.

**Где выполнить:** Локальный конфигурационный файл MCP-клиента.

**Команда или пример:**

```json
{
  "mcpServers": {
    "test-data-agent-generator": {
      "command": "/ABSOLUTE/PATH/.venv-ru/bin/test-data-agent-mcp-generator",
      "env": {"TEST_DATA_AGENT_WORKSPACE_ROOT": "/ABSOLUTE/PATH/out/ru-mcp"}
    }
  }
}
```

**Что должно произойти:** При запуске клиента поднимается generator stdio server.

**Как проверить:** В списке инструментов клиента есть plan_dataset и inspect_dataset_plan.

**Если не получилось:** На Windows command указывает на .venv-ru\Scripts\test-data-agent-mcp-generator.exe. Проверьте синтаксис клиента, extra и права; не вставляйте secrets в JSON.

### Шаг 3. Проверьте локальный SDK

**Что сделать:** Проверьте доступность generator tool registration.

**Где выполнить:** Терминал с активным окружением.

**Команда или пример:**

```bash
test-data-agent doctor --require-extra mcp
```

**Что должно произойти:** Проверка локального MCP проходит без запуска внешнего сервиса.

**Как проверить:** Код 0; это не проверка конфигурации конкретного клиента.

**Если не получилось:** Если missing_dependency, установите .[mcp] тем же интерпретатором.

## Проверка результата

Положите только разрешённый синтетический CSV в workspace. В клиенте сначала вызовите plan_dataset, затем inspect_dataset_plan; генерация должна ждать review точного spec. Инструменты, аргументы и JSON-примеры: [MCP Tools](../../mcp_examples.md).

## Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| `Tool arguments failed validation` | Аргументы не соответствуют схеме | Запросите tools/list; исправьте типы, не повторяйте чувствительный payload в чате. |
| `Invalid request parameters` | Некорректный MCP/JSON-RPC запрос | Используйте совместимый SDK и корректную схему. |
| `unsafe filesystem path` | Путь вне workspace или symlink | Перенесите разрешённый файл в обычную папку workspace. |

## Безопасная последовательность инструментов

1. `plan_dataset`: источник внутри workspace, новый agent workspace, count, seed, format.
2. `inspect_dataset_plan`: прочитать checklist и `review.current_spec_sha256`.
3. Человек проверяет `dataset_spec.yaml` и именно этот fingerprint.
4. `approve_dataset_plan`: передать одобренный `reviewed_spec_sha256`.
5. Проверить manifest и validation; сообщить только сводку и пути.

Для Trino сначала `profile_table_safe`, затем `plan_trino_dataset` и тот же review. Другие этапы доступны отдельно: `profile_csv`, `infer_dataset_spec`, `generate_dataset`, `validate_dataset`. Наличие низкоуровневого инструмента не отменяет согласованную политику review.

Trino **default aggregate-only** инструменты возвращают метаданные без исходных литералов. Отдельный **explicit opt-in** `run_safe_select` включается через `TRINO_ENABLE_SAFE_SELECT`; он маскирует строки, но может сохранять нечувствительные нестроковые значения источника. Такой результат не является анонимным или source-free; его нельзя передавать LLM или использовать как сгенерированные данные. Не включайте этот инструмент для описанного workflow.

Generator ограничивает пути workspace, но это не sandbox процесса. Используйте отдельного системного пользователя/контейнер для недоверенных клиентов. Значения по умолчанию: frame 1 MiB, response 4 MiB, 32 active requests; Trino дополнительно ограничивает работу и параллельность. См. [границы MCP](mcp.md) и [аудит](../../operations/audit-logging.md).


## Следующий шаг

[AI workflow](../ai_integration.md).

## Отдельные инструменты трансформации 1.6.0

Generator MCP также регистрирует `execute_transformation`, `common_transformation` и `configured_query_session`. Они возвращают ограниченные метаданные и пути, не строки. Наличие инструмента не разрешает обработку набора или сохранение source values. MCP и агент не выдают preservation receipts: человек делает это отдельно в local controlling-TTY. Capture использует согласованные read-only scopes; исполнение должно потреблять тот же frozen batch без повторного подключения. См. [трансформацию](transformation.md) и [MCP contract](mcp.md).

`TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS` по умолчанию 120 секунд задаётся server-side; tool arguments его не расширяют. Независимые лимиты генерации, ввода/вывода и правил остаются в силе.
