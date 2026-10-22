# Модель угроз

[English](../../concepts/threat-model.md) · Русский

Границы доверия проходят между исходными данными, профилем, spec, внешним provider, детерминированным ядром, файловой системой и MCP-клиентом. Данные профиля, имена и предложения AI рассматриваются как недоверенные.

| Угроза | Защита и предел |
| --- | --- |
| Утечка PII/секретов | Маскирование, замена категорий, запрет небезопасных literals, проверки выхода; это не сертификат анонимности |
| Prompt injection в metadata | Статические instructions отделены от profile data; provider не получает право выполнять tools |
| SQL injection/запись | Ограниченный parser, allowlists, quoted identifiers, read-only роль и бюджеты |
| Выход за workspace | Проверка путей и symlinks; это application boundary, а не OS sandbox |
| Истощение ресурсов | Ограничения входов, строк, правил, output, времени и response |
| Подмена review | Fingerprints связывают утверждённый spec или transformation snapshot с исполнением |
| Сбой публикации | Staging/rollback и проверенный recovery; нет полной гарантии при отключении питания |
| Подмена audit | HMAC chain; владелец ключа и удаление корректного хвоста вне гарантии локальной цепочки |

Default aggregate-only Trino tools отделены от explicit opt-in run_safe_select. Последний возвращает строки с отдельным риском раскрытия. Трансформация смешанного происхождения также отделена от source-free generation; preservation требует local controlling-TTY receipt, который не выдаёт агент.

Процесс с правами пользователя может иметь доступ за пределами workspace. Для строгой изоляции нужны отдельная учётная запись, mounts, network policy и секреты вне доступной клиенту папки. См. [безопасность](safety-model.md), [права MCP](../reference/mcp-permissions.md) и [контейнеры](../operations/containers.md).
