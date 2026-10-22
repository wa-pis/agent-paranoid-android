# Операционная карта для AI-агента

[English](../../how-to/reference-agent.md) · Русский

Этот раздел — база инструкций, а не новый API или автоматическое разрешение на операции. `AGENTS.md` репозитория и явный scope пользователя остаются обязательными. YAML workflows на соседней странице являются документационным форматом.

| Запрос | Инструкция | Успешное завершение |
| --- | --- | --- |
| Проверить установку | [Первый запуск](../getting-started/installation.md) | Doctor и manifest демо проверены |
| Создать данные по CSV | [CSV](../getting-started/first-csv.md), workflow plan_csv_review | Spec проверен человеком, данные прошли валидацию |
| Связанные таблицы | [Основной процесс](../getting-started/related-tables.md) | Проверены значения контрактов и foreign keys |
| Применить правила | [Бизнес-правила](business-rules.md) | Проверен отдельный бизнес-отчёт |
| Прочитать БД | [Базы](postgresql.md) | Только allowlisted агрегаты и reviewable spec |
| Подключить MCP | [MCP](mcp.md) | Узкий workspace и совместимый stdio-клиент |
| Обратиться к AI | [AI](../ai_integration.md) | Согласованная передача метаданных, proposal validation и повторный review |
| Явная mixed-origin трансформация | [Отдельная трансформация](transformation.md) | Точный snapshot, разрешённые действия и provenance; local receipt только от человека |
| Ошибка/прерывание | [Диагностика](../operations/troubleshooting.md) | Безопасный статус и проверенный next action |

## До выбора workflow

1. Уточните вход, формат, count, seed и назначение. Не читайте вне разрешённых путей.
2. Сопоставьте установленную версию и checkout. Проверьте `COMMAND --help` этой версии.
3. Проверьте наличие входов и новую выходную папку без печати строк. Считайте возможную PII чувствительной.
4. Проверьте extras локально. Не запускайте сеть для «проверки доступности» без разрешённого endpoint/scope.
5. Выполните [workflow](reference-agent.md) до границы согласования. Сформируйте конкретный spec/checklist, а затем запросите требуемый review.

Не нужно запрашивать повторное разрешение для уже авторизованного локального обратимого действия. Но общее поручение «сгенерировать» не одобряет любой fingerprint: review-first протокол требует конкретный проверенный контракт. Новый spec, source bytes, provider destination или более широкий доступ требуют пересмотра соответствующего согласования.

## Отчёт пользователю

Сообщите число строк на сущность, seed, путь к файлам, validation status и ограничения. Не печатайте строки, секреты, SQL literals, provider prompts или необработанные ошибки. Указывайте «Не проверено выполнением», если ограничились чтением кода. Не объявляйте задачу завершённой при непроверенном manifest или нарушениях без оговорённого negative-сценария.

Дополнительные обязательные [правила безопасности](reference-agent.md).


## Workflows для AI-агента

Это YAML-описания операций для чтения агентом, не конфигурация исполняемого workflow engine. Пути относительно корня checkout. Входы, scope и новая папка проверяются до чтения. Секреты не передаются как inputs. При каждом ненулевом exit code прекратите зависимые действия; используйте [диагностику](../operations/troubleshooting.md).

### Локальная демонстрация

```yaml
workflow_id: offline_demo
title: "Проверить локальную установку"
description: "Создать и проверить встроенный синтетический набор"
preconditions:
  - "Python >=3.11; версия команды соответствует проверяемому пакету"
  - "Пользователь разрешил локальную запись; out/ru-demo не существует"
inputs:
  - name: output_folder
    type: path
    required: true
steps:
  - id: doctor
    action: "test-data-agent doctor"
    verification: "exit code 0; smoke пройден"
    on_failure: "Исправить окружение; не обращаться к внешним системам"
  - id: generate
    action: "test-data-agent demo --output out/ru-demo"
    verification: "exit code 0; 12 customers; manifest и validation существуют"
    on_failure: "Сохранить безопасную ошибку; выбрать новый output при конфликте"
  - id: verify
    action: "Прочитать локально manifest и validation_report"
    verification: "synthetic=true; source_rows_copied=false; validation_valid=true; seed=20260801; report.valid=true"
    on_failure: "Не принимать набор; прекратить передачу"
expected_outputs:
  - "out/ru-demo/customers.csv"
  - "out/ru-demo/dataset_spec.json"
  - "out/ru-demo/generation_manifest.json"
  - "out/ru-demo/validation_report.json"
requires_human_approval: false
```

`requires_human_approval: false` означает отсутствие дополнительного approval внутри уже разрешённой локальной демонстрации. Оно не расширяет разрешения пользователя.

### CSV с точным review перед генерацией

