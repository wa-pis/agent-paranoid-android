# feedback-corrections Specification

## Purpose
Define the reviewed numeric, rule and CLI contracts delivered by the external-feedback corrections, preserving conservative privacy and deterministic behavior.

## Requirements

### Requirement: Reviewed decimal inference
Declared decimal schema metadata SHALL retain precision and scale. Inference SHALL use only explicitly supplied reviewed synthetic bounds, or return a value-free actionable refusal. It SHALL NOT approximate decimal with FLOAT or copy source extrema.

#### Scenario: Trino declared measure
- WHEN a direct allowed Trino column is decimal(38,16)
- THEN its safe profile retains that schema metadata and a supplied reviewed range yields an exact DatasetSpec.

### Requirement: Honest numeric shape
Numeric profiles SHALL distinguish zero and subunit prevalence from maximum log10 magnitude. Negative magnitudes SHALL remain meaningful and no observed maximum SHALL imply typical frequency.

#### Scenario: Rare large values with mostly subunits
- WHEN an aggregate profile has a positive maximum order and high subunit prevalence
- THEN generation samples the subunit group separately without exposing source values.

### Requirement: Explicit synthetic measure semantics
An explicitly reviewed numeric_measure decimal field MAY generate arbitrary supported synthetic fixed-point amounts. Sensitive names, classifications and identifiers SHALL veto this interpretation; all defaults remain conservative.

#### Scenario: Sensitive policy veto
- WHEN numeric_measure conflicts with a sensitive name, flag or privacy classification
- THEN generation refuses without echoing the disputed numeric value.

### Requirement: Transparent business rule application
Formula rules SHALL expose assignment or check-only intent. Reports SHALL identify assignments without claiming semantic business correctness. SQL export SHALL support the same rule application and mandatory privacy/budget checks. Null and bounded range conditions SHALL be deterministic.

#### Scenario: Formula check preserves input
- WHEN a formula has mode check and its target is inconsistent
- THEN the target remains unchanged and validation records the mismatch.

#### Scenario: Formula assignment audits distribution drift
- WHEN an assigned numeric target exceeds its generation range
- THEN the report and manifest count the checked assignments and violations separately from business constraint validity.

### Requirement: Clear generation contracts
CLI help and diagnostics SHALL state supported modes, output path meaning, ordered-spec seed identity and intentional invalid dataset status, without exposing input values or backend details.

#### Scenario: Saved invalid ratio override
- WHEN a reviewed mixed specification is generated with explicit edge mode and no explicit invalid ratio
- THEN the saved invalid ratio is reset and valid boundary rows are generated.

#### Scenario: Explicit invalid ratio remains invalid
- WHEN edge mode is requested with an explicit nonzero invalid ratio
- THEN generation refuses the incompatible request before publishing output.

### Requirement: Rules travel with the reviewed specification
DatasetSpec SHALL accept typed business_rules. Every deterministic generation consumer, including direct Python, CLI, MCP and reviewed agent workspaces, SHALL apply and validate these rules with the same seed and budget. Validators and exporters SHALL verify supplied rows without reassigning them. Omitted rules SHALL preserve legacy behavior and serialization.

#### Scenario: Format and interface parity
- WHEN one reviewed specification contains formula, conditional and aggregate rules
- THEN generation applies them once and validation checks them across CSV, JSON, Parquet and SQL, including after reload.

### Requirement: Exact decimal rule arithmetic
Ordinary DECIMAL formula assignments and aggregate mappings SHALL use bounded rational arithmetic and a single HALF_UP rounding at the declared target scale, with precision overflow rejected. Aggregate-only business checks SHALL compare bounded exact totals and expressions without reassigning rows or imposing a single-row precision limit on a total. Comparisons SHALL preserve decimal distinctions beyond FLOAT precision. Mixed FLOAT operands SHALL use their finite decimal text representation explicitly; source decimal values SHALL never pass through FLOAT. This ordinary rule contract SHALL NOT authorize or change selective transformation.

#### Scenario: High-precision decimal formula
- WHEN a decimal amount above 2**53 is multiplied by a fractional literal
- THEN assignment and validation agree exactly at the declared target scale under any ambient decimal context.

#### Scenario: Decimal constraint on an unrelated field
- WHEN an entity contains a decimal measure and a constraint on another field
- THEN the constraint is applied and validated rather than rejecting the entire entity.
