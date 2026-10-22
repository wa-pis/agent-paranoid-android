# Рабочие процессы CLI

[English](../../reference/cli-workflows.md) · Русский

Для запуска откройте терминал в корне checkout 1.6.0, активируйте окружение и выберите новые выходные папки. Для нового домена остановитесь на review spec до генерации.

| Задача | Проверенная инструкция |
| --- | --- |
| Проверить установку без своих данных | [Установка и встроенное demo](../getting-started/installation.md) |
| Один CSV, seed и replay | [Первый CSV](../getting-started/first-csv.md) |
| Profile → spec → related dataset | [Связанные таблицы](../getting-started/related-tables.md) |
| Авторский spec и edge/load_test/count | [DatasetSpec](../dataset_profile_and_spec.md) |
| CSV/JSON/SQL/Parquet и validate | [Проверить результат](../getting-started/review-output.md) |
| Exact DECIMAL и profile-parquet | [Матрица источников/форматов](source-output-matrix.md) |
| Структурированные бизнес-правила | [Business rules](../how-to/business-rules.md) |
| Plan → review → human gate → approve | [AI-интеграция](../ai_integration.md), [агентные workflows](../how-to/reference-agent.md) |
| Явные замены без preserve | [Отдельная трансформация](../how-to/transformation.md) |

MCP planning approval и local preservation receipt — разные контракты. Агент может потребить ранее выданный matching receipt, но не выдать его или имитировать TTY.

Mixed/negative generation может сохранить намеренно неверный bundle и вернуть exit 1. Это ожидаемый validation_failed, а не успешная проверка. Privacy failure остаётся блокирующим.

Overwrite из DatasetSpec заменяет всю выходную папку с staging/rollback; не применяйте его к входам, spec или правилам. MCP не наследует это право CLI. При recovery_required используйте ровно next action из agent-status с ранее одобренным fingerprint.
