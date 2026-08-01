from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path

import pytest


PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "test_data_agent"

LOWER_LAYER_MODULES = {
    "test_data_agent.agent_contracts",
    "test_data_agent.agent_planning",
    "test_data_agent.agent_review",
    "test_data_agent.agent_approval",
    "test_data_agent.agent_recovery",
    "test_data_agent.agent_advising",
    "test_data_agent.agent_status",
    "test_data_agent.workspace_store",
    "test_data_agent.trino_config",
    "test_data_agent.trino_sql_policy",
    "test_data_agent.trino_query_builders",
    "test_data_agent.trino_client",
    "test_data_agent.trino_profiling",
    "test_data_agent.trino_masking",
}

BOUNDARY_MODULES = LOWER_LAYER_MODULES | {
    "test_data_agent.agent",
    "test_data_agent.cli",
    "test_data_agent.cli_agent",
    "test_data_agent.cli_application",
    "test_data_agent.cli_commands",
    "test_data_agent.cli_contract",
    "test_data_agent.cli_dependencies",
    "test_data_agent.cli_doctor",
    "test_data_agent.cli_parser",
    "test_data_agent.cli_presenter",
    "test_data_agent.mcp_generator_server",
    "test_data_agent.mcp_generator_transport",
    "test_data_agent.mcp_trino_server",
    "test_data_agent.mcp_trino_transport",
}

REQUIRED_POLICY_IMPORTS = {
    "test_data_agent.agent_approval": {"test_data_agent.safety"},
    "test_data_agent.agent_planning": {"test_data_agent.safety"},
    "test_data_agent.agent_review": {"test_data_agent.safety"},
    "test_data_agent.generation.entity_generator": {"test_data_agent.safety"},
    "test_data_agent.validation.reconciliation": {"test_data_agent.safety"},
    "test_data_agent.trino_query_builders": {
        "test_data_agent.trino_sql_policy"
    },
    "test_data_agent.trino_profiling": {"test_data_agent.trino_sql_policy"},
    "test_data_agent.trino_masking": {"test_data_agent.trino_sql_policy"},
}

POLICY_SYMBOL_OWNERS = {
    "assert_profile_safe": "test_data_agent.safety",
    "assert_spec_safe": "test_data_agent.safety",
    "check_allowlist": "test_data_agent.trino_sql_policy",
    "infer_sensitive_from_name": "test_data_agent.core.privacy",
    "mask_row": "test_data_agent.trino_masking",
    "summarize_top_values": "test_data_agent.trino_masking",
    "validate_safe_select": "test_data_agent.trino_sql_policy",
    "validate_safe_select_shape": "test_data_agent.trino_sql_policy",
}


@pytest.mark.parametrize("module", sorted(LOWER_LAYER_MODULES))
def test_lower_layers_do_not_import_cli_or_mcp(module: str) -> None:
    imports = imported_modules(module)
    forbidden = sorted(
        imported
        for imported in imports
        if imported.startswith(("test_data_agent.cli", "test_data_agent.mcp_"))
    )

    assert forbidden == []


@pytest.mark.parametrize(
    ("module", "required"),
    sorted(REQUIRED_POLICY_IMPORTS.items()),
)
def test_safety_policy_is_enforced_below_transports(
    module: str,
    required: set[str],
) -> None:
    assert required <= imported_modules(module)


@pytest.mark.parametrize(
    "module",
    [
        "test_data_agent.mcp_generator_transport",
        "test_data_agent.mcp_trino_transport",
    ],
)
def test_mcp_transports_only_register_injected_services(module: str) -> None:
    application_imports = {
        imported
        for imported in imported_modules(module)
        if imported.startswith("test_data_agent.")
    }

    assert application_imports == {"test_data_agent.audit"}


@pytest.mark.parametrize(
    ("symbol", "owner"),
    sorted(POLICY_SYMBOL_OWNERS.items()),
)
def test_policy_symbol_has_one_owner(symbol: str, owner: str) -> None:
    definitions = {
        module
        for module in package_modules()
        if symbol in top_level_definitions(module)
    }

    assert definitions == {owner}


def test_application_boundary_import_graph_is_acyclic() -> None:
    graph = {
        module: imported_modules(module) & BOUNDARY_MODULES
        for module in BOUNDARY_MODULES
    }

    assert find_cycle(graph) is None


def package_modules() -> Iterable[str]:
    for path in PACKAGE_ROOT.rglob("*.py"):
        if path.name != "__init__.py":
            yield module_name(path)


def module_name(path: Path) -> str:
    relative = path.relative_to(PACKAGE_ROOT).with_suffix("")
    return ".".join(("test_data_agent", *relative.parts))


def module_path(module: str) -> Path:
    relative = module.removeprefix("test_data_agent.").replace(".", "/")
    return PACKAGE_ROOT / f"{relative}.py"


def module_tree(module: str) -> ast.Module:
    return ast.parse(module_path(module).read_text(encoding="utf-8"))


def imported_modules(module: str) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(module_tree(module)):
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports


def top_level_definitions(module: str) -> set[str]:
    return {
        node.name
        for node in module_tree(module).body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }


def find_cycle(graph: dict[str, set[str]]) -> tuple[str, ...] | None:
    visited: set[str] = set()
    active: list[str] = []

    def visit(module: str) -> tuple[str, ...] | None:
        if module in active:
            start = active.index(module)
            return (*active[start:], module)
        if module in visited:
            return None
        active.append(module)
        for dependency in sorted(graph[module]):
            cycle = visit(dependency)
            if cycle is not None:
                return cycle
        active.pop()
        visited.add(module)
        return None

    for module in sorted(graph):
        cycle = visit(module)
        if cycle is not None:
            return cycle
    return None
