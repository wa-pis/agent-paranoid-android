# Verification: Whole-Column CSV Semantics

Completed 2026-11-22. All fixtures and bounded review probes are synthetic.
No live database or provider access, dependency, release action or historical
benchmark edit was needed.

## Implemented Scope

The pure `ColumnSemanticEvidence` dataclass is shared by single-file CSV and
folder CSV accumulators and their batch helpers. It counts every nonempty
value using the existing bounded content-classification outcome. Integer
comparisons implement the inclusive 80% threshold; any secret retains priority.
Conflicting name/content evidence or insufficient support returns no semantic.
The first matching sensitive value and the first-100-row sample no longer
select column semantics.

Name hints split snake case, camel case, acronyms and separators into words.
Numeric roles suppress incompatible hints; bare numeric phone candidates need
an explicit compatible phone hint. A rejected hint cannot reappear through the
previous CSV substring type fallback. SSN representation is consistently
string, and name/address semantics normalize to string across all four views.

The evidence model stores counts and one numeric-compatibility flag, receives
no source values and is not serialized. Streaming accumulation reuses parsing
and classification performed in the existing pass. No additional source read,
value cache, random call or per-row evidence collection was introduced.

## Privacy And Determinism

Any recognizable sensitive content still sets the independent sensitive flag.
Rare values cannot escape through exact bounds, raw categories or profiles/specs.
Tokenized semantic hints do not replace conservative name-based privacy checks,
masking, category validation or mandatory generated-row checks.

The shared `core/privacy.py` is byte-identical to the pre-task snapshot:
SHA-256 `642dfde5ce68f256bc2a0bcd833f97d603104f509e82008a6c5c00c87af0c23f`.
Its frozen-policy tests and the row-privacy equivalence tests pass unchanged.
The older late-phone regression now expects unknown whole-column semantics
while retaining its sensitivity and raw-value/bounds suppression assertions.

For a fixed field name and value multiset, semantics, physical type and
sensitivity are invariant under row permutations. Existing reservoir samples,
category labels and pattern ordering remain outside this guarantee, so complete
profile bytes and specifications inferred from reordered samples need not match.
Generation from the same corrected specification remains deterministic with
an explicit seed. Corrected specs intentionally need not match old erroneous
phone/email specs.

Cache format 7 rejects matching version-5 and version-6 entries, recomputes
corrected metadata and safely reuses the new entry. Existing saved profiles
and plans are not rewritten; reprofile them to obtain the new inference.

## Executed Verification

- `tests/test_column_semantics.py`: **51 passed** in 0.97 seconds. Covers all
  four profiling views, snake/camel/acronym names, numeric roles and substring
  false positives, 79/80% boundaries, null denominators, late evidence, reverse
  and seeded-shuffle permutations, conflicts and secret priority. Public
  CSV/folder-to-spec generation remains deterministic and validates normally.
- Additional tests prove compact aggregate state without source retention and
  one classifier call per nonempty accumulation step. Resolver execution reuses
  metadata without calling the content classifier again.
- Broader focused regression: **196 passed** in 2.89 seconds before the final
  physical-type alignment. The final full suite includes all these checks plus
  the added name/address/SSN type regressions.
- Final full suite with coverage: **2,228 passed, 10 skipped** in 77.58 seconds;
  **91.7352% coverage**, above the existing 85% gate. No new skip was added.
- Ruff over `src tests scripts`: passed.
- Mypy over 126 configured source files: passed.
- Strict MkDocs, strict OpenSpec validation and `git diff --check`: passed.

Independent read-only review compared 500 fixed-seed synthetic groups with the
exact pre-task CSV module snapshot: no sensitivity downgrade, exposed sensitive
numeric bound or semantic/type/sensitivity change after shuffling was observed.
Review found a name/address physical-type mismatch, which was corrected. A final
32 bounded checks confirmed name/address/SSN typing and retained sensitivity
across four views and reversed orders. No actionable review finding remains.

The large CSV-export performance experiment was not repeated: it uses a fixed
handwritten specification and this change concerns source-profile inference.
Historical timing and source-fingerprint evidence remains unchanged. No general
recognition-accuracy or full-profile permutation guarantee is inferred from
these regression checks.
