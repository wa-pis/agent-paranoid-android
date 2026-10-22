# Ошибки CLI и коды завершения

[English](../../reference/cli-errors.md) · Русский

Без --json ожидаемые ошибки дают короткое сообщение stderr и доступный recovery action. Потенциально чувствительные значения ограничиваются или исключаются.

| Код | Значение |
| --- | --- |
| 0 | Успех; вызов без команды также возвращает 0 |
| 1 | Validation failed, в том числе для намеренного negative output |
| 2 | Неверные arguments, input, path, safety/resource checks или configuration |
| 69 | Недоступная optional dependency или external service |
| 70 | Неожиданная внутренняя ошибка; --debug только при безопасном отображении деталей |
| 74 | Ошибка I/O операционной системы |
| 130 | Ctrl+C; сначала выполняется доступный staging cleanup/rollback |

JSON error.code: invalid_arguments, input_not_found, invalid_path, invalid_input, configuration, missing_dependency, external_service, io_failure, internal_error, cancelled.

## Прерванный approval

Agent-status только читает workspace. Если bundle уже опубликован, а completion metadata отсутствует, статус recovery_required сообщает точную команду agent-recover с reviewed-spec-sha256. Выполняйте только действие для текущего состояния и ранее одобренного fingerprint.

Recovery повторно проверяет checkpoint, fingerprints, manifest, rows и source-row non-reuse; новые строки не генерирует. Не исправляйте workspace вручную и не запускайте approve вслепую. См. [диагностику](../operations/troubleshooting.md).
