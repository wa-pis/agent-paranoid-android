from __future__ import annotations

import re
from importlib.metadata import PackageMetadata, distributions


APPROVED_SPDX_IDS = frozenset(
    {
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "LGPL-3.0-only",
        "MIT",
        "MIT-0",
        "MPL-2.0",
        "PSF-2.0",
    }
)
APPROVED_CLASSIFIERS = frozenset(
    {
        "License :: OSI Approved :: Apache Software License",
        "License :: OSI Approved :: BSD License",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "License :: OSI Approved :: Python Software Foundation License",
    }
)
LEGACY_LICENSE_IDS = {
    "apache 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "mit": "MIT",
    "mit license": "MIT",
    "mpl-2.0": "MPL-2.0",
    "psfl": "PSF-2.0",
}
_SPDX_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+-]*")
_SPDX_OPERATORS = frozenset({"AND", "OR", "WITH"})


def _approved_spdx_expression(value: str) -> bool:
    identifiers = {
        token
        for token in _SPDX_TOKEN.findall(value)
        if token.upper() not in _SPDX_OPERATORS
    }
    return bool(identifiers) and identifiers <= APPROVED_SPDX_IDS


def approved_license(metadata: PackageMetadata) -> str | None:
    expression = metadata.get("License-Expression")
    if expression:
        if _approved_spdx_expression(expression):
            return expression
        return None

    classifiers = metadata.get_all("Classifier") or []
    approved = sorted(set(classifiers) & APPROVED_CLASSIFIERS)
    if approved:
        return ", ".join(item.rsplit(" :: ", maxsplit=1)[-1] for item in approved)

    legacy_value = (metadata.get("License") or "").strip()
    identifier = LEGACY_LICENSE_IDS.get(legacy_value.lower())
    if identifier in APPROVED_SPDX_IDS:
        return identifier
    if _approved_spdx_expression(legacy_value):
        return legacy_value
    return None


def main() -> None:
    accepted: list[tuple[str, str]] = []
    rejected: list[str] = []
    for distribution in distributions():
        name = distribution.metadata.get("Name")
        if not name:
            continue
        license_name = approved_license(distribution.metadata)
        if license_name is None:
            expression = distribution.metadata.get("License-Expression")
            legacy = distribution.metadata.get("License")
            rejected.append(f"{name}: {expression or legacy or 'unknown'}")
        else:
            accepted.append((name, license_name))

    if rejected:
        details = "\n".join(f"- {item}" for item in sorted(rejected, key=str.lower))
        raise SystemExit(f"unapproved or unknown dependency licenses:\n{details}")

    for name, license_name in sorted(accepted, key=lambda item: item[0].lower()):
        print(f"{name}: {license_name}")
    print(f"Approved dependency licenses: {len(accepted)}")


if __name__ == "__main__":
    main()
