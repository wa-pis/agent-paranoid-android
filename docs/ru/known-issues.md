# Известные проблемы

[English](../known-issues.md) · Русский

Stable 1.6.0 прошла [публичную проверку](../release-evidence-1.6.0.md). Внешние отзывы сверены с main 22 октября 2026 года; [план обработки — English](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/external-feedback-1-6) отделяет прежние исправления, текущие ограничения и неподтверждённые наблюдения.

- CSV numeric strings могут выглядеть как телефоны и оставаться sensitive. Не обходите privacy checks и не меняйте exact measures на float ради подавления ошибки. Reviewed numeric profiling планируется; exact decimal generation сохраняет отдельный проверенный контракт --decimal-fields.
- Trino уже поддерживает runtime authentication по проверяемому HTTPS. Для сообщения о внешнем authentication failure нужны configuration/version evidence; fake-driver tests не доказывают работу с конкретным server.
- Numeric shape поддерживает optional zero/subunit frequencies и minimum subunit exponent. В старом профиле evidence может отсутствовать; получите профиль заново. Отрицательный exponent допустим для значений меньше единицы. Отсутствующий Parquet distinct count не означает ноль.
- Validation проверяет объявленные relationships. Пропущенные логические связи, source orphan rates и temporal granularity не подтверждаются одним passing report. Используйте reviewed declarations и явные counts сущностей.

Это направления дальнейшей разработки, а не изменения уже опубликованного wheel 1.6.0. Текущие исправления main и версия выпущенного пакета должны различаться.

Более широкая transformation/session acceptance campaign, включая требуемое настоящее local-terminal preservation acceptance, остаётся открытой. При этом конечный набор вымышленных stable-проверок завершён с [записанными пределами](../release-evidence-1.6.0.md); эти два scope нельзя смешивать. Автотесты не доказывают пригодность приватного набора. Provider adapters остаются experimental, resource/artifact durability имеют отдельные ограничения.

[Отчёт перевода](quality-report.md) перечисляет непроверенные здесь сценарии. Исторические исправления и risk dispositions сохранены в [Security History — English](../security-history.md).
