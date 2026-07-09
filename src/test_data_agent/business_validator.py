"""Legacy compatibility wrapper for business-rule validation."""

from test_data_agent.rules.validation import BusinessValidationReport, RuleResult, validate_business_rules

__all__ = [
    "BusinessValidationReport",
    "RuleResult",
    "validate_business_rules",
]
