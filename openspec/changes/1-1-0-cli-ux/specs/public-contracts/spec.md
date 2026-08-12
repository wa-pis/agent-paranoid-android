# Public Contracts Specification Delta

## Added Requirements

### Requirement: CLI Machine Output Is Versioned And Isolated

Every public CLI workflow SHALL offer one versioned machine-readable result
without mixing human output into stdout.

#### Scenario: A command succeeds in JSON mode

- **GIVEN** a supported command with `--json`
- **WHEN** the command completes
- **THEN** stdout contains exactly one `CliSuccessResponse` or the command's
  existing versioned agent document
- **AND** stderr is empty
- **AND** the response contains no source or generated rows

#### Scenario: A command fails in JSON mode

- **GIVEN** usage, dependency, configuration, input, I/O, provider,
  cancellation, or internal failure
- **WHEN** JSON mode is active
- **THEN** stdout contains exactly one bounded `CliErrorResponse`
- **AND** stderr and traceback output are empty
- **AND** callers can branch on a stable error category and process code

### Requirement: Existing CLI Invocation Remains Compatible

The `1.1.0` CLI SHALL preserve all current commands, aliases, successful
arguments, and expected `0`, `1`, and `2` process meanings.

#### Scenario: An existing valid script runs

- **GIVEN** a correctly suffixed output and no cross-run bundle collision
- **WHEN** an existing command or compatibility alias executes
- **THEN** its arguments, defaults, artifacts, and human output remain valid
- **AND** JSON mode remains optional

#### Scenario: A technical failure occurs

- **GIVEN** I/O, provider, internal, or cancellation failure
- **WHEN** the top-level CLI handles it
- **THEN** it uses the documented distinct process code
- **AND** expected validation failure remains code `1`
- **AND** ordinary usage/input failure remains code `2`

### Requirement: CLI Help Is Installed-Package Discoverable

Built-in help SHALL lead a new user through a checkout-free core workflow and
remain readable in a standard terminal.

#### Scenario: A base-wheel user follows help

- **GIVEN** no repository checkout or optional extra
- **WHEN** the user reads root help and the demo help
- **THEN** the first dataset example uses the bundled offline demo
- **AND** every other example either uses a user placeholder or declares its
  checkout/extra prerequisite
- **AND** significant defaults, units, output scope, and overwrite behavior are
  visible without reading source

#### Scenario: Help is rendered at standard widths

- **GIVEN** terminal widths of 80 and 120 columns
- **WHEN** root and command help are rendered without a TTY
- **THEN** descriptions, options, and examples remain within the selected width
- **AND** no color, prompt, or progress output is introduced

### Requirement: Shell Completion Follows The Parser

The CLI SHALL generate completion candidates from the current public parser
for bash, zsh, fish, and PowerShell.

#### Scenario: A user requests completion

- **GIVEN** one supported shell name
- **WHEN** the completion command runs
- **THEN** it writes only the generated completion script to stdout
- **AND** command, alias, and option candidates match the parser
- **AND** no separately maintained command inventory is required
