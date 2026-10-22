# Права MCP

[English](../../reference/mcp-permissions.md) · Русский

Tool discovery — перечень возможностей, а не разрешение на набор данных. Сначала сравните версию пакета и tools/list, затем настройте узкую политику фактического клиента.

## Кто предоставляет доступ

| Слой | Ответственный | Что разрешает |
| --- | --- | --- |
| MCP client | Оператор клиента | Discovery/calls и confirmation rules, если клиент их поддерживает |
| OS/контейнер | Администратор deployment | Process identity, readable inputs, writable outputs/tmp, secrets и outbound network |
| Application configuration | Администратор server | Workspace, DB allowlists, optional row tools и budgets |
| База данных | DBA | Read-only grants и metadata visibility |
| Workflow review | Человек | Exact synthetic spec; отдельно local controlling-TTY receipt для preservation |

Оба console servers используют stdio: клиент запускает локальный процесс и обменивается сообщениями через stdin/stdout. Эти entrypoints не требуют listening HTTP port, remote MCP login, MCP OAuth scopes или inbound firewall rule. Не придумывайте permissions/scopes keys в server config. DB authentication — отдельное исходящее подключение.

Client confirmation не ограничивает другой клиент и не создаёт OS sandbox. Нормальный server не предоставляет произвольный per-tool ACL; optional row-tool registration — отдельная настройка. Для строгой изоляции нужны отдельные process credentials, mounts и network policy.

## Минимальные права процесса

Synthetic generation требует runtime, выбранные workspace inputs/spec/rules, запись новых bundles и bounded tmp. Ни DB/provider credentials, ни network не нужны. TEST_DATA_AGENT_WORKSPACE_ROOT должен быть узкой существующей папкой; без него используется cwd. Paths проверяются на выход за root и symlink escapes, но OS rights владельца процесса не исчезают.

Trino profiling требует только проверенные TLS/auth files, временное хранилище и outbound доступ к выбранному endpoint read-only ролью; generator workspace не нужен. Transformation читает только разрешённые snapshots/policies/mappings/receipt, пишет новый bundle и owned temporary work. Configured SQL capture отдельно требует DB authority и собственного provisioned network deployment.

Secrets хранятся вне client-accessible workspace. Root, sudo, весь home и Docker socket worker не нужны. Generator MCP не имеет folder-overwrite argument: CLI --overwrite не расширяет его права.

## Generator tools

| Tool | Эффект и review |
| --- | --- |
| profile_csv | Прочитать выбранный CSV, создать безопасный profile |
| infer_dataset_spec | Создать spec из безопасного profile; без generation |
| plan_dataset | Создать planning directory; остановиться для human review |
| plan_trino_dataset | То же по bounded safe Trino profile; подключения к БД нет |
| inspect_dataset_plan | Прочитать состояние и current fingerprint |
| approve_dataset_plan | После human review exact reviewed_spec_sha256 создать synthetic output и completion |
| recover_dataset_plan | Revalidate ранее одобренный checkpoint без новых строк |
| generate_dataset | Прямая generation из reviewed spec/rules; сама не enforce planning sequence |
| export_dataset | Новая generation в выбранном формате, не конвертация source rows |
| validate_dataset | Прочитать matching spec/manifest/bundle; новый report только при output_path |
| review_transformation | Value-free review fixed snapshot; не approve/execute |
| execute_transformation | Exact digest и matching local receipt при preserve; новый mixed-origin bundle |
| common_transformation | Batch review/temporary validate/execute; local receipt потребляется, не выдаётся |
| configured_query_session | Open один раз захватывает разрешённые queries; дальнейшие review/validate/execute используют frozen capture без reconnect; expiry/close/shutdown очищают owned state |

Console composition регистрирует 14 tools. Module-level SDK object содержит 12 base tools; common/session extensions требуют явно внедрённого workspace/session owner и close при shutdown. Ответы содержат metadata, reports и paths, а не source/generated rows или mapping literals. Audit добавляет started/terminal events даже к read-only calls.

Synthetic approval проверяет hash, но не может доказать фактическое чтение spec человеком. Клиент обязан получить review перед approve; direct generation не должна обходить эту политику. Возобновление старого чата не расширяет scope: проверьте сохранённый plan и полный текущий spec перед новым consent.

Preservation receipt выдаёт только человек в local controlling-TTY. MCP не имеет issuer, approved boolean или права вводить APPROVE. Tool confirmation, database grant и новый hash не заменяют matching receipt. После изменения source/policy/classification/mapping нужен новый review/approval.

## Trino tools

Default aggregate-only tools: list_catalogs, list_schemas, list_tables, describe_table, profile_table, profile_column, profile_table_safe и ограниченные rule probes profile_foreign_key, profile_temporal_ordering, profile_formula_rule, profile_conditional_required, profile_conditional_allowed_values, profile_aggregate_mapping.

Explicit opt-in run_safe_select отсутствует по умолчанию и включается только TRINO_ENABLE_SAFE_SELECT=true. Он возвращает bounded row-shaped результат: strings и распознанные sensitive values маскируются, другие source values могут сохраниться. Не используйте эти строки для генерации и не передавайте LLM.

Catalog/schema allowlists — независимые множества, а не пары. TRINO_ALLOWED_TABLE_COLUMNS сужает profile_table_safe, но не является универсальным ACL metadata/count/rule/row tools. Strict table/column visibility должна задаваться самой DB identity. Wildcard разворачивает разрешённую таблицу в bounded explicit columns, не даёт unrestricted SQL или право раскрывать категории.

## Проверка политики

Разрешите plan/inspect; потребуйте human review перед approve; добавляйте profile/infer/validate/direct generation по задаче. Transformation и row-returning tools исключите из synthetic-only policy.

На вымышленной фикстуре проверьте отсутствие generated output до approval, confinement и responses без rows. Независимо проверьте DB grants и отказ вне allowlist. Missing tools требуют проверки версии/extras/runtime/client policy, а не расширения прав. Safety refusal исправляется сужением scope, paths или budgets; unrestricted/insecure flags не являются recovery.

MCP server не требует OpenAI/GigaChat keys и не предоставляет advisor tool. Собственный AI-клиент может использовать внешний model provider по своей политике; его shell/file access — отдельные возможности.
