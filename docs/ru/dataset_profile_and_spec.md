# Настроить DatasetSpec

[English](../dataset_profile_and_spec.md) · Русский

Действующие relationship/constraint используют числовой confidence от 0 до 1.
Расширенный evidence envelope в английском справочнике — будущий проект,
а не текущая сериализованная схема; confidence: medium не является допустимым
значением в действующих моделях.

## Для чего это нужно

Спецификация задаёт число строк, типы, распределения и правила для генерации. Используйте её, когда автоматический вывод требует исправлений или нужно работать без источника.

## Что получится в результате

Проверенный YAML/JSON и 4 синтетических support_tickets.

## Предварительные требования

Установлен Python 3.11+ и пакет проекта. Терминал открыт в корне репозитория `agent-paranoid-android`; виртуальное окружение активно. Входы — только вымышленные файлы из репозитория. Папка назначения новая; есть права чтения входов и записи результата. Для команд ниже используйте macOS/Linux; в PowerShell вводите каждую команду одной строкой без `\`.

## Пошаговое выполнение

### Шаг 1. Откройте готовую спецификацию

**Что сделать:** Просмотрите examples/output_formats/dataset_spec.yaml в редакторе. Для изменений сохраните отдельную копию.

**Где выполнить:** Локальный редактор, корень checkout.

**Команда или пример:**

```yaml
schema_version: "1.1"
entities:
  - name: support_tickets
    row_count: 4
    primary_key: ticket_id
    fields:
      - name: ticket_id
        data_type: integer
        is_identifier: true
      - name: resolved
        data_type: boolean
generation_settings:
  seed: 271828
  output_format: json
```

**Что должно произойти:** Это минимальный самостоятельный пример структуры, а полный файл также содержит requester_email и summary.

**Как проверить:** primary_key ссылается на поле с is_identifier=true; row_count положительный.

**Если не получилось:** Не добавляйте реальные значения или непроверенные ключи. Пользуйтесь справочником и schema, не полагайтесь на догадки.

### Шаг 2. Создайте набор из полного готового файла

**Что сделать:** Передайте проверенный файл без ручных правок.

**Где выполнить:** Терминал, корень checkout.

**Команда или пример:**

```bash
test-data-agent generate examples/output_formats/dataset_spec.yaml --seed 271828 --format json --output out/ru-spec
```

**Что должно произойти:** Созданы support_tickets.json и отчёты.

**Как проверить:** validation_valid=true в manifest; seed=271828.

**Если не получилось:** Если spec отклонён, проверьте schema_version, ссылки полей и распределения; не меняйте защиту.

### Шаг 3. Перепроверьте данные

**Что сделать:** Валидируйте по исходному spec.

**Где выполнить:** Корень checkout.

**Команда или пример:**

```bash
test-data-agent validate examples/output_formats/dataset_spec.yaml out/ru-spec
```

**Что должно произойти:** Контракт выполнен.

**Как проверить:** Код 0.

**Если не получилось:** Прочитайте отчёт и проверьте, не менялся ли файл после генерации.

## Проверка результата

Выполните `test-data-agent validate examples/output_formats/dataset_spec.yaml out/ru-spec`. Ожидается код 0.

Для изменения количества используйте `generate ... --count 10` в новой папке. CLI-параметры соответствующих настроек имеют приоритет над сохранёнными значениями. Этот вариант изменения count сверён с parser; отдельно не запускался.

## Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| Неподдерживаемый schema_version | Spec другой версии | Используйте 1.1 для новых spec; 1.0 поддерживается без decimal. Проверьте руководство совместимости. |
| Неизвестное поле связи/ключа | Ошибка имени или удалённое поле | Согласуйте ссылки с entities[].fields. |



## Следующий шаг

[Справочник конфигурации](reference/configuration.md).

## Режимы edge и load_test в 1.6.0

На вымышленном spec из примера форматов можно проверить три случая из корня checkout. Каждый вызов использует новую папку; `--mode edge` создаёт валидные границы, а `load_test` увеличивает объём без отправки нагрузки в другую систему.

```bash
test-data-agent generate examples/output_formats/dataset_spec.yaml --mode edge --seed 271828 --format json --output out/ru-edge
test-data-agent generate examples/output_formats/dataset_spec.yaml --mode load_test --seed 271828 --format json --output out/ru-load
test-data-agent generate examples/output_formats/dataset_spec.yaml --mode load_test --count 3 --seed 271828 --format json --output out/ru-load-count
```

Проверка: в support_tickets.json соответственно 4, 40 и 3 строки; validation_valid=true в каждом manifest. Явный count отменяет умножение. Если сработал лимит, уменьшите тестовый объём; режим не разрешает обход budgets. Даже edge не обещает все границы: constraints, rules и малое число строк ограничивают покрытие. Подробности: [режимы](../reference/generation-modes.md).
