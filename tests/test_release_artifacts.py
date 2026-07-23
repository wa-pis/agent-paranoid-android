import json
import re
import stat
import tomllib
from pathlib import Path

import pytest

from scripts.check_release_tag import check_release_tag
from test_data_agent.core.dataset import DATASET_SPEC_SCHEMA_VERSION, DatasetSpec


ROOT = Path(__file__).parent.parent


def test_dataset_spec_schema_matches_pydantic_contract() -> None:
    schema = json.loads((ROOT / "schemas" / "dataset_spec.schema.json").read_text())
    expected = DatasetSpec.model_json_schema(ref_template="#/$defs/{model}")

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("/schemas/dataset_spec.schema.json")
    assert schema["title"] == "DatasetSpec"
    assert schema["x-schema-version"] == DATASET_SPEC_SCHEMA_VERSION
    assert schema["properties"] == expected["properties"]
    assert schema["$defs"] == expected["$defs"]


def test_project_metadata_uses_public_name_and_stable_cli() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]

    assert metadata["name"] == "agent-paranoid-android"
    assert metadata["description"] == "Safety-first synthetic data generation agent"
    assert metadata["license"] == "MIT"
    assert "License :: OSI Approved :: MIT License" in metadata["classifiers"]
    assert metadata["scripts"]["test-data-agent"] == "test_data_agent.cli:main"


def test_public_release_artifacts_are_present() -> None:
    required_files = [
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "docs/public_release_checklist.md",
        ".github/dependabot.yml",
        ".github/workflows/ci.yml",
        ".github/workflows/release.yml",
        ".github/workflows/security.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        "scripts/check_installed_package.py",
        "src/test_data_agent/py.typed",
        "uv.lock",
    ]

    for relative_path in required_files:
        assert (ROOT / relative_path).is_file(), relative_path


def test_public_docs_disclose_ai_assisted_development() -> None:
    readme = (ROOT / "README.md").read_text()
    contributing = (ROOT / "CONTRIBUTING.md").read_text()

    assert "## AI-Assisted Development" in readme
    assert "## AI-Assisted Contributions" in contributing
    assert "Do not send production data, raw PII, credentials" in contributing


def test_ci_uses_locked_dependencies_and_runs_vulnerability_audit() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()

    assert "uv sync --frozen --extra dev" in workflow
    assert "--extra dev --no-emit-project" in workflow
    assert "python -m pip_audit --require-hashes" in workflow
    assert "python -m mypy" in workflow
    assert "name: Wheel smoke" in workflow
    assert "scripts/check_installed_package.py" in workflow
    assert "test-data-agent doctor --skip-smoke" in workflow
    assert "actions/checkout@v7" not in workflow
    assert "actions/setup-python@v7" not in workflow
    assert "astral-sh/setup-uv@v7" not in workflow


def test_workflow_actions_are_pinned_to_full_commit_shas() -> None:
    action_reference = re.compile(r"^\s*uses:\s*[^@\s]+@([^\s#]+)", re.MULTILINE)
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))

    assert workflows
    for workflow in workflows:
        references = action_reference.findall(workflow.read_text())
        assert references, workflow
        assert all(re.fullmatch(r"[0-9a-f]{40}", reference) for reference in references), workflow


def test_security_workflow_runs_code_and_secret_scans() -> None:
    workflow = (ROOT / ".github" / "workflows" / "security.yml").read_text()

    assert "github/codeql-action/init@" in workflow
    assert "queries: security-extended" in workflow
    assert "gitleaks/gitleaks-action@" in workflow
    assert "actions/dependency-review-action@" in workflow
    assert "fail-on-severity: moderate" in workflow
    assert "fetch-depth: 0" in workflow
    assert "security-events: write" in workflow


def test_release_workflow_builds_sbom_and_attests_packages() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()

    assert 'tags:\n      - "v*.*.*"' in workflow
    assert "scripts/check_release_tag.py" in workflow
    assert "scripts/check_release.sh" in workflow
    assert "uv build --no-build-isolation" in workflow
    assert "scripts/check_installed_package.py" in workflow
    assert "test-data-agent doctor --skip-smoke" in workflow
    assert "--format cyclonedx1.5" in workflow
    assert workflow.count("actions/attest@") == 2
    assert "sbom-path: dist/sbom.cdx.json" in workflow
    assert "softprops/action-gh-release@" in workflow
    assert "files: dist/*" not in workflow
    assert "          path: dist/\n" not in workflow
    assert workflow.count("            dist/SHA256SUMS\n") == 2


def test_release_tag_must_match_package_version() -> None:
    check_release_tag("v0.4.0")

    with pytest.raises(ValueError, match="does not match"):
        check_release_tag("v9.9.9")
    with pytest.raises(ValueError, match="start with"):
        check_release_tag("0.4.0")


def test_release_script_is_executable_and_covers_release_gates() -> None:
    script = ROOT / "scripts" / "check_release.sh"
    text = script.read_text()

    assert script.stat().st_mode & stat.S_IXUSR
    assert "python3 -m ruff check src tests scripts" in text
    assert "python3 -m mypy" in text
    assert "python3 -m compileall -q src tests scripts" in text
    assert "python3 -m pytest --cov=test_data_agent" in text
    assert "scripts/export_dataset_schema.py" in text
    assert "generate-from-example tests/fixtures/example_dataset" in text
    assert 'manifest.get("source_rows_copied") is False' in text
    assert "quickstart smoke failed" in text


def test_openspec_specs_have_requirements_and_scenarios() -> None:
    spec_paths = sorted((ROOT / "openspec" / "specs").glob("*/spec.md"))

    assert spec_paths
    for path in spec_paths:
        text = path.read_text()
        assert "## Purpose" in text
        assert "## Requirements" in text
        assert "### Requirement:" in text
        assert "#### Scenario:" in text


def test_openspec_change_template_is_complete() -> None:
    template = ROOT / "openspec" / "changes" / "_template"

    assert (template / "proposal.md").is_file()
    assert (template / "design.md").is_file()
    assert (template / "tasks.md").is_file()
    assert (template / "specs" / "capability" / "spec.md").is_file()


def test_plantuml_architecture_diagrams_are_present_and_well_formed() -> None:
    required_diagrams = {
        "architecture.puml",
        "architecture_agent_workflow.puml",
        "architecture_safety_boundaries.puml",
    }
    diagram_paths = {path.name: path for path in (ROOT / "docs").glob("*.puml")}

    assert required_diagrams <= diagram_paths.keys()
    for path in diagram_paths.values():
        text = path.read_text()
        assert text.startswith("@startuml")
        assert text.rstrip().endswith("@enduml")
