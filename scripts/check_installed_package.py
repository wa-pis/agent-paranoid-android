"""Verify the installed distribution rather than the source checkout."""

from __future__ import annotations

import argparse
import importlib.util
import re
from importlib.metadata import distribution, distributions
from importlib.resources import files
from pathlib import Path

from test_data_agent.version import __version__


DISTRIBUTION_NAME = "agent-paranoid-android"
EXPECTED_SCRIPTS = {
    "test-data-agent": "test_data_agent.cli:main",
    "test-data-agent-mcp-generator": "test_data_agent.mcp_generator_server:main",
    "test-data-agent-mcp-trino": "test_data_agent.mcp_trino_server:main",
}
EXPECTED_PROJECT_URLS = {
    "Documentation, https://wa-pis.github.io/agent-paranoid-android/",
    "Issues, https://github.com/wa-pis/agent-paranoid-android/issues",
    "Changelog, https://github.com/wa-pis/agent-paranoid-android/blob/main/CHANGELOG.md",
    "Release Notes, https://github.com/wa-pis/agent-paranoid-android/releases",
    (
        "Container Images, "
        "https://github.com/wa-pis/agent-paranoid-android/pkgs/container/"
        "agent-paranoid-android-cli"
    ),
}
EXPECTED_BASE_DEPENDENCIES = {"faker", "pydantic", "pyyaml"}
EXPECTED_EXTRAS = {"all", "dev", "mcp", "parquet", "trino"}
EXPECTED_RUNTIME_EXTRA_DEPENDENCIES = {
    "all": {"mcp", "pyarrow", "sqlglot", "trino"},
    "mcp": {"mcp"},
    "parquet": {"pyarrow"},
    "trino": {"sqlglot", "trino"},
}
OPTIONAL_MODULES = {
    "mcp": {"mcp"},
    "parquet": {"pyarrow"},
    "trino": {"sqlglot", "trino"},
}
MAX_DISTRIBUTIONS = {
    "base": 10,
    "mcp": 35,
    "parquet": 11,
    "trino": 25,
}
BOOTSTRAP_DISTRIBUTIONS = {"pip", "setuptools", "uv", "wheel"}
MAX_WHEEL_SIZE_BYTES = 256 * 1024


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    installed = distribution(DISTRIBUTION_NAME)
    if installed.version != __version__:
        raise SystemExit(
            f"installed metadata version {installed.version!r} does not match "
            f"package version {__version__!r}"
        )

    project_urls = set(installed.metadata.get_all("Project-URL") or [])
    missing_urls = EXPECTED_PROJECT_URLS - project_urls
    if missing_urls:
        raise SystemExit(f"installed wheel is missing project URLs: {sorted(missing_urls)}")

    requirements = installed.requires or []
    dependencies_by_extra = group_dependencies_by_extra(requirements)
    base_dependencies = dependencies_by_extra.get("base", set())
    if base_dependencies != EXPECTED_BASE_DEPENDENCIES:
        raise SystemExit(
            "installed wheel has invalid base dependencies: "
            f"{sorted(base_dependencies)}"
        )
    for extra, expected in EXPECTED_RUNTIME_EXTRA_DEPENDENCIES.items():
        actual = dependencies_by_extra.get(extra, set())
        if actual != expected:
            raise SystemExit(
                f"installed wheel has invalid {extra} dependencies: "
                f"{sorted(actual)}"
            )
    extras = set(installed.metadata.get_all("Provides-Extra") or [])
    if extras != EXPECTED_EXTRAS:
        raise SystemExit(f"installed wheel has invalid extras: {sorted(extras)}")

    marker = files("test_data_agent").joinpath("py.typed")
    if not marker.is_file():
        raise SystemExit("installed wheel is missing test_data_agent/py.typed")

    scripts = {
        entry.name: entry.value
        for entry in installed.entry_points
        if entry.group == "console_scripts"
    }
    missing_or_changed = {
        name: target
        for name, target in EXPECTED_SCRIPTS.items()
        if scripts.get(name) != target
    }
    if missing_or_changed:
        raise SystemExit(f"installed wheel has invalid console scripts: {missing_or_changed}")

    verify_install_profile(args.profile)
    if args.wheel is not None:
        verify_wheel_size(args.wheel)

    print(
        f"Installed wheel verified: {DISTRIBUTION_NAME} {installed.version} "
        f"({args.profile} profile)"
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        choices=sorted(MAX_DISTRIBUTIONS),
        default="base",
        help="Expected isolated installation profile.",
    )
    parser.add_argument(
        "--wheel",
        type=Path,
        help="Built wheel whose compressed size must stay within budget.",
    )
    return parser.parse_args(argv)


def group_dependencies_by_extra(
    requirements: list[str],
) -> dict[str, set[str]]:
    grouped: dict[str, set[str]] = {}
    for requirement in requirements:
        name = requirement_name(requirement)
        extras = requirement_extras(requirement)
        for extra in extras or {"base"}:
            grouped.setdefault(extra, set()).add(name)
    return grouped


def requirement_extras(requirement: str) -> set[str]:
    return set(
        re.findall(
            r"""extra\s*==\s*["']([A-Za-z0-9_.-]+)["']""",
            requirement,
        )
    )


def verify_install_profile(profile: str) -> None:
    expected_feature = None if profile == "base" else profile
    for feature, modules in OPTIONAL_MODULES.items():
        for module in modules:
            available = importlib.util.find_spec(module) is not None
            if available != (feature == expected_feature):
                state = "present" if available else "missing"
                raise SystemExit(
                    f"{profile} profile has invalid optional module "
                    f"{module}: {state}"
                )

    installed_names = {
        requirement_name(str(item.metadata["Name"]))
        for item in distributions()
        if item.metadata["Name"]
    } - BOOTSTRAP_DISTRIBUTIONS
    maximum = MAX_DISTRIBUTIONS[profile]
    if len(installed_names) > maximum:
        raise SystemExit(
            f"{profile} profile exceeds dependency budget: "
            f"{len(installed_names)} installed, maximum {maximum}"
        )


def verify_wheel_size(path: Path) -> None:
    if not path.is_file() or path.suffix != ".whl":
        raise SystemExit(f"wheel path is invalid: {path}")
    size = path.stat().st_size
    if size > MAX_WHEEL_SIZE_BYTES:
        raise SystemExit(
            f"wheel exceeds size budget: {size} bytes, "
            f"maximum {MAX_WHEEL_SIZE_BYTES}"
        )


def requirement_name(requirement: str) -> str:
    match = re.match(r"[A-Za-z0-9_.-]+", requirement)
    if match is None:
        raise SystemExit(f"installed wheel has invalid requirement: {requirement!r}")
    return match.group(0).lower().replace("_", "-")


if __name__ == "__main__":
    main()
