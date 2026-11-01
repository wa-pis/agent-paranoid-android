# Версии документации

[English](../versions.md) · Русский

Default site содержит поддерживаемую документацию для последнего публично проверенного stable package. Banner различает версию/source пакета и documentation revision; исправления текста не считаются повторной проверкой package commit.

Откройте [stable selector](https://wa-pis.github.io/agent-paranoid-android/versions/stable/) и выберите доступную версию. Mike хранит version directories, stable alias и отдельные search indexes. Старые guides автоматически сегодняшним текстом не пересобираются.

Русская версия находится внутри той же выбранной версии сайта: /ru/ либо /versions/X.Y.Z/ru/. Переключатель языка сохраняет страницу, а не переводит на другой package release. Если перевода нет, ссылка явно ведёт на главную другого языка.

Поддерживаемая guide может получать reviewed corrections; её metadata содержит отдельный documentation commit. Это не обещание неизменной release-era prose. Для старого package без guide сохраняется release evidence, а не выдуманный snapshot.

Документация RC сохраняется отдельно: `versions/X.Y.ZrcN/`, например
`versions/1.7.0rc1/`. Копия-алиас `next` ведёт на текущий RC; более ранние
кандидаты сохраняются в собственных каталогах. Статус явно указывает, что
это не стабильная версия. Остальные development docs размещаются в
`versions/next/` с видимым статусом и не продвигают stable автоматически. Package 1.6.0 и DatasetSpec schema 1.1 — разные версии. См. [совместимость](concepts/dataset-spec-compatibility.md), [скачивание](downloads.md) и [публикацию — English](../development/documentation.md).
