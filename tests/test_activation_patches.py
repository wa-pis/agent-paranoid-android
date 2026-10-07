"""Registration patch sequences must compose and preserve strict factories."""
import ast
import subprocess
from pathlib import Path


def _compose_activation_patches(root: Path, destination: Path) -> None:
    directory = root / "openspec/changes/selective-source-transformation"
    names = ["common-cli-activation.patch", "common-mcp-activation.patch",
        "oauth-browser-registration.patch", "registration-contract-activation.patch"]
    sql = directory / "sql-query-public-activation.patch"
    if sql.exists():
        names.append(sql.name)
    patches = [directory / name for name in names]
    # Handle both Git-style and unified patches, including newly created files.
    targets = {line[6:] for patch in patches for line in patch.read_text().splitlines()
        if line.startswith("+++ b/")}
    for target in targets:
        relative = Path(target)
        assert not relative.is_absolute() and ".." not in relative.parts
        original = root / relative
        if original.exists():
            output = destination / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(original.read_bytes())

    def applies(patch: Path, *, reverse: bool = False) -> bool:
        arguments = ["git", "apply", "--check"]
        if reverse:
            arguments.append("--reverse")
        return subprocess.run([*arguments, str(patch)], cwd=destination,
            capture_output=True).returncode == 0

    def apply(patch: Path, *, reverse: bool = False) -> None:
        assert applies(patch, reverse=reverse), patch.name
        arguments = ["git", "apply"]
        if reverse:
            arguments.append("--reverse")
        subprocess.run([*arguments, str(patch)], cwd=destination, check=True, capture_output=True)

    # Unwind a fully composed SQL overlay before the four earlier registrations.
    # A four-patch copy and a closed author checkout remain valid starting points.
    if len(patches) == 5 and applies(patches[-1], reverse=True):
        apply(patches[-1], reverse=True)
    if applies(patches[0], reverse=True):
        for patch in reversed(patches[:4]):
            apply(patch, reverse=True)
    for patch in patches:
        apply(patch)
    expected = {target: (destination / target).read_bytes() for target in targets}
    # Verify reversibility of the COMPLETE composition, not only the first patch.
    for patch in reversed(patches):
        apply(patch, reverse=True)
    for patch in patches:
        apply(patch)
    assert {target: (destination / target).read_bytes() for target in targets} == expected


def test_common_mcp_patch_enables_strict_arguments_at_both_factories(tmp_path):
    root = Path(__file__).resolve().parents[1]
    _compose_activation_patches(root, tmp_path)
    tree = ast.parse((tmp_path / "src/test_data_agent/mcp_generator_server.py").read_text())
    factories = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "create_generator_mcp"]
    assert len(factories) == 2
    for factory in factories:
        strict = [keyword.value for keyword in factory.keywords if keyword.arg == "strict_arguments"]
        assert len(strict) == 1 and isinstance(strict[0], ast.Constant) and strict[0].value is True


def test_activation_patches_compose_with_current_contracts(tmp_path):
    _compose_activation_patches(Path(__file__).resolve().parents[1], tmp_path)
