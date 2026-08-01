from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from test_data_agent.mcp_trino_server import (
    describe_table,
    list_catalogs,
    list_schemas,
    list_tables,
    profile_table_safe,
)


def installed_cli() -> str:
    command = shutil.which("test-data-agent")
    if command is None:
        raise RuntimeError("installed command is unavailable: test-data-agent")
    return command


def run_example(output: Path) -> dict[str, object]:
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    cli = installed_cli()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent)
    )
    try:
        catalogs = list_catalogs()
        schemas = list_schemas("tpch")
        tables = list_tables("tpch", "tiny")
        columns = describe_table("tpch", "tiny", "nation")
        profile = profile_table_safe(
            "tpch",
            "tiny",
            "nation",
            max_top_values=5,
        )
        profile_path = temporary / "profile.json"
        profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n")
        spec_path = temporary / "dataset_spec.yaml"
        generated = temporary / "generated"
        subprocess.run(
            [
                cli,
                "infer-spec",
                str(profile_path),
                "--count",
                "12",
                "--output",
                str(spec_path),
            ],
            check=True,
        )
        subprocess.run(
            [
                cli,
                "generate",
                str(spec_path),
                "--seed",
                "141421",
                "--format",
                "json",
                "--output",
                str(generated),
            ],
            check=True,
        )
        manifest = json.loads((generated / "generation_manifest.json").read_text())
        result: dict[str, object] = {
            "catalog_available": "tpch" in catalogs,
            "schema_available": "tiny" in schemas,
            "table_available": "nation" in tables,
            "profile_row_count": profile["row_count"],
            "profile_column_count": len(columns),
            "generated_row_counts": manifest["row_counts"],
            "seed": manifest["seed"],
            "validation_valid": manifest["validation_valid"],
            "synthetic": manifest["synthetic"],
            "source_rows_copied": manifest["source_rows_copied"],
        }
        (temporary / "example_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        temporary.replace(output)
        return result
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = run_example(args.output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
