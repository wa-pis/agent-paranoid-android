# CSV Encoding Performance

## Status

Implementation and regression verification completed on 2026-11-23; evidence
audit finalized on 2026-11-24, unreleased. All twelve public CSV runs succeeded.
[benchmark.md](benchmark.md) and [validation.md](validation.md) record the modest
encoding improvement and the higher total API times. This internal execution
change selects no version, tag or publication.

The [paired follow-up](paired-benchmark.md) on 2026-11-24 completed 32 successful
measured runs, alternating before/after order in four pairs per case. Retain the
two-line guard: encoding took less time in 15 of 16 pairs, with median paired
reductions of 3.85–5.94% across the four cases. No consistent total-time or
material memory regression appeared. The bounded local result is not a general
end-to-end speed guarantee; the original historical evidence remains unchanged.

## Why

The latest [public CSV benchmark](../value-normalization-performance/benchmark.md)
shows CSV encoding remains a measurable export stage. Profile the ordinary and
streaming writers on fictional data, then remove only repeated work that can be
shown to preserve the current bytes and safety behavior.

## What Changes

- Skip unnecessary stripping for exact built-in strings whose first character
  excludes the existing formula cases, through the helper shared by both paths.
  Retain scalar formatting, column order and the original subclass path.
- Preserve header/cell formula neutralization, quoting, delimiters, line endings,
  schema handling, exceptions and input non-mutation.
- Retain all validation/privacy checks, finite output/work budgets, private
  temporary files and atomic file/bundle publication.
- Compare exact encoding behavior against frozen previous implementations and
  repeat both public CSV benchmarks without replacing historical evidence.
  Use adjacent balanced before/after pairs to assess whether to retain the guard.

## Safety And Compatibility

No source access, public signature, option, dependency, artifact layout,
classifier, random-call order or seed algorithm changes. Shared CSV formatting
applies to every source-derived specification. Encoding does not authorize rows
for publication; mandatory validation and privacy boundaries remain in place.

