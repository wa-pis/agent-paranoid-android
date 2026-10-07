"""Proposed registration patches must target the actual factory call sites."""

import ast
import subprocess
from pathlib import Path


def test_common_mcp_patch_enables_strict_arguments_at_both_factories(tmp_path):
    root = Path(__file__).resolve().parents[1]
    relative = Path("src/test_data_agent/mcp_generator_server.py")
    destination = tmp_path / relative
    destination.parent.mkdir(parents=True)
    destination.write_bytes((root / relative).read_bytes())
    patch = root / "openspec/changes/selective-source-transformation/common-mcp-activation.patch"
    # The same regression applies to closed and composed candidate source.
    applied = subprocess.run(["git", "apply", "--reverse", "--check", str(patch)],
                             cwd=tmp_path, capture_output=True).returncode == 0
    if applied:
        subprocess.run(["git", "apply", "--reverse", str(patch)],
                       cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "apply", str(patch)],
                   cwd=tmp_path, check=True, capture_output=True)
    tree = ast.parse(destination.read_text())
    factories = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "create_generator_mcp"]
    assert len(factories) == 2
    for factory in factories:
        strict = [keyword.value for keyword in factory.keywords if keyword.arg == "strict_arguments"]
        assert len(strict) == 1 and isinstance(strict[0], ast.Constant) and strict[0].value is True


def test_activation_patches_compose_with_current_contracts(tmp_path):
    root = Path(__file__).resolve().parents[1]
    patches = [root / "openspec/changes/selective-source-transformation" / filename
               for filename in ("common-cli-activation.patch", "common-mcp-activation.patch",
                                "oauth-browser-registration.patch", "registration-contract-activation.patch")]
    # Only patch targets are needed; prospective source copies may have no Git metadata.
    targets = {line.split()[2].removeprefix("a/") for patch in patches
               for line in patch.read_text().splitlines() if line.startswith("diff --git ")}
    for target in targets:
        relative = Path(target)
        assert not relative.is_absolute() and ".." not in relative.parts
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((root / relative).read_bytes())
    applied = subprocess.run(["git", "apply", "--reverse", "--check", str(patches[0])],
                             cwd=tmp_path, capture_output=True).returncode == 0
    if applied:
        for patch in reversed(patches):
            subprocess.run(["git", "apply", "--reverse", str(patch)], cwd=tmp_path,
                           check=True, capture_output=True)
    for patch in patches:
        subprocess.run(["git", "apply", str(patch)], cwd=tmp_path,
                       check=True, capture_output=True)