```yaml
workflow_id: plan_csv_review
title: "Создать CSV через проверенный план"
description: "Подготовить spec, получить review точного отпечатка, затем сгенерировать и проверить"
preconditions:
  - "Разрешён вход examples/csv_quickstart/customers.csv и запись out/ru-agent"
  - "Вход вымышленный; workspace не существует; seed=12345 и count=25 согласованы"
inputs:
  - name: source_csv
    type: path
    required: true
  - name: workspace
    type: path
    required: true
  - name: reviewed_spec_sha256
    type: string
    required: false
steps:
  - id: plan
    action: "test-data-agent agent-plan examples/csv_quickstart/customers.csv --workspace out/ru-agent --count 25 --seed 12345 --format csv"
    verification: "exit code 0; phase awaiting_approval; spec записан, данные ещё не созданы"
    on_failure: "Не продолжать; проверить путь, бюджеты и вход"
  - id: review
    action: "test-data-agent agent-review out/ru-agent --json; локально проверить dataset_spec.yaml"
    verification: "Проверены поля, sensitive, identifiers, диапазоны, связи; записан review.current_spec_sha256"
    on_failure: "Уточнить предметную область; после правок повторить review"
  - id: approval_gate
    action: "Показать человеку конкретный spec/checklist и fingerprint; получить review этого fingerprint"
    verification: "Согласование относится к текущему spec; source bytes не изменились"
    on_failure: "Остановиться до генерации; не считать молчание одобрением"
  - id: approve
    action: "Выполнить agent-approve out/ru-agent с --reviewed-spec-sha256, равным одобренному значению"
    verification: "exit code 0; статус сообщает завершение; manifest synthetic=true, source_rows_copied=false, validation_valid=true"
    on_failure: "Прочитать agent-status; при recovery_required использовать только его проверенный next action"
  - id: validate
    action: "Взять путь готовой папки из agent-status и выполнить validate с reviewed dataset_spec.yaml"
    verification: "exit code 0; report.valid=true; проверены все ожидаемые секции и count"
    on_failure: "Не принимать и не передавать набор"
expected_outputs:
  - "out/ru-agent/dataset_spec.yaml"
  - "Готовый набор и отчёты по путям из agent-status"
requires_human_approval: true
```

В YAML строки с `;` описывают последовательность действий, а не готовую shell-команду. Выполняйте каждое действие отдельно. `reviewed_spec_sha256` отсутствует при планировании и обязателен при approve. Нельзя автоматически взять свежий hash и считать его согласованным человеком.

### Профиль PostgreSQL

```yaml
workflow_id: postgres_profile_review
title: "Получить разрешённый профиль БД"
description: "Прочитать ограниченные агрегаты и подготовить spec без source rows"
preconditions:
  - "Человек подтвердил endpoint, TLS, read-only роль, schema/table/column scope и бюджеты"
  - "Extra postgres установлен; secret внедрён runtime и не выводится"
  - "Выходные файлы отсутствуют; назначение локальное и разрешённое"
inputs:
  - name: approved_database_scope
    type: configuration
    required: true
  - name: output_profile
    type: path
    required: true
steps:
  - id: local_check
    action: "test-data-agent doctor --require-extra postgres"
    verification: "exit code 0; проверка локальная, сетевой доступ не доказан"
    on_failure: "Исправить extra тем же Python"
  - id: profile
    action: "test-data-agent profile-postgres --output out/ru-postgres/profile.json"
    verification: "exit code 0; только согласованные entities/fields и агрегаты"
    on_failure: "Остановиться; не ослаблять scope/TLS; не возвращать driver text"
  - id: infer
    action: "test-data-agent infer-spec out/ru-postgres/profile.json --count 25 --output out/ru-postgres/dataset_spec.yaml"
    verification: "Spec создан; человек может проверить контракт; исходных строк нет"
    on_failure: "Уточнить метаданные; не брать row sample"
expected_outputs:
  - "out/ru-postgres/profile.json"
  - "out/ru-postgres/dataset_spec.yaml"
requires_human_approval: true
```

Этот workflow не разрешает генерацию по непроверенному spec или запись в БД. Живой пример **не проверен выполнением**. Trino-эквивалент и tool arguments: [MCP-инструкция](mcp.md) и [MCP Tools](../../mcp_examples.md).

Для AI-предложения используйте локальный plan и [advisor exchange](../ai_integration.md). Перед внешней отправкой требуется отдельное согласование назначения и содержимого; после proposal — новый review. Для неопределённого запроса выберите безопасное планирование, остановитесь на первом отсутствующем обязательном факте и сообщите, что именно требуется.

### Отдельное планирование mixed-origin трансформации

