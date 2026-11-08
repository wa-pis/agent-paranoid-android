# Поддержка runtime и интеграций

[English](../../reference/support-policy.md) · Русский

Поддерживаемая CI-матрица — CPython 3.11, 3.12, 3.13, 3.14 и 3.15. Минимум — 3.11. Другие реализации Python могут работать, но не проходят release gate. Новая версия Python считается поддерживаемой после CI и installed-wheel smoke.

Отказ от версии Python — breaking packaging change: нужны release notes, migration и предупреждение минимум за один feature release. Security constraint может сократить срок с явным объяснением. Python 3.11 сохраняется в 1.x, пока это допускают безопасность и зависимости.

| Установка | Возможность и проверка |
| --- | --- |
| base | Детерминированные CSV/JSON и SQL export |
| parquet | Чтение/запись Parquet, installed-wheel/doctor/tests |
| mcp | MCP transport и contract tests |
| trino | Read-only Trino, safe parser, fake и opt-in live checks |
| postgres | Read-only profiling; SQL export остаётся в base |
| openai | Reference adapter, fake-transport tests |
| gigachat | Experimental adapter, fake-SDK tests |
| all | Разработка, демо, контейнеры; обычному пользователю не нужен |

Удаление extra, перенос base-функции в extra или новая неожиданная зависимость между extras — breaking packaging change. JDBC-style URL — только синтаксис endpoint, без JVM.

Provider-neutral DatasetAdvisor/AdvisorExchange/AdvisorProposal — версионированные контракты. OpenAI и GigaChat adapters экспериментальны. Они получают безопасные metadata, а не source/generated rows или секреты; результат ограничен и проверяется по fingerprint. SDK не входит в base. Реальные provider services не используются в обычных тестах.

При сообщении об ошибке укажите версии пакета/Python, extras, платформу и минимальную синтетическую репродукцию. Не прикладывайте production rows, credentials, provider payload или audit keys.

На Python 3.15 PyYAML 6.0.3 на macOS arm64 пока собирается из исходников;
может потребоваться компилятор. Проверяемый профиль использует PyArrow 26.0.1
и Pydantic 2.14.3.
