from __future__ import annotations

import json
import re
import shutil
import tomllib
from pathlib import Path
from urllib.parse import unquote

import pytest

from test_data_agent.cli import main
from test_data_agent.mcp_generator_server import (
    generate_dataset as generate_dataset_mcp,
)


ROOT = Path(__file__).parent.parent
PROJECT_VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
    "version"
]
LOCAL_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REQUIRED_DOCS = {
    "index.md",
    "getting-started/installation.md",
    "getting-started/first-csv.md",
    "getting-started/related-tables.md",
    "getting-started/review-output.md",
    "how-to/business-rules.md",
    "how-to/gigachat.md",
    "how-to/mcp.md",
    "how-to/reference-agent.md",
    "concepts/safety-model.md",
    "concepts/dataset-spec-compatibility.md",
    "concepts/profiles-and-specs.md",
    "concepts/relational-synthesis-contract.md",
    "reference/application-boundaries.md",
    "reference/cli.md",
    "reference/compatibility.md",
    "reference/dependency-compatibility.md",
    "reference/stability.md",
    "reference/support-policy.md",
    "reference/configuration.md",
    "operations/troubleshooting.md",
    "operations/resource-budgets.md",
    "operations/audit-logging.md",
    "operations/containers.md",
    "operations/migrating-to-0.6.md",
    "changelog-policy.md",
    "release-evidence-1.0.0rc1.md",
    "release-evidence-1.0.0rc2.md",
    "release-evidence-1.0.0rc4.md",
    "release-evidence-1.0.0rc5.md",
    "release-evidence-1.0.0rc6.md",
    "release-evidence-1.0.0.md",
    "rc6-acceptance-checklist.md",
    "security-review-2026-08-01-rc2.md",
    "unreleased-inventory-1.0.0rc1.md",
}
CLI_COMMANDS = {
    "demo",
    "doctor",
    "audit-verify",
    "profile-csv",
    "profile-example",
    "infer-spec",
    "generate-from-csv",
    "generate-from-example",
    "generate",
    "validate",
    "agent-plan",
    "agent-review",
    "agent-approve",
}


def test_readme_is_a_focused_entrypoint() -> None:
    readme = (ROOT / "README.md").read_text()

    assert len(readme.splitlines()) <= 140
    assert (
        f'python3 -m pip install "agent-paranoid-android=={PROJECT_VERSION}"'
        in readme
    )
    assert f'"agent-paranoid-android[mcp,trino]=={PROJECT_VERSION}"' in readme
    assert "--pre" not in readme
    assert "test-data-agent doctor" in readme
    assert "test-data-agent demo --output out/demo" in readme
    assert "source rows copied: no" in readme
    assert "statistical anonymity" in readme
    assert "cross-environment byte identity" in readme
    assert "relationship or business-rule evidence" in readme
    assert "https://wa-pis.github.io/agent-paranoid-android/" in readme
    assert "## Choose A Guide" in readme
    assert "## Release Checklist" not in readme
    assert "## Legacy GenerationSpec Compatibility" not in readme


def test_active_release_surfaces_match_project_version() -> None:
    active_surfaces = (
        ROOT / "README.md",
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "getting-started" / "installation.md",
        ROOT / "docs" / "release.md",
        ROOT / "pyproject.toml",
        ROOT / "src" / "test_data_agent" / "version.py",
        ROOT / "uv.lock",
    )

    for path in active_surfaces:
        content = path.read_text()
        assert "1.0.0rc5" not in content, path
        assert re.search(
            rf"(?<![0-9A-Za-z]){re.escape(PROJECT_VERSION)}(?![0-9A-Za-z])",
            content,
        ), path


def test_changelog_policy_defines_user_facing_categories_and_guidance() -> None:
    policy = (ROOT / "docs" / "changelog-policy.md").read_text()
    contributing = (ROOT / "CONTRIBUTING.md").read_text()
    release = (ROOT / "docs" / "release.md").read_text()

    for category in (
        "`Added`",
        "`Changed`",
        "`Fixed`",
        "`Security`",
        "`Deprecated`",
        "`Removed`",
        "`Migration`",
    ):
        assert category in policy
    for classification in (
        "user impact",
        "security impact",
        "migration impact",
        "internal evidence",
    ):
        assert classification in policy
    assert "docs/changelog-policy.md" in contributing
    assert "changelog-policy.md" in release


