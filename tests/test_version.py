import tomllib
from pathlib import Path

import test_data_agent


def test_package_and_project_versions_match() -> None:
    project = tomllib.loads((Path(__file__).parent.parent / "pyproject.toml").read_text())

    assert test_data_agent.__version__ == project["project"]["version"] == "0.5.0"
