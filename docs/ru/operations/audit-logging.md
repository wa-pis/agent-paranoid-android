# Аудит MCP

[English](../../operations/audit-logging.md) · Русский

Опциональный append-only JSONL log использует HMAC-SHA256. Для включения нужны путь TEST_DATA_AGENT_AUDIT_LOG и ровно один источник ключа: TEST_DATA_AGENT_AUDIT_HMAC_KEY либо TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE.

На invocation записываются started и succeeded/failed. Запись содержит service, operation, time, invocation ID, status, sequence и previous MAC. Arguments, SQL, profile payload, rows, return values и error messages не логируются.

## Настройка

Администратор создаёт приватный существующий parent directory и внедряет base64 key минимум из 32 случайных bytes через secret manager. Не публикуйте ключ в чат, shell transcript, CI или MCP client config. Symlink, hard links и group/world-writable log files отклоняются.

Key file ограничен 4096 bytes, читается no-follow, содержит только base64 key с допустимым завершающим newline. Одновременные env key и file key отклоняются. Некорректная включённая audit configuration блокирует tools.

Admission limit по умолчанию 64 MiB, TEST_DATA_AGENT_AUDIT_MAX_BYTES может задать до 1 GiB. Новая invocation допускается только при резерве started + maximum terminal record; уже принятые concurrent terminal events могут ограниченно превысить admission ceiling.

## Проверка и rotation

Audit-verify читает log с тем же ключом и проверяет sequence, previous link и MAC. Одна физическая строка не превышает 4096 bytes с newline; превышение отклоняется до JSON/HMAC parsing.

Для rotation остановите writer, выполните audit-verify, сохраните проверенный файл и final MAC в retention storage, затем запустите worker с новым пустым путём. HMAC не защищает от владельца ключа; локальная chain не доказывает, что корректный хвост не был удалён. Для усиленной retention сохраняйте независимые immutable checkpoints.

Audit на реальном deployment в этом аудите не включался. Примеры provision/verify с локальными путями: [English](../../operations/audit-logging.md).
