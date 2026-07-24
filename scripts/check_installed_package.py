"""Verify the installed distribution rather than the source checkout."""

from __future__ import annotations

from importlib.metadata import distribution
from importlib.resources import files

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
}


def main() -> None:
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

    print(f"Installed wheel verified: {DISTRIBUTION_NAME} {installed.version}")


if __name__ == "__main__":
    main()
