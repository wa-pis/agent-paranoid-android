# Проверка русской документации

Дата: **23 октября 2026 года**. Основа — актуальный main **bcfaaf94**, включая новую структуру и сборку из PR #631, исправления #632/#633 и уточнение пулов идентификаторов #634. Ветка — codex/docs-ru-current. Package release **1.6.0** и documentation revision различаются: перевод текущих исправлений main не меняет уже выпущенный wheel.

## Структура и перевод

Основные пользовательские страницы повторяют пути существующих документов после префикса ru/. Новая боковая навигация сохраняет разделы Start Here, How-To, Integrations, Reference, Help, Documentation и History в русском варианте. Переключатель English / Русский остаётся внутри выбранной версии сайта и открывает ту же страницу, если перевод есть; fallback явно ведёт на главную.

Специализированные непереведённые API tutorials и release/ADR evidence открываются в оригинале и помечены English. Технические ключи, команды, --help и API names не переводятся. Старые numbered directories и отдельный корневой ru.md в эту ветку не перенесены.

Сборка использует существующие MkDocs, mike, print-site, HTMLArk и Chrome. Новых зависимостей нет. Печатный handbook содержит пользовательские главы обоих языков; history/roadmap/downloads/versions исключены в обоих вариантах. Исторический русский материал исключается из обычного search так же, как English. ZIP исходников и offline site сохраняют оба языка.

## Проверенные примеры 1.6.0

Команды ранее выполненных примеров сохранены без изменения; менялись страницы и ссылки. Они используют только вымышленные fixtures, новые output directories и явный seed. Контрольный набор включает:

- Demo и manifest assertions; CSV quickstart; generate-from-csv и seeded byte replay.
- CSV-folder profile → reviewed spec → generate → validate.
- DatasetSpec и edge/load_test/count override (4/40/3 строки).
- CSV/JSON/SQL/Parquet output и revalidation без исполнения SQL.
- Business rules; локальный agent plan/review/advisor exchange без provider calls и approval.
- Exact DECIMAL, Parquet profile → spec → generation.
- Явные substitute mappings: review → exact snapshot → execution без preserve и receipt issuance.
- Python DatasetSpec 1.1 API: 3 строки сущности checks и valid=true.

Историческая проверка 22 октября: 36 bash-блоков и Python API прошли на локально собранном wheel 1.6.0, установленном в окружение с уже имеющимися dependencies. Это не clean dependency installation и не проверка PyPI.

## Повторная проверка и сборка

- 48 страниц в docs/ru/; 47 пар соответствующих английских и русских страниц.
- Все 36 сохранённых bash-блоков и пример Python API повторно прошли на установленном wheel 1.6.0 и исходниках main. Проверены результаты и counts 4/40/3; четыре YAML workflow проверены на структуру. Запросов к внешним сервисам и выдачи approval не было.
- 76 существующих проверок документации и сборки прошли. Проверка стиля документационного hook и git diff --check прошли.
- Строгая сборка MkDocs прошла. Проверены 94 направления переключения языка и язык бокового меню.
- Полная сборка с настоящим Chrome создала PDF, автономный HTML, Markdown ZIP и offline site ZIP для корня, versions/1.6.0 и versions/stable. Контрольные суммы выгрузок совпадают; русские главы включены в HTML и архивы, исторические страницы исключены из обычного поиска, служебные страницы исключены из handbook.

Это локальная проверка; новые страницы ещё не опубликованы. Сборка использует существующие закреплённые зависимости и не меняет runtime, тесты, lockfile или OpenSpec.

## Непроверенное

Не выполнялись новая установка из PyPI, Windows/Linux, live PostgreSQL/Trino, внешние OpenAI/GigaChat, интерактивная preservation approval и UI конкретного MCP-клиента. Local SDK/fake checks не подтверждают remote availability. Перевод не выдаёт dataset consent и не закрывает gates изменённой activation.

Исходная рабочая копия, старый незавершённый перевод и посторонняя папка OpenSpec сохранены отдельно. Публикация, merge и push не входят в этот локальный коммит документации.
