"""Closed local batch profile loader; references only, no source-row persistence."""
from pathlib import Path
import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Literal, TextIO

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS, GenerationBudget, GenerationLimitError
from test_data_agent.core.transformation_snapshot import SnapshotPart
from test_data_agent.core.transformation_limits import EffectiveInputLimit, InputDimension, TransformationInputLimits, TransformationLimitError, resolve_input_limit, resolve_profile_capture_limit
from test_data_agent.core.transformation_yaml import _load_private_yaml, load_behavior_policy_yaml
from test_data_agent.core.transformation_policy import BehaviorPolicy, transformation_schema_fingerprint
from test_data_agent.core.transformation_yaml import dump_behavior_policy_yaml
from test_data_agent.io.mapping_snapshot import read_mapping_snapshot
from test_data_agent.io.path_policy import atomic_write_bytes, make_staging_directory, publish_directory, discard_staging_directory
from test_data_agent.io.transformation_batch import TransformationBatch, TransformationBatchError, prepare_batch, review_batch
from test_data_agent.io.transformation_source import prepare_csv_review_request, _profile_transformation_csv


class BatchProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    entity: str = Field(min_length=1, max_length=256)
    source: str
    policy: str
    mappings: list[str] = Field(default_factory=list, max_length=DEFAULT_MAX_INPUT_COLUMNS)
    generation_policies: list[str] = Field(default_factory=list, max_length=DEFAULT_MAX_INPUT_COLUMNS)


class BatchProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    schema_version: Literal["0.1"]
    validation: str
    inputs: list[BatchProfileInput] = Field(min_length=2, max_length=DEFAULT_MAX_INPUT_COLUMNS)
    resource_limits: TransformationInputLimits | None = None

    @field_validator("resource_limits")
    @classmethod
    def require_supported_shared_limits(cls, value: TransformationInputLimits | None) -> TransformationInputLimits | None:
        if value is not None and value.model_fields_set - {"max_total_input_bytes", "max_output_bytes"}:
            raise ValueError("shared profile supports only total-input and output byte limits")
        return value


