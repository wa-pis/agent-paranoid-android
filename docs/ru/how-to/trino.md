# Профилирование через Trino

[English](../../how-to/trino.md) · Русский

Trino — отдельный read-only источник метаданных и агрегатов. В 1.6.0 сохранены JDBC-style endpoints без credentials, точные allowlists, ограниченные table-qualified wildcards и profile-query. Java и JDBC driver не нужны.

## Перед запуском

Нужны extra trino, а для MCP — также mcp; проверенный HTTPS endpoint, read-only роль и явно согласованный catalog/schema/table/column scope. Секреты внедряются через runtime secret mechanism. Сетевое выполнение этого руководства **не проверено**.

Локальная проверка установки из активного окружения:

```bash
test-data-agent doctor --require-extra trino
```

Doctor проверяет клиент и SQL policy без обращения к координатору. Он не подтверждает аутентификацию или доступ к таблицам.

## Настройте scope

Иллюстрация конфигурации для вымышленного endpoint; заменяйте её только согласованными параметрами:

```bash
export TRINO_HOST=trino.example.internal
export TRINO_PORT=8443
export TRINO_USER=test_data_agent
export TRINO_HTTP_SCHEME=https
export TRINO_ALLOWED_CATALOGS=warehouse
export TRINO_ALLOWED_SCHEMAS=analytics
export TRINO_ALLOWED_TABLE_COLUMNS='warehouse.analytics.orders.*'
export TRINO_DEPLOYMENT_PROFILE=shared-hardened
export TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES=1073741824
```

Catalog и schema — независимые allowlist-множества. Wildcard разрешён только для точной таблицы в restricted mode: ограниченные metadata разворачиваются в отсортированные явные столбцы до первого агрегата. Он не разрешает SQL `*`, literals, preserve или provider payload. Column selectors не являются общим ACL всех MCP tools; ограничения видимости задаются также правами БД.

Вместо компонентов endpoint допускается TRINO_JDBC_URL без credentials. Явные компоненты должны совпадать с URL. SSL=false, неизвестные свойства, токены, роли, proxies и headers в URL отклоняются. Basic/JWT/Kerberos/GSSAPI/OAuth2 и client certificates требуют своих настроек; см. [оригинальный полный справочник подключения](../../reference/configuration.md#trino-connection).

## Получите профиль

MCP server запускается локальным клиентом через test-data-agent-mcp-trino. Default aggregate-only tools возвращают разрешённые metadata и агрегаты. Затем безопасный профиль передаётся generator plan_trino_dataset без исходных строк; spec проверяется до генерации. См. [MCP](mcp.md).

Отдельный explicit opt-in run_safe_select по умолчанию отсутствует. Его ограниченные строки могут содержать исходные нестроковые значения; маскирование не делает их анонимными. Эти строки не передаются генератору или LLM.

## Воспроизводимый инфраструктурный пример

В репозитории есть examples/local_trino/run.sh и варианты run-jdbc.sh, run-wildcard.sh, run-query.sh. Они используют синтетический TPC-H tiny в одноразовом контейнере, удаляют контейнер и сохраняют безопасный профиль, spec, новые данные и отчёты. В этом аудите инфраструктурные сценарии не запускались.

Query-source требует явного column scope, хранит fingerprint вместо текста SQL и результатов. Не обходите отказ через unrestricted/insecure flags. Успех проверяется по scope, коду завершения, профилю без строк и отчётам сгенерированного набора; ошибка авторизации требует исправления grants или сужения запроса.
