# Campaign design

Use the existing deterministic suites and CI jobs as the foundation. Add only
missing installed/interface acceptance cases and a small coverage-ledger/report
layer; do not create another generation engine or duplicate all unit tests.

One logical case identifies source route, output, mode, reviewed option/rule
fixture and interface. Acquisition and generation are separate steps: a route
without a native MCP profiler hands a safe profile or reviewed specification to
MCP. Record that composition, rather than pretending MCP acquired the source.

At today's inventory, 10 sources × 4 outputs × 5 modes × 3 interfaces yields
600 logical core cells. MCP 1/2 executions are environment repetitions of the
same cells. The existing 200 Python cases may satisfy the Python slice only
after installed-wheel execution is verified. Derive expected counts from the
final inventory and fail on omitted cells; do not rely on this number forever.

Beyond that core, require every public option's omitted/default, supported
non-default, boundary and invalid cases where applicable. Use compatible
pairwise combinations and explicit high-risk three-way cases, not an impossible
claim to enumerate every numeric value or arbitrary formula. Rule families run
against every output and interface through the common reviewed specification.

Reuse owned MCP processes within bounded fixture groups to avoid hundreds of
startup costs, while retaining fresh request budgets, independent workspaces,
deadline checks and teardown assertions. Installed subprocesses run outside the
checkout with source-tree import paths removed. Compare typed restored values,
effective contracts, reports and provenance after normalizing only documented
volatile fields, never rounding exact decimals or deleting failure details.

Acceptance report states are passed, failed, blocked and not_applicable. Missing
dependencies or unexecuted required coverage are blocked. N/A needs a documented
contract reason and, for shared generation semantics, a tested supported route.
Manual human review evidence remains distinct from automated fictional approval
fixtures. Any repair supersedes exact-SHA acceptance and triggers relevant
rechecks plus the final full project gate.
