"""Installed offline demo application workflow."""

from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

from test_data_agent.core.settings import OutputFormat
from test_data_agent.io.path_policy import discard_staging_directory
from test_data_agent.io.workflows import (
    commit_temp_output_folder,
    generate_dataset_from_csv_artifacts,
    make_temp_output_folder,
)


DEMO_COUNT = 12
DEMO_SEED = 20260801


def run_demo(output_folder: Path) -> int:
    """Generate one atomic synthetic bundle from the packaged fixture."""

    if output_folder.exists() or output_folder.is_symlink():
        raise ValueError(f"demo output already exists: {output_folder}")

    resource = files("test_data_agent.resources").joinpath("demo_customers.csv")
    if not resource.is_file():
        raise ValueError("installed demo fixture is missing")

    temp_folder = make_temp_output_folder(output_folder)
    try:
        with as_file(resource) as fixture_path:
            report, _ = generate_dataset_from_csv_artifacts(
                fixture_path,
                count=DEMO_COUNT,
                seed=DEMO_SEED,
                output_path=temp_folder / "customers.csv",
                output_format=OutputFormat.CSV,
                table_name="customers",
            )
        if not report.valid:
            raise ValueError("installed demo dataset failed validation")
        commit_temp_output_folder(temp_folder, output_folder)
    except BaseException:
        discard_staging_directory(temp_folder)
        raise
    return 0
