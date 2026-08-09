from pathlib import Path

import pytest

from test_data_agent.io.path_policy import (
    atomic_binary_writer,
    atomic_write_bytes,
    make_staging_directory,
    path_identity,
    publish_directory,
    remove_tree_if_identity,
)


def test_atomic_write_rejects_symlinked_parent(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="unsafe filesystem path"):
        atomic_write_bytes(linked / "result.json", b"safe")

    assert not (outside / "result.json").exists()


def test_atomic_write_rejects_destination_inode_change(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    output.write_bytes(b"old")

    with pytest.raises(ValueError, match="changed during publication"):
        with atomic_binary_writer(output) as handle:
            handle.write(b"new")
            output.unlink()
            output.write_bytes(b"attacker")

    assert output.read_bytes() == b"attacker"


def test_directory_publication_rejects_symlink_destination(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    output = tmp_path / "output"
    output.symlink_to(outside, target_is_directory=True)
    staging = make_staging_directory(output)
    atomic_write_bytes(staging / "result.json", b"safe")

    with pytest.raises(ValueError, match="generation output must be a folder"):
        publish_directory(staging, output)

    assert not (outside / "result.json").exists()


def test_cleanup_refuses_replaced_directory(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    expected = path_identity(output)
    output.rename(tmp_path / "original")
    output.mkdir()
    (output / "keep.txt").write_text("keep")

    assert remove_tree_if_identity(output, expected) is False
    assert (output / "keep.txt").read_text() == "keep"