def test_rc_changelog_cleanup_preserves_inventory_evidence() -> None:
    inventory = (ROOT / "docs" / "unreleased-inventory-1.0.0rc1.md").read_text()
    evidence = (ROOT / "docs" / "release-evidence-1.0.0rc1.md").read_text()
    changelog = (ROOT / "CHANGELOG.md").read_text()
    changelog = changelog.split("## [1.0.0rc1]", 1)[1]
    changelog = changelog.split("## [0.12.0]", 1)[0]

    assert "89 top-level bullets" in inventory
    assert sum(line.startswith("- ") for line in changelog.splitlines()) == 44
    assert sum(line.startswith("- ") for line in evidence.splitlines()) == 44
    assert "**37**" in inventory
    assert "**9**" in inventory
    assert "**0**" in inventory
    assert "**43**" in inventory


def test_rc2_public_evidence_records_immutable_release() -> None:
    evidence = (ROOT / "docs" / "release-evidence-1.0.0rc2.md").read_text()

    for expected in (
        "e5030b6ae3a06885296d530a4a99f86b760118dd",
        "actions/runs/30689390871",
        "actions/runs/30690800129",
        "63e7e3fe9abeb82b968314068c6180e5a3a64a6f",
        "Public agent approval and audit verification",
        "8982b0fe05dc380ac948c1b3d37eda1bd5f2211a0299549be0b77952847c9297",
        "sha256:7f2b93ce9570e2dc702d34bc098b0756ee64b13588f4eb73ede950694d5de73b",
        "sha256:5fa30138b86fc4d9ce9eb80742ca4e9652da6507ea523508ac5fe7f0a9fa3d02",
        "sha256:d53df07ea4bab935ec95592f9aa0e1f64e0a84825cf3241a62ef1d393060574c",
    ):
        assert expected in evidence


def test_rc5_public_evidence_records_immutable_release() -> None:
    evidence = (ROOT / "docs" / "release-evidence-1.0.0rc5.md").read_text()

    for expected in (
        "9e6e55fa6eeceab925e4432dcbb147de9c88f201",
        "actions/runs/31274057391",
        "actions/runs/31274142268",
        "actions/runs/31274057394",
        "actions/runs/31274217410",
        "f4f04d23b70f9d9d7997f5f4ecfdac1207007f07ff30ec7f1e9155c4be841cbc",
        "sha256:3ff31a229a7b0e0ecbd125e667a21346e9d1f0256c8d2f693439e04d170c46ac",
        "sha256:0cdeb0f3ab68ec488898d8cffc8999d2cebfaadfb57d3e8f7f68a60a0c494989",
        "sha256:3c46fe8168fafb40d9142cde8e5f39350c890b2722ae40f297528202659d60c6",
    ):
        assert expected in evidence


def test_rc6_public_evidence_records_immutable_release() -> None:
    evidence = (ROOT / "docs" / "release-evidence-1.0.0rc6.md").read_text()

    for expected in (
        "2b65515313281aaeb180bb95328785ef46be0202",
        "issues/397",
        "issues/398",
        "actions/runs/31526175512",
        "actions/runs/31526175468",
        "actions/runs/31526347718",
        "actions/runs/31526588778",
        "2346ed729b2e5594d204beb615e8ae3d94d13bf5ecc7625af7e6fca01826f830",
        "sha256:a6a2741ba933242d8fda9f6ceef798b669506a016a6f0660826425f643928c2e",
        "sha256:bb8f4d944d837e54aecc3ff38193fe1aededfe7a52da860765acd44b5d6152d0",
        "sha256:94e95a986d79d2af634676646b817f436066883dea706eb1f38dd7ae63ff8bd9",
        "AI-assisted independent review",
    ):
        assert expected in evidence


def test_stable_public_evidence_records_immutable_release() -> None:
    evidence = (ROOT / "docs" / "release-evidence-1.0.0.md").read_text()

    for expected in (
        "eb4ef2a5d111ef31390f0a204068369e3f934a3b",
        "2b65515313281aaeb180bb95328785ef46be0202",
        "issues/401",
        "actions/runs/31535172632",
        "actions/runs/31535172612",
        "actions/runs/31535349523",
        "actions/runs/31535631328",
        "88644f9f266b9e146cb8d813737d4799b970ab654c7bcd3b1b0a3ad40f76ab6a",
        "sha256:1635b23a0bfa44e3e0becb5aac33bc76d2cabd08bcecb6cfe34c457fda6692da",
        "sha256:6289583e594c73cc7fd8a4567a46443fbf12d3db36714a60414c1e6fd5c7fab7",
        "sha256:f4464d836f3e531a0cc780de288f36af1772338e1279203d452e2997a3acedc7",
        "AI-assisted independent review",
    ):
        assert expected in evidence


