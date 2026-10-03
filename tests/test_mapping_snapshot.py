import hashlib

import pytest

from test_data_agent.core.limits import GenerationBudget
from test_data_agent.core.transformation_mapping import MappingDeclarationError
from test_data_agent.io.mapping_snapshot import read_mapping_snapshot


def test_snapshot_hashes_returned_private_bytes(tmp_path):
    root = tmp_path.resolve()
    payload = b"old,new\na,b\n"
    (root / "map.csv").write_bytes(payload)
    snapshot = read_mapping_snapshot(root, "map.csv", max_bytes=len(payload), budget=GenerationBudget())
    assert snapshot.payload == payload
    assert snapshot.sha256 == hashlib.sha256(payload).hexdigest()
    assert repr(snapshot) == "MappingSnapshot()"


def test_snapshot_checks_per_file_limit_before_first_read(tmp_path):
    from test_data_agent.core.transformation_limits import (
        EffectiveInputLimit, InputDimension, TransformationLimitError,
    )
    (tmp_path / "source.csv").write_bytes(b"key\n1\n2\n")
    calls = [0]

    def clock():
        calls[0] += 1
        if calls[0] > 2:
            raise AssertionError("read loop reached before file-limit rejection")
        return 0.0

    with pytest.raises(TransformationLimitError) as caught:
        read_mapping_snapshot(tmp_path.resolve(), "source.csv", max_bytes=1024,
            budget=GenerationBudget(max_seconds=1, clock=clock),
            input_limit=EffectiveInputLimit(InputDimension.BYTES, 1, "profile"))
    assert caught.value.amount == 8 and caught.value.limit == 1
    assert caught.value.origin == "profile"


@pytest.mark.parametrize("case", ["overflow", "escape", "absolute", "symlink", "missing"])
def test_snapshot_rejects_unsafe_inputs_without_path_leaks(tmp_path, case):
    root = tmp_path.resolve()
    (root / "map.csv").write_bytes(b"fictional-private-marker")
    name, limit = "map.csv", 100
    if case == "overflow":
        limit = 2
    elif case == "escape":
        name = "../fictional-private-marker"
    elif case == "absolute":
        name = str(root / name)
    elif case == "symlink":
        (root / "linked.csv").symlink_to(root / name)
        name = "linked.csv"
    else:
        name = "fictional-private-marker"
    try:
        raise ValueError("fictional-private-marker")
    except ValueError:
        with pytest.raises(MappingDeclarationError) as caught:
            read_mapping_snapshot(root, name, max_bytes=limit, budget=GenerationBudget())
    assert str(caught.value) == "invalid mapping snapshot"
    assert caught.value.__context__ is None


def test_snapshot_rejects_parent_symlink(tmp_path):
    root = tmp_path.resolve()
    (root / "real").mkdir()
    (root / "real" / "map.csv").write_bytes(b"old,new\na,b\n")
    (root / "linked").symlink_to(root / "real", target_is_directory=True)
    with pytest.raises(MappingDeclarationError):
        read_mapping_snapshot(root, "linked/map.csv", max_bytes=100, budget=GenerationBudget())


def test_snapshot_does_not_reset_expired_budget(tmp_path):
    tick = [0.0]
    budget = GenerationBudget(max_seconds=1, clock=lambda: tick[0])
    tick[0] = 2.0
    with pytest.raises(MappingDeclarationError, match="^invalid mapping snapshot$"):
        read_mapping_snapshot(tmp_path.resolve(), "map.csv", max_bytes=100, budget=budget)


def test_snapshot_rejects_mutation_during_read(tmp_path):
    root = tmp_path.resolve()
    source = root / "map.csv"
    source.write_bytes(b"original")
    calls = [0]

    def clock():
        calls[0] += 1
        # Budget construction, entry, then first read: mutate after initial fstat.
        if calls[0] == 3:
            source.write_bytes(b"changed-length")
        return 0.0

    budget = GenerationBudget(max_seconds=1, clock=clock)
    with pytest.raises(MappingDeclarationError, match="^invalid mapping snapshot$"):
        read_mapping_snapshot(root, "map.csv", max_bytes=100, budget=budget)
