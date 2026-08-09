"""Race-resistant filesystem publication helpers."""

from __future__ import annotations

import os
import secrets
import shutil
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator


@dataclass(frozen=True, slots=True)
class PathIdentity:
    device: int
    inode: int
    mode: int


def _identity(value: os.stat_result) -> PathIdentity:
    return PathIdentity(value.st_dev, value.st_ino, value.st_mode)


def _file_version(value: os.stat_result) -> tuple[PathIdentity, int, int]:
    return _identity(value), value.st_ctime_ns, value.st_size


def _flags(*, directory: bool = False) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if directory:
        flags |= os.O_DIRECTORY
    return flags


@contextmanager
def _parent_descriptor(path: Path, *, create: bool = False) -> Iterator[tuple[int, str]]:
    if not hasattr(os, "O_NOFOLLOW"):
        raise ValueError("secure filesystem publication requires POSIX no-follow support")
    absolute = path.expanduser().absolute()
    descriptor = os.open(absolute.anchor, _flags(directory=True))
    try:
        for component in absolute.parent.parts[1:]:
            try:
                child = os.open(component, _flags(directory=True), dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(component, 0o700, dir_fd=descriptor)
                child = os.open(component, _flags(directory=True), dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor, absolute.name
    except OSError as exc:
        raise ValueError("unsafe filesystem path") from exc
    finally:
        os.close(descriptor)


def _stat_at(parent: int, name: str) -> os.stat_result | None:
    try:
        return os.stat(name, dir_fd=parent, follow_symlinks=False)
    except FileNotFoundError:
        return None


def path_identity(path: Path) -> PathIdentity:
    with _parent_descriptor(path) as (parent, name):
        value = _stat_at(parent, name)
        if value is None:
            raise ValueError("filesystem path no longer exists")
        return _identity(value)


def inspect_file_output(path: Path) -> PathIdentity | None:
    with _parent_descriptor(path, create=True) as (parent, name):
        value = _stat_at(parent, name)
        if value is None:
            return None
        if not stat.S_ISREG(value.st_mode):
            raise ValueError("output path must be a regular file")
        return _identity(value)


def ensure_directory(path: Path) -> tuple[PathIdentity, bool]:
    with _parent_descriptor(path, create=True) as (parent, name):
        value = _stat_at(parent, name)
        created = value is None
        if created:
            os.mkdir(name, 0o700, dir_fd=parent)
            value = _stat_at(parent, name)
        if value is None or not stat.S_ISDIR(value.st_mode):
            raise ValueError("output path must be a directory")
        descriptor = os.open(name, _flags(directory=True), dir_fd=parent)
        try:
            if _identity(os.fstat(descriptor)) != _identity(value):
                raise ValueError("output path changed")
        finally:
            os.close(descriptor)
        return _identity(value), created


@contextmanager
def atomic_binary_writer(path: Path) -> Iterator[BinaryIO]:
    with _parent_descriptor(path, create=True) as (parent, name):
        original = _stat_at(parent, name)
        if original is not None and not stat.S_ISREG(original.st_mode):
            raise ValueError("output path must be a regular file")
        temporary_name = f".{name}.{secrets.token_hex(8)}.tmp"
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=parent,
        )
        handle = os.fdopen(descriptor, "wb")
        try:
            yield handle
            handle.flush()
            os.fsync(handle.fileno())
            handle.close()
            current = _stat_at(parent, name)
            if original is None:
                changed = current is not None
            else:
                changed = current is None or _file_version(current) != _file_version(original)
            if changed:
                raise ValueError("output path changed during publication")
            os.replace(temporary_name, name, src_dir_fd=parent, dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            if not handle.closed:
                handle.close()
            try:
                os.unlink(temporary_name, dir_fd=parent)
            except FileNotFoundError:
                pass


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    with atomic_binary_writer(path) as handle:
        handle.write(payload)


@contextmanager
def open_regular_file(path: Path) -> Iterator[BinaryIO]:
    with _parent_descriptor(path) as (parent, name):
        descriptor = os.open(name, _flags(), dir_fd=parent)
        value = os.fstat(descriptor)
        if not stat.S_ISREG(value.st_mode):
            os.close(descriptor)
            raise ValueError("filesystem input must be a regular file")
        with os.fdopen(descriptor, "rb") as handle:
            yield handle


def make_staging_directory(destination: Path) -> Path:
    with _parent_descriptor(destination, create=True) as (parent, name):
        for _ in range(100):
            temporary_name = f".{name}.{secrets.token_hex(8)}"
            try:
                os.mkdir(temporary_name, 0o700, dir_fd=parent)
            except FileExistsError:
                continue
            return destination.parent / temporary_name
    raise FileExistsError("could not allocate staging directory")


def publish_directory(source: Path, destination: Path) -> PathIdentity:
    if source.parent.absolute() != destination.parent.absolute():
        raise ValueError("staging and output folders must share a parent")
    with _parent_descriptor(destination) as (parent, destination_name):
        source_name = source.name
        source_stat = _stat_at(parent, source_name)
        if source_stat is None or not stat.S_ISDIR(source_stat.st_mode):
            raise ValueError("staging path must be a directory")
        destination_stat = _stat_at(parent, destination_name)
        if destination_stat is not None:
            if not stat.S_ISDIR(destination_stat.st_mode):
                raise ValueError("generation output must be a folder")
            output_descriptor = os.open(
                destination_name, _flags(directory=True), dir_fd=parent
            )
            try:
                if os.listdir(output_descriptor):
                    raise ValueError("generation output folder must be empty")
                if _identity(os.fstat(output_descriptor)) != _identity(destination_stat):
                    raise ValueError("output path changed during publication")
            finally:
                os.close(output_descriptor)
        if _stat_at(parent, source_name) != source_stat:
            raise ValueError("staging path changed during publication")
        if _stat_at(parent, destination_name) != destination_stat:
            raise ValueError("output path changed during publication")
        os.replace(source_name, destination_name, src_dir_fd=parent, dst_dir_fd=parent)
        published = _stat_at(parent, destination_name)
        if published is None:
            raise ValueError("output publication did not complete")
        os.fsync(parent)
        return _identity(published)


def replace_path(source: Path, destination: Path) -> None:
    with _parent_descriptor(source) as (source_parent, source_name):
        with _parent_descriptor(destination, create=True) as (
            destination_parent,
            destination_name,
        ):
            source_stat = _stat_at(source_parent, source_name)
            destination_stat = _stat_at(destination_parent, destination_name)
            if source_stat is None or stat.S_ISLNK(source_stat.st_mode):
                raise ValueError("source path is not safe to publish")
            if destination_stat is not None and stat.S_ISLNK(destination_stat.st_mode):
                raise ValueError("output path must not be a symbolic link")
            if _stat_at(source_parent, source_name) != source_stat:
                raise ValueError("source path changed during publication")
            if _stat_at(destination_parent, destination_name) != destination_stat:
                raise ValueError("output path changed during publication")
            os.replace(
                source_name,
                destination_name,
                src_dir_fd=source_parent,
                dst_dir_fd=destination_parent,
            )


def remove_tree(path: Path, expected: PathIdentity) -> None:
    with _parent_descriptor(path) as (parent, name):
        current = _stat_at(parent, name)
        if current is None:
            return
        if _identity(current) != expected or not stat.S_ISDIR(current.st_mode):
            raise ValueError("cleanup path changed")
        if not shutil.rmtree.avoids_symlink_attacks:
            raise ValueError("secure directory cleanup is unavailable")
        shutil.rmtree(name, dir_fd=parent)


def remove_tree_if_identity(path: Path, expected: PathIdentity) -> bool:
    with _parent_descriptor(path) as (parent, name):
        current = _stat_at(parent, name)
        if (
            current is None
            or _identity(current) != expected
            or not stat.S_ISDIR(current.st_mode)
        ):
            return False
        if not shutil.rmtree.avoids_symlink_attacks:
            raise ValueError("secure directory cleanup is unavailable")
        shutil.rmtree(name, dir_fd=parent)
        return True


def discard_staging_directory(path: Path) -> None:
    try:
        expected = path_identity(path)
    except ValueError:
        return
    remove_tree_if_identity(path, expected)
