# Public Contracts Delta

## Added Requirements

### Requirement: Compatibility Surface Inventory

Every retained command alias, Python wrapper, and transitional compatibility
behavior SHALL have a documented status, canonical replacement, and support
window.

#### Scenario: A user adopts a retained wrapper

- **GIVEN** an application imports a documented compatibility wrapper
- **WHEN** the user reviews migration guidance
- **THEN** the canonical import is identifiable
- **AND** the minimum supported lifetime is explicit

#### Scenario: A retained surface is deprecated

- **GIVEN** maintainers plan to remove a supported alias or wrapper
- **WHEN** deprecation begins
- **THEN** migration guidance and a changelog notice are published
- **AND** the surface remains for at least one feature release and 90 days
- **AND** removal does not occur before the documented major-version boundary
