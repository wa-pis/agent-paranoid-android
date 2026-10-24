# Профилирование через Trino

[English](../../how-to/trino.md) · Русский

Trino — отдельный read-only источник метаданных и агрегатов. В 1.6.0 сохранены JDBC-style endpoints без credentials, точные allowlists, ограниченные table-qualified wildcards и profile-query. Java и JDBC driver не нужны.

## Перед запуском

Нужны extra trino, а для MCP — также mcp; проверенный HTTPS endpoint, read-only роль и явно согласованный catalog/schema/table/column scope. Секреты внедряются через runtime secret mechanism. Сетевое выполнение этого руководства **не проверено**.

Локальная проверка установки из активного окружения:

```bash
test-data-agent doctor --require-extra trino
```

Doctor проверяет клиент и SQL policy без обращения к координатору. Он не подтверждает аутентификацию или доступ к таблицам.

## Настройте scope

Иллюстрация конфигурации для вымышленного endpoint; заменяйте её только согласованными параметрами:

```bash
export TRINO_HOST=trino.example.internal
export TRINO_PORT=8443
export TRINO_USER=test_data_agent
export TRINO_HTTP_SCHEME=https
export TRINO_ALLOWED_CATALOGS=warehouse
export TRINO_ALLOWED_SCHEMAS=analytics
export TRINO_ALLOWED_TABLE_COLUMNS='warehouse.analytics.orders.*'
export TRINO_DEPLOYMENT_PROFILE=shared-hardened
export TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES=1073741824
```

Catalog и schema — независимые allowlist-множества. Wildcard разрешён только для точной таблицы в restricted mode: ограниченные metadata разворачиваются в отсортированные явные столбцы до первого агрегата. Он не разрешает SQL `*`, literals, preserve или provider payload. Column selectors не являются общим ACL всех MCP tools; ограничения видимости задаются также правами БД.

