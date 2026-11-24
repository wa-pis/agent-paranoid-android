# Design: String Generation Performance

## Measured Candidate

Keep string construction in the shared `generation/entity_generator.py` helper.
Replace the per-character generator expression with a list comprehension; retain
each `rng.choice(string.ascii_lowercase)` operation in the same order. Do not
replace choices with bulk sampling or bind a method/alphabet across characters:
custom RNGs may change either between calls.

Create the character range before the exception guard. Join the character list
inside the guard, translate only `StopIteration` into the old `RuntimeError`
message/cause, and concatenate the prefix after the guard. This preserves PEP 479
behavior without converting exceptions raised by length/range setup or prefix
concatenation. The list is released by `join` before the final concatenation;
no rows, strings or privacy decisions are cached.

Row metadata hoisting is outside scope because callbacks can mutate entity/domain
metadata between fields. The scalar dispatch improvement from the preceding
change remains in both benchmark arms.

Freeze the complete pre-change source and original public/parallel benchmark
helpers before edits. Bind that 126-file map to the preceding dispatch benchmark's
after arm. Only the generator module may differ in the candidate; AST comparison
further confines the change to `synthetic_string`. Keep the original public
worker, timing instrumentation, process-tree RSS sampler and independent audit.
Reuse the paired driver with a reference parameter instead of adding another copy.

Run four adjacent pairs per case in AB/BA/AB/BA order, also alternating path order;
use four small smoke runs outside summaries. No tests or heavy verification run
concurrently. Preserve all times, ranges, paired changes, CSV hashes, validator
counts, private permissions and scratch cleanup. Streaming generation/IPC is
coordinator work and exposed waiting, not summed worker computation.

Retain the change only with equivalent values/states/errors and repeated local
generation gains without a consistent material API-time or high-water-memory
regression. Report all RSS increases and counterexamples. Four pairs and nominal
100 ms RSS samples are bounded local evidence, not confidence intervals or a
general speed/memory guarantee.

## Decision

Reject the runtime candidate. The bounded diagnostic improves in 9/9 pairs,
but public generation/IPC improves in only 10/16 pairs, and public API changes
are mostly below 1%. The 100k streaming generation result changes sign with
AB/BA order; its sampled tree RSS rises in every pair. The 750k ordinary API
improves in all four pairs, which supports a small local effect, but does not
establish a sufficiently repeatable public benefit for the extra exception
compatibility code. This is an inconclusive benefit, not a proven slowdown.

The final selected runtime matches the raw `before` map. Raw `after` fingerprints
describe the rejected measured candidate. Keep its exact reversible patch and
all observations for replay; do not rewrite measurements after reverting.
Retain only the benchmark driver's explicit reference option and equivalence
regressions as implementation changes.
