from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).parent.parent
REQUIREMENT_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)>=(?P<minimum>[0-9.]+)"
    r"(?:,<(?P<upper>[0-9]+)\.0\.0)?$"
)


class CompatibilityError(ValueError):
    pass


def _normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_requirement(requirement: str) -> tuple[str, str, int | None]:
    match = REQUIREMENT_RE.fullmatch(requirement)
    if match is None:
        raise CompatibilityError(f"unsupported dependency declaration: {requirement}")
    upper = match.group("upper")
    return (
        _normalized_name(match.group("name")),
        match.group("minimum"),
        int(upper) if upper is not None else None,
    )


def _read_constraints(path: Path) -> dict[str, str]:
    constraints: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, separator, version = line.partition("==")
        if not separator:
            raise CompatibilityError(f"constraint must use an exact pin: {line}")
        constraints[_normalized_name(name)] = version
    return constraints


def _policy(root: Path) -> dict[str, Any]:
    return tomllib.loads(
        (root / ".github" / "dependency-compatibility.toml").read_text()
    )


def check_repository(root: Path = ROOT) -> dict[str, str]:
    policy = _policy(root)
    dependencies: dict[str, dict[str, Any]] = policy["dependencies"]
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]

    declared: dict[str, tuple[str, str, int | None]] = {}
    for requirement in project["dependencies"]:
        name, minimum, upper = _parse_requirement(requirement)
        declared[name] = ("base", minimum, upper)
    for extra, requirements in project["optional-dependencies"].items():
        if extra in {"all", "dev"}:
            continue
        for requirement in requirements:
            name, minimum, upper = _parse_requirement(requirement)
            declared[name] = (extra, minimum, upper)

    expected_names = set(dependencies)
    if set(declared) != expected_names:
        raise CompatibilityError(
            "dependency policy inventory differs from runtime metadata: "
            f"policy={sorted(expected_names)}, metadata={sorted(declared)}"
        )

    for name, entry in dependencies.items():
        actual = declared[name]
        expected = (entry["extra"], entry["minimum"], entry.get("upper_major"))
        if actual != expected:
            raise CompatibilityError(
                f"unreviewed dependency range drift for {name}: "
                f"expected {expected}, got {actual}"
            )

    all_names = {
        _parse_requirement(requirement)[0]
        for requirement in project["optional-dependencies"]["all"]
    }
    optional_names = {
        name for name, entry in dependencies.items() if entry["extra"] != "base"
    }
    if all_names != optional_names:
        raise CompatibilityError("the all extra does not match reviewed optional dependencies")

    minimum_expected = {
        name: entry["minimum"] for name, entry in dependencies.items()
    }
    for profile, profile_entry in policy["minimum_profiles"].items():
        expected = dict(minimum_expected)
        expected.update(
            {
                _normalized_name(name): version
                for name, version in profile_entry.items()
                if name != "constraint"
            }
        )
        constraint = root / profile_entry["constraint"]
        actual = _read_constraints(constraint)
        if profile == "mcp":
            expected = {
                name: version
                for name, version in expected.items()
                if dependencies[name]["extra"] in {"base", "mcp"}
            }
        if actual != expected:
            raise CompatibilityError(
                f"minimum constraint drift for {profile}: "
                f"expected {expected}, got {actual}"
            )

    lock = tomllib.loads((root / "uv.lock").read_text())
    locked = {package["name"]: package["version"] for package in lock["package"]}
    reviewed_latest = {
        name: entry["latest"] for name, entry in dependencies.items()
    }
    for name, version in reviewed_latest.items():
        if locked.get(name) != version:
            raise CompatibilityError(
                f"unreviewed latest dependency drift for {name}: "
                f"expected {version}, got {locked.get(name)}"
            )

    workflow = (root / ".github" / "workflows" / "ci.yml").read_text()
    for profile, profile_entry in policy["minimum_profiles"].items():
        constraint_name = Path(profile_entry["constraint"]).name
        if f"profile: {profile}" not in workflow or constraint_name not in workflow:
            raise CompatibilityError(f"minimum profile {profile} is not wired into CI")

    documentation = (root / "docs" / "reference" / "dependency-compatibility.md").read_text()
    for name, entry in dependencies.items():
        if entry["minimum"] not in documentation or entry["latest"] not in documentation:
            raise CompatibilityError(f"dependency versions for {name} are not documented")

    return reviewed_latest


def check_manifest(manifest_path: Path, reviewed_latest: dict[str, str]) -> None:
    manifest = json.loads(manifest_path.read_text())
    reproducibility = manifest.get("reproducibility")
    if not isinstance(reproducibility, dict):
        raise CompatibilityError("manifest is missing reproducibility evidence")
    normalized = reproducibility.get("normalized_dependencies")
    if not isinstance(normalized, dict):
        raise CompatibilityError("manifest is missing normalized dependency evidence")

    package_version = manifest.get("package_version")
    if (
        not isinstance(package_version, str)
        or reproducibility.get("generator_algorithm_version") != package_version
    ):
        raise CompatibilityError("manifest is missing generator version evidence")

    required = set(reviewed_latest)
    missing = required - set(normalized)
    if missing:
        raise CompatibilityError(
            f"manifest dependency evidence is incomplete: {sorted(missing)}"
        )

    payload = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    expected_digest = hashlib.sha256(payload).hexdigest()
    if reproducibility.get("normalized_dependencies_sha256") != expected_digest:
        raise CompatibilityError("manifest dependency evidence digest is invalid")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    reviewed_latest = check_repository()
    if args.manifest is not None:
        check_manifest(args.manifest, reviewed_latest)
    print("Dependency compatibility policy is complete and reviewed.")


if __name__ == "__main__":
    main()