```yaml
workflow_id: transformation_review_only
title: "Проверить отдельный план трансформации"
description: "Получить value-free решения и digest без выпуска receipt"
preconditions:
  - "Пользователь явно выбрал mixed-origin трансформацию, а не synthetic generation"
  - "Разрешены точные local source, policy, mappings и новое назначение"
  - "Версия CLI 1.6.0; бюджеты конечны; входы проверены локально"
inputs:
  - name: source
    type: path
    required: true
  - name: policy
    type: path
    required: true
steps:
  - id: review
    action: "Выполнить transform-review SOURCE POLICY --json по согласованным локальным путям"
    verification: "exit 0; result.status=review_only; snapshot_sha256; value-free field decisions"
    on_failure: "Остановиться; исправить policy или schema; не выдавать старый receipt за новый"
  - id: classify
    action: "Проверить выбранные действия и fallback для каждого поля без печати literals"
    verification: "Preserve/fallback выявлены отдельно; sensitive/unknown/disputed не разрешены для preserve"
    on_failure: "Запросить конкретное решение человека; не менять классификацию автоматически"
  - id: human_gate
    action: "Если требуется сохранение, передать человеку exact digest и локальную команду transform-approve; остановиться до receipt"
    verification: "Агент не вводил APPROVE, не имитировал TTY и не выпускал receipt; новое исполнение требует отдельного согласованного scope"
    on_failure: "Не исполнять трансформацию; сообщить недостающую авторизацию"
expected_outputs:
  - "Value-free review и exact snapshot digest"
  - "При необходимости — запрос на local controlling-TTY review человеком, без агентского approval"
requires_human_approval: true
```

Исполняемый пример явных замен на вымышленных данных без preserve приведён в [отдельной инструкции](transformation.md). `agent-approve` для синтетической генерации и `transform-approve` для сохранения source values — разные границы.


## Правила безопасности AI-агента

### Допустимые операции

Чтение разрешённых метаданных, локальное профилирование с бюджетами, построение spec, генерация новых значений с seed, валидация и сохранение в согласованную новую папку. Для базы — только allowlisted read-only агрегаты. Для AI — ограниченное metadata proposal после согласования передачи.

### Недопустимые операции

Копирование/shuffle исходных строк; сохранение реальных ID или свободного текста как shortcut; произвольный SQL; DDL/DML на источнике; расширение scope для обхода ошибки; выключение TLS; извлечение credentials; source rows в prompts, exceptions, fixtures или MCP responses; auto-approve provider proposal. Не используйте row-returning результаты как synthetic output.

### Файлы и ошибки

Читайте только явные разрешённые входы. Выходы размещайте отдельно; не перезаписывайте source, не обходите symlink/workspace guards. Не просматривайте `.env`, домашнюю папку или системные секреты для «поиска настройки». Для диагностики используйте только имена требуемых настроек и локальные статусы без значений secret.

При ошибке не выполняйте зависимые этапы. Не повторяйте неверный provider/database payload в сообщении пользователю. Сообщайте код, фиксированную категорию и безопасное действие. При budget exhaustion уменьшите объём; не поднимайте лимиты автоматически.

### Когда требуется человек

- До доступа к новому внешнему источнику: точные endpoint/scope/read-only роль/бюджеты.
- До передачи метаданных новому внешнему AI или другому получателю.
- До `agent-approve`: конкретный проверенный spec и SHA-256.
- До local-category: конкретное поле, нечувствительный domain и назначение.
- До исполнения SQL или иной записи в целевую систему.
- Если неоднозначны sensitive flag, identifier, inferred relationship или предметное правило.

Уже согласованный scope сохраняется, пока входы, контракт и назначение не изменились. Это не повод спрашивать повторно о каждом локальном чтении, но и не разрешение на новую границу доступа.

### Условия остановки и завершения

Остановитесь, если неизвестна версия или схема, изменился вход после review, отсутствует необходимый approval, появились чувствительные литералы, противоречивые правила или ошибка проверки. Не подменяйте «Не подтверждено» утверждением об успехе.

Завершение: spec соответствует задаче и review; count и seed зафиксированы; manifest подтверждает synthetic=true и source_rows_copied=false; проверки включены и прошли; для negative ожидаемые нарушения совпали; назначение и пути известны. Пользователь получает сводку без строк.

Связанные обязательные guides проекта: [профилирование](../../agent-guides/profiling.md), [генерация](../../agent-guides/generation-and-rules.md), [Trino/MCP](../../agent-guides/trino-security.md), [advisor](../../agent-guides/advisors.md). Читайте guide только для выполняемой задачи.

### Отдельная трансформация 1.6.0

Запрет копирования относится к source-free generation. Для явно заказанной opt-in трансформации действуют отдельные policy/snapshot/receipt gates; результат mixed-origin. Агент может подготовить value-free review и потребить разрешённый точный receipt в согласованном scope, но не может выпускать receipt, вводить APPROVE за человека или имитировать TTY. Не выбирайте трансформацию вместо генерации автоматически. Согласие на agent-approve синтетического spec не является сохранением source values.
