# Установка

[English](../../getting-started/installation.md) · Русский

Рекомендуемая стабильная версия — **1.6.0**; см. [публичную проверку](../../release-evidence-1.6.0.md). Нужны Python 3.11+, место для результата и отдельная рабочая папка. CI поддерживает CPython 3.11–3.14; этот локальный аудит выполнен на macOS с Python 3.11.2.

## Установка из PyPI

На macOS/Linux откройте терминал в выбранной рабочей папке и выполните по очереди:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install "agent-paranoid-android==1.6.0"
test-data-agent --version
test-data-agent doctor
```

Ожидается версия 1.6.0 и doctor passed. Если команда не найдена, активируйте окружение и проверьте путь команды. Doctor использует временную вымышленную фикстуру и не обращается к внешним сервисам. Ошибка TLS при установке требует исправления сертификатов/индекса, а не отключения проверки.

Установка из индекса и загрузка зависимостей **не проверялись выполнением** этим аудитом. Локальный wheel 1.6.0 и доступные зависимости проверены отдельно; это не доказательство чистой PyPI installation.

## Windows PowerShell

Откройте PowerShell в рабочей папке; не используйте Bash activation. Отдельный маршрут без изменения ExecutionPolicy:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install "agent-paranoid-android==1.6.0"
.\.venv\Scripts\test-data-agent.exe --version
.\.venv\Scripts\test-data-agent.exe doctor
```

Ожидается 1.6.0 и doctor passed. При отсутствии launcher установите поддерживаемый Python. Windows-выполнение здесь не проверено. В следующих инструкциях заменяйте python и test-data-agent этими путями; вводите Bash-команды с продолжением строки одной строкой.

## Необязательные extras

Base поддерживает CSV, JSON и SQL export. Устанавливайте нужный extra с тем же точным pin: например, python -m pip install "agent-paranoid-android[parquet]==1.6.0". Доступны parquet, mcp, trino, postgres, openai и gigachat; all предназначен для разработки/демо/контейнеров.

Проверьте extra локально через test-data-agent doctor --require-extra parquet, заменив имя. Это не проверка сети, credentials или подключения БД/provider. GigaChat и OpenAI adapters остаются experimental. См. [поддержку](../reference/support-policy.md) и [footprint — English](../../reference/dependency-compatibility.md#installation-footprint).

## Когда нужна копия репозитория

Демо ниже работает без Git. Примеры с examples/ требуют checkout 1.6.0, например отдельный clone тега v1.6.0. Не переключайте изменённую или старую рабочую копию автоматически. Разработка описана в [Contributing](https://github.com/wa-pis/agent-paranoid-android/blob/main/CONTRIBUTING.md), сборка сайта — в [Publishing Documentation — English](../../development/documentation.md).

Перед обновлением существующих фикстур прочитайте [миграцию](../reference/generation-contract-migration.md). Package version и DatasetSpec schema_version различаются.

## Первый запуск без собственных данных

### Для чего это нужно

Демонстрация проверяет весь базовый путь на встроенной вымышленной таблице. Она не требует клонирования репозитория, базы данных или AI.

### Что получится в результате

Новая папка `out/ru-demo` с 12 синтетическими покупателями и проверочными артефактами.

### Предварительные требования

Установка завершена. Откройте терминал в выбранной рабочей папке, активируйте окружение; убедитесь, что out/ru-demo ещё не существует.

### Пошаговое выполнение

#### Шаг 1. Запустите демонстрацию

**Что сделать:** Создайте набор из встроенной фикстуры.

**Где выполнить:** Терминал, рабочая папка.

**Команда или пример:**

```bash
test-data-agent demo --output out/ru-demo
```

**Что должно произойти:** Генератор создаёт customers.csv, csv_profile.json, dataset_spec.json, validation_report.json и generation_manifest.json.

**Как проверить:** Команда завершилась кодом 0; вывод содержит validation: passed.

**Если не получилось:** При существующей папке выберите out/ru-demo-2. При недоступной команде вернитесь к установке.

#### Шаг 2. Проверьте manifest

**Что сделать:** Проверьте флаги и фиксированный seed демо, не печатая строки.

**Где выполнить:** Тот же каталог.

**Команда или пример:**

```bash
python -c "import json; from pathlib import Path; m=json.loads(Path('out/ru-demo/generation_manifest.json').read_text()); assert m['synthetic'] is True and m['source_rows_copied'] is False and m['validation_valid'] is True and m['seed']==20260801; print('demo: ok')"
```

**Что должно произойти:** Печатается demo: ok.

**Как проверить:** Все assert выполнены.

**Если не получилось:** При отсутствующем файле проверьте путь и предыдущую ошибку. При неверном флаге остановитесь и не используйте набор.

### Проверка результата

Откройте `validation_report.json`: `valid` должен быть `true`. В `customers.csv` должно быть 12 строк данных плюс заголовок. Демо не подтверждает сохранение связей и бизнес-правил: в его входе нет таких свидетельств.

### Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| `unsafe filesystem path` | Путь содержит запрещённый компонент или symlink | Используйте обычную новую папку внутри рабочей папки. На macOS `/tmp` может вести в `/private/tmp`. |
| `output` уже существует (точный текст зависит от операции) | Защита от перезаписи | Выберите новое имя папки. |



### Следующий шаг

[Быстрый старт с CSV](first-csv.md).
