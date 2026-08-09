from __future__ import annotations

from pathlib import Path

import yaml

from scripts.classify_ci_changes import (
    is_documentation_path,
    requires_heavy_checks,
    should_run_heavy_checks,
)


BASE = "1" * 40
HEAD = "2" * 40
ROOT = Path(__file__).resolve().parents[1]


def test_documentation_paths_skip_heavy_checks() -> None:
    paths = (
        "README.md",
        "docs/operations.md",
        "openspec/specs/public-contracts/spec.md",
        "mkdocs.yml",
    )

    assert all(is_documentation_path(path) for path in paths)
    assert requires_heavy_checks(paths) is False
    assert (
        should_run_heavy_checks(
            event="pull_request",
            ref="refs/pull/1/merge",
            base=BASE,
            head=HEAD,
            path_loader=lambda _base, _head: paths,
        )
        is False
    )
    assert (
        should_run_heavy_checks(
            event="push",
            ref="refs/heads/main",
            base=BASE,
            head=HEAD,
            path_loader=lambda _base, _head: paths,
        )
        is False
    )


def test_code_configuration_and_examples_require_heavy_checks() -> None:
    for path in (
        "src/test_data_agent/cli.py",
        "pyproject.toml",
        "uv.lock",
        "Dockerfile",
        "scripts/classify_ci_changes.py",
        "scripts/check_release_tag.py",
        ".github/workflows/ci.yml",
        "examples/negative_cases/dataset_spec.yaml",
    ):
        assert is_documentation_path(path) is False
        assert requires_heavy_checks(("README.md", path)) is True


def test_unknown_or_release_events_fail_closed() -> None:
    assert requires_heavy_checks(()) is True
    assert (
        should_run_heavy_checks(
            event="pull_request",
            ref="refs/pull/1/merge",
            base="not-a-sha",
            head=HEAD,
            path_loader=lambda _base, _head: ("README.md",),
        )
        is True
    )


def test_heavy_workflow_jobs_use_change_scope() -> None:
    expected = {
        "ci.yml": {
            "dependency-minimum",
            "package",
            "package-compatibility",
            "trino-integration",
        },
        "containers.yml": {"validate", "validate-arm64"},
        "security.yml": {"dependency-review", "secrets"},
    }

    for workflow_name, job_names in expected.items():
        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / workflow_name).read_text()
        )
        jobs = workflow["jobs"]
        assert jobs["changes"]["outputs"]["code"] == "${{ steps.scope.outputs.code }}"
        classifier = jobs["changes"]["steps"][1]
        assert classifier["env"]["TRUSTED_SHA"] == (
            "${{ github.event.pull_request.base.sha || github.sha }}"
        )
        assert (
            'git show "${TRUSTED_SHA}:scripts/classify_ci_changes.py"'
            in classifier["run"]
        )
        assert (
            'python3 "${RUNNER_TEMP}/classify_ci_changes.py"'
            in classifier["run"]
        )
        assert "python3 scripts/classify_ci_changes.py" not in classifier["run"]
        assert '>> "${GITHUB_OUTPUT}"' in classifier["run"]
        for job_name in job_names:
            job = jobs[job_name]
            assert job["needs"] == "changes"
            assert "needs.changes.outputs.code == 'true'" in job["if"]

    security = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "security.yml").read_text()
    )["jobs"]
    codeql = security["codeql"]
    assert codeql["needs"] == "changes"
    assert "github.event_name != 'pull_request'" in codeql["if"]
    assert "needs.changes.outputs.code == 'true'" in codeql["if"]

    quality = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    )["jobs"]["quality"]
    assert quality["needs"] == "changes"
    assert "if" not in quality
    assert quality["steps"][0]["if"] == "needs.changes.outputs.code != 'true'"
    assert all(
        step["if"] == "needs.changes.outputs.code == 'true'"
        for step in quality["steps"][1:]
    )

    minimum = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    )["jobs"]["dependency-minimum"]
    profiles = minimum["strategy"]["matrix"]["include"]
    assert {profile["profile"] for profile in profiles} == {
        "base",
        "parquet",
        "mcp",
        "trino",
        "openai",
    }
    assert minimum["steps"][1]["with"]["python-version"] == "3.11"
    assert "matrix.constraint-file" in minimum["steps"][3]["run"]
    contracts = {
        profile["profile"]: profile["test-paths"]
        for profile in profiles
    }
    assert "test_io_workflows.py" in contracts["base"]
    assert "test_business_rules.py" in contracts["base"]
    assert "test_io_commands.py" in contracts["parquet"]
    assert "test_mcp_generator_transport.py" in contracts["mcp"]
    assert "test_mcp_trino_transport.py" in contracts["mcp"]
    assert "test_mcp_trino_server.py" in contracts["trino"]
    assert "test_openai_provider.py" in contracts["openai"]
    mcp_profile = next(profile for profile in profiles if profile["profile"] == "mcp")
    assert mcp_profile["constraint-file"] == "dependency-minimum-mcp.txt"
    assert "--all-extras" in quality["steps"][4]["run"]

    documentation = (
        ROOT / ".github" / "workflows" / "docs.yml"
    ).read_text()
    assert "mkdocs build --strict" in documentation
    assert "Classify changes" not in documentation
    assert (
        should_run_heavy_checks(
            event="push",
            ref="refs/tags/v1.0.0",
            base=BASE,
            head=HEAD,
            path_loader=lambda _base, _head: ("README.md",),
        )
        is True
    )
    assert (
        should_run_heavy_checks(
            event="schedule",
            ref="refs/heads/main",
            base="",
            head="",
        )
        is True
    )
