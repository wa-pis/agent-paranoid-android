# PostgreSQL transport gate — 2026-09-28

## Scope reconciliation superseded by owner capacity decision

Owner accepted a target of 1,000,000 x100 and mandatory 300,000 x50 acceptance,
with actionable session/profile configuration in limit errors. Implement that
measured capacity contract; do not introduce hard RSS/wire guarantees or change
platform support without separate authority. Retain existing guards and identify
unmeasured properties honestly. The historical pause below is no longer current.

The author's recent notes elevated hard worker-memory/wire-byte containment
into release gates without a separate owner decision. The existing contract
(policy-contract.md, native Parquet decoded-payload paragraph) explicitly does
not promise peak-memory containment. PostgreSQL baseline config defines rows,
cells, columns, statements and timeouts, not exact wire-byte or RSS limits;
Trino separately retains its configured scan/time and measured payload budgets.
Existing implementation guards must not be removed or relabelled as stronger
guarantees. No new platform/dependency restriction has been authorized.

Owner question: retain these existing measured budgets and honestly disclose
unmeasured peak-memory/wire properties for 1.6, leaving hard OS/wire containment
as a separately scoped enhancement, or explicitly add that stronger guarantee
to this release? Automation paused pending this safety/scope clarification.
No current runtime policy changed and no activation gate declared passed.

Status: private supervisor plus fictional evidence; public capture remains inactive. No database contacted,
no new minimum dependency requirement and no completed transport gate claimed.

## Evidence

- Declared dependency is `psycopg>=3.2.0`; local inspected implementation is
  psycopg 3.3.4 (`connection_async.py`, `connection.py`, `waiting.py`).
- Official [connection API](https://www.psycopg.org/psycopg3/docs/api/connections.html)
  says `cancel_safe(timeout=...)` falls back to legacy cancellation with libpq
  before 17; its timeout has no effect there. A successful cancellation request
  is not confirmation that server work stopped.
- Local async `wait()` catches cancellation, calls `_try_cancel(timeout=5.0)`,
  then resumes waiting for the original operation. Therefore merely wrapping
  an async call in an application timeout is not evidence of bounded shutdown.
- Local `_try_cancel()` logs cancellation exception text. Do not allow driver
  diagnostics onto the agent's value-free error/log surface during a timeout.
- Named server cursors bound rows per fetch, not an individual value's wire
  size, protocol error size, or libpq's pre-return allocations. Arrow `nbytes`
  and the Parquet output cap are post-receive limits, not transport limits.
- Existing repository code has no general subprocess/resource supervisor to
  reuse. Existing Trino work-budget accounting is not a PostgreSQL wire reader.

## Completed experiment (fictional only)

`tests/test_transformation_postgres_isolation.py`: 11 cases passed locally on
Python 3.11/macOS, using spawn and the real private capture/stream functions with
an injected fictional driver, without monkeypatching product code. Fixed-size
shared memory bounds the return channel; bytes are accepted only after normal
worker exit and valid length. Worker fd 1/2 go to the null device.

Success, oversized result, backend failure, partial-write interruption, caller
cancellation, and blocked connect/execute/fetch/cursor-close/rollback/connection-
close are covered. Startup has a separate 10-second allowance; blocked-call
probe waits 150 ms, then terminate/join with kill/join fallback (one second each).
Every tested child was reaped. This is not yet a production supervisor or evidence
for uninterruptible kernel waits, Windows behavior, memory caps, wire-byte limits,
or server-side termination. Do not reuse the startup allowance as a release SLA.

## Private supervisor integration

`io/transformation_postgres_capture.py` calls the actual capture/stream path
inside a spawned process. `_PostgresCapture` carries explicit typed inputs;
the callable driver factory is trusted development code, not an external script
or a user-selectable module. No public entry point or default live driver exists.
One monotonic deadline starts before shared-buffer allocation/process startup.
Reserve min(2 seconds, one quarter of budget) for terminate/kill/reap; only normal
exit, valid bounded length and remaining time permit returning a snapshot.
Fd diagnostics and exception objects do not pass through the result channel.
Memoryview copies avoid expanding result bytes into a Python integer list.

Integration cases cover success, driver failure and six blocked driver stages;
six control cases reject invalid byte/time limits. The eleven earlier test-only
lifecycle cases remain. Two additional POSIX tests now exercise the actual
supervisor: isolated-harness SIGINT while the driver is blocked in fetch, and a
worker ignoring SIGTERM that requires the kill fallback. Both passed locally;
the cancellation case verifies no output, no active child and no remaining
worker PID. Signals target only test-owned processes, not pytest/the terminal.
These two tests skip non-POSIX hosts; Windows cancellation is not claimed passed.

This bounds ordinary process waits and result IPC, not absolute OS scheduling,
uninterruptible process start/kill, worker memory or network bytes. Failure to
reap is a fixed error, never a successful snapshot. Resource enforcement and
backend-work evidence remain the next implementation gates.
No thread-only timeout: an abandoned thread retains its connection and work.
Do not call this experiment a wire-byte or memory cap. Evaluate those separately
before wiring a real driver, and retain server read-only/statement limits because
client process termination is not proof of immediate backend cancellation.

Acceptance before activation still needs: bounded connect/execute/fetch/cleanup;
pre-allocation or isolated resource enforcement; explicit backend work limits;
no partial snapshot/publication; exact context binding; independent safety review.
If portability requires a new supported-platform or libpq-version restriction,
obtain the owner's decision rather than silently changing compatibility.
