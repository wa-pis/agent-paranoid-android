# Матрица источников и форматов

[English](../../reference/source-output-matrix.md) · Русский

Все источники дают безопасное evidence для одного reviewed DatasetSpec. Это переходы генерации новых строк, а не конвертация source rows. JSON profile — metadata, а не произвольный JSON dataset.

| Источник → reviewed spec | CSV | JSON | Parquet | SQL INSERT bundle |
| --- | --- | --- | --- | --- |
| Один CSV | Да | Да | Да | Да |
| Папка CSV | Да | Да | Да | Да |
| Один Parquet | Да | Да | Да | Да |
| Сохранённый DatasetProfile | Да | Да | Да | Да |
| Trino aggregate table profile | Да | Да | Да | Да |
| PostgreSQL aggregate table profile | Да | Да | Да | Да |
| PostgreSQL query aggregate profile | Да | Да | Да | Да |
| Trino query aggregate profile | Да | Да | Да | Да |
| YAML DatasetSpec | Да | Да | Да | Да |
| JSON DatasetSpec | Да | Да | Да | Да |

Все семь field types, settings, relationships, constraints, privacy rules и embedded business_rules проходят в общий engine. Valid/edge/load_test/mixed/negative, seed, locale и multiplier не зависят от source/output. Противоречивый spec и превышение limits отклоняются; unknown null statistics, отсутствующие exact DECIMAL bounds и unmodeled query dependencies требуют авторского контракта.

CSV manifest объявляет backslash-null-v1: \N — null, empty cell — пустая строка, leading backslash удваивается, \F обезвреживает formula-capable strings/headers. Не удаляйте manifest. JSON сохраняет native scalars и decimal text. Parquet сохраняет Arrow types либо явно отмеченные apa.scalar_encoding columns для wide integers, mixed offsets и malformed negative cells. Direct reader должен учитывать metadata. SQL bundle содержит quoted INSERT VALUES; validate разбирает только эту generated grammar и никогда не исполняет SQL. DDL/functions/comments и произвольный SQL отклоняются.

Сохраняйте spec, manifest и business report вместе. Single-entity filename отражается в entity_artifacts. Format adapters не назначают formulas заново и не масштабируют count дважды. См. [проверку форматов](../getting-started/review-output.md) и [режимы](generation-modes.md).

## Проверенный пример: точный DECIMAL

## Для чего это нужно

Используйте DECIMAL для финансовых тестов, где важны десятичные разряды. FLOAT — приближённое двоичное число; он не заменяет точный контракт decimal_range. Границы ниже придуманы для теста, а не извлечены из источника.

## Что получится в результате

Четыре строки `items` с точным amount от 1.00 до 9.99, JSON bundle и отчёт.

## Предварительные требования

Базовая установка 1.6.0, активное окружение, терминал в корне checkout. Папки out/ru-decimal и out/ru-decimal-data ещё не существуют. Для Parquet понадобился бы extra parquet; для JSON он не нужен.

## Пошаговое выполнение

### Шаг 1. Создайте явный spec

**Что сделать:** создайте вымышленный контракт в отдельной папке.

**Где выполнить:** терминал, корень checkout.

**Команда или пример:**

```bash
python - <<'PYCODE'
from pathlib import Path
p = Path('out/ru-decimal')
p.mkdir(parents=True, exist_ok=False)
(p / 'spec.yaml').write_text("""schema_version: "1.1"
entities:
  - name: items
    row_count: 4
    fields:
      - name: amount
        data_type: decimal
        distribution:
          kind: decimal_range
          precision: 6
          scale: 2
          min: '1.00'
          max: '9.99'
""", encoding='utf-8')
PYCODE
```

**Что должно произойти:** создан spec.yaml с десятичными границами в строках.

**Как проверить:** schema_version=1.1; precision=6, scale=2; min≤max.

**Если не получилось:** используйте новую папку. Не заменяйте строки границ на float и не переносите source extrema.

### Шаг 2. Сгенерируйте и перепроверьте

**Что сделать:** выполните команды по очереди.

**Где выполнить:** тот же терминал.

**Команда или пример:**

```bash
test-data-agent generate out/ru-decimal/spec.yaml --seed 17 --format json --output out/ru-decimal-data
test-data-agent validate out/ru-decimal/spec.yaml out/ru-decimal-data
```

**Что должно произойти:** создан items.json, manifest и validation report.

**Как проверить:** обе команды завершаются кодом 0.

**Если не получилось:** проверьте тип decimal_range, precision≤38, scale, строковые границы и privacy flags; не отключайте safety.

## Проверка результата

```bash
python - <<'PYCODE'
import json
from decimal import Decimal
from pathlib import Path
p = Path('out/ru-decimal-data')
rows = json.loads((p / 'items.json').read_text())
assert len(rows) == 4
assert all(isinstance(r['amount'], str) for r in rows)
assert all(Decimal('1.00') <= Decimal(r['amount']) <= Decimal('9.99') for r in rows)
assert json.loads((p / 'validation_report.json').read_text())['valid'] is True
print('decimal: ok')
PYCODE
```

