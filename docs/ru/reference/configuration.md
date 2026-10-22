# Справочник конфигурации

[English](../../reference/configuration.md) · Русский

Код: `core/dataset.py`, `core/field.py`, `core/entity.py`, `core/settings.py`, `limits.py`, `postgres_config.py`, `trino_config.py`. JSON Schema: [dataset_spec.schema.json](https://github.com/wa-pis/agent-paranoid-android/blob/main/schemas/dataset_spec.schema.json). Версия пакета 1.6.0 и DatasetSpec `schema_version: "1.1"` — разные версии. Совместимость с 1.0 сохраняется без decimal; при импорте payload без schema_version используется legacy 1.0, тогда как новый Python DatasetSpec по умолчанию создаёт 1.1. Указывайте версию явно.

## DatasetSpec

| Ключ | Тип / значение по умолчанию | Назначение и проверка |
| --- | --- | --- |
| schema_version | строка `"1.1"`; совместимая `"1.0"` | decimal требует 1.1; при импорте без ключа действует legacy 1.0 |
| entities | список EntitySpec | Таблицы; имена не дублируются |
| entities[].name | непустая строка | Имя сущности; служебные имена артефактов зарезервированы |
| entities[].row_count | целое >0 | Число генерируемых строк |
| entities[].primary_key | строка или null | Поле существует и имеет is_identifier=true |
| entities[].fields | список FieldSpec | Поля с неповторяющимися именами |
| fields[].name | строка | Имя столбца |
| fields[].data_type | integer/float/decimal/boolean/string/date/datetime | Поддерживаемые скалярные типы |
| fields[].nullable | bool, false | Разрешён ли null |
| fields[].null_ratio | число [0,1], 0 | Доля null; согласуйте с nullable |
| fields[].sensitive | bool, false | Поле требует защиты |
| fields[].semantic_type | строка или null | Семантика; например email |
| fields[].is_identifier | bool, false | Синтетический идентификатор |
| fields[].distribution | объект, {} | Типизированное правило распределения |
| relationships | список, [] | Проверяемые ссылки parent/child |
| constraints | список, [] | Структурированные ограничения |
| business_rules | объект BusinessRules или null | Встроенные правила, общие для интерфейсов и форматов |
| privacy_rules | список, [] | Явные правила приватности; ссылки должны существовать |
| privacy_settings | объект | Политика приватности |
| local_category_fields | список, [] | Отдельные локально разрешённые нечувствительные категории |
| generation_settings | объект | Параметры генерации ниже |
| validation_settings | объект | Какие секции включить в отчёт |

| generation_settings | По умолчанию | Ограничение |
| --- | --- | --- |
| seed | null | Целое 0…2**63-1 для сохранённого spec; укажите явно |
| mode | valid | valid, mixed, negative, edge, load_test |
| invalid_ratio | 0.0 | От 0 до 1; имеет смысл для отрицательных режимов |
| output_format | json | csv, json, sql, parquet |
| load_multiplier | 10 | Целое ≥1; масштаб load_test при отсутствии явного count |
| locale | null | Окружение генерации; фиксируйте вместе с зависимостями |

В `validation_settings` `validate_schema`, `validate_relationships`, `validate_constraints`, `validate_privacy` по умолчанию true, `fail_fast` — false. Не отключайте секции для получения положительного результата. Обязательные post-solve type/privacy проверки генератора не отменяются настройками отчёта.

`synthetic_identifier` может задавать `pool_size` — положительное целое число синтетических ключей для повторяемого ID. Для primary key pool не может быть меньше row_count. Это число, а не сохранённая карта реальных идентификаторов. Типы распределений и полные вложенные модели: [DatasetProfile и DatasetSpec](../dataset_profile_and_spec.md).

## Приоритет

Явный CLI override меняет соответствующий параметр spec: count, seed, mode, invalid_ratio, format. Если override не задан, используются сохранённые настройки и defaults конкретного пути. Значения defaults команд перечислены в [CLI](cli.md); для `generate` не переносите defaults сокращённой CSV-команды по догадке. Переменные окружения управляют только перечисленными в коде интеграциями и бюджетами; они сами по себе не включают AI.

## Основные локальные бюджеты

Байты — целые байты; время — секунды. Значения должны быть положительными, время — конечным. Превышение означает остановку, а не разрешение частичного доверенного результата.

| Переменная | По умолчанию | Что ограничивает |
| --- | ---: | --- |
| TEST_DATA_AGENT_MAX_GENERATION_COUNT | 100000 | Строк на сущность |
| TEST_DATA_AGENT_MAX_INPUT_FILE_BYTES | 134217728 | Байт на входной файл |
| TEST_DATA_AGENT_MAX_TOTAL_INPUT_BYTES | 536870912 | Суммарный вход |
| TEST_DATA_AGENT_MAX_INPUT_ROWS | 1000000 | Входных строк |
| TEST_DATA_AGENT_MAX_INPUT_COLUMNS | 1000 | Столбцов |
| TEST_DATA_AGENT_MAX_INPUT_CELLS | 10000000 | Ячеек |
| TEST_DATA_AGENT_MAX_INPUT_FILES | 100 | Файлов |
| TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS | 1000000 | Символов в ячейке/строке JSON |
| TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES | 536870912 | Оценка распакованного Parquet |
| TEST_DATA_AGENT_MAX_YAML_ALIASES | 50 | YAML aliases |
| TEST_DATA_AGENT_MAX_YAML_DEPTH | 100 | Глубина YAML |
| TEST_DATA_AGENT_MAX_JSON_DEPTH | 100 | Глубина JSON |
| TEST_DATA_AGENT_MAX_BUSINESS_RULES_BYTES | 1048576 | Размер правил |
| TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS | 5000000 | Оценка строк × правил |
| TEST_DATA_AGENT_MAX_OUTPUT_BYTES | 536870912 | Полный выходной bundle |
| TEST_DATA_AGENT_MIN_FREE_DISK_BYTES | 134217728 | Резерв диска |
| TEST_DATA_AGENT_MAX_GENERATION_SECONDS | 300 | Время генерации |
| TEST_DATA_AGENT_MAX_LOCAL_PROFILE_SECONDS | 120 | Время профиля папки |
| TEST_DATA_AGENT_MAX_LOCAL_PROFILE_SAMPLE_ROWS | 1000000 | Общая выборка для правил |

## Интеграционные настройки

| Группа | Обязательные / ключевые настройки | Безопасный смысл |
| --- | --- | --- |
| Generator MCP | TEST_DATA_AGENT_WORKSPACE_ROOT | Явный узкий корень; без настройки используется cwd |
| MCP deadline | TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS=120 | Конечные положительные секунды, server-side настройка |
| Inline profile | TEST_DATA_AGENT_MAX_PROFILE_PAYLOAD_BYTES | По умолчанию 4 MiB, не безграничный payload |
| MCP audit | TEST_DATA_AGENT_AUDIT_LOG; TEST_DATA_AGENT_AUDIT_HMAC_KEY либо TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE | Ровно один источник ключа, base64 ≥32 случайных байт; key file ≤4096 байт без ссылок и групповой/общей записи |
| PostgreSQL | POSTGRES_ALLOWED_SCHEMAS, POSTGRES_ALLOWED_TABLES, POSTGRES_ALLOWED_COLUMNS | Обязательные явные scopes |
| PostgreSQL endpoint | POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DATABASE, POSTGRES_USER, POSTGRES_SSLMODE либо POSTGRES_JDBC_URL | URL без credentials, конфликтующие компоненты отклоняются |
| PostgreSQL secret | POSTGRES_PASSWORD_ENV | Имя runtime переменной с паролем, не пароль |
| PostgreSQL work | POSTGRES_MAX_TABLES=100, POSTGRES_MAX_COLUMNS=1000, POSTGRES_MAX_STATEMENTS=1500, POSTGRES_MAX_RESULT_ROWS=10000, POSTGRES_MAX_RESULT_CELLS=100000, POSTGRES_MAX_SECONDS=120 | Бюджеты одного профиля |
| PostgreSQL timeout | POSTGRES_STATEMENT_TIMEOUT_MS=30000, POSTGRES_LOCK_TIMEOUT_MS=5000 | Миллисекунды; роль отдельно должна быть read-only |
| Trino scope | TRINO_ALLOWED_CATALOGS, TRINO_ALLOWED_SCHEMAS, TRINO_ALLOWED_TABLE_COLUMNS | Первые два обязательны по умолчанию; для query-source обязателен также столбцовый scope |
| Trino endpoint | TRINO_HOST, TRINO_PORT, TRINO_USER, TRINO_HTTP_SCHEME либо TRINO_JDBC_URL | По умолчанию HTTPS; JDBC URL без секретов |
| Trino work | TRINO_MAX_INVOCATION_PROFILED_COLUMNS=100, TRINO_MAX_INVOCATION_STATEMENTS=150, TRINO_MAX_INVOCATION_SECONDS=120 | Общие бюджеты вызова, включая вложенные helpers |
| Trino hardened | TRINO_DEPLOYMENT_PROFILE=shared-hardened и конечный TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES | Нужна явная оценка суммарного scan |
| Query file | SQL_QUERY_MAX_BYTES=65536, SQL_QUERY_MAX_AST_NODES=500, SQL_QUERY_MAX_AST_DEPTH=32, SQL_QUERY_MAX_PROJECTED_COLUMNS=100 | Локальный разбор ограниченного SQL |
| OpenAI | OPENAI_API_KEY | Runtime secret только после согласования передачи |
| GigaChat | GIGACHAT_CREDENTIALS либо GIGACHAT_ACCESS_TOKEN, GIGACHAT_SCOPE, GIGACHAT_CA_BUNDLE_FILE | Ровно один credential, обязательный TLS; experimental |

Полный перечень параметров подключения, per-query scan/time limits, допустимых единиц, audit actor/size и transport budgets сохранён в [расширенном справочнике](configuration.md). Перед изменением конкретного интеграционного параметра прочитайте его строку там; значения из разных единиц не взаимозаменяемы. Не включайте insecure/unrestricted overrides ради обхода ошибки.

Проверка локальной конфигурации: [диагностика](../operations/troubleshooting.md). Проверка результата: [валидация](../getting-started/review-output.md).

## Режимы и точные значения 1.6.0

`edge` создаёт валидные границы, но constraints и business rules могут заменить отдельную границу; маленький count не покрывает всё. `load_test` умножает row_count на load_multiplier (по умолчанию 10); явный --count задаёт точное число без умножения. Повторяемость требует тот же порядок entities в spec, seed и окружение. Python core дополнительно поддерживает signed 64-bit отрицательный seed для совместимости; сохранённый spec — только 0…2**63-1.

`decimal` требует schema_version 1.1 и distribution.kind=decimal_range с precision≤38, scale и строковыми min/max. `numeric_measure` разрешён только для явно проверенной нечувствительной numeric меры; sensitive flags, names и identifiers имеют veto. Пример: [DECIMAL](source-output-matrix.md).

Трансформация использует отдельные BehaviorPolicy/BatchProfile schema_version 0.1; их нельзя подавать вместо DatasetSpec. `resource_limits` и TEST_DATA_AGENT_TRANSFORM_* настраивают её acquisition/decoding, а run caps могут понижать, не молча расширять session/profile ceilings. Полный перечень и единицы: [transformation input limits](../../reference/configuration.md#private-transformation-input-limits-16-development). Receipt и точный snapshot не заменяются переменной окружения.
