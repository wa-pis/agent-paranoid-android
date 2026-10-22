# CLI для автоматизации и JSON

[English](../../reference/cli-automation.md) · Русский

Core commands с --json пишут один версионированный CliSuccessResponse в stdout; human summaries туда не добавляются. Успех имеет schema_version="1.0", ok=true, exit_code=0, status="succeeded", command, artifacts и result. Пути артефактов появляются после публикации.

При validation failure используется тот же envelope с exit_code=1 и status=validation_failed; это возможно для намеренно отрицательного набора. Known errors имеют ok=false и объект error с code, message, command, exit_code, retryable и help. Ветвитесь по error.code, а не тексту message.

## Агентный контракт

| Команда | Тип result |
| --- | --- |
| agent-plan, agent-approve | AgentResult |
| agent-advisor-request | AdvisorRequest либо AdvisorExchange |
| agent-advisor-apply, agent-status | AgentWorkspaceStatus |
| agent-review | AgentReviewReport |

Review не генерирует данные, возвращает fingerprints, metadata полей/связей и safety flags без distribution values. Approval требует fingerprint конкретного spec, рассмотренного человеком. Нельзя автоматически прочитать hash и считать это человеческим review.

Doctor JSON различает available, not_installed, failed и skipped. Успех локальной проверки не подтверждает внешние credentials и сервисы. Проверенные команды планирования: [AI-интеграция](../ai_integration.md); коды: [ошибки CLI](cli-errors.md).