def test_rc2_security_review_records_exact_disposition() -> None:
    review = (ROOT / "docs" / "security-review-2026-08-01-rc2.md").read_text()

    for expected in (
        "e5030b6ae3a06885296d530a4a99f86b760118dd",
        "actions/runs/30684756448",
        "actions/runs/30684756459",
        "actions/runs/30684853166",
        "actions/runs/30689390871",
        "Critical | 0",
        "High | 0",
        "Medium | 1",
        "repository maintainer (`@wa-pis`)",
        "2026-11-01",
    ):
        assert expected in review


def test_completed_openspec_changes_are_archived_and_baselined() -> None:
    changes = ROOT / "openspec" / "changes"
    archive = (
        changes / "archive" / "2026-08-01-1-0-0-rc1-security-hardening"
    )
    tasks = (archive / "tasks.md").read_text()

    assert "- [ ]" not in tasks
    active = {
        path.name
        for path in changes.iterdir()
        if path.is_dir() and path.name != "archive"
    }
    assert active == {
        "1-2-0-mcp-malformed-log-redaction",
        "1-2-0-portable-release-provenance",
        "_template",
    }

    archived = changes / "archive"
    completed = (
        "1-0-0-rc4-privacy-invocation-hardening",
        "1-0-0-rc5-public-release-invocation-hardening",
        "1-0-0-rc6-final-release-candidate",
        "1-1-0-cli-ux",
        "1-2-0-provider-response-preparse-bound",
        "gigachat-advisor-provider",
    )
    for change_id in completed:
        archived_tasks = (
            archived / f"2026-08-14-{change_id}" / "tasks.md"
        ).read_text()
        assert "- [ ]" not in archived_tasks

    json_depth_tasks = (
        archived
        / "2026-08-15-1-2-0-json-depth-preparse-bound"
        / "tasks.md"
    ).read_text()
    assert "- [ ]" not in json_depth_tasks

    mcp_argument_tasks = (
        archived
        / "2026-08-15-1-2-0-mcp-argument-redaction"
        / "tasks.md"
    ).read_text()
    assert "- [ ]" not in mcp_argument_tasks

    superseded = archived / "2026-08-14-1-0-0-postgres-multi-source"
    assert "Status: superseded" in (superseded / "proposal.md").read_text()
    assert "not an active backlog" in (superseded / "tasks.md").read_text()

    provenance_tasks = (
        changes / "1-2-0-portable-release-provenance" / "tasks.md"
    ).read_text()
    assert "- [x] Merge through a normal pull request" in provenance_tasks
    assert "- [ ] Exercise the contract on the next release candidate" in (
        provenance_tasks
    )

    requirements = {
        "synthetic-generation": (
            "Generation Entry Points Enforce Spec Safety",
            "Reproducibility Claims Are Bounded And Evidenced",
            "Approved Relational Semantics Are Preserved",
            "SQL Export Contains Synthetic Inserts Only",
        ),
        "dataset-validation": (
            "Validation Settings Have Executable Semantics",
            "Privacy Assurance Claims Are Bounded",
        ),
        "safe-mcp-workflow": (
            "External Trino Execution Is Read-Only And Validated",
            "Rejected MCP Arguments Are Not Reflected",
        ),
        "agent-orchestration": (
            "Relationship Discovery Is Reviewable And Deterministic",
        ),
    }
    for capability, headings in requirements.items():
        spec = (ROOT / "openspec" / "specs" / capability / "spec.md").read_text()
        for heading in headings:
            assert f"### Requirement: {heading}" in spec


