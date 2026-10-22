# Бюджеты ресурсов

[English](../../operations/resource-budgets.md) · Русский

Профилирование, генерация и validation имеют отдельные конечные пределы. Их превышение останавливает операцию; увеличение бюджета не расширяет доступ к данным.

| Работа | Предел по умолчанию |
| --- | --- |
| Representative release workload | 2500 строк в двух связанных сущностях; 15 секунд и 256 MiB traced allocation на фазу |
| PostgreSQL profile | 100 таблиц, 1000 столбцов, 1500 statements, 10000 metadata/aggregate rows, 100000 cells, 120 секунд |
| Trino invocation | 100 profiled columns, 150 statements, 120 секунд, 4 MiB DB results и response |
| Query source | 64 KiB UTF-8 SQL, 500 AST nodes, depth 32, 100 projected fields |
| JSON depth | 100 до materialization |

Release ceilings — regression guard, а не обещание производительности на любом hardware. Shared-hardened Trino требует finite cumulative estimated-scan ceiling. Metadata wildcard разворачивается в один проверенный snapshot явных столбцов до агрегатов и расходует те же бюджеты.

## Сбои и публикация

Staging, same-filesystem rename и rollback защищают normal/handled failure transitions. Single-entity update нескольких файлов не является общей atomic transaction. Receipt/result markers могут записываться отдельно; agent recovery проверяет checkpoint, spec, manifest и rows без регенерации.

Fsync отдельных writers не создаёт полную гарантию crash/power-loss durability. SIGKILL, storage failure и отключение питания могут оставить staging; это не завершённый bundle. При ENOSPC или deadline во время обработки staging удаляется, final destination и success metadata не публикуются, если процесс может завершить cleanup.

Освободите место или уменьшите согласованный объём; перед увеличением timeout проверьте сложность rules. Не принимайте abandoned staging за результат и не удаляйте rollback без локальной проверки. Точные переменные: [конфигурация](../reference/configuration.md).
