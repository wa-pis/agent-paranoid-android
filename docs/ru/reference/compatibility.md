# Поверхности совместимости

[English](../../reference/compatibility.md) · Русский

В 1.6.0 сохранены принятые RC5 контракты. Текущий статус подтверждается stable evidence, а не устаревшими формулировками подготовки версии.

| Сохранённая команда | Каноническая | Срок |
| --- | --- | --- |
| profile-csv-folder | profile-example | Все 1.x |
| generate-from-csv-folder | generate-from-example | Все 1.x |

Aliases принимают те же options и dispatch; пока не deprecated.

| Python wrapper | Канонический модуль |
| --- | --- |
| test_data_agent.business_rules | test_data_agent.rules.models |
| test_data_agent.business_validator | test_data_agent.rules.validation |
| test_data_agent.rules_engine | test_data_agent.rules.engine |
| test_data_agent.scenario | test_data_agent.rules.scenarios |

Wrappers переэкспортируют те же объекты через __all__ и сохраняются в 1.x. Новый код использует test_data_agent.rules. Transitional summary["field"]/summary.get("field") также остаётся в 1.x; предпочтительны typed attributes.

Deprecation требует replacement, migration, предупреждения и минимум одного feature release и 90 дней. Удаление transitional access невозможно до 2.0. Security fixes могут сократить срок с объяснением.

GenerationSpec удалён в 0.6.0. Safe legacy profile с columns — поддерживаемый input adapter metadata, не старый generation spec.

Transformation consumers появились после 1.5.0 и входят в 1.6.0 отдельно от source-free API. Консольный MCP server регистрирует common_transformation/configured_query_session с workspace/session owner; при custom SDK embedding владелец должен быть передан явно и закрыт при shutdown.

FieldProfile/FieldSpec distributions принимают {} либо поддерживаемый typed kind. Непустые opaque dict без корректного kind отклоняются, а не передаются provider. См. [совместимость DatasetSpec](../concepts/dataset-spec-compatibility.md).
