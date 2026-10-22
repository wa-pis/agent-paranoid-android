# Трансформация локальных данных

[English](../../how-to/transformation.md) · Русский

## Для чего это нужно

Используйте эту opt-in операцию, когда нужна обработка один к одному по явной policy: drop, synthesize, substitute, replace_text и разрешённое preserve. Выход имеет смешанное происхождение (mixed-origin); его нельзя выдавать за полностью синтетический или анонимный набор.

## Что получится в результате

В примере — value-free review, точный snapshot digest и новая локальная таблица с двумя явно заданными заменами. Сохранение source values и issuance receipt здесь не выполняются.

## Предварительные требования

Базовая установка 1.6.0, активное окружение, терминал в корне checkout на macOS/Linux. Папки out/ru-transform и out/ru-transform-output не существуют. Только вымышленные данные ниже. Политика и schema fingerprint рассчитаны именно для этих bytes и entity items; для другого источника они не подходят. Bash heredoc на Windows заменяется локальным Python-файлом; Windows-выполнение не проверено.

## Пошаговое выполнение

### Шаг 1. Подготовьте вымышленный источник и policy

**Что сделать:** запишите три небольших локальных файла без реальных данных.

**Где выполнить:** терминал, корень checkout.

**Команда или пример:**

```bash
python - <<'PYCODE'
from pathlib import Path
p = Path('out/ru-transform')
p.mkdir(parents=True, exist_ok=False)
(p / 'items.csv').write_bytes(b'status\nready\nwaiting\n')
(p / 'map.csv').write_bytes(b'old,new\nready,done\nwaiting,pending\n')
(p / 'policy.yaml').write_text("""schema_version: '0.1'
schema_fingerprint: bcc0d673c3991184ddadf0acdffeb759fd65f53b4ec65b6367bc3cfd5fdb72cc
seed: 7
fields:
  - entity: items
    field: status
    sensitivity: non_sensitive
    behavior:
      action: substitute
      mapping:
        kind: csv
        path: map.csv
        source_columns: [old]
        replacement_columns: [new]
""", encoding='utf-8')
PYCODE
```

**Что должно произойти:** создана ограниченная policy с явными replacement values в локальном mapping. Ни одна ветка не разрешает preserve fallback.

**Как проверить:** файлы в одной папке; map.csv задаётся относительно policy, не текущего shell.

**Если не получилось:** выберите новую папку; не подставляйте неизвестный источник под этот fingerprint.

### Шаг 2. Получите review без значений

**Что сделать:** прочитайте fixed snapshot; сохраните JSON только в новый файл.

**Где выполнить:** корень checkout.

**Команда или пример:**

```bash
test-data-agent transform-review out/ru-transform/items.csv out/ru-transform/policy.yaml --trace --json > out/ru-transform/review.json
```

**Что должно произойти:** result.status=review_only; review содержит решения полей, digest и ordinal trace без literals.

**Как проверить:** код 0; snapshot_sha256 имеет 64 hex-символа; receipt не создан.

**Если не получилось:** не используйте перенаправленный JSON после ненулевого кода. Проверьте policy, schema, пути и бюджеты; не выдавайте новый hash за старое approval.

### Шаг 3. Выполните только явные замены

**Что сделать:** используйте digest только что проверенного фиксированного плана. Этот пример не содержит preserve, поэтому preservation receipt не нужен.

**Где выполнить:** корень checkout; policy, mapping и source после review не менялись.

**Команда или пример:**

```bash
python - <<'PYCODE'
import json
import subprocess
from pathlib import Path
p = Path('out/ru-transform')
r = json.loads((p / 'review.json').read_text())['result']
assert r['status'] == 'review_only'
subprocess.run([
    'test-data-agent', 'transform-execute', str(p / 'items.csv'),
    str(p / 'policy.yaml'), 'out/ru-transform-output',
    '--snapshot-sha256', r['snapshot_sha256'],
    '--max-total-input-bytes', '8192', '--max-output-bytes', '8192', '--json',
], check=True)
PYCODE
```

**Что должно произойти:** создан mixed-origin bundle; summary содержит transformation_completed и provenance, не строки.

**Как проверить:** код 0; digest соответствует review; replacement counters отражают две ячейки, original — ноль. Не требуйте synthetic=true от transformation manifest.

**Если не получилось:** при изменении любого bound input нужен новый review; не переиспользуйте receipt или digest. Cleanup-incomplete требует локальной проверки staging/output, а не overwrite.

## Проверка результата

Прочитайте value-free report/provenance созданного bundle. Подтвердите ноль original и две replacement ячейки. Не отправляйте transformed rows в AI: explicit mapping может законно совпадать с другими source values, включая sensitive permutations, а mixed-origin output остаётся потенциально чувствительным.

## Типичные ошибки

| Ошибка | Причина | Решение |
| --- | --- | --- |
| Stale snapshot / invalid transformation request | После review изменились source/policy/mapping bytes | Получите новый review; сохранение требует нового local approval |
| Требуется receipt | Выбрано preserve либо preserve fallback | Остановитесь для человека в local controlling-TTY |
| Cleanup incomplete | Не подтверждено полное удаление staging/output | Проверьте состояние локально; не перезаписывайте результат |

## Когда нужен человек

`transform-approve SOURCE POLICY RECEIPT --snapshot-sha256 SHA` выдаёт receipt только после свежего ввода APPROVE в управляющем локальном терминале. Агент и MCP не могут вводить это за человека, подменять подтверждение флагом/pipe или имитировать терминал. Receipt привязан к exact source, policy, classification и mapping bytes. Sensitive/unknown/disputed поля не разрешены для preserve; DECIMAL preservation по умолчанию заблокирован. Локальный wizard `transform-review --decide` и SAVE сохраняют policy, но не создают receipt.

`transform-batch` объединяет минимум два входа и независимо проверенный validation spec. create сохраняет references/policies, review выдаёт digest, approve — local-only receipt, validate проверяет временный выход, execute может сохранить новый direct-child bundle. Обязательны явные input/review/output caps согласно справке. `common_transformation` MCP использует ту же границу; `configured_query_session`/`transform-batch query-execute` отдельно захватывают разрешённые SQL results один раз и потребляют frozen batch без reconnect. Нет MCP receipt issuer.

## Следующий шаг

[Полная справка CLI](../reference/cli.md), [публичный контракт](../../reference/cli.md#common-profile-workflow-16-rc) и [границы безопасности](../concepts/safety-model.md). Локальный review и explicit replacement пример проверены; интерактивный preserve и live SQL session в этом аудите не выполнялись.
