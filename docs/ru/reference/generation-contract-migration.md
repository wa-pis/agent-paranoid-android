# Изменения контракта генерации

[English](../../reference/generation-contract-migration.md) · Русский

Stable 1.6.0 сохраняет принятые RC5 исправления. Версия DatasetSpec остаётся 1.1. После обновления регенерируйте затронутые фикстуры и рассмотрите отличия; seed не обещает прежние байты между версиями.

- Зависимости формул вычисляются до consumers независимо от порядка списка. Циклы и несколько assignments одному target отклоняются.
- Rejected constraints/relationships игнорируются; inferred правила явно переданного spec исполняются. Active aggregate mapping на rejected link требует исправления.
- Nullable FK сохраняют null; one-to-one capacity учитывает только non-null ссылки; required identifiers не бывают пустыми.
- String lengths включают synthetic prefix. Короткая нечувствительная строка использует случайные символы, если prefix не помещается; required string не допускает max length 0.

Valid/edge/load_test проходят обязательные schema/relationship/constraint/privacy проверки до возврата строк и публикации. Отключение report sections не отменяет safety checks генерации. Business-rule mutations перепроверяются; конфликт поздних temporal/aggregate/conditional изменений приводит к отказу, а не частичному output.

Mixed/negative публикуют controlled-invalid data только в допустимом представлении с отчётом. CLI возвращает validation_failed/exit 1. Parquet может использовать marked scalar columns; direct Arrow consumer должен учитывать apa.scalar_encoding. Privacy остаётся обязательной для всех режимов.

Standalone validate проверяет значения при включённой privacy section. CSV numeric operands интерпретируются по заявленному типу для revalidation; это не ослабляет pre-export проверку generated strings. Связи назначаются round-robin, numeric sampling uniform: сохранение корреляций и source fan-out не обещается.

После 1.6.0 main также исправляет numeric CSV evidence/cache и scalar PostgreSQL PK profiling. Описание исправлений не меняет содержимое выпущенного wheel. Подробности и точная история: [оригинальная миграция — English](../../reference/generation-contract-migration.md).


## Сведения о числовом хранении CSV

Перепрофилируйте CSV-папки: формат кэша 8 заменяет формат 7. Неоднозначные поля
могут получить `numeric_storage_type`, сохраняя чувствительность и маскировку.
Для старого неоднозначного профиля без этих сведений сначала нужно новое
профилирование. Явный синтетический `numeric_measure`/`decimal_range` задаётся
через существующий `infer-spec --decimal-fields`; исходные границы не выводятся.
Проверьте изменённые отпечатки. В ожидающем подтверждения workspace перенесите
только проверенное поле, сохраните настройки генерации плана и выполните
`agent-review` с подтверждением нового отпечатка. Для изменённого источника или
профиля создайте новый план; уже подтверждённый план не редактируйте. DatasetSpec остаётся версии 1.1.
Подробнее: [профилирование](profiling.md#reviewed-csv-numeric-replacements).