@contextmanager
def temporary_batch_profile(root: Path, profile: BatchProfile, *, max_total_bytes: int,
                            max_review_bytes: int, budget: GenerationBudget,
                            create_csv_policies: bool = False, seed: int | None = None,
                            _captured_query_sources: Mapping[str, SnapshotPart] | None = None,
                            _captured_query_policies: Mapping[str, bytes] | None = None
                            ) -> Iterator[tuple[Path, TransformationBatch]]:
    """Materialize explicit fictional candidate references; no user-file writes or approval."""
    valid = False
    try:
        # Exclude unset inherited limits: serializing their defaults would add
        # unsupported shared dimensions and silently change configuration identity.
        payload = profile.model_dump(mode="json", exclude_unset=True, warnings=False)
        profile = BatchProfile.model_validate(payload)
        profile_yaml = yaml.safe_dump(payload, sort_keys=True).encode()
        limit = EffectiveInputLimit(InputDimension.TOTAL_BYTES, max_total_bytes, "batch_input_run")
        resolve_input_limit(InputDimension.TOTAL_BYTES, profile.resource_limits, os.environ).check(
            max_total_bytes, requested=True)
        consumed = len(profile_yaml)
        limit.check(consumed)
        paths = [profile.validation]
        source_limits: dict[str, EffectiveInputLimit] = {}
        policy_paths = {Path(item.policy) for item in profile.inputs}
        for item in profile.inputs:
            paths.extend((item.source, *item.mappings, *item.generation_policies))
            if not create_csv_policies:
                paths.append(item.policy)
        if type(create_csv_policies) is not bool or create_csv_policies and (
                type(seed) is not int or len(policy_paths) != len(profile.inputs)
                or policy_paths.intersection(Path(path) for path in paths)
                or any(path.is_absolute() or ".." in path.parts or not path.parts
                       or path.parts[0] == "batch.yaml" for path in policy_paths)):
            raise ValueError
        captured: dict[str, bytes] = {}
        query_sources = dict(_captured_query_sources or {})
        query_policies = dict(_captured_query_policies or {})
        if set(query_sources) != set(query_policies):
            raise ValueError
        if create_csv_policies and query_sources:
            raise ValueError
        forbidden = {profile.validation, *(item.policy for item in profile.inputs),
                     *(path for item in profile.inputs for path in (*item.mappings, *item.generation_policies))}
        if set(query_sources) - {item.source for item in profile.inputs} or set(query_sources) & forbidden:
            raise ValueError
        for path in query_sources:
            relative = Path(path)
            if relative.is_absolute() or ".." in relative.parts or not relative.parts:
                raise ValueError
        # Existing policies determine each source ceiling before any source capture.
        if not create_csv_policies:
            for item in profile.inputs:
                if item.policy not in captured:
                    data = read_mapping_snapshot(root, item.policy, max_bytes=max_total_bytes,
                        budget=budget, total_limit=limit, consumed_bytes=consumed).payload
                    captured[item.policy] = data
                    consumed += len(data)
                policy = load_behavior_policy_yaml(captured[item.policy],
                    max_bytes=max_total_bytes, budget=budget)
                if item.source in query_sources:
                    source = query_sources[item.source]
                    if captured[item.policy] != query_policies[item.source]:
                        raise ValueError
                    if (type(source) is not SnapshotPart or source.kind != "source"
                            or source.name != item.entity
                            or policy.input_format not in {"postgres_query", "trino_query"}):
                        raise ValueError
                    from test_data_agent.io.transformation_query_snapshot import _query_result_payload
                    _query_result_payload(source.payload, policy.input_format)
                input_limit = resolve_input_limit(InputDimension.BYTES, policy.resource_limits, os.environ)
                previous = source_limits.get(item.source)
                if previous is None or input_limit.value < previous.value:
                    source_limits[item.source] = input_limit
        else:
            source_limits = {item.source: resolve_input_limit(InputDimension.BYTES, None, os.environ)
                             for item in profile.inputs}
        for path in dict.fromkeys(paths):
            if Path(path).parts and Path(path).parts[0] == "batch.yaml":
                raise ValueError
            if path in captured:
                if path in source_limits:
                    source_limits[path].check(len(captured[path]))
                continue
            if path in query_sources:
                data = query_sources[path].payload
                source_limits[path].check(len(data))
                consumed += len(data)
                limit.check(consumed)
                captured[path] = data
                continue
            snapshot = read_mapping_snapshot(root, path, max_bytes=max_total_bytes,
                budget=budget, total_limit=limit, consumed_bytes=consumed,
                input_limit=source_limits.get(path))
            captured[path] = snapshot.payload
            consumed += len(snapshot.payload)
        if create_csv_policies:
            for item in profile.inputs:
                source = SnapshotPart("source", item.entity, captured[item.source])
                evidence = _profile_transformation_csv(source, null_token=None,
                    max_bytes=max_total_bytes, budget=budget)
                draft = BehaviorPolicy.model_validate({"schema_version": "0.1", "seed": seed,
                    "schema_fingerprint": transformation_schema_fingerprint(evidence),
                    "fields": [{"entity": entity.name, "field": field.name,
                                "sensitivity": "unknown", "behavior": {"action": "drop"}}
                               for entity in evidence.entities for field in entity.fields]})
                data = dump_behavior_policy_yaml(draft, max_bytes=max_total_bytes, budget=budget)
                consumed += len(data)
                limit.check(consumed)
                captured[item.policy] = data
    except (GenerationLimitError, TransformationLimitError):
        raise
    except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError):
        pass
    else:
        valid = True
    if not valid:
        raise TransformationBatchError("invalid transformation batch profile") from None
    # All writes confined to an owned temporary root. Existing policy/source
    # writers deliberately replace files and are not create-only APIs.
    with TemporaryDirectory(prefix="apa-fictional-profile-") as temporary:
        candidate_root = Path(temporary).resolve()
        for path, data in captured.items():
            budget.check("batch profile materialization")
            atomic_write_bytes(candidate_root / path, data)
        atomic_write_bytes(candidate_root / "batch.yaml", profile_yaml)
        batch = load_batch_profile(candidate_root, "batch.yaml",
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget)
        yield candidate_root, batch


