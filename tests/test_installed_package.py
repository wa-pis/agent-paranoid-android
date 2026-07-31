from __future__ import annotations

from pathlib import Path

import pytest

from scripts.check_installed_package import (
    MAX_WHEEL_SIZE_BYTES,
    group_dependencies_by_extra,
    requirement_extras,
    verify_wheel_size,
)


def test_requirements_are_grouped_by_runtime_extra() -> None:
    requirements = [
        "faker>=25.0.0",
        'mcp<2.0.0,>=1.0.0; extra == "mcp"',
        'mcp<2.0.0,>=1.0.0; extra == "all"',
        'pyarrow>=15.0.0; extra == "parquet"',
        'pyarrow>=15.0.0; extra == "all"',
    ]

    assert group_dependencies_by_extra(requirements) == {
        "base": {"faker"},
        "mcp": {"mcp"},
        "parquet": {"pyarrow"},
        "all": {"mcp", "pyarrow"},
    }


def test_requirement_extras_accepts_combined_markers() -> None:
    requirement = 'mcp<2.0.0,>=1.0.0; extra == "all" or extra == "mcp"'

    assert requirement_extras(requirement) == {"all", "mcp"}


def test_wheel_size_budget_accepts_small_wheel(tmp_path: Path) -> None:
    wheel = tmp_path / "package.whl"
    wheel.write_bytes(b"synthetic wheel")

    verify_wheel_size(wheel)


def test_wheel_size_budget_rejects_large_wheel(tmp_path: Path) -> None:
    wheel = tmp_path / "package.whl"
    wheel.write_bytes(b"x" * (MAX_WHEEL_SIZE_BYTES + 1))

    with pytest.raises(SystemExit, match="wheel exceeds size budget"):
        verify_wheel_size(wheel)
