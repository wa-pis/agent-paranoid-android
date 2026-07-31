from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import test_data_agent
from test_data_agent.advisor import AdvisorExchange
from test_data_agent.agent import AgentResult
from test_data_agent.core import DatasetSpec
from test_data_agent.io import GenerationManifest

from scripts.contract_fixtures import (
    CONTRACT_FIXTURE_NAMES,
    build_contract_fixtures,
)


CONTRACT_FIXTURE_DIR = Path("tests/fixtures/contracts")


def test_public_contract_fixtures_are_current(tmp_path: Path) -> None:
    actual = build_contract_fixtures(tmp_path)
    assert {path.name for path in CONTRACT_FIXTURE_DIR.glob("*.json")} == set(
        CONTRACT_FIXTURE_NAMES
    )
    expected = {
        name: json.loads(
            CONTRACT_FIXTURE_DIR.joinpath(name).read_text(encoding="utf-8")
        )
        for name in CONTRACT_FIXTURE_NAMES
    }

    assert actual == expected, (
        "public contract fixture changed; review compatibility and run "
        "python3 scripts/update_contract_fixtures.py"
    )


def test_public_contract_fixtures_remain_typed_and_row_free() -> None:
    cli_plan = _load_fixture("cli-agent-plan.json")
    advisor_exchange = _load_fixture("advisor-exchange.json")
    dataset_spec = _load_fixture("dataset-spec.json")
    generation_manifest = _load_fixture("generation-manifest.json")
    mcp_plan = _load_fixture("mcp-plan.json")
    mcp_generate = _load_fixture("mcp-generate.json")
    public_python_api = _load_fixture("public-python-api.json")

    AgentResult.model_validate(cli_plan)
    AdvisorExchange.model_validate(advisor_exchange)
    DatasetSpec.model_validate(dataset_spec)
    GenerationManifest.model_validate(generation_manifest)

    assert mcp_plan["approval_required"] is True
    assert mcp_generate["source_rows_copied"] is False
    assert mcp_generate["synthetic"] is True
    assert "rows" not in mcp_plan
    assert "rows" not in mcp_generate
    serialized = json.dumps(
        {
            "cli": cli_plan,
            "advisor": advisor_exchange,
            "mcp_plan": mcp_plan,
            "mcp_generate": mcp_generate,
        }
    )
    assert "@" not in serialized
    assert "sk-" not in serialized
    assert public_python_api["exports"] == sorted(test_data_agent.__all__)
    assert all(hasattr(test_data_agent, name) for name in public_python_api["exports"])


def _load_fixture(name: str) -> dict[str, Any]:
    return json.loads(CONTRACT_FIXTURE_DIR.joinpath(name).read_text(encoding="utf-8"))
