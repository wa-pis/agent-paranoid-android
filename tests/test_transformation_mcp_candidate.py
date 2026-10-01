"""Workspace containment for unregistered fictional execution candidate."""

import pytest

from test_data_agent.mcp_generator_server import WorkspacePathError
from test_data_agent.mcp_transformation_candidate import _execute_candidate_transformation


@pytest.mark.parametrize("argument", ["input_path", "policy_path", "output_path", "receipt_path"])
def test_candidate_paths_cannot_escape_workspace(tmp_path, monkeypatch, argument):
    monkeypatch.setenv("TEST_DATA_AGENT_WORKSPACE_ROOT", str(tmp_path))
    (tmp_path / "items.csv").write_text("label\nfictional\n")
    (tmp_path / "policy.yaml").write_text("invalid fixture; must never be parsed")
    (tmp_path / "receipt.json").write_text("invalid fixture; must never be parsed")
    arguments = {"input_path": "items.csv", "policy_path": "policy.yaml",
        "output_path": "output", "receipt_path": "receipt.json", "snapshot_sha256": "0" * 64}
    arguments[argument] = "../fictional-outside-marker"
    with pytest.raises(WorkspacePathError) as error:
        _execute_candidate_transformation(**arguments)
    assert "fictional-outside-marker" not in str(error.value)
    assert not (tmp_path / "output").exists()
