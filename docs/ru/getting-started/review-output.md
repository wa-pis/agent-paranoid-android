# Проверить результат

[English](../../getting-started/review-output.md) · Русский

## Для чего это нужно

Валидация сверяет данные с DatasetSpec; manifest помогает восстановить условия генерации. Это обязательные технические проверки перед использованием фикстуры, но предметную полезность оценивает человек.

## Что получится в результате

Повторный отчёт valid=true и подтверждённое число строк.

## Предварительные требования

Выполните [CSV-генерацию](first-csv.md), не изменяйте её spec и файлы. Команды выполняйте в корне того же checkout.

## Пошаговое выполнение

### Шаг 1. Выполните повторную валидацию

**Что сделать:** Создайте отдельный отчёт, сохранив первоначальный.

**Где выполнить:** Терминал, корень checkout.

**Команда или пример:**

```bash
test-data-agent validate out/ru-csv/dataset_spec.json out/ru-csv --output out/ru-csv-revalidation.json
```

**Что должно произойти:** Сверены типы, связи, ограничения и privacy.

**Как проверить:** Код 0, valid=true в новом JSON.

**Если не получилось:** Код 1 означает нарушение; прочитайте errors. Код 2 означает ошибку входов/параметров.

### Шаг 2. Прочитайте итоговые флаги

**Что сделать:** Проверьте manifest автоматически.

**Где выполнить:** Тот же терминал.

**Команда или пример:**

```bash
python -c "import json; from pathlib import Path; p=Path('out/ru-csv'); m=json.loads((p/'generation_manifest.json').read_text()); assert m['synthetic'] is True and m['source_rows_copied'] is False and m['validation_valid'] is True and m['seed']==12345; print('manifest: ok')"
```

**Что должно произойти:** Флаги прошли проверку.

**Как проверить:** Код 0.

**Если не получилось:** При false или отсутствующем поле остановите передачу набора и проверьте версию артефакта.

## Проверка результата

Проверьте, что в отчёте включены schema, relationships, constraints, privacy. Не считайте отсутствие секции успешной проверкой. Дополнительно оцените нужные диапазоны, null, распределения и полноту правил для вашей задачи. При business-rules прочитайте также business_validation_report.json: validate использует embedded business_rules или явно переданный --business-rules и не изменяет проверяемые строки. Сверьте также отдельный бизнес-отчёт.

## Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| Код 1 | Данные не соответствуют spec | Прочитайте ошибки секций; проверьте, что spec именно от этого набора. |
| valid=true, но нужного свойства нет | Свойство не формализовано или проверка отключена | Добавьте проверяемое правило; включите соответствующую validation_settings. |

## Как читать артефакты

| Артефакт | Что проверять |
| --- | --- |
| csv_profile.json / profile.json | Сущности, типы, чувствительность, границы наблюдений |
| dataset_spec.json / dataset_spec.yaml | Итоговый контракт; счётчики, поля, ключи, правила |
| validation_report.json | `valid`, включённые секции, errors |
| generation_manifest.json | seed, синтетичность, отсутствие копирования строк, результаты проверок, окружение |
| business_validation_report.json | При правилах: valid и ожидаемые/наблюдаемые нарушения |

`mixed` и `negative` могут намеренно создавать ошибки. Для них проверяют `expectations_met`, `unexpected_violation_count`, `missing_expected_violation_count`, а не требуют обычное `valid=true`. В `valid` ожидается отсутствие нарушений. В 1.6.0 при неуспешной валидации generate возвращает exit code 1 / JSON status validation_failed даже для mixed/negative, сохраняя намеренно неверные артефакты и отчёты. Код 1 не означает rollback. Приватность остаётся обязательной: её нарушение блокирует публикацию.


## Следующий шаг

[Безопасность данных](../concepts/safety-model.md).


## Выбрать формат результата

### Для чего это нужно

Выберите формат, который принимает ваша тестовая система. Генерируемые файлы содержат новые строки; экспорт SQL не читает и не выгружает исходные строки.

### Что получится в результате

CSV, JSON, SQL, Parquet и отдельный PostgreSQL DDL+INSERT из одного spec.

### Предварительные требования

