# Режимы генерации и замена папки

[English](../../reference/generation-modes.md) · Русский

Valid создаёт корректные строки. Edge добавляет валидные нижние/верхние числовые и временные границы, zero in range, boolean/category/length/null cases. Ограничения, уникальность, связи и rules могут заменить отдельную границу; малое число строк не покрывает всё. Sensitive strings остаются синтетическими.

Load_test умножает row_count каждой сущности на load_multiplier, по умолчанию 10. Явный CLI --count или Python bundle count задаёт точный размер без умножения. Generate-from-csv и generate --profile требуют count и используют его точно. Folder shortcut может взять inferred counts; для режима load_test в раздельном пути используйте reviewed DatasetSpec.

Все row/payload/disk/time budgets действуют до allocation. Режим генерирует данные для нагрузочного теста, но не посылает трафик и не запускает benchmark. Проверенный блок с 4/40/3 строками: [DatasetSpec](../dataset_profile_and_spec.md).

Generate --overwrite из spec заменяет всю папку, включая устаревшие файлы. Сначала завершаются generation/rules/validation, затем staging и previous-folder backup обеспечивают rollback при обработанной ошибке. Есть короткий rename interval; concurrent-reader atomic exchange не гарантируется. Не меняйте destination параллельно.

Symlinks, input spec/rules внутри заменяемой папки и collisions отклоняются. Скрытый .rollback после сбоя нельзя удалять до проверки recovery. Default multiplier не сериализуется ради совместимости fingerprints; custom multiplier и materialized count меняют fingerprint и требуют нового review.
