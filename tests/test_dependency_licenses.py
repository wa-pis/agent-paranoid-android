from __future__ import annotations

from email import message_from_string

from scripts.check_dependency_licenses import approved_license


def test_approved_license_accepts_composed_spdx_expression() -> None:
    metadata = message_from_string(
        "Name: example\nLicense-Expression: Apache-2.0 OR BSD-3-Clause\n"
    )

    assert approved_license(metadata) == "Apache-2.0 OR BSD-3-Clause"


def test_approved_license_accepts_legacy_osi_classifier() -> None:
    metadata = message_from_string(
        "Name: example\nLicense: UNKNOWN\n"
        "Classifier: License :: OSI Approved :: MIT License\n"
    )

    assert approved_license(metadata) == "MIT License"


def test_approved_license_accepts_spdx_expression_in_legacy_field() -> None:
    metadata = message_from_string("Name: example\nLicense: MPL-2.0 AND MIT\n")

    assert approved_license(metadata) == "MPL-2.0 AND MIT"


def test_approved_license_rejects_unknown_or_unapproved_metadata() -> None:
    unknown = message_from_string("Name: unknown\n")
    proprietary = message_from_string(
        "Name: proprietary\nLicense-Expression: LicenseRef-Proprietary\n"
    )

    assert approved_license(unknown) is None
    assert approved_license(proprietary) is None