def test_application_boundaries_refactor_is_archived_for_stable_1_0() -> None:
    roadmap = (ROOT / "docs" / "roadmap.md").read_text()
    archive = (
        ROOT
        / "openspec"
        / "changes"
        / "archive"
        / "2026-08-01-application-boundaries-refactor"
    )
    proposal = (archive / "proposal.md").read_text()
    tasks = (archive / "tasks.md").read_text()
    stable_scope = roadmap.split("### 1.0.0: Stable Release", 1)[1].split(
        "### Post-1.0", 1
    )[0]
    post_1_0_scope = roadmap.split("### Post-1.0", 1)[1]

    assert "Status: required before the stable 1.0" in proposal
    assert "2026-08-01-application-boundaries-refactor/proposal.md" in stable_scope
    assert "promote the verified RC6 baseline" in stable_scope
    assert "application-boundaries-refactor/proposal.md" not in post_1_0_scope
    assert "- [ ]" not in tasks


def test_application_boundary_inventory_matches_frozen_contracts() -> None:
    inventory = (
        ROOT / "docs" / "reference" / "application-boundaries.md"
    ).read_text()
    contracts = ROOT / "tests" / "fixtures" / "contracts"
    python_api = json.loads((contracts / "public-python-api.json").read_text())
    cli = json.loads((contracts / "cli-parser-surface.json").read_text())
    generator_tools = json.loads(
        (contracts / "mcp-generator-tools.json").read_text()
    )
    trino_tools = json.loads((contracts / "mcp-trino-tools.json").read_text())
    catalog = json.loads((contracts / "contract-catalog.json").read_text())

    names = {
        *python_api["exports"],
        *cli["commands"],
        *cli["aliases"],
        *(tool["name"] for tool in generator_tools),
        *(tool["name"] for tool in trino_tools),
        *catalog["contracts"],
    }
    for name in names:
        assert f"`{name}`" in inventory

    for artifact in (
        "agent_request.json",
        "agent_plan.json",
        "profile.json",
        "dataset_spec.yaml",
        "advisor_review.json",
        "approval_receipt.json",
        "agent_result.json",
        "agent_completion.json",
        "generation_manifest.json",
        "validation_report.json",
        "business_validation_report.json",
    ):
        assert f"`{artifact}`" in inventory

    assert "application services -> policy/core -> typed ports" in inventory
    assert "transport factory" in inventory

    tasks = (
        ROOT
        / "openspec"
        / "changes"
        / "archive"
        / "2026-08-01-application-boundaries-refactor"
        / "tasks.md"
    ).read_text()
    assert "- [x] Inventory public imports" in tasks


def test_application_boundary_migration_notes_cover_extracted_owners() -> None:
    inventory = (
        ROOT / "docs" / "reference" / "application-boundaries.md"
    ).read_text()

    assert "No user migration is required" in inventory
    for owner in (
        "agent_contracts.py",
        "agent_planning.py",
        "agent_review.py",
        "agent_approval.py",
        "agent_recovery.py",
        "agent_advising.py",
        "agent_status.py",
        "workspace_store.py",
        "cli_application.py",
        "cli_agent.py",
        "cli_commands.py",
        "cli_dependencies.py",
        "cli_doctor.py",
        "trino_config.py",
        "trino_sql_policy.py",
        "trino_query_builders.py",
        "trino_client.py",
        "trino_profiling.py",
        "trino_masking.py",
    ):
        assert f"`{owner}`" in inventory

    assert "normal compatibility window" in inventory


def test_unreleased_changelog_headings_follow_policy_order() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text()
    unreleased = changelog.split("## Unreleased", 1)[1].split("\n## [", 1)[0]
    headings = re.findall(r"^### (.+)$", unreleased, flags=re.MULTILINE)
    allowed = [
        "Added",
        "Changed",
        "Fixed",
        "Security",
        "Deprecated",
        "Removed",
        "Migration",
    ]

    assert len(headings) == len(set(headings))
    assert all(heading in allowed for heading in headings)
    assert headings == sorted(headings, key=allowed.index)


def test_public_governance_files_define_owners_and_safe_support() -> None:
    required_files = {
        "CODE_OF_CONDUCT.md": "onepis2word@gmail.com",
        "SUPPORT.md": "SECURITY.md",
        "GOVERNANCE.md": "single-maintainer",
        ".github/CODEOWNERS": "* @wa-pis",
    }

    for relative_path, required_text in required_files.items():
        content = (ROOT / relative_path).read_text()
        assert required_text in content, relative_path

    readme = (ROOT / "README.md").read_text()
    for relative_path in required_files:
        if not relative_path.startswith(".github/"):
            assert f"]({relative_path})" in readme


