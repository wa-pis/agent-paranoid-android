# Safe CSV Profiling Specification

## Purpose

Convert CSV files and CSV folders into safe profile metadata that can drive
synthetic generation without exposing source rows or raw sensitive values.

## Requirements

### Requirement: Profile Metadata Only

CSV profiling SHALL produce metadata, aggregates, distributions, ranges, null
ratios, type hints, relationship candidates, and masked patterns instead of raw
source rows.

#### Scenario: Sensitive values are profiled

- **GIVEN** a CSV contains email, phone, name, address, token, credential, or
  identifier-like columns
- **WHEN** the profiler creates a profile
- **THEN** raw sensitive values are not written to profile artifacts
- **AND** the profile may include only masked patterns or synthetic examples for
  those fields

#### Scenario: Non-sensitive categorical values are profiled

- **GIVEN** a non-sensitive field has a small enum-like distribution
- **WHEN** the profiler creates a profile
- **THEN** the profile may include bounded value counts for generation guidance
- **AND** rare free-text values are not treated as safe examples by default

### Requirement: CSV Structure Detection

CSV profiling SHALL detect practical CSV structure before reading records.

#### Scenario: CSV has a delimiter and header

- **GIVEN** a CSV uses comma, semicolon, tab, or pipe delimiters
- **WHEN** the profiler reads the file
- **THEN** it detects the dialect where practical
- **AND** it rejects missing, blank, or duplicate headers

#### Scenario: CSV has mixed encodings

- **GIVEN** a CSV is encoded as UTF-8, UTF-8 with BOM, or another supported
  fallback encoding
- **WHEN** the profiler reads the file
- **THEN** it selects a readable encoding
- **AND** profile artifacts record safe metadata rather than raw file content

### Requirement: Streaming First

CSV folder profiling SHALL process large files without requiring all source rows
to be held in memory.

#### Scenario: Large folder is profiled

- **GIVEN** a folder contains multiple CSV tables
- **WHEN** the profiler builds a dataset profile
- **THEN** schema, null ratios, distinct estimates, type hints, and safe
  distributions are computed in a streaming pass
- **AND** row-level rule mining uses a bounded sample controlled by
  `--rule-sample-rows`

### Requirement: Safe Cache Contents

Profile caches SHALL contain only safe profile metadata.

#### Scenario: Cached profile is reused

- **GIVEN** a CSV folder profile cache exists for matching file names, sizes,
  modification times, and rule sample settings
- **WHEN** the profiler reuses the cache
- **THEN** the cache contains no source rows or raw PII
- **AND** stale or incomplete cache entries are treated as misses
