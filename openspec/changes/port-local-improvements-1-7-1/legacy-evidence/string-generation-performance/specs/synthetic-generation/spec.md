# Synthetic Generation Delta

## ADDED Requirements

### Requirement: Preserve random string construction during optimization

String-generation optimization SHALL preserve seeded values, types, Random/Faker
state, length/prefix behavior, dynamic per-character choices and exceptions for
supported inputs. It SHALL retain shared privacy and generation policy across
every source-derived specification and SHALL NOT introduce row/value caches.

#### Scenario: Ordinary and tiled generation construct random strings

- **GIVEN** a fictional specification, explicit seed and existing generation engine
- **WHEN** optimized string construction runs
- **THEN** its rows and CSV bytes match that engine's previous output
- **AND** random-call order, privacy, validation and work/output budgets remain.

#### Scenario: A custom RNG interrupts character selection

- **GIVEN** a custom random-choice implementation raises an exception
- **WHEN** string construction cannot complete
- **THEN** previous exception type/message, cause and random state are preserved
- **AND** setup exceptions retain their existing conversion behavior.

### Requirement: Retain checked bounded export during string optimization

String optimization SHALL retain mandatory validation, strict privacy, private
temporary files and atomic publication. Performance evidence SHALL preserve
all paired observations, both memory metrics and within-engine byte equality.

#### Scenario: An export fails after candidate generation

- **GIVEN** a budget, worker, encoding or validation failure interrupts export
- **WHEN** successful publication is impossible
- **THEN** no partial trusted bundle is published
- **AND** existing destination protection and owned-resource cleanup remain.
