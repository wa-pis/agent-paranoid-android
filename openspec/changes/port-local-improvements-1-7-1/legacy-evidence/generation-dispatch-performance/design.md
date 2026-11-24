# Design: Generation Dispatch Performance

Keep generation in `generation/entity_generator.py`; both the ordinary entity
loop and `generation/tiled_generator.py` call its shared row/field helpers.
Move distribution selection into the already existing scalar branches. The
categorical selection remains ahead of scalar dispatch, including cross-type
categorical distributions. No selected distribution, scalar operation, comparison,
random draw or provider request changes for the branch actually reached.

Null, controlled invalid, identifier, sensitive string and semantic-provider
handling retain their priority and early returns. Typed distribution preparation
remains local to the ordinary entity or logical tile. No metadata or row-result
cache is introduced, so later spec edits are still observed.

Freeze the complete current package and original benchmark helpers before edits.
Compare with a separate candidate copy differing only in the generator module.
Reuse the previous paired driver's fresh-process measurement, AB/BA schedule and
paired statistics; reuse the original public worker, phase instrumentation,
process-tree RSS sampling and independent bundle audit without modification.
Verify source origins/fingerprints and exact CSV hashes within each engine.

Use four adjacent pairs per case, alternate path order, and exclude four small
smoke runs from performance summaries. Preserve every run, including regressions.
Retain the candidate only if equivalent results and safety checks pass and paired
generation improvements repeat without a consistent material total-time or
memory regression. Report all stages and limits. Streaming generation/IPC is
coordinator work plus exposed waiting; overlapped worker computation is not its
sum, so a faster producer need not produce the same total-time gain as serial
generation. RSS is sampled and may count shared pages repeatedly; four pairs
are a local experiment, not a statistical confidence interval or a general claim.
