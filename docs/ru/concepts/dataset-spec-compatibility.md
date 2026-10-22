# Совместимость DatasetSpec

[English](../../concepts/dataset-spec-compatibility.md) · Русский

Версия пакета 1.6.0 отличается от версии контракта DatasetSpec. Новые спецификации рекомендуется сохранять с явным schema_version: "1.1".

| Вход | Поведение |
| --- | --- |
| schema_version 1.0 | Поддерживается без decimal |
| schema_version 1.1 | Поддерживает exact DECIMAL и текущий общий контракт |
| Payload без schema_version | Импортируется как legacy 1.0 |
| Новый Python DatasetSpec без явной версии | По умолчанию создаётся 1.1 |
| Неизвестная версия | Отказ; не угадывается |

Decimal требует 1.1 и типизированного decimal_range. При переходе не достаточно поменять номер: проверьте precision, scale, строковые границы, identifiers, чувствительность и бизнес-правила. Источники bounds должны быть явным проверенным синтетическим контрактом.

Неизвестные поля и некорректные typed distributions не следует сохранять как непрозрачный словарь. Используйте модели и каноническую schema. Старый GenerationSpec удалён в 0.6.0; он не является legacy DatasetSpec. Safe profile JSON с columns — отдельный адаптер метаданных.

После изменения spec повторите review fingerprint, генерацию и валидацию. Совместимость схемы не гарантирует прежние байты результата между версиями. Подробности: [справочник](../dataset_profile_and_spec.md), [миграция](../reference/generation-contract-migration.md).