def test_relational_synthesis_contract_bounds_preservation_claims() -> None:
    contract = (
        ROOT / "docs" / "concepts" / "relational-synthesis-contract.md"
    ).read_text()

    for term in (
        "Foreign-key graph",
        "Distribution shape",
        "Temporal dependencies",
        "Business invariants",
        "Source key values",
        "statistical privacy guarantee",
        "proposal has no generation authority",
        "deterministic validation",
    ):
        assert term in contract


def test_required_user_documentation_exists_and_is_navigable() -> None:
    config = (ROOT / "mkdocs.yml").read_text()

    assert "site_url: https://wa-pis.github.io/agent-paranoid-android/" in config
    for relative_path in REQUIRED_DOCS:
        assert (ROOT / "docs" / relative_path).is_file(), relative_path
        assert relative_path in config, relative_path
    assert (ROOT / "examples" / "orders_rules.yaml").is_file()
    assert (ROOT / "examples" / "reference_agent.py").is_file()


def test_installation_documents_dependency_budgets() -> None:
    installation = (
        ROOT / "docs" / "getting-started" / "installation.md"
    ).read_text()

    assert "Maximum installed distributions" in installation
    for maximum in (10, 11, 20, 25, 35):
        assert f"| {maximum} |" in installation
    assert 'pip install "agent-paranoid-android[all]"' not in installation
    assert f'"agent-paranoid-android=={PROJECT_VERSION}"' in installation
    for extra in ("parquet", "mcp", "mcp,trino", "openai"):
        assert (
            f'"agent-paranoid-android[{extra}]=={PROJECT_VERSION}"'
            in installation
        )
    assert "The stable release is" in installation
    assert "not the recommended user installation" in installation


def test_documentation_workflow_deploys_only_from_main() -> None:
    workflow = (ROOT / ".github" / "workflows" / "docs.yml").read_text()

    main_only = (
        "if: github.ref == 'refs/heads/main' && "
        "github.event_name != 'pull_request'"
    )
    assert workflow.count(main_only) == 2
    assert "actions/upload-pages-artifact@" in workflow
    assert "actions/deploy-pages@" in workflow
    assert "name: github-pages" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "permissions: {}" in workflow
    assert "needs: deploy" in workflow
    assert "Agent Paranoid Android" in workflow
    assert "group: docs-build-${{ github.ref }}" in workflow
    assert "group: github-pages" in workflow
    assert "cancel-in-progress: false" in workflow
    action_lines = [
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith("uses: actions/")
    ]
    assert action_lines
    for line in action_lines:
        assert re.fullmatch(
            r"uses: actions/[a-z0-9-]+@[0-9a-f]{40} # v[0-9.]+",
            line,
        )


def test_cli_reference_covers_every_public_command() -> None:
    reference = (ROOT / "docs" / "reference" / "cli.md").read_text()

    for command in CLI_COMMANDS:
        assert f"`{command}`" in reference


def test_ai_guidance_matches_safe_public_contract() -> None:
    integration = (ROOT / "docs" / "ai_integration.md").read_text()
    prompts = "\n".join(
        path.read_text()
        for path in sorted((ROOT / "prompts").glob("*.md"))
    )

    assert 'pip install -e ".[all,dev]"' not in integration
    assert 'agent-paranoid-android[mcp,trino]' in integration
    assert "Use The GigaChat Advisor" in integration
    assert "`plan_trino_dataset`" in integration
    assert "`inspect_dataset_plan`" in integration
    assert "`approve_dataset_plan`" in integration
    assert "{csv/json/parquet/sql}" not in prompts
    assert "explicit human approval" in prompts
    assert "do not return source or generated rows in chat" in prompts.lower()
    assert "untrusted data" in prompts


def test_trino_mcp_docs_define_default_privacy_boundary() -> None:
    guide = (ROOT / "docs" / "how-to" / "mcp.md").read_text()
    integration = (ROOT / "docs" / "ai_integration.md").read_text()
    boundaries = (
        ROOT / "docs" / "reference" / "application-boundaries.md"
    ).read_text()
    default_tools = json.loads(
        (
            ROOT
            / "tests"
            / "fixtures"
            / "contracts"
            / "mcp-trino-tools.json"
        ).read_text()
    )

    for tool in default_tools:
        assert f"`{tool['name']}`" in guide
    assert "`run_safe_select`" not in {
        f"`{tool['name']}`" for tool in default_tools
    }
    assert "source-literal-free" in guide
    assert "TRINO_ENABLE_SAFE_SELECT=true" in guide
    assert "row-shaped result masks every string" in guide
    for public_doc in (guide, integration, boundaries):
        assert "sample_rows_masked" not in public_doc
    assert "does not\nmake returned rows source-free, anonymous" in guide


