from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from test_data_agent import container_health
from test_data_agent.container_health import ContainerHealthError


ROOT = Path(__file__).parent.parent


def test_dockerfile_uses_digest_pinned_minimal_targets() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert re.search(
        r"ARG PYTHON_IMAGE=python:3\.12-slim-bookworm@sha256:[0-9a-f]{64}",
        dockerfile,
    )
    assert re.search(
        r"ARG UV_IMAGE=ghcr\.io/astral-sh/uv:0\.11\.23@sha256:[0-9a-f]{64}",
        dockerfile,
    )
    assert "USER 65532:65532" in dockerfile
    assert "FROM runtime-base AS cli" in dockerfile
    assert "FROM runtime-base AS generator-mcp" in dockerfile
    assert "FROM runtime-base AS trino-mcp" in dockerfile
    assert "--extra mcp" in dockerfile
    assert "--extra mcp --extra trino" in dockerfile
    assert "--extra all" not in dockerfile
    assert dockerfile.count("HEALTHCHECK ") == 3
    assert "PATH=/app/.venv/bin" in dockerfile
    assert dockerfile.count("/app/.venv /app/.venv") == 3
    assert "/app/.venv /opt/venv" not in dockerfile


def test_compose_keeps_generator_and_trino_boundaries_separate() -> None:
    config = yaml.safe_load((ROOT / "compose.yaml").read_text())
    services = config["services"]

    assert set(services) == {"cli", "generator-mcp", "trino-mcp"}
    for service in services.values():
        assert service["read_only"] is True
        assert service["cap_drop"] == ["ALL"]
        assert service["security_opt"] == ["no-new-privileges:true"]
        assert service["pids_limit"] == 128
        assert service.get("privileged", False) is False
        assert "ports" not in service

    generator = services["generator-mcp"]
    trino = services["trino-mcp"]
    assert generator["network_mode"] == "none"
    assert "networks" not in generator
    assert {volume["target"] for volume in generator["volumes"]} == {
        "/audit",
        "/workspace",
    }
    assert {volume["target"] for volume in trino["volumes"]} == {"/audit"}
    assert "network_mode" not in trino
    assert trino["networks"] == ["trino-egress"]
    assert "TEST_DATA_AGENT_AUDIT_HMAC_KEY" not in generator["environment"]
    assert (
        generator["environment"]["TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE"]
        == "/run/secrets/generator_audit_hmac_key"
    )
    assert (
        trino["environment"]["TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE"]
        == "/run/secrets/trino_audit_hmac_key"
    )
    assert set(config["secrets"]) == {
        "generator_audit_hmac_key",
        "trino_audit_hmac_key",
    }
    assert generator["volumes"][1]["source"] != trino["volumes"][0]["source"]
    assert "TRINO_ALLOW_UNRESTRICTED" not in trino["environment"]
    assert "TRINO_ALLOW_INSECURE_HTTP" not in trino["environment"]


def test_container_workflow_builds_before_tag_only_publish() -> None:
    workflow = (ROOT / ".github" / "workflows" / "containers.yml").read_text()
    validate_job = workflow.split("\n  validate:\n", maxsplit=1)[1]
    validate_job = validate_job.split("\n  release-gate:\n", maxsplit=1)[0]
    release_gate = workflow.split("\n  release-gate:\n", maxsplit=1)[1]
    release_gate = release_gate.split("\n  publish:\n", maxsplit=1)[0]
    publish_job = workflow.split("\n  publish:\n", maxsplit=1)[1]

    assert 'tags:\n      - "v*.*.*"' in workflow
    assert "packages: write" not in validate_job
    assert "push: false" in validate_job
    assert "scripts/check_release_tag.py" in release_gate
    assert "scripts/check_release.sh" in release_gate
    assert "needs:\n      - validate\n      - release-gate" in publish_job
    assert "startsWith(github.ref, 'refs/tags/')" in publish_job
    assert "platforms: linux/amd64,linux/arm64" in publish_job
    assert "provenance: mode=max" in publish_job
    assert "sbom: true" in publish_job
    assert "actions/attest-build-provenance@" in publish_job
    assert "cosign sign --yes" in publish_job
    assert "cosign verify" in publish_job
    assert "id-token: write" in publish_job
    assert "packages: write" in publish_job
    assert "password: ${{ secrets.GITHUB_TOKEN }}" in publish_job
    assert "COSIGN_PASSWORD" not in publish_job
    assert "cache-from:" not in publish_job
    assert "cache-to:" not in publish_job
    assert "docker run --rm" in validate_job
    assert "--read-only" in validate_job
    assert "--network none" in validate_job
    assert "--cap-drop ALL" in validate_job


def test_container_workflow_uses_node24_docker_actions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "containers.yml").read_text()

    assert (
        workflow.count(
            "docker/build-push-action@53b7df96c91f9c12dcc8a07bcb9ccacbed38856a # v7.3.0"
        )
        == 2
    )
    assert (
        "docker/setup-qemu-action@96fe6ef7f33517b61c61be40b68a1882f3264fb8 # v4.2.0"
        in workflow
    )
    assert (
        "docker/login-action@abd2ef45e78c5afb21d64d4ca52ee8550d9572c7 # v4.5.1"
        in workflow
    )


def test_dependabot_tracks_docker_and_workflow_dependencies() -> None:
    config = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text())
    ecosystems = {update["package-ecosystem"] for update in config["updates"]}

    assert {"docker", "github-actions", "pip"} <= ecosystems


def test_generator_health_contract_accepts_only_expected_modules(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    required, _ = container_health.TARGET_MODULES["generator-mcp"]
    monkeypatch.setattr(container_health.os, "geteuid", lambda: 65532)
    monkeypatch.setattr(
        container_health.importlib.util,
        "find_spec",
        lambda module_name: object() if module_name in required else None,
    )
    monkeypatch.setenv(container_health.WORKSPACE_ROOT_ENV, str(tmp_path))
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_LOG", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY", raising=False)
    monkeypatch.delenv("TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE", raising=False)

    assert (
        container_health.check_container_health("generator-mcp")
        == "generator-mcp container healthy"
    )


def test_container_health_rejects_root_and_unexpected_dependency(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(container_health.os, "geteuid", lambda: 0)
    with pytest.raises(ContainerHealthError, match="must not run as root"):
        container_health.check_container_health("cli")

    monkeypatch.setattr(container_health.os, "geteuid", lambda: 65532)
    monkeypatch.setenv(container_health.WORKSPACE_ROOT_ENV, str(tmp_path))
    required, _ = container_health.TARGET_MODULES["cli"]
    monkeypatch.setattr(
        container_health.importlib.util,
        "find_spec",
        lambda module_name: object()
        if module_name in required | {"trino"}
        else None,
    )
    with pytest.raises(ContainerHealthError, match="unexpected modules: trino"):
        container_health.check_container_health("cli")
