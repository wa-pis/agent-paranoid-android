# MCP-инструменты

[English](../mcp_examples.md) · Русский

Начните с [подключения клиента](how-to/mcp.md); точные schemas установленного server смотрите в tools/list. Transport — stdio, ответы — metadata и paths.

## Безопасный synthetic workflow

1. Profile_csv или заранее разрешённый Trino aggregate profile создаёт безопасное evidence.
2. Plan_dataset либо plan_trino_dataset создаёт plan и spec без generated rows.
3. Inspect_dataset_plan показывает текущий fingerprint. Человек проверяет полный spec.
4. Approve_dataset_plan получает именно этот reviewed_spec_sha256 и создаёт deterministic bundle.
5. Validate_dataset перепроверяет результат; при recovery_required используйте matching reviewed fingerprint.

Generate_dataset и export_dataset — lower-level direct generation. Они не обеспечивают сами по себе human planning gate; клиент должен требовать рассмотрение spec до вызова.

## Отдельные поверхности

Review_transformation не выдаёт receipt. Execute_transformation/common_transformation потребляют exact digest и ранее выданный человеком local receipt, если preservation требуется. Configured_query_session захватывает данные один раз в owned snapshot, затем не reconnect; требует отдельной DB authority и cleanup/expiry.

Default aggregate-only Trino tools не возвращают source rows. Explicit opt-in run_safe_select имеет отдельный row-privacy контракт: source non-string values могут остаться. Он не нужен synthetic workflow и не должен поставлять строки генератору или LLM.

Полная матрица прав, effects и gates: [MCP permissions](reference/mcp-permissions.md). Оригинальные JSON examples и полный tool argument reference: [English](../mcp_examples.md). Примеры client UI и live DB не выполнялись этим аудитом.