def test_public_mcp_docs_reject_stale_or_broad_privacy_claims() -> None:
    markdown_paths = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
    forbidden_claims = (
        "all mcp responses are source-free",
        "all mcp responses are privacy-safe",
        "every mcp response is source-free",
        "every mcp response is privacy-safe",
        "run_safe_select is source-free",
        "run_safe_select is pii-free",
        "run_safe_select is anonymous",
        "run_safe_select is privacy-safe",
    )

    for markdown_path in markdown_paths:
        if markdown_path.name == "roadmap.md":
            continue
        content = markdown_path.read_text()
        normalized = " ".join(content.lower().replace("`", "").split())
        assert "sample_rows_masked" not in normalized, markdown_path
        if "run_safe_select" not in normalized:
            continue
        assert "default aggregate-only" in normalized, markdown_path
        assert "explicit opt-in" in normalized, markdown_path
        for claim in forbidden_claims:
            assert claim not in normalized, f"{markdown_path}: {claim}"


def test_local_markdown_links_resolve() -> None:
    markdown_files = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
    failures: list[str] = []

    for markdown_path in markdown_files:
        for raw_target in LOCAL_LINK.findall(markdown_path.read_text()):
            target = raw_target.strip().strip("<>")
            if (
                not target
                or target.startswith(("#", "http://", "https://", "mailto:"))
            ):
                continue
            path_part = unquote(target.split("#", maxsplit=1)[0])
            resolved = (markdown_path.parent / path_part).resolve()
            if not resolved.exists():
                failures.append(
                    f"{markdown_path.relative_to(ROOT)} -> {raw_target}"
                )

    assert not failures, "\n".join(failures)


def test_public_stability_table_covers_contract_surfaces() -> None:
    stability = (ROOT / "docs" / "reference" / "stability.md").read_text()

    for surface in (
        "test_data_agent.__all__",
        "test-data-agent",
        "Generator MCP",
        "Trino MCP",
        "DatasetSpec",
        "Advisor",
        "Generated bundle",
        "Provider adapters",
    ):
        assert surface in stability
    for fixture in (
        "public-python-api.json",
        "cli-parser-surface.json",
        "mcp-generator-tools.json",
        "mcp-trino-tools.json",
        "dataset-spec.json",
        "advisor-exchange.json",
        "artifact-layout.json",
    ):
        assert fixture in stability
    assert "additive change" in stability
    assert "breaking change" in stability


def test_runtime_support_policy_covers_release_boundaries() -> None:
    support = (ROOT / "docs" / "reference" / "support-policy.md").read_text()

    for version in ("3.11", "3.12", "3.13", "3.14"):
        assert version in support
    for extra in ("parquet", "mcp", "trino", "openai", "gigachat", "all"):
        assert f"`{extra}`" in support
    assert "breaking packaging change" in support
    assert "provider-neutral" in support
    assert "safe metadata only" in support
    assert "local fakes" in support


def test_gigachat_documentation_matches_provider_boundary() -> None:
    guide = (ROOT / "docs" / "how-to" / "gigachat.md").read_text()
    configuration = (
        ROOT / "docs" / "reference" / "configuration.md"
    ).read_text()
    cli = (ROOT / "docs" / "reference" / "cli.md").read_text()
    installation = (
        ROOT / "docs" / "getting-started" / "installation.md"
    ).read_text()

    for expected in (
        "official `gigachat` Python SDK directly",
        "GIGACHAT_CREDENTIALS",
        "GIGACHAT_ACCESS_TOKEN",
        "GIGACHAT_API_PERS",
        "GIGACHAT_API_B2B",
        "GIGACHAT_API_CORP",
        "GIGACHAT_CA_BUNDLE_FILE",
        "TLS verification is mandatory",
        "locally preserved category values",
        "agent-approve",
        "provider quota",
    ):
        assert expected in guide
    assert "--provider gigachat" in cli
    assert "default remains\n`openai`" in cli
    assert f'agent-paranoid-android[gigachat]=={PROJECT_VERSION}' in guide
    assert f'agent-paranoid-android[gigachat]=={PROJECT_VERSION}' in installation
    assert "TLS verification cannot be disabled" in configuration


