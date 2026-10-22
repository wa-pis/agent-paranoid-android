# Профилирование PostgreSQL

[English](../../how-to/postgresql.md) · Русский

## Для чего это нужно

Используйте базу как источник разрешённых метаданных и агрегатов, когда CSV неудобен. Этот путь не предназначен для выгрузки строк или выполнения произвольного SQL.

## Что получится в результате

Профиль PostgreSQL или Trino для последующего review DatasetSpec; исходная база не изменяется.

## Предварительные требования

**Не проверено выполнением на живой БД.** Нужны соответствующие extras, сетевой доступ, TLS и уже созданная администратором read-only роль. Человек согласует точные сервер, БД, таблицы, поля, бюджеты и локальное место сохранения. Секрет вводится через runtime secret mechanism, не через Git или чат.

## Пошаговое выполнение

### Шаг 1. Настройте точный scope PostgreSQL

**Что сделать:** Замените вымышленные host/database/user на согласованные значения. Секрет WAREHOUSE_PASSWORD должен быть уже внедрён средой; не печатайте его.

**Где выполнить:** macOS/Linux, терминал в корне checkout; PowerShell требует собственного синтаксиса $env:.

**Команда или пример:**

```bash
export POSTGRES_SOURCE_ID=warehouse
export POSTGRES_HOST=db.example.internal
export POSTGRES_PORT=5432
export POSTGRES_DATABASE=analytics
export POSTGRES_USER=synthetic_reader
export POSTGRES_SSLMODE=verify-full
export POSTGRES_PASSWORD_ENV=WAREHOUSE_PASSWORD
export POSTGRES_ALLOWED_SCHEMAS=public
export POSTGRES_ALLOWED_TABLES=public.orders
export POSTGRES_ALLOWED_COLUMNS=public.orders.order_id,public.orders.amount
```

**Что должно произойти:** Scope ограничен одной таблицей и двумя полями.

**Как проверить:** Локально: test-data-agent doctor --require-extra postgres. Администратор отдельно подтверждает SELECT-only права и цепочку сертификатов.

**Если не получилось:** Doctor не проверяет БД. При недоступности сертификата или секрета остановитесь; не отключайте TLS.

### Шаг 2. Получите безопасный профиль

**Что сделать:** После согласования выполните ограниченное чтение.

**Где выполнить:** Тот же терминал.

**Команда или пример:**

```bash
test-data-agent profile-postgres --output out/ru-postgres/profile.json
```

**Что должно произойти:** Создан агрегированный профиль без строк источника.

**Как проверить:** Код 0; entities содержит только согласованные поля.

**Если не получилось:** Используйте фиксированную категорию ошибки; не публикуйте driver output, DSN или secret. Проверьте allowlist и права с администратором.

### Шаг 3. Создайте контракт для review

**Что сделать:** Выведите spec, затем откройте его локально.

**Где выполнить:** Корень checkout.

**Команда или пример:**

```bash
test-data-agent infer-spec out/ru-postgres/profile.json --count 25 --output out/ru-postgres/dataset_spec.yaml
```

**Что должно произойти:** Спецификация готова к проверке человеком.

**Как проверить:** Проверьте типы, sensitive, диапазоны и row_count; строки ещё не сгенерированы.

**Если не получилось:** Если метаданных недостаточно, уточните правило у владельца данных; не добавляйте sample rows.

## Проверка результата

После review продолжите командой generate с явным seed в новой папке и validate из [основного процесса](../getting-started/related-tables.md). Read-only session — дополнительная защита; права самой роли должны исключать запись.

## Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| Ошибка конфигурации / код 2 | Отсутствует allowlist или конфликтуют компоненты URL | Проверьте scope; не включайте unrestricted-доступ. |
| external_service / код 69 | Сеть, TLS, аутентификация или доступ | Согласуйте с администратором; не передавайте исходное сообщение драйвера. |

## Trino

