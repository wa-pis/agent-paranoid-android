# Контракт синтеза связанных таблиц

[English](../../concepts/relational-synthesis-contract.md) · Русский

Профиль связи — свидетельство, а не доказанный бизнес-факт. Разделяйте объявленные PK/FK, наблюдаемые агрегаты и гипотезы advisor. Confidence помогает review, но не даёт права автоматически принять связь.

## Что гарантирует детерминированное ядро

- Identifiers создаются заново; карта source ID → output ID не сохраняется.
- Foreign keys указывают на сгенерированные parent keys; nullable child references сохраняют null.
- One-to-one capacity считается по ненулевым ссылкам.
- Явные ограничения и бизнес-правила валидируются; rejected relationships/constraints не исполняются.
- Identifier pool задаёт число синтетических ключей и циклирование, а не распределение исходных ID.

## Что не следует выводить из результата

FK coverage не доказывает бизнес-смысл связи. Round-robin назначение не сохраняет fan-out, частоты или корреляции источника. Uniform numeric sampling не является полным моделированием распределения. Arbitrary interacting rules не решаются универсальным solver.

Если active aggregate mapping зависит от rejected связи, исправьте spec: молчаливое игнорирование не разрешено. При нехватке parent capacity, конфликте уникальности, правил или temporal changes генерация останавливается, а не выдаёт частичный доверенный набор.

Проверьте имена parent/child полей, статус связей, cardinality, nullable и число строк до генерации. После неё прочитайте relationships и constraints в validation_report, затем business_validation_report. Практика: [связанные таблицы](../getting-started/related-tables.md).