def test_artifact_durability_contract_matches_implementation() -> None:
    stability = (ROOT / "docs" / "reference" / "stability.md").read_text()
    operations = (
        ROOT / "docs" / "operations" / "resource-budgets.md"
    ).read_text()
    normalized_operations = " ".join(operations.split())
    persistence_sources = (
        ROOT / "src" / "test_data_agent" / "io" / "artifacts.py",
        ROOT / "src" / "test_data_agent" / "io" / "workflows.py",
        ROOT / "src" / "test_data_agent" / "workspace_store.py",
    )

    for boundary in (
        "Atomic visibility",
        "Process-interruption recovery",
        "Crash or power-loss durability",
    ):
        assert boundary in stability
    assert "not one filesystem transaction" in stability
    assert "deferred until after 1.0" in stability
    assert "not release-blocking for RC4 or stable 1.0" in normalized_operations
    assert "repository maintainer owns the follow-up" in normalized_operations
    assert "before promising crash/power-loss durability" in normalized_operations
    for source in persistence_sources:
        assert "fsync" not in source.read_text()


def test_stable_promotion_contract_is_metadata_only() -> None:
    release = (ROOT / "docs" / "release.md").read_text()
    normalized_release = " ".join(release.split())
    design = (
        ROOT
        / "openspec"
        / "changes"
        / "archive"
        / "2026-08-14-1-0-0-rc4-privacy-invocation-hardening"
        / "design.md"
    ).read_text()
    normalized_design = " ".join(design.split())
    tasks = (
        ROOT
        / "openspec"
        / "changes"
        / "archive"
        / "2026-08-14-1-0-0-rc4-privacy-invocation-hardening"
        / "tasks.md"
    ).read_text()

    assert "## RC6 To Stable Promotion" in release
    assert "git diff --name-status v1.1.0rc2 HEAD" in release
    for path in (
        "pyproject.toml",
        "src/test_data_agent/version.py",
        "uv.lock",
        "CHANGELOG.md",
    ):
        assert f"`{path}`" in release
    assert "newly numbered release candidate" in normalized_release
    assert "All other changes require a new release candidate" in release
    assert "generated release metadata" in release
    assert "every final release gate" in normalized_release
    assert "macOS-derived sdist digest" in normalized_release
    assert "## Stable Promotion Contract" in design
    assert "remain byte-for-byte at the accepted RC4 state" in normalized_design
    assert "- [x] Define stable promotion" in tasks


def test_rc4_remaining_findings_have_dispositions() -> None:
    change = (
        ROOT
        / "openspec"
        / "changes"
        / "archive"
        / "2026-08-14-1-0-0-rc4-privacy-invocation-hardening"
    )
    design = (change / "design.md").read_text()
    tasks = (change / "tasks.md").read_text()
    finding_register = design.split("## Remaining Finding Register", 1)[1].split(
        "## Stable Promotion Contract", 1
    )[0]
    normalized_register = " ".join(finding_register.split())
    finding_rows = [
        line for line in finding_register.splitlines() if line.startswith("| RC4-F")
    ]

    assert len(finding_rows) == 3
    for finding_id, row in zip(("RC4-F1", "RC4-F2", "RC4-F3"), finding_rows):
        assert finding_id in row
        assert "@wa-pis" in row
        assert "2026-11-01" in row
    assert "No unresolved P0 or release-blocking P1" in finding_register
    assert "pending release evidence, not findings" in normalized_register
    assert "remain release-blocking tasks" in normalized_register
    assert "- [x] Confirm every remaining finding" in tasks


def test_compatibility_inventory_covers_retained_surfaces() -> None:
    compatibility = (
        ROOT / "docs" / "reference" / "compatibility.md"
    ).read_text()

    for alias in (
        "profile-csv-folder",
        "generate-from-csv-folder",
    ):
        assert alias in compatibility
    for wrapper in (
        "test_data_agent.business_rules",
        "test_data_agent.business_validator",
        "test_data_agent.rules_engine",
        "test_data_agent.scenario",
    ):
        assert wrapper in compatibility
    assert 'summary["field"]' in compatibility
    assert "GenerationSpec" in compatibility
    assert "one feature release and 90 days" in compatibility
    assert "before `2.0`" in compatibility


