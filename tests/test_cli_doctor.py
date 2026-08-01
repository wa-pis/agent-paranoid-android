import ast
from pathlib import Path
from types import ModuleType

import test_data_agent.cli_doctor as cli_doctor_module
from test_data_agent.cli_doctor import CliDoctorService, ModuleImporter


def test_doctor_service_reports_optional_and_required_extras() -> None:
    def import_without_pyarrow(name: str) -> ModuleType:
        if name == "pyarrow":
            raise ImportError("not installed")
        return ModuleType(name)

    service = _service(import_without_pyarrow)

    optional = service.inspect(skip_smoke=True)
    required = service.inspect(skip_smoke=True, required_extras={"parquet"})

    assert "extra parquet: not installed (optional)" in optional.checks
    assert required.failures == (
        "extra parquet: missing pyarrow (install agent-paranoid-android[parquet])",
    )


def test_doctor_service_redacts_capability_failure() -> None:
    def fail_with_secret() -> None:
        raise RuntimeError("secret-provider-token")

    service = CliDoctorService(
        import_module=lambda name: ModuleType(name),
        parquet_smoke=lambda _fixture, _output: None,
        mcp_smoke=fail_with_secret,
        trino_smoke=lambda: None,
        openai_smoke=lambda: None,
    )

    report = service.inspect(required_extras={"mcp"})

    assert report.failures == (
        "capability mcp: failed (reinstall agent-paranoid-android[mcp] and retry)",
    )
    assert "secret-provider-token" not in repr(report)


def test_doctor_boundary_has_no_cli_compatibility_import() -> None:
    assert "test_data_agent.cli" not in _top_level_imports(cli_doctor_module)


def _service(import_module: ModuleImporter) -> CliDoctorService:
    return CliDoctorService(
        import_module=import_module,
        parquet_smoke=lambda _fixture, _output: None,
        mcp_smoke=lambda: None,
        trino_smoke=lambda: None,
        openai_smoke=lambda: None,
    )


def _top_level_imports(module: ModuleType) -> set[str]:
    tree = ast.parse(Path(module.__file__).read_text())
    imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
    return imports
