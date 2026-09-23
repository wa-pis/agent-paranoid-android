import os
from collections.abc import Callable
from pathlib import Path

import pytest

from test_data_agent.io import path_policy

from test_data_agent.io.path_policy import (
    atomic_binary_writer,
    atomic_write_bytes,
    make_staging_directory,
    path_identity,
    publish_directory,
    replace_path,
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


@pytest.mark.parametrize("operation", [publish_directory, replace_path])
def test_directory_publication_ignores_access_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    operation: Callable[[Path, Path], object],
) -> None:
    staging = tmp_path / "staging"
    output = tmp_path / "output"
    staging.mkdir()
    output.mkdir()
    (staging / "result.txt").write_text("synthetic")
    original = path_policy._stat_at
    reads: dict[str, int] = {}

    def stat_with_access(parent: int, name: str) -> os.stat_result | None:
        reads[name] = reads.get(name, 0) + 1
        if reads[name] == 2:
            current = original(parent, name)
            if current is not None:
                os.utime(name, ns=(current.st_atime_ns + 2_000_000_000,
                                   current.st_mtime_ns), dir_fd=parent)
        return original(parent, name)

    monkeypatch.setattr(path_policy, "_stat_at", stat_with_access)
    operation(staging, output)
    assert (output / "result.txt").read_text() == "synthetic"
    assert not staging.exists()


@pytest.mark.parametrize("operation", [publish_directory, replace_path])
@pytest.mark.parametrize("initially_present", [False, True])
def test_publication_rejects_destination_presence_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    operation: Callable[[Path, Path], object], initially_present: bool,
) -> None:
    staging = tmp_path / "staging"
    output = tmp_path / "output"
    staging.mkdir()
    if initially_present:
        output.mkdir()
    original = path_policy._stat_at
    output_reads = 0

    def changed_stat(parent: int, name: str) -> os.stat_result | None:
        nonlocal output_reads
        if name == output.name:
            output_reads += 1
            if output_reads == 2:
                if initially_present:
                    output.rename(tmp_path / "previous")
                else:
                    output.mkdir()
        return original(parent, name)

    monkeypatch.setattr(path_policy, "_stat_at", changed_stat)
    with pytest.raises(ValueError, match="output path changed"):
        operation(staging, output)
    assert staging.exists()


def test_replace_rejects_same_inode_file_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    staging = tmp_path / "staging.txt"
    output = tmp_path / "output.txt"
    staging.write_text("synthetic")
    output.write_text("existing")
    original = path_policy._stat_at
    output_reads = 0

    def changed_stat(parent: int, name: str) -> os.stat_result | None:
        nonlocal output_reads
        if name == output.name:
            output_reads += 1
            if output_reads == 2:
                output.write_text("changed contents")
        return original(parent, name)

    monkeypatch.setattr(path_policy, "_stat_at", changed_stat)
    with pytest.raises(ValueError, match="output path changed"):
        replace_path(staging, output)
    assert output.read_text() == "changed contents"
    assert staging.read_text() == "synthetic"


@pytest.mark.parametrize("operation", [publish_directory, replace_path])
@pytest.mark.parametrize("target", ["staging", "output"])
@pytest.mark.parametrize("replacement", ["directory", "symlink"])
def test_publication_rejects_path_identity_swap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    operation: Callable[[Path, Path], object], target: str, replacement: str,
) -> None:
    staging = tmp_path / "staging"
    output = tmp_path / "output"
    outside = tmp_path / "outside"
    staging.mkdir()
    output.mkdir()
    outside.mkdir()
    (staging / "data.txt").write_text("synthetic")
    original = path_policy._stat_at
    reads = 0

    def swapped_stat(parent: int, name: str) -> os.stat_result | None:
        nonlocal reads
        if name == target:
            reads += 1
            if reads == 2:
                path = tmp_path / target
                path.rename(tmp_path / "previous")
                if replacement == "directory":
                    path.mkdir()
                else:
                    path.symlink_to(outside, target_is_directory=True)
        return original(parent, name)

    monkeypatch.setattr(path_policy, "_stat_at", swapped_stat)
    with pytest.raises(ValueError, match="path changed during publication"):
        operation(staging, output)
    assert not (outside / "data.txt").exists()
    preserved = tmp_path / "previous" if target == "staging" else staging
    assert (preserved / "data.txt").read_text() == "synthetic"
