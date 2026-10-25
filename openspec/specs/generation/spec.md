# generation Specification

## Purpose
Define executable edge/load generation and recoverable folder publication, sharing relationship, rule, privacy and resource enforcement with other modes.

## Requirements

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
destinations and folder replacements containing an input spec or business-rule
file, including path aliases. Single-file and stdout publication SHALL protect
input rule files from collisions with generated data and control artifacts.
Without overwrite nonempty
folders SHALL remain unchanged.

#### Scenario: Publication failure
- WHEN replacement fails after old output moves to backup
- THEN old output is restored and no partial replacement is visible.

#### Scenario: Rule input is inside the destination
- WHEN folder overwrite would remove an input business-rule file, or generated
  artifacts would replace that file or its symlink/hardlink alias
- THEN admission rejects the request before publication and preserves the input
  and existing bundle.
