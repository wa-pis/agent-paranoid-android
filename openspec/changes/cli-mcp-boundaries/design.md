# Design: cli-mcp-boundaries

## Approach

Refactor one boundary at a time:

1. move CLI parser construction behind a function while retaining `cli.main`;
2. isolate human and JSON presentation from command application logic;
3. make generator MCP registration call narrow application services;
4. make Trino MCP registration call narrow allowlisted application services.

Each step keeps the old public entry point and passes the complete contract
suite before the next extraction begins.

## Data And Contracts

No public model or wire format changes. Affected surfaces are:

- the `test-data-agent` entry point, subcommands, help, errors, and exit codes;
- versioned agent CLI JSON;
- generator and Trino MCP tool names, input schemas, results, and errors;
- existing `DatasetSpec`, advisor, approval, audit, and artifact contracts.

Application services accept typed values or validated models. Transport code
may decode requests and encode responses, but core safety checks remain below
that boundary.

## Failure Modes

- Parser extraction can alter defaults, aliases, help, or JSON parser errors.
  CLI and golden tests compare the public behavior.
- Presentation extraction can leak exception details or rows. Typed response
  tests continue to require bounded metadata-only output.
- MCP extraction can weaken validation or change schemas. Contract fixtures
  and safety tests run against registered tools and direct services.
- Partial refactors can create circular imports. Every increment must compile,
  type-check, and remain independently shippable.

## Alternatives

- One large module rewrite was rejected because it obscures contract drift.
- Replacing `argparse` or the MCP SDK was rejected because it adds migration
  risk without product value.
- Postponing all structure work until 1.0 was rejected because current module
  boundaries make stabilization harder.
