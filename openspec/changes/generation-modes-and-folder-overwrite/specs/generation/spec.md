## ADDED Requirements

### Requirement: Executable edge and load modes
The generator SHALL create deterministic valid edge values and load_test data
with default tenfold volume. Explicit count SHALL override multiplication.
Relationships, business rules, privacy and bounded resource checks SHALL remain enforced.

#### Scenario: Explicit load count
- WHEN load_test is requested with count 7
- THEN each selected entity has exactly 7 rows and valid declared relationships.

### Requirement: Recoverable folder overwrite
The generation adapter SHALL stage a complete replacement before publication
and SHALL restore previous output if publication fails. It SHALL reject symlink
destinations and output containing the input spec. Without overwrite nonempty
folders SHALL remain unchanged.

#### Scenario: Publication failure
- WHEN replacement fails after old output moves to backup
- THEN old output is restored and no partial replacement is visible.
