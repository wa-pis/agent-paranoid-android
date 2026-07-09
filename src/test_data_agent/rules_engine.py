"""Legacy compatibility wrapper for business-rule application."""

from test_data_agent.core.settings import GenerationMode
from test_data_agent.rules.engine import apply_business_rules

__all__ = ["GenerationMode", "apply_business_rules"]