Установлен Python 3.11+ и пакет проекта. Терминал открыт в корне репозитория `agent-paranoid-android`; виртуальное окружение активно. Входы — только вымышленные файлы из репозитория. Папка назначения новая; есть права чтения входов и записи результата. Для команд ниже используйте macOS/Linux; в PowerShell вводите каждую команду одной строкой без `\`. Дополнительно установлен extra parquet; Bash для готового скрипта.

### Пошаговое выполнение

#### Шаг 1. Сгенерируйте все форматы

**Что сделать:** Запустите существующий сценарий форматов.

**Где выполнить:** macOS/Linux, корень checkout.

**Команда или пример:**

```bash
bash examples/output_formats/run.sh out/ru-formats
```

**Что должно произойти:** Созданы подпапки csv, json, sql, parquet и postgres.sql.

**Как проверить:** В каждой подпапке есть manifest и validation_report.json.

**Если не получилось:** Если PyArrow отсутствует, установите .[parquet] в активное окружение; повторите в новой папке.

#### Шаг 2. Проверьте доступные для чтения форматы

**Что сделать:** Повторите валидацию CSV, JSON, SQL и Parquet по тому же spec.

**Где выполнить:** Корень checkout.

**Команда или пример:**

```bash
test-data-agent validate examples/output_formats/dataset_spec.yaml out/ru-formats/csv
test-data-agent validate examples/output_formats/dataset_spec.yaml out/ru-formats/json
test-data-agent validate examples/output_formats/dataset_spec.yaml out/ru-formats/sql
test-data-agent validate examples/output_formats/dataset_spec.yaml out/ru-formats/parquet
```

**Что должно произойти:** Прочитаны экспортированные данные.

**Как проверить:** Каждая команда возвращает 0.

**Если не получилось:** SQL-папка должна содержать именно сгенерированный INSERT bundle с manifest. Произвольный SQL и отдельный PostgreSQL DDL-файл не принимаются.

### Проверка результата

В manifest каждого набора проверьте synthetic=true, source_rows_copied=false и validation_valid=true. SQL здесь только сформирован; его исполнение на сервере в этом аудите не проверялось.

### Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| Отсутствует pyarrow / missing_dependency | Не установлен extra parquet | Установите `.[parquet]` и проверьте doctor --require-extra parquet. |
| SQL не читается validate | Передан произвольный SQL или DDL export | Передайте папку с созданным проектом INSERT bundle и manifest; validate не выполняет SQL. |

### Физическое представление в 1.6.0

CSV bundle объявляет в manifest `csv_encoding: backslash-null-v1`: `\N` — null, пустая ячейка — пустая строка, начальный обратный слеш удваивается. Формулы и опасные для spreadsheet строки/заголовки экранируются `\F`. Сохраняйте manifest вместе с CSV для обратимого чтения; не применяйте это декодирование к старым немаркированным CSV.

DECIMAL хранится точной строкой в CSV/JSON и decimal128 в Parquet. Для широких integer, смешанных timezone offsets и malformed negative cells Parquet может использовать маркированные строковые представления; при прямом чтении проверяйте `apa.scalar_encoding` или используйте bundle reader. Native decode одного Arrow batch предшествует проверке payload: лимит expanded bytes не гарантирует верхнюю границу памяти процесса.

В 1.6.0 validate читает ограниченную грамматику созданных INSERT bundles без исполнения SQL и без подключения к БД. DDL, функции, комментарии и произвольные SQL-скрипты этим не разрешаются.

### Различия форматов

| Формат | Файлы | Ограничения |
| --- | --- | --- |
| csv | `<entity>.csv` | Текстовое представление; типы задаются spec |
| json | `<entity>.json` | Строки сущности в JSON |
| parquet | `<entity>.parquet` | Нужен PyArrow; отдельное optional extra |
| sql | `<entity>.sql` | Кавычки и INSERT; без CREATE TABLE |
| export-postgres-sql | Один `.sql` | Транзакция, CREATE TABLE, FK и INSERT; PostgreSQL |

Для одного формата выполните `test-data-agent generate examples/output_formats/dataset_spec.yaml --seed 271828 --format csv --output out/ru-one-format`. Команда сверена с parser; эквивалентный вызов исполняется скриптом выше.

`export-postgres-sql` создаёт файл, но не подключается к целевой БД. Сам файл содержит операции записи. Перед его исполнением человек должен проверить целевой сервер, базу, роли и SQL; используйте отдельную пустую тестовую БД. Создание файла не является разрешением на его исполнение.


### Следующий шаг

[Валидация](review-output.md).
