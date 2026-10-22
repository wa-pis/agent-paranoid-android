# Стабильность публичных контрактов

[English](../../reference/stability.md) · Русский

Публичная поверхность определяется контрактом и __all__, а не доступностью внутреннего имени для import. Новые optional fields и tools могут быть additive; удаление, несовместимые типы или смысл поля — breaking change с migration guidance.

| Поверхность | Контракт |
| --- | --- |
| Python | test_data_agent.__all__ и public-python-api.json |
| CLI | Parser, aliases, exit codes, versioned JSON; cli-parser-surface.json |
| Generator/Trino MCP | Tools, schemas и response boundaries; mcp-generator-tools.json, mcp-trino-tools.json |
| DatasetSpec | Схема 1.1 и совместимость 1.0; dataset-spec.json |
| Advisor | Provider-neutral exchange/proposal; advisor-exchange.json |
| Bundle | Manifest, validation, layout и encodings; artifact-layout.json |
| Provider adapters | Experimental, пока явно не повышен статус |

Fixtures находятся в tests/fixtures/contracts. Не делайте внутренние helpers публичным API по аналогии. Регистрация transformation consumers не является одобрением набора или review изменённой activation.

Поддерживаемые aliases/wrappers сохраняются по [политике совместимости](compatibility.md). Версии runtime и extras описаны в [поддержке](support-policy.md). Любое изменение safety boundary требует отдельных исполнимых проверок.
