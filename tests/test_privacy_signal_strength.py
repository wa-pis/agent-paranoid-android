"""Reason codes add context without changing conservative recognition."""

import pytest

from test_data_agent.core.limits import InputLimitError
from test_data_agent.core.privacy import (
    SensitiveValueSignal,
    infer_profile_string_signal,
    infer_sensitive_value_signal,
    infer_sensitive_value_type,
    infer_source_value_signal,
)
from test_data_agent.csv_profiler import _csv_sensitive_signal, _csv_sensitive_value_type


@pytest.mark.parametrize("parts,signal,context,strong", [
    (("-----BEGIN ", "PRIVATE KEY-----"), SensitiveValueSignal.PRIVATE_KEY, None, True),
    (("Bear", "er synthetic_payload"), SensitiveValueSignal.BEARER_TOKEN, None, True),
    (("sk", "_test_", "A1b2C3d4E5f6"), SensitiveValueSignal.KNOWN_SECRET, None, True),
    (("pass", "word=synthetic_value"), SensitiveValueSignal.SECRET_ASSIGNMENT, None, True),
    (("abcdefgh.", "ijklmnop.", "qrstuvwx"), SensitiveValueSignal.JWT_SHAPE, "secret", False),
    (("0123456789abcdef",) * 2, SensitiveValueSignal.HIGH_ENTROPY, "secret", False),
    (("fictional", "@example.test"), SensitiveValueSignal.EMAIL, None, False),
    (("000-", "00-", "0000"), SensitiveValueSignal.SSN_FORMAT, None, False),
    (("000", "00", "0000"), SensitiveValueSignal.SSN_DIGITS, "ssn", False),
    (("000-", "00", "0000"), SensitiveValueSignal.SSN_DIGITS, "ssn", False),
    (("000", "00-", "0000"), SensitiveValueSignal.SSN_DIGITS, "ssn", False),
    (("42424242",) * 2, SensitiveValueSignal.LUHN, "card", False),
    (("+1-202-", "555-0100"), SensitiveValueSignal.PHONE, None, False),
], ids=["private_key", "bearer", "known_key", "assignment", "jwt_shape", "entropy",
        "email", "formatted_ssn", "ssn_digits", "ssn_first_dash", "ssn_second_dash",
        "luhn", "phone"])
def test_fixed_reason_codes_preserve_legacy_types_and_retain_no_input(
    parts: tuple[str, ...], signal: SensitiveValueSignal, context: str | None, strong: bool,
) -> None:
    value = "".join(parts)
    actual = infer_sensitive_value_signal(value)
    assert actual is signal
    assert infer_sensitive_value_signal(value) is actual
    assert infer_sensitive_value_type(value) == signal.value_type
    assert signal.required_context == context
    assert signal.strong_secret is strong
    assert value not in repr(signal)


def test_ssn_reason_uses_underlying_string_format_independently_of_subclass_methods() -> None:
    class SyntheticString(str):
        def strip(self, chars: str | None = None) -> str:
            return self

        def count(self, sub: str, start: int = 0, end: int | None = None) -> int:
            raise AssertionError("overridden string count was called")

    candidate = SyntheticString("000-" + "00-" + "0000")
    assert infer_sensitive_value_signal(candidate) is SensitiveValueSignal.SSN_FORMAT
    assert infer_sensitive_value_type(candidate) == "ssn"


@pytest.mark.parametrize("value,signal", [
    ("4.242424242424242e15", SensitiveValueSignal.LUHN),
    ("4242424242424242.1", SensitiveValueSignal.LUHN),
    ("-4242424242424242.1", SensitiveValueSignal.LUHN),
    ("9.12345678e8", SensitiveValueSignal.SSN_DIGITS),
], ids=["exponent_card", "rounded_card", "negative_rounded_card", "exponent_ssn"])
def test_numeric_normalization_preserves_the_evidence_reason(
    value: str, signal: SensitiveValueSignal,
) -> None:
    assert _csv_sensitive_signal(value) is signal
    assert _csv_sensitive_value_type(value) == signal.value_type


@pytest.mark.parametrize("detector", [
    infer_profile_string_signal, infer_source_value_signal, _csv_sensitive_signal,
])
def test_source_detectors_honor_scoped_character_limits(detector, monkeypatch) -> None:
    monkeypatch.setenv("TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS", "4")
    candidate = "synthetic_status"
    with pytest.raises(InputLimitError, match="character limit"):
        detector(candidate)
    assert detector(candidate, max_chars=len(candidate)) is None
    with pytest.raises(InputLimitError, match="character limit"):
        detector(candidate, max_chars=len(candidate) - 1)
