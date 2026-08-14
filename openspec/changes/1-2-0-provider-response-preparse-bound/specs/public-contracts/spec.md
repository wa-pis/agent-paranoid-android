# Public Contracts Specification Delta

## Added Requirements

### Requirement: Bounded Provider Response Parsing

Optional external advisor adapters SHALL apply a finite local byte budget to
structured response text before application JSON/Pydantic parsing.

#### Scenario: Provider response is within budget

- **GIVEN** an external advisor returns non-empty structured response text
- **WHEN** its UTF-8 size is within the configured response budget
- **THEN** the application may parse and validate it against the typed response
  model
- **AND** per-call metadata records the measured bounded response size

#### Scenario: Provider response exceeds the budget

- **GIVEN** an external advisor returns response text larger than the configured
  byte budget
- **WHEN** the application receives the response
- **THEN** it rejects the response before application JSON/Pydantic parsing
- **AND** no proposal is returned or applied
- **AND** public errors and per-call metadata do not retain provider text,
  credentials, source literals, or nested provider exceptions
