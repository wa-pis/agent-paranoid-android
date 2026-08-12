import ast
from pathlib import Path
from types import ModuleType

import pytest
import test_data_agent.cli_dependencies as cli_dependencies_module
from test_data_agent.cli_dependencies import CliDependencyResolver


def test_dependency_resolver_reports_missing_extra_modules_in_order() -> None:
    def import_without_trino(name: str) -> ModuleType:
        if name in {"sqlglot", "trino"}:
            raise ImportError("not installed")
        return ModuleType(name)

    resolver = CliDependencyResolver(import_without_trino)

    assert resolver.missing_modules("trino") == ("sqlglot", "trino")


def test_dependency_resolver_tracks_postgres_as_optional() -> None:
    def import_without_postgres(name: str) -> ModuleType:
        if name == "psycopg":
            raise ImportError("not installed")
        return ModuleType(name)

    assert CliDependencyResolver(import_without_postgres).missing_modules(
        "postgres"
    ) == ("psycopg",)


def test_dependency_resolver_tracks_gigachat_as_optional() -> None:
    def import_without_gigachat(name: str) -> ModuleType:
        if name == "gigachat":
            raise ImportError("not installed")
        return ModuleType(name)

    assert CliDependencyResolver(import_without_gigachat).missing_modules(
        "gigachat"
    ) == ("gigachat",)


def test_dependency_resolver_normalizes_required_extra_error() -> None:
    cause = ImportError("secret-local-path")

    def missing_loader() -> object:
        raise cause

    resolver = CliDependencyResolver()

    with pytest.raises(
        ValueError,
        match=r"OpenAI advice requires agent-paranoid-android\[openai\]",
    ) as exc_info:
        resolver.load(
            extra="openai",
            purpose="OpenAI advice",
            loader=missing_loader,
        )

    assert exc_info.value.__cause__ is cause
    assert "secret-local-path" not in str(exc_info.value)


def test_dependency_resolver_rejects_unknown_extra() -> None:
    with pytest.raises(ValueError, match="unsupported optional extra"):
        CliDependencyResolver().missing_modules("unknown")


def test_dependency_boundary_has_no_cli_or_transport_imports() -> None:
    forbidden = {
        "test_data_agent.cli",
        "test_data_agent.cli_doctor",
        "test_data_agent.mcp_generator_server",
        "test_data_agent.mcp_trino_server",
    }

    assert _top_level_imports(cli_dependencies_module).isdisjoint(forbidden)


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports
