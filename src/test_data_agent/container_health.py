"""Non-networking health checks for the supported container targets."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from test_data_agent.audit import audit_logger_from_env


CONTAINER_TARGET_ENV = "TEST_DATA_AGENT_CONTAINER_TARGET"
WORKSPACE_ROOT_ENV = "TEST_DATA_AGENT_WORKSPACE_ROOT"
TARGET_MODULES = {
    "cli": (
        frozenset({"faker", "pydantic", "yaml"}),
        frozenset({"mcp", "pyarrow", "sqlglot", "trino"}),
    ),
    "generator-mcp": (
        frozenset({"faker", "mcp", "pydantic", "yaml"}),
        frozenset({"pyarrow", "sqlglot", "trino"}),
    ),
    "trino-mcp": (
        frozenset({"faker", "mcp", "pydantic", "sqlglot", "trino", "yaml"}),
        frozenset({"pyarrow"}),
    ),
}


class ContainerHealthError(RuntimeError):
    """Raised when a container violates its expected runtime contract."""


def check_container_health(target: str | None = None) -> str:
    selected = target or os.environ.get(CONTAINER_TARGET_ENV, "")
    if selected not in TARGET_MODULES:
        raise ContainerHealthError("unknown container target")
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise ContainerHealthError("container must not run as root")

    required, forbidden = TARGET_MODULES[selected]
    available = {
        module_name
        for module_name in required | forbidden
        if importlib.util.find_spec(module_name) is not None
    }
    missing = sorted(required - available)
    unexpected = sorted(forbidden & available)
    if missing:
        raise ContainerHealthError(
            f"{selected} container is missing required modules: {', '.join(missing)}"
        )
    if unexpected:
        raise ContainerHealthError(
            f"{selected} container contains unexpected modules: {', '.join(unexpected)}"
        )

    if selected in {"cli", "generator-mcp"}:
        try:
            workspace = Path(
                os.environ.get(WORKSPACE_ROOT_ENV, "/workspace")
            ).resolve(strict=True)
        except OSError as exc:
            raise ContainerHealthError("container workspace does not exist") from exc
        if not workspace.is_dir() or not os.access(workspace, os.R_OK | os.W_OK):
            raise ContainerHealthError("container workspace must be readable and writable")

    if selected == "trino-mcp":
        from test_data_agent.mcp_trino_server import TrinoConfig

        TrinoConfig.from_env()

    if selected.endswith("-mcp"):
        audit_logger_from_env(selected)

    return f"{selected} container healthy"


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=sorted(TARGET_MODULES))
    args = parser.parse_args()
    print(check_container_health(args.target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
