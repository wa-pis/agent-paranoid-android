# Дорожная карта

[English](../roadmap.md) · Русский

Это направления, а не обещанные даты. Приоритет определяется отзывами и подтверждёнными дефектами. Stable 1.6.0 уже опубликована и публично проверена; завершённая работа относится к [истории](history.md).

## Сейчас

- Обработать внешний feedback 1.6.0: reviewed numeric CSV profiling, authenticated Trino access, relational planning и проверку полезности, bounded statistics и понятные CLI diagnostics. Сохранять conservative privacy defaults и read-only DB budgets; начинать с воспроизведённых отказов, а не повторно открывать исправленные ошибки прежнего harness.
- Улучшать onboarding, инструкции по задачам, версионную и скачиваемую документацию.
- Проводить пилоты разработки и аналитики.
- Исправлять подтверждённые client defects, migration feedback и зависимости.
- Следить за source/output consistency, portable business rules и MCP permissions.

## Далее

- Спроектировать batch validation CSV/JSON/Parquet без удержания всего набора в памяти. Ограничить cross-table key/uniqueness checks, сохранить deterministic results и измерить память на вымышленных fixtures. До реализации нужен отдельный OpenSpec change.
- Упростить CSV/DB workflow по итогам пилотов.
- Публиковать runnable examples и короткие кейсы с синтетическими входами.
- Улучшать повторно затрудняющую пользователей диагностику.

## Позднее

Преобразование исходных EAV-строк (pivot/unpivot) отложено. Условные формулы
и синтетическая EAV-модель вошли в 1.7.0rc1; для преобразования существующих
строк нужен отдельный проект с правилами изменения количества строк,
дубликатов, null, типов и происхождения данных, а также явное разрешение
на доступ к источнику. Синтетическая генерация и преобразование один-к-одному
такого разрешения не дают.

Новые интеграции — только после подтверждённого спроса. Reporting/validation adapters — для конкретных задач; публичные контракты развиваются по compatibility/deprecation policy.

Конечная fictional transformation/session campaign для stable завершена с [ограниченным покрытием](../release-evidence-1.6.0.md). Это не dataset consent и не завершение более широкой acceptance campaign. Изменённая public activation по-прежнему требует specifications, executable evidence и независимого exact-source safety review.
