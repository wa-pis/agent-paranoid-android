"""Neutral accessors for business rule configuration."""

from __future__ import annotations

from pathlib import Path

from test_data_agent.business_rules import BusinessRules, business_rules_from_dict, load_business_rules

__all__ = [
    "BusinessRules",
    "business_rules_from_dict",
    "load_business_rules",
    "Path",
]