Не печатайте значения; достаточно assert и сводки. Для PowerShell сохраните Python-блоки в локальные .py файлы и выполните `python имя.py`; Bash heredoc там не работает. Windows-выполнение не проверено.

## Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| decimal требует 1.1 | Legacy spec 1.0 | Укажите schema_version 1.1 |
| Нет точных bounds | Профиль несёт только precision/scale | Задайте reviewed decimal_range или infer-spec --decimal-fields |
| Privacy rejection | Поле/значение похоже на чувствительный идентификатор | Пересмотрите смысл поля; numeric_measure допустим только для явно проверенной нечувствительной меры, не как обход |

Профили numeric(p,s) и decimal128 сохраняют типовую форму, но не точные source extrema. `infer-spec --decimal-fields FILE` принимает mapping ENTITY.FIELD → полный FieldSpec с согласованными precision/scale и синтетическими bounds. Подробный формат: [reviewed decimal inference](../../rc4-external-feedback.md#reviewed-decimal-inference). Nullable/unknown статистики требуют review. Сохранение DECIMAL при отдельной трансформации по умолчанию заблокировано.

## Следующий шаг

[Parquet-профиль](source-output-matrix.md) или [правила](../how-to/business-rules.md).


## Безопасный профиль Parquet

### Для чего это нужно

`profile-parquet` анализирует локальный Parquet и возвращает ограниченные метаданные. Используйте его для подготовки DatasetSpec, а не для конвертации исходных строк в synthetic output.

### Что получится в результате

Безопасный profile.json, reviewed spec и JSON-набор по вымышленному Parquet из примера форматов.

### Предварительные требования

Установка 1.6.0 с extra parquet. Выполнена [инструкция форматов](../getting-started/review-output.md): существует `out/ru-formats/parquet/support_tickets.parquet`. Команды выполняются из корня checkout; out/ru-parquet и out/ru-parquet-data — новые папки. Не используйте сторонний production Parquet для знакомства.

### Пошаговое выполнение

#### Шаг 1. Получите профиль

**Что сделать:** прочитайте вымышленный Parquet.

**Где выполнить:** терминал, корень checkout.

**Команда или пример:**

```bash
test-data-agent profile-parquet out/ru-formats/parquet/support_tickets.parquet --output out/ru-parquet/profile.json
```

**Что должно произойти:** записаны метаданные без строк источника.

**Как проверить:** команда возвращает 0; source_type указывает Parquet.

**Если не получилось:** проверьте doctor --require-extra parquet, типы Arrow и budgets; не увеличивайте пределы автоматически.

#### Шаг 2. Выведите spec

**Что сделать:** создайте spec по доступным статистикам.

**Где выполнить:** тот же терминал.

**Команда или пример:**

```bash
test-data-agent infer-spec out/ru-parquet/profile.json --count 4 --output out/ru-parquet/spec.yaml
```

**Что должно произойти:** для данного вымышленного входа создан контракт генерации.

**Как проверить:** код 0; локально проверьте поля, nullable и чувствительность в spec.

**Если не получилось:** отсутствующие null/distinct статистики обозначаются null, не 0. Unknown null ratio блокирует auto-inference; задайте independently reviewed spec. DECIMAL требует явных синтетических bounds.

#### Шаг 3. Создайте новый набор

**Что сделать:** после review создайте JSON и проверьте его.

**Где выполнить:** тот же терминал.

**Команда или пример:**

```bash
test-data-agent generate out/ru-parquet/spec.yaml --seed 271828 --format json --output out/ru-parquet-data
test-data-agent validate out/ru-parquet/spec.yaml out/ru-parquet-data
```

**Что должно произойти:** создан новый набор, а не копия Parquet-строк.

**Как проверить:** обе команды возвращают 0; manifest synthetic=true, source_rows_copied=false, validation_valid=true.

**Если не получилось:** проверьте inferred spec и ошибки секций; не меняйте source path на output path.

### Проверка результата

Сопоставьте row_count=4 и поля support_tickets; повторный validate должен пройти. Просмотрите только метаданные profile/spec и manifest. Не используйте исходные row values как эталон совпадения: совпадение строк не является целью генератора.

### Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| missing_dependency | Нет PyArrow | Установите .[parquet] в том же окружении |
| Unknown null ratio | В файле нет достаточной статистики | Явный проверенный spec вместо догадки |
| Превышен expanded-byte/cell budget | Decode слишком объёмен | Уменьшите тестовый источник; предел payload не является hard peak-RSS гарантией |

### Следующий шаг

[DECIMAL](source-output-matrix.md), [источники и форматы](source-output-matrix.md).