@contextmanager
def temporary_batch_decisions(root: Path, profile: BatchProfile, *,
                              input_stream: TextIO, output_stream: TextIO,
                              max_total_bytes: int, max_review_bytes: int,
                              budget: GenerationBudget, edit_actions: bool = False,
                              edit_formats: bool = False, create_csv_policies: bool = False,
                              seed: int | None = None
                              ) -> Iterator[tuple[Path, TransformationBatch]]:
    """Closed wizard over valid policy proposals; SAVE is never source approval."""
    from test_data_agent.io.transformation_decisions import _answer, edit_csv_policy_decisions

    if create_csv_policies and not edit_actions:
        raise TransformationBatchError("common profile creation requires explicit action decisions") from None
    with temporary_batch_profile(root, profile, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, budget=budget,
            create_csv_policies=create_csv_policies, seed=seed) as (candidate_root, _):
        completed: TransformationBatch | None = None
        try:
            if not input_stream.isatty() or not output_stream.isatty():
                raise ValueError
            saved = BatchProfile.model_validate(_load_private_yaml(
                (candidate_root / "batch.yaml").read_bytes(), max_total_bytes))
            for item in saved.inputs:
                budget.check("batch decision wizard")
                edit_csv_policy_decisions(candidate_root / item.source, item.entity,
                    candidate_root / item.policy, input_stream=input_stream,
                    output_stream=output_stream, max_total_bytes=max_total_bytes,
                    max_review_bytes=max_review_bytes, budget=budget,
                    edit_actions=edit_actions, edit_formats=edit_formats)
            updated = load_batch_profile(candidate_root, "batch.yaml",
                max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget)
            review = review_batch(updated, max_total_bytes=max_total_bytes,
                max_review_bytes=max_review_bytes, budget=budget)
            output_stream.write(review.decode("ascii") + "\n")
            if _answer(input_stream.fileno(), output_stream,
                      "Type SAVE for the common profile (not approval): ") != "SAVE":
                raise ValueError
            current = load_batch_profile(candidate_root, "batch.yaml",
                max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget)
            if current != updated:
                raise ValueError
            completed = current
        except (GenerationLimitError, TransformationLimitError):
            raise
        except (OSError, ValueError, TypeError, AttributeError, ImportError):
            pass
        if completed is None:
            raise TransformationBatchError("common profile decisions not saved") from None
        yield candidate_root, completed


def save_batch_profile(root: Path, relative_destination: str, batch: TransformationBatch, *,
                       max_total_bytes: int, max_review_bytes: int,
                       budget: GenerationBudget) -> TransformationBatch:
    """Closed configuration-only publication; source snapshots are never saved."""
    staging: Path | None = None
    saved: TransformationBatch | None = None
    try:
        path = Path(relative_destination)
        if not root.is_absolute() or path.is_absolute() or len(path.parts) != 1 or path.parts[0] in {".", ".."}:
            raise ValueError
        canonical = prepare_batch(batch.requests, batch.validation_yaml,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
            budget=budget, profile_yaml=batch.profile_yaml)
        if canonical != batch:
            raise ValueError
        profile = BatchProfile.model_validate(_load_private_yaml(batch.profile_yaml, max_total_bytes))
        payload = profile.model_dump(mode="json", exclude_unset=True, warnings=False)
        artifacts = {"validation.yaml": batch.validation_yaml}
        payload["validation"] = f"{path.as_posix()}/validation.yaml"
        external: dict[str, bytes] = {}
        for index, (item, request) in enumerate(zip(profile.inputs, batch.requests, strict=True)):
            source = next(part for part in request.parts if part.kind == "source")
            if source.name != item.entity:
                raise ValueError
            entries = [(item.source, source.payload)] + [
                (part.name, part.payload) for part in request.parts if part.kind in {"mapping", "generation_policy"}]
            for name, data in entries:
                if name in external and external[name] != data:
                    raise ValueError
                external[name] = data
            name = f"policy-{index}.yaml"
            artifacts[name] = next(part.payload for part in request.parts if part.kind == "policy")
            payload["inputs"][index]["policy"] = f"{path.as_posix()}/{name}"
        consumed = 0
        limit = EffectiveInputLimit(InputDimension.TOTAL_BYTES, max_total_bytes, "batch_input_run")
        for name, expected in external.items():
            captured = read_mapping_snapshot(root, name, max_bytes=min(max_total_bytes, len(expected)),
                budget=budget, total_limit=limit, consumed_bytes=consumed)
            consumed += len(captured.payload)
            if captured.payload != expected:
                raise ValueError
        profile_yaml = yaml.safe_dump(payload, sort_keys=True).encode()
        expected_batch = prepare_batch(batch.requests, batch.validation_yaml,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
            budget=budget, profile_yaml=profile_yaml)
        artifacts["batch.yaml"] = profile_yaml
        destination = root / path
        staging = make_staging_directory(destination)
        for name, data in artifacts.items():
            budget.check("batch profile publication")
            atomic_write_bytes(staging / name, data)
        publish_directory(staging, destination)
        current = load_batch_profile(root, f"{path.as_posix()}/batch.yaml",
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget)
        if current != expected_batch:
            raise ValueError
        saved = current
    except (GenerationLimitError, TransformationLimitError):
        raise
    except (OSError, ValueError, TypeError, AttributeError, StopIteration, yaml.YAMLError):
        pass
    finally:
        if staging is not None:
            discard_staging_directory(staging)
    if saved is None:
        raise TransformationBatchError("common profile not saved or requires revalidation") from None
    return saved


