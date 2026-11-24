"""Freeze detector policy while allowing equivalent implementation changes.

All values are assembled synthetic test inputs. Failures identify cases and
classification outcomes without including the candidate text or exception text.
"""

from __future__ import annotations

import json
import math
import random
import re
import string
from collections import Counter
from collections.abc import Callable, Iterator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from test_data_agent.core import privacy


# Frozen pre-optimization policy: never import production regexes or helpers here.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[\d\s().-]{7,}$")
_SSN_RE = re.compile(r"^\d{3}-?\d{2}-?\d{4}$")
_PAYMENT_CARD_RE = re.compile(r"^(?:\d[ -]*?){13,19}$")
_JWT_RE = re.compile(r"^[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}$")
_KNOWN_SECRET_RE = re.compile(
    r"^(?:"
    r"(?:sk|pk)_(?:live|test)_[A-Za-z0-9_-]{8,}"
    r"|(?:gh[opurs]|github_pat)_[A-Za-z0-9_]{20,}"
    r"|(?:AKIA|ASIA)[A-Z0-9]{16}"
    r"|xox[baprs]-[A-Za-z0-9-]{10,}"
    r")$"
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret)"
    r"\s*[:=]\s*\S+",
    re.IGNORECASE,
)
_PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
_BEARER_TOKEN_RE = re.compile(r"^Bearer\s+\S+$", re.IGNORECASE)
_TOKEN_ALPHABET_RE = re.compile(r"^[A-Za-z0-9_+/=-]+$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _original_is_iso_date(text: str) -> bool:
    if _ISO_DATE_RE.fullmatch(text) is None:
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _original_passes_luhn_check(text: str) -> bool:
    digits = [int(char) for char in text if char.isdigit()]
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return bool(digits) and checksum % 10 == 0


def _original_looks_high_entropy_token(text: str) -> bool:
    if not 24 <= len(text) <= 4096 or not _TOKEN_ALPHABET_RE.fullmatch(text):
        return False
    character_classes = sum(
        (
            any(char.islower() for char in text),
            any(char.isupper() for char in text),
            any(char.isdigit() for char in text),
            any(char in "_+/=-" for char in text),
        )
    )
    if character_classes < 2:
        return False
    counts = Counter(text)
    entropy = -sum(
        (count / len(text)) * math.log2(count / len(text)) for count in counts.values()
    )
    return entropy >= 3.5


def _original_infer_sensitive_value_type(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if _original_is_iso_date(text):
        return None
    if _PRIVATE_KEY_RE.search(text) or _BEARER_TOKEN_RE.fullmatch(text):
        return "secret"
    if _KNOWN_SECRET_RE.fullmatch(text) or _SECRET_ASSIGNMENT_RE.search(text):
        return "secret"
    if _JWT_RE.fullmatch(text) or _original_looks_high_entropy_token(text):
        return "secret"
    if _EMAIL_RE.fullmatch(text):
        return "email"
    if _SSN_RE.fullmatch(text):
        return "ssn"
    if _PAYMENT_CARD_RE.fullmatch(text) and _original_passes_luhn_check(text):
        return "secret"
    if _PHONE_RE.fullmatch(text) and 7 <= sum(char.isdigit() for char in text) <= 15:
        return "phone"
    return None


def _assert_classification(case_id: str, value: Any) -> None:
    expected = _original_infer_sensitive_value_type(value)
    actual = privacy.infer_sensitive_value_type(value)
    assert actual == expected, f"classification differed for synthetic case {case_id}"
    actual_sensitive = privacy.looks_sensitive_value(value)
    expected_sensitive = expected is not None
    assert actual_sensitive == expected_sensitive, f"sensitivity differed for synthetic case {case_id}"


def _helper_outcome(helper: Callable[[str], bool], text: str) -> tuple[str, bool | str]:
    try:
        return ("returned", helper(text))
    except Exception as error:
        # Direct Luhn calls intentionally retain ValueError for some isdigit chars.
        return ("raised", type(error).__name__)


def _targeted_cases() -> Iterator[tuple[str, str]]:
    email = "fictional" + "@" + "example.test"
    token = "aB3dE5fG7hJ9" + "kL2mN4pQ6rS8" + "tU0vW1xY"
    yield from (
        ("empty", ""), ("ordinary_word", "cancelled"),
        ("ordinary_sentence", "the synthetic parcel arrived"),
        ("email", email), ("email_missing_dot", "fictional" + "@localhost"),
        ("email_inner_newline", "fictional" + "@example.\ntest"),
        ("email_inner_cr", "fictional" + "@example.\rtest"),
        ("email_unicode", "invented\u0131" + "@example.test"),
        ("valid_leap_date", "2024-02-29"), ("invalid_leap_date", "2023-02-29"),
        ("invalid_month", "2024-13-01"), ("invalid_day", "2024-02-30"),
        ("short_date", "2024-2-29"), ("compact_date", "20240229"),
        ("unicode_date", "２０２４-０２-２９"),
        ("arabic_date", "٢٠٢٤-٠٢-٢٩"),
        ("ssn", "000-" + "00-" + "0000"),
        ("ssn_no_first_dash", "000" + "00-" + "0000"),
        ("ssn_no_last_dash", "000-" + "00" + "0000"),
        ("ssn_no_dashes", "000" + "00" + "0000"),
        ("unicode_ssn", "٠٠٠-" + "٠٠-" + "٠٠٠٠"),
        ("phone", "+1-202-" + "555-0100"),
        ("phone_inner_newline", "123\n4567"),
        ("phone_inner_unicode_space", "123\u20034567"),
        ("unicode_phone", "١٢٣٤٥٦٧"),
        ("superscript_phone_rejected", "²" * 7),
        ("zero_card", "0" * 16),
        ("unicode_zero_card", "٠" * 16),
        ("card_unbounded_separators", "0" + " - " * 40 + "0" * 12),
        ("non_luhn_card", "42424242" + "42424243"),
        ("card_trailing_separators", "0" * 13 + " - -"),
        ("high_entropy", token),
        ("assignment_over_email", "client_" + "secret=" + email),
        ("quoted_assignment_over_email", "client_" + 'secret="' + email + '"'),
        ("single_quoted_assignment_over_email", "client_" + "secret='" + email + "'"),
        ("assignment_dotless_i", "apı_" + "key=" + email),
        ("assignment_dotted_i", "apİ_" + "key=" + email),
        ("assignment_long_s", "paſſ" + "word=" + email),
        ("assignment_kelvin", "api_K" + "ey=" + email),
        ("assignment_newlines", "secret\n=\n" + email),
        ("assignment_embedded", "prefixclient_" + "secret:" + email),
        ("assignment_missing_value", "client_" + "secret=\n"),
        ("bearer_over_email", "Bear" + "er " + email),
        ("bearer_newline", "Bear" + "er\n" + email),
        ("bearer_empty", "Bear" + "er \t"),
        ("bearer_embedded_rejected", "prefixBear" + "er " + email),
        ("private_key_embedded", "prefix-----BEGIN " + "PRIVATE KEY-----suffix"),
        ("private_key_rsa", "-----BEGIN " + "RSA PRIVATE KEY-----"),
        ("private_key_invalid_case", "-----begin " + "PRIVATE KEY-----"),
        ("private_key_invalid_newline", "-----BEGIN \n" + "PRIVATE KEY-----"),
    )
    for case_id, prefix, minimum in (
        ("stripe", "sk" + "_test_", 8),
        ("public_key", "pk" + "_live_", 8),
        ("github", "gh" + "p_", 20),
        ("github_pat", "github" + "_pat_", 20),
        ("aws", "AK" + "IA", 16),
        ("aws_session", "AS" + "IA", 16),
        ("slack", "xo" + "xb-", 10),
    ):
        for length in (minimum - 1, minimum, minimum + 1, 4097):
            yield f"known_{case_id}_{length}", prefix + "A" * length
    for length in (7, 8, 9):
        yield f"jwt_segment_{length}", ".".join("A" * length for _ in range(3))
    for digits in (6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 19, 20):
        yield f"zero_digits_{digits}", "0" * digits
        yield f"separated_digits_{digits}", "-".join("0" * digits)
    for length in (0, 1, 7, 8, 9, 10, 11, 12, 13, 19, 20, 23, 24, 25, 4095, 4096, 4097):
        repeated = (token * ((length // len(token)) + 1))[:length]
        yield f"entropy_length_{length}", repeated
        yield f"single_class_length_{length}", "a" * length
    # Exact H=3.5, with adjacent distributions above and below that threshold.
    threshold = "a" * 4 + "b" * 4 + "c" * 4 + "d" * 4 + "EFGH2345" * 2
    for case_id, value in (
        ("entropy_equal", threshold),
        ("entropy_below", threshold.replace("E", "a", 1)),
        ("entropy_above", threshold.replace("a", "E", 1)),
        ("entropy_one_class", "abcdefghijkl" * 2),
        ("entropy_two_classes", "abcdefGHIJKL" * 2),
        ("entropy_11_distinct", "abcdeFGHIJ2" * 4),
        ("entropy_12_distinct", "abcdeFGHIJ23" * 4),
    ):
        yield case_id, value
        yield f"{case_id}_reverse", value[::-1]
        yield f"{case_id}_sorted", "".join(sorted(value))
    for whitespace_id, whitespace in enumerate((" ", "\t", "\n", "\r\n", "\x1c", "\x85", "\u2003", "\u2028", "\u3000", "\u200b")):
        for case_id, value in (("email", email), ("token", token), ("date", "2024-02-29")):
            yield f"padding_{whitespace_id}_{case_id}", whitespace + value + whitespace
            yield f"embedded_space_{whitespace_id}_{case_id}", value[:4] + whitespace + value[4:]


def test_detector_matches_frozen_policy_on_existing_corpus() -> None:
    corpus_path = Path(__file__).parent / "fixtures" / "privacy_detection_cases.json"
    corpus = json.loads(corpus_path.read_text())
    for case in corpus["value_cases"]:
        value = "".join(case["parts"])
        expected = _original_infer_sensitive_value_type(value)
        corpus_expected = case["expected"]
        assert expected == corpus_expected, f"frozen oracle differs for corpus case {case['id']}"
        _assert_classification(case["id"], value)


def test_detector_matches_frozen_policy_on_targeted_synthetic_cases() -> None:
    for case_id, value in _targeted_cases():
        _assert_classification(case_id, value)
    non_strings = (None, False, True, 0, 1234567, 1234567.0, float("nan"),
                   Decimal("1234567"), b"synthetic_bytes", date(2024, 1, 2),
                   datetime(2024, 1, 2, 3, 4), {}, [], (), {1}, frozenset({1}))
    for index, value in enumerate(non_strings):
        _assert_classification(f"non_string_{index}", value)


def test_detector_preserves_string_subclasses_without_calling_overridden_membership() -> None:
    email = "fictional" + "@example.test"
    cases = (
        ("email", email, "email"),
        ("assignment_equals", "client_" + "secret=synthetic_value", "secret"),
        ("assignment_colon", "client_" + "secret:synthetic_value", "secret"),
        ("assignment_over_email", "client_" + "secret=" + email, "secret"),
        ("quoted_assignment_over_email", "client_" + 'secret="' + email + '"', "secret"),
        ("ordinary", "cancelled", None),
    )
    for behavior in ("false", "raise"):
        contains_calls: list[None] = []

        class HostileString(str):
            def strip(self, chars: str | None = None) -> str:
                return self

            def __contains__(self, item: str) -> bool:
                contains_calls.append(None)
                if behavior == "raise":
                    raise AssertionError("overridden string membership was called")
                return False

        for case_id, value, expected in cases:
            candidate = HostileString(value)
            _assert_classification(f"subclass_{behavior}_{case_id}", candidate)
            actual = privacy.infer_sensitive_value_type(candidate)
            assert actual == expected, f"subclass classification differed for synthetic case {case_id}"
        assert not contains_calls, f"subclass membership was invoked for {behavior} behavior"

    class OrdinaryString(str):
        pass

    for case_id, value, _ in cases:
        candidate = OrdinaryString(" \t" + value + "\n")
        stripped_type = type(candidate.strip())
        assert stripped_type is str
        _assert_classification(f"ordinary_subclass_{case_id}", candidate)


def test_detector_matches_frozen_policy_on_generated_synthetic_strings() -> None:
    rng = random.Random(20261122)
    alphabets = (
        string.ascii_letters + string.digits + "_+/=-",
        string.digits + " -().+\t\n\u2003٠١٢٣٤٥٦٧٨٩²",
        string.ascii_letters + string.digits + "@.:=_- \n\r",
        "aA1_@.=:- \t\nıİſK٠９²\u2003\u200b",
    )
    for index in range(1600):
        alphabet = alphabets[index % len(alphabets)]
        length = rng.choice((0, 1, 6, 7, 8, 9, 10, 11, 12, 13, 19, 20, 23, 24, 25, 32, 64, 128))
        value = "".join(rng.choice(alphabet) for _ in range(length))
        _assert_classification(f"random_{index}", value)
    seeds = tuple(_targeted_cases())
    mutations = ("", " ", "\n", "@", ".", ":", "=", "ı", "İ", "ſ", "K", "٠", "²", "\u2003")
    for index in range(600):
        _, original = rng.choice(seeds)
        position = rng.randrange(len(original) + 1)
        fragment = rng.choice(mutations)
        value = original[:position] + fragment + original[position + rng.choice((0, 1)):]
        _assert_classification(f"mutation_{index}", value)


def test_detector_helpers_match_frozen_policy_including_exception_types() -> None:
    helpers = (
        ("iso_date", privacy.is_iso_date, _original_is_iso_date),
        ("luhn", privacy.passes_luhn_check, _original_passes_luhn_check),
        ("entropy", privacy.looks_high_entropy_token, _original_looks_high_entropy_token),
    )
    cases = list(_targeted_cases())
    cases.extend((
        ("superscript_digit", "²"), ("circled_digit", "①"),
        ("mixed_non_decimal_digit", "0²0"), ("unicode_decimal_digit", "٠"),
        ("no_digits", "synthetic_text"), ("ignored_non_digits", "synthetic_0_value"),
    ))
    for case_id, value in cases:
        for helper_id, actual_helper, original_helper in helpers:
            expected = _helper_outcome(original_helper, value)
            actual = _helper_outcome(actual_helper, value)
            assert actual == expected, f"{helper_id} differed for synthetic case {case_id}"


def test_collection_classifier_preserves_first_detection_and_secret_priority() -> None:
    email = "fictional" + "@example.test"
    phone = "+1-202-" + "555-0100"
    ssn = "000-" + "00-0000"
    secret = "client_" + "secret=synthetic_value"
    cases = (
        ((), None), ((None, "cancelled"), None),
        ((email, phone, ssn), "email"), ((phone, email, ssn), "phone"),
        ((ssn, email, phone), "ssn"), ((email, secret, phone), "secret"),
        ((secret, email), "secret"),
    )
    for index, (values, expected) in enumerate(cases):
        actual = privacy.infer_sensitive_type_from_values(iter(values))
        assert actual == expected, f"collection priority differed for synthetic case {index}"
