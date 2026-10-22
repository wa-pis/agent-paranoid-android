# Команды CLI

[English](../../reference/cli.md) · Русский

Команда пакета — test-data-agent. Справка установленной версии является точным источником options:

```bash
test-data-agent --version
test-data-agent --help
```

Для конкретной команды используйте test-data-agent COMMAND --help. Вызов без команды показывает доступные операции и безопасные начальные действия, затем возвращает 0.

## Генерация и проверка

| Команда | Назначение | Результат |
| --- | --- | --- |
| demo | Встроенный вымышленный пример | Синтетический CSV bundle |
| profile-csv | Один CSV | Безопасный profile JSON |
| profile-parquet | Один Parquet с extra parquet | Безопасный profile JSON |
| profile-example | Папка CSV, файл на сущность | Relational profile JSON |
| infer-spec | Вывод проверяемого DatasetSpec | YAML/JSON spec |
| generate-from-csv | Сокращённый путь одной таблицы | Файл и проверочные артефакты |
| generate-from-example | Сокращённый путь связанных таблиц | Bundle |
| generate | По spec или безопасному профилю | Файл или bundle |
| validate | Проверка bundle по spec | Validation report |

## Базы данных

| Команда | Назначение |
| --- | --- |
| profile-postgres | Ограниченный read-only профиль PostgreSQL |
| profile-query | Aggregate-only профиль виртуальной сущности из проверенного PostgreSQL/Trino SELECT |
| export-postgres-sql | Новый PostgreSQL DDL/INSERT script из проверенного контракта |

SQL export создаёт файл. Ни экспорт, ни validate сгенерированного SQL bundle не исполняют SQL в БД. Прямой команды profile-trino нет: используйте Trino MCP или документированный Python API.

## Review-first агент

| Команда | Назначение |
| --- | --- |
| agent-plan | Создать профиль и spec; остановиться до generation |
| agent-review | Metadata checklist и текущий fingerprint |
| agent-advise | Проверяемое предложение optional provider |
| agent-advisor-request | Локальный AdvisorRequest/Exchange |
| agent-advisor-apply | Проверить и применить proposal, сохранив review gate |
| agent-status | Прочитать фазу и next action |
| agent-approve | Генерация по конкретному одобренному spec |
| agent-recover | Проверить опубликованный checkpoint и завершить metadata без новых строк |

Локальный exchange не следует отправлять провайдеру без provider-safe projection. Review fingerprint не заменяет фактического рассмотрения spec человеком.

## Отдельная трансформация

Transform-review читает fixed source/policy/mappings и возвращает value-free решения и snapshot_sha256. --trace добавляет ограниченные ordinal events без literals. --decide редактирует уже валидную policy; SAVE не является approval. --edit-actions/--edit-formats требуют --decide.

Transform-approve — локальный controlling-TTY issuer receipt для eligible preservation. Transform-execute потребляет exact digest и matching receipt, когда сохранение требуется. Agents/MCP receipt не выдают.

Transform-batch имеет create, review, approve, validate, execute и query-execute. Создание profile не одобряет решения. Configured SQL acquisition захватывает разрешённые результаты один раз; дальнейшие session consumers используют frozen capture без reconnect, с конечными admission/expiry/cleanup budgets.

Вход review выбирается policy: CSV, ограниченный Parquet либо captured-query envelope, а не SQL-script. Mapping paths относительны policy. Native Parquet transformation имеет более узкий контракт, чем генерация Parquet; произвольные nested/timestamp shapes не обещаются.

Finite fictional stable campaign завершена с [записанными ограничениями](../../release-evidence-1.6.0.md); она не одобряет пользовательский набор или изменённую activation. Полные options и форматы: [оригинальный CLI contract — English](../../reference/cli.md). Готовый проверенный пример: [локальная трансформация](../how-to/transformation.md).

## Утилиты и aliases

Examples показывает рецепты; doctor выполняет локальный smoke; completion печатает сценарий оболочки; audit-verify проверяет HMAC log.

Profile-csv-folder — alias profile-example; generate-from-csv-folder — alias generate-from-example. Они сохраняют options канонических команд.

Далее: [workflow](cli-workflows.md), [JSON](cli-automation.md), [ошибки](cli-errors.md).