Прямой команды `profile-trino` нет. Используйте Trino MCP `profile_table_safe`, а затем generator `plan_trino_dataset`, либо документированный Python API. Для воспроизводимого изолированного примера есть [local_trino](https://github.com/wa-pis/agent-paranoid-android/tree/main/examples/local_trino); он не запускался в этом аудите и требует своей инфраструктуры.

Минимальные согласованные настройки: `TRINO_HOST`, `TRINO_PORT`, `TRINO_USER`, `TRINO_HTTP_SCHEME=https`, `TRINO_ALLOWED_CATALOGS`, `TRINO_ALLOWED_SCHEMAS`, `TRINO_ALLOWED_TABLE_COLUMNS`. Укажите точные `catalog.schema.table.column`; задайте бюджеты из [справочника](../reference/configuration.md). Для `shared-hardened` обязателен конечный `TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES`.

## Профиль результата ограниченного запроса

`profile-query` принимает локальный UTF-8 файл с одним разрешённым single-table SELECT. Пример для scope выше, **не проверен выполнением на БД**:

```sql
SELECT o.order_id, o.amount
FROM public.orders AS o
WHERE o.order_id < 1000
```

Сохраните как `query.sql` в корне checkout. После локального review и разрешения на чтение выполните:

```bash
test-data-agent profile-query query.sql --adapter postgres --source-id warehouse --entity orders_query --output out/ru-query/profile.json
```

Для Trino используйте `--adapter trino` с полностью квалифицированной таблицей `catalog.schema.table`, явным allowlist полей и настроенным Trino-клиентом. JOIN, CTE/WITH, подзапросы и запись не поддерживаются; запрос проходит разбор AST (синтаксического дерева), затем только no-row schema probe и агрегатные обёртки. Результат содержит fingerprint, не SQL-текст, литералы или query rows. Профиль проверяют и передают infer-spec так же, как табличный профиль.

Endpoint можно задавать credential-free `POSTGRES_JDBC_URL` или `TRINO_JDBC_URL`; это не JDBC-исполнение. Wildcard `schema.table.*` / `catalog.schema.table.*` разрешает лишь ограниченное раскрытие столбцов через метаданные, не сохранение исходных категорий.

Подробности: [PostgreSQL](postgresql.md), [Trino](trino.md), [SQL policy](../../agent-guides/trino-security.md). Прямые нечувствительные date/timestamp projections могут получать проверенные temporal bounds; sensitive и derived поля их не получают. Declared numeric(p,s) несёт precision/scale, но не exact bounds: используйте reviewed decimal_range.


## Следующий шаг

[MCP и Trino](mcp.md).

## Зависимости SQL-выражений

Профиль запроса может помечать `has_unmodeled_expressions=true`. В этом случае автоматический infer-spec по умолчанию останавливается: независимая генерация столбцов не сохраняет SQL-формулы. Составьте независимо проверенный spec; публичного флага обхода для автоматического inference здесь нет. В SQL policy 1.1 разрешены aliased SUM/COUNT/MIN/MAX/AVG и ограниченный GROUP BY по явным столбцам одной таблицы; HAVING, DISTINCT aggregates и grouping expressions не поддерживаются. Такой профиль не доказывает сохранение SQL-зависимостей. Обычное агрегатное профилирование не смешивайте с отдельной configured_query_session capture-трансформацией.


## Исправление primary key в текущем main

После 1.6.0 main распознаёт объявленный single-column integer или string primary key независимо от имени, например ticket_no/record_code. Identifiers создаются заново; sensitivity сохраняется. Чтобы получить эти metadata, сохранённый профиль нужно построить заново.

Composite primary key отклоняется до aggregate scans, даже если column allowlist открывает только один компонент. Он не превращается в ложный однопольный PK. Для других типов нужен независимо проверенный generation spec; automatic inference не поддерживает composite uniqueness.

Это описание текущего main, а не новое содержимое выпущенного wheel 1.6.0. Полный контракт: [исходная инструкция — English](../../how-to/postgresql.md).
