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
        "ci.yml": {"package", "package-compatibility", "trino-integration"},
        "containers.yml": {"validate", "validate-arm64"},
        "security.yml": {"dependency-review", "codeql", "secrets"},
    }

    for workflow_name, job_names in expected.items():
        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / workflow_name).read_text()
        )
        jobs = workflow["jobs"]
        assert jobs["changes"]["outputs"]["code"] == "${{ steps.scope.outputs.code }}"
        classifier = jobs["changes"]["steps"][1]
        assert '>> "${GITHUB_OUTPUT}"' in classifier["run"]
        for job_name in job_names:
            job = jobs[job_name]
            assert job["needs"] == "changes"
            assert "needs.changes.outputs.code == 'true'" in job["if"]

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