def capture_batch_profile(root: Path, relative_path: str, *, max_total_bytes: int,
                          budget: GenerationBudget) -> bytes:
    """Apply configured session ceilings before capturing or parsing a profile."""
    limit = resolve_profile_capture_limit(max_total_bytes, os.environ, run_origin="batch_input_run")
    return read_mapping_snapshot(root, relative_path, max_bytes=max_total_bytes,
        budget=budget, total_limit=limit).payload


def load_batch_profile(root: Path, relative_path: str, *, max_total_bytes: int,
                       max_review_bytes: int, budget: GenerationBudget) -> TransformationBatch:
    """Capture exact bounded local files once; reject traversal and symlinks."""
    try:
        limit = EffectiveInputLimit(InputDimension.TOTAL_BYTES, max_total_bytes, "batch_input_run")
        consumed = 0

        def read(path: str, input_limit: EffectiveInputLimit | None = None) -> bytes:
            nonlocal consumed
            budget.check("batch profile capture")
            payload = read_mapping_snapshot(root, path, max_bytes=max_total_bytes,
                budget=budget, total_limit=limit, consumed_bytes=consumed,
                input_limit=input_limit).payload
            consumed += len(payload)
            return payload

        profile_yaml = capture_batch_profile(root, relative_path,
            max_total_bytes=max_total_bytes, budget=budget)
        consumed = len(profile_yaml)
        profile = BatchProfile.model_validate(_load_private_yaml(profile_yaml, max_total_bytes))
        resolve_input_limit(InputDimension.TOTAL_BYTES, profile.resource_limits, os.environ).check(
            max_total_bytes, requested=True)
        validation = read(profile.validation)
        requests = []
        for item in profile.inputs:
            budget.check("batch profile input")
            policy = read(item.policy)
            parsed = load_behavior_policy_yaml(policy, max_bytes=max_total_bytes, budget=budget)
            input_limit = resolve_input_limit(InputDimension.BYTES, parsed.resource_limits, os.environ)
            source = SnapshotPart("source", item.entity, read(item.source, input_limit))
            mappings = tuple(SnapshotPart("mapping", path, read(path)) for path in item.mappings)
            generation = tuple(SnapshotPart("generation_policy", path, read(path))
                               for path in item.generation_policies)
            requests.append(prepare_csv_review_request(policy, source, mappings + generation,
                max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget))
        return prepare_batch(tuple(requests), validation, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, budget=budget, profile_yaml=profile_yaml)
    except (GenerationLimitError, TransformationLimitError):
        raise
    except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError):
        pass
    raise TransformationBatchError("invalid transformation batch profile") from None