Вместо компонентов endpoint допускается TRINO_JDBC_URL без credentials. Явные компоненты должны совпадать с URL. SSL=false, неизвестные свойства, токены, роли, proxies и headers в URL отклоняются. Basic/JWT/Kerberos/GSSAPI/OAuth2 и client certificates требуют своих настроек; см. [оригинальный полный справочник подключения](../../reference/configuration.md#trino-connection).

## Получите профиль

MCP server запускается локальным клиентом через test-data-agent-mcp-trino. Default aggregate-only tools возвращают разрешённые metadata и агрегаты. Затем безопасный профиль передаётся generator plan_trino_dataset без исходных строк; spec проверяется до генерации. См. [MCP](mcp.md).

Отдельный explicit opt-in run_safe_select по умолчанию отсутствует. Его ограниченные строки могут содержать исходные нестроковые значения; маскирование не делает их анонимными. Эти строки не передаются генератору или LLM.

## Воспроизводимый инфраструктурный пример

В репозитории есть examples/local_trino/run.sh и варианты run-jdbc.sh, run-wildcard.sh, run-query.sh. Они используют синтетический TPC-H tiny в одноразовом контейнере, удаляют контейнер и сохраняют безопасный профиль, spec, новые данные и отчёты. В этом аудите инфраструктурные сценарии не запускались.

Query-source требует явного column scope, хранит fingerprint вместо текста SQL и результатов. Не обходите отказ через unrestricted/insecure flags. Успех проверяется по scope, коду завершения, профилю без строк и отчётам сгенерированного набора; ошибка авторизации требует исправления grants или сужения запроса.

## MCP с логином и паролем {#trino-mcp-basic}

Для входа по логину и паролю явно выберите `TRINO_AUTH_METHOD=basic`.
По умолчанию стоит `none`: один `TRINO_USER` не включает отправку пароля.
`TRINO_AUTH_SECRET_ENV` содержит **имя переменной с паролем**, а не сам пароль.
Basic требует HTTPS с проверкой сертификата, в том числе при локальном запуске.

### 1. Подготовьте окружение и доступ

```bash
python3 -m venv /ABSOLUTE/PATH/trino-env
/ABSOLUTE/PATH/trino-env/bin/python -m pip install 'agent-paranoid-android[mcp,trino]'
/ABSOLUTE/PATH/trino-env/bin/test-data-agent --version
/ABSOLUTE/PATH/trino-env/bin/test-data-agent doctor --require-extra trino
```

Замените `/ABSOLUTE/PATH` своим абсолютным путём. Doctor проверяет локальную
установку, а не вход на сервер. У администратора Trino уточните HTTPS host/port,
логин, разрешённые catalog/schema/table/column и права чтения метаданных и
агрегатов. Из среды MCP должны быть доступны сервер, при необходимости VPN,
и доверенная цепочка сертификата. Корпоративный CA должен быть доверенным в
используемом Python/окружении; отключать проверку TLS не нужно.

### 2. Передайте пароль процессу

Если MCP-клиент умеет передавать секреты в окружение дочернего процесса через
защищённое хранилище, создайте там `MY_TRINO_PASSWORD`. Не помещайте пароль в
JSON, репозиторий, аргументы команды или переписку. Переменная из терминала
не обязательно видна графическому приложению; файл `.env` автоматически не
загружается. После изменения настроек перезапустите MCP-сервер.

Готовый вариант для **macOS**: в приложении «Связка ключей» создайте запись
пароля с именем `agent-paranoid-android-trino`, учётной записью, совпадающей с
`TRINO_USER`, и вашим паролем. Сохраните следующий скрипт как
`/ABSOLUTE/PATH/start-trino-mcp.sh`, заменив путь к установленному серверу:

```bash
#!/bin/bash
# Пароль читается локально; stdout используется только протоколом MCP.
if ! MY_TRINO_PASSWORD=$(/usr/bin/security find-generic-password \
    -s agent-paranoid-android-trino -a "$TRINO_USER" -w 2>/dev/null); then
  printf '%s\n' 'Trino password is unavailable in Keychain' >&2
  exit 1
fi
export MY_TRINO_PASSWORD
exec /ABSOLUTE/PATH/trino-env/bin/test-data-agent-mcp-trino
```

Выполните `chmod 700 /ABSOLUTE/PATH/start-trino-mcp.sh`. Разрешите локальному
запуску чтение нужной записи, если macOS запросит доступ. Не включайте `set -x`
и не добавляйте печать пароля. Этот вариант получает секрет при запуске и не
зависит от наследования окружения графическим приложением. Для другой ОС
используйте защищённое хранилище клиента или локальный механизм секретов.

### 3. Добавьте сервер в MCP-клиент

Это распространённый формат `mcpServers`; точное место настройки зависит от
клиента. Все адреса, логины и имена данных ниже вымышлены — замените их локально.
Пример использует скрипт со Связкой ключей из предыдущего шага:

```json
{
  "mcpServers": {
    "trino": {
      "command": "/ABSOLUTE/PATH/start-trino-mcp.sh",
      "env": {
        "TRINO_HOST": "trino.example.internal",
        "TRINO_PORT": "443",
        "TRINO_HTTP_SCHEME": "https",
        "TRINO_USER": "your_login",
        "TRINO_AUTH_METHOD": "basic",
        "TRINO_AUTH_SECRET_ENV": "MY_TRINO_PASSWORD",
        "TRINO_ALLOWED_CATALOGS": "warehouse",
        "TRINO_ALLOWED_SCHEMAS": "analytics",
        "TRINO_ALLOWED_TABLE_COLUMNS": "warehouse.analytics.orders.*",
        "TRINO_DEPLOYMENT_PROFILE": "shared-hardened",
        "TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES": "1073741824"
      }
    }
  }
}
```

При передаче `MY_TRINO_PASSWORD` защищённым механизмом клиента вместо Связки
ключей задайте `command` напрямую:
`/ABSOLUTE/PATH/trino-env/bin/test-data-agent-mcp-trino`.
Синтаксис подстановки секретов зависит от клиента: `${MY_TRINO_PASSWORD}`
в JSON не является универсальной подстановкой.

`TRINO_HOST` — только имя сервера, без схемы URL и пути; порт должен совпадать
с HTTPS endpoint. Catalog/schema — обязательные allowlists через запятую.
Column scope необязателен для обычных таблиц, но обязателен для `profile-query`.
Вместо `warehouse.analytics.orders.*` можно перечислить точные столбцы через
запятую. Wildcard разрешает только ограниченное агрегатное профилирование,
не выдаёт права на исходные строки и не заменяет grants в Trino.

Указанный cumulative scan budget — 1 ГиБ на вызов. По умолчанию действуют
также request timeout 30 секунд, execution time 30 секунд, run time 45 секунд
и scan budget 1 ГиБ на запрос. `TRINO_CATALOG` и `TRINO_SCHEMA` — необязательные
значения по умолчанию внутри allowlists. Полный список — в
[справочнике конфигурации](../../reference/configuration.md#trino-connection).

### 4. Проверьте запуск и разберите ошибку

Перезапустите сервер в MCP-клиенте и убедитесь, что появились Trino-инструменты.
Сначала вызовите разрешённый инструмент метаданных, например `list_catalogs`,
затем `describe_table` для согласованной таблицы. Успешный запуск процесса и
Doctor не доказывают успешную аутентификацию. Эти инструкции проверены локально
по конфигурационному контракту; вход на ваш сервер не проверен.

При 401 локально проверьте `basic`, доступность переменной, указанной в
`TRINO_AUTH_SECRET_ENV`, правильность логина и перезапуск процесса. При 403
проверьте серверные права и политику доступа; сам статус не устанавливает
точную причину. Ошибки TLS требуют проверки endpoint и доверия сертификату.

Для обращения за помощью достаточно версии пакета, способа запуска,
`TRINO_AUTH_METHOD`, `TRINO_HTTP_SCHEME`, признаков «логин задан»,
«secret reference задан», «переменная с паролем доступна процессу» и результата
входа другим клиентом. Не передавайте значения логина/пароля, полный `.env`,
URL подключения, исходные строки или необработанные ответы драйвера.

## Ошибки аутентификации

При сбое запишите локально версию пакета и выбранный `TRINO_AUTH_METHOD`.
Для разбора достаточно этих сведений: не передавайте пароли, токены, адреса
подключения и необработанные ответы драйвера. Один код HTTP 401 не позволяет
установить причину сбоя настройки или совместимости.

Профилирование SQL-запроса преобразует нетипизированные ошибки HTTP 401/403
и TLS в фиксированную ошибку `SQL query source profiling failed`, не сохраняя
исходное исключение в cause или context. CLI сохраняет категорию
`external_service` и прежний выходной файл. MCP возвращает фиксированную
ошибку Trino, а аудит не содержит значений источника или секретов.
Эти проверки не подтверждают успешный вход на конкретный сервер.
