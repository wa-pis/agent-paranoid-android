"""Central optional-dependency resolution for CLI application services."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import TypeVar

from test_data_agent.version import __version__

CORE_DEPENDENCY_MODULES = ("faker", "pydantic", "yaml")
OPTIONAL_EXTRA_MODULES: dict[str, tuple[str, ...]] = {
    "parquet": ("pyarrow",),
    "mcp": ("mcp",),
    "trino": ("sqlglot", "trino"),
    "postgres": ("psycopg", "sqlglot"),
    "openai": ("openai",),
    "gigachat": ("gigachat",),
}

ModuleImporter = Callable[[str], ModuleType]
LoadedDependency = TypeVar("LoadedDependency")


class CliDependencyError(ValueError):
    """An unavailable optional CLI capability with copy-ready recovery."""


def install_extra_command(extra: str) -> str:
    """Return the exact package-version install command for one extra."""
    return (
        'python -m pip install '
        f'"agent-paranoid-android[{extra}]=={__version__}"'
    )


@dataclass(frozen=True)
class CliDependencyResolver:
    """Resolve optional CLI capabilities through one injected importer."""

    import_module: ModuleImporter = importlib.import_module

    def missing_modules(self, extra: str) -> tuple[str, ...]:
        try:
            module_names = OPTIONAL_EXTRA_MODULES[extra]
        except KeyError:
            raise ValueError(f"unsupported optional extra: {extra}") from None

        missing = []
        for module_name in module_names:
            try:
                self.import_module(module_name)
            except ImportError:
                missing.append(module_name)
        return tuple(missing)

    def require_module(
        self,
        module_name: str,
        *,
        extra: str,
        purpose: str,
    ) -> ModuleType:
        return self.load(
            extra=extra,
            purpose=purpose,
            loader=lambda: self.import_module(module_name),
        )

    def load(
        self,
        *,
        extra: str,
        purpose: str,
        loader: Callable[[], LoadedDependency],
    ) -> LoadedDependency:
        if extra not in OPTIONAL_EXTRA_MODULES:
            raise ValueError(f"unsupported optional extra: {extra}")
        try:
            return loader()
        except ImportError as exc:
            raise CliDependencyError(
                f"{purpose} requires the `{extra}` extra. Install it with: "
                f"{install_extra_command(extra)}"
            ) from exc


DEFAULT_CLI_DEPENDENCY_RESOLVER = CliDependencyResolver()