def test_dependency_compatibility_defines_semantic_profiles() -> None:
    compatibility = (
        ROOT / "docs" / "reference" / "dependency-compatibility.md"
    ).read_text()

    for dependency in (
        "Faker",
        "Pydantic",
        "PyYAML",
        "PyArrow",
        "MCP",
        "sqlglot",
        "Trino client",
        "OpenAI",
    ):
        assert dependency in compatibility
    for profile in (
        "base-minimum",
        "parquet-minimum",
        "mcp-minimum",
        "trino-minimum",
        "openai-minimum",
        "latest-all",
    ):
        assert f"`{profile}`" in compatibility
    assert "Byte identity" in compatibility
    assert "No new upper major bound" in compatibility
    assert "Same environment" in compatibility
    assert "Same package version" in compatibility
    assert "Cross-version" in compatibility
    assert "byte_identical_across_versions: false" in compatibility
    assert "Retain `<2.0.0`" in compatibility
    assert "Retain `<3.0.0`" in compatibility
    assert "Add no upper bound" in compatibility
    assert "user-facing changelog entry" in compatibility

    minimum_constraints = (
        ROOT / ".github" / "constraints" / "dependency-minimum.txt"
    ).read_text()
    for requirement in (
        "faker==25.0.0",
        "pydantic==2.7.0",
        "PyYAML==6.0.0",
        "pyarrow==15.0.0",
        "mcp==1.0.0",
        "sqlglot==30.0.0",
        "trino==0.330.0",
        "openai==2.46.0",
    ):
        assert requirement in minimum_constraints

    mcp_constraints = (
        ROOT / ".github" / "constraints" / "dependency-minimum-mcp.txt"
    ).read_text()
    assert "mcp==1.0.0" in mcp_constraints
    assert "pydantic==2.8.0" in mcp_constraints


def test_documented_business_rules_workflow_succeeds(tmp_path: Path) -> None:
    profile = tmp_path / "profile.json"
    spec = tmp_path / "dataset_spec.yaml"
    generated = tmp_path / "generated"

    assert main(
        [
            "profile-example",
            str(ROOT / "tests" / "fixtures" / "example_dataset"),
            "--output",
            str(profile),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    ) == 0
    assert main(
        [
            "infer-spec",
            str(profile),
            "--count",
            "25",
            "--output",
            str(spec),
        ]
    ) == 0
    assert main(
        [
            "generate",
            str(spec),
            "--seed",
            "12345",
            "--format",
            "csv",
            "--business-rules",
            str(ROOT / "examples" / "orders_rules.yaml"),
            "--output",
            str(generated),
        ]
    ) == 0

    manifest = json.loads((generated / "generation_manifest.json").read_text())
    business_report = json.loads(
        (generated / "business_validation_report.json").read_text()
    )
    assert manifest["synthetic"] is True
    assert manifest["source_rows_copied"] is False
    assert manifest["validation_valid"] is True
    assert manifest["business_validation"]["valid"] is True
    assert business_report["valid"] is True


def test_documented_negative_cli_and_mcp_examples_match(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    example = workspace / "negative_cases"
    shutil.copytree(ROOT / "examples" / "negative_cases", example)
    cli_output = workspace / "negative-cli"

    assert main(
        [
            "generate",
            str(example / "dataset_spec.yaml"),
            "--seed",
            "1300",
            "--mode",
            "mixed",
            "--invalid-ratio",
            "0.5",
            "--format",
            "json",
            "--business-rules",
            str(example / "business_rules.yaml"),
            "--output",
            str(cli_output),
        ]
    ) == 0

    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(workspace))
    mcp_result = generate_dataset_mcp(
        "negative_cases/dataset_spec.yaml",
        "negative-mcp",
        output_format="json",
        seed=1300,
        business_rules_path="negative_cases/business_rules.yaml",
    )
    mcp_output = workspace / "negative-mcp"

    assert (cli_output / "orders.json").read_bytes() == (
        mcp_output / "orders.json"
    ).read_bytes()
    cli_report = json.loads(
        (cli_output / "business_validation_report.json").read_text()
    )
    mcp_report = json.loads(
        (mcp_output / "business_validation_report.json").read_text()
    )
    assert cli_report == mcp_report
    assert cli_report["expectations_met"] is True
    assert cli_report["expected_violation_count"] == 4
    assert cli_report["observed_violation_count"] == 4
    assert mcp_result["business_validation"]["unexpected_violation_count"] == 0
