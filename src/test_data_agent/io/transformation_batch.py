"""Closed fictional multi-input candidate; no public registration or publication.

Preservation requires a verified common TTY receipt, never inherited individual
receipts. All results remain private until validation; no public registration.
"""
import hashlib
import hmac
import json
import os
from typing import Any
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory

from test_data_agent.core.limits import DEFAULT_MAX_INPUT_COLUMNS, GenerationBudget, GenerationLimitError
from test_data_agent.core.transformation_approval import ApprovalRequest
from test_data_agent.core.transformation_csv import normalize_csv_scalar
from test_data_agent.csv_profiler import validate_csv_headers
from test_data_agent.core.transformation_mapping import CsvMapping, DomainMapping
from test_data_agent.core.dataset import DatasetProfile
from test_data_agent.core.transformation_limits import InputDimension, TransformationLimitError, resolve_input_limit
from test_data_agent.core.transformation_policy import ParquetOutput, SqlOutput, PreserveAction, ReplaceTextAction, SubstituteAction, SynthesizeAction
from test_data_agent.core.transformation_yaml import _load_private_yaml, load_behavior_policy_yaml, load_generation_policy_yaml
from test_data_agent.io.transformation_execute import CsvTransformationResult, _replace_csv_snapshot
from test_data_agent.io.transformation_input import source_reader
from test_data_agent.io.transformation_parquet import render_transformation_parquet
from test_data_agent.io.transformation_sql import render_transformation_sql
from test_data_agent.io.transformation_receipt import _canonical_request
from test_data_agent.io.path_policy import atomic_write_bytes, make_staging_directory, publish_directory
from test_data_agent.validation.constraint_validator import validate_constraints
from test_data_agent.validation.relationship_validator import validate_relationships
from test_data_agent.validation.schema_validator import validate_schema


class TransformationBatchError(ValueError):
    """Detached value-free batch failure; no partial result is returned."""


@dataclass(frozen=True, repr=False)
class TransformationBatch:
    requests: tuple[ApprovalRequest, ...] = field(repr=False)
    validation_yaml: bytes = field(repr=False)
    snapshot_sha256: str
    profile_yaml: bytes = field(default=b"", repr=False)


def prepare_batch(requests: tuple[ApprovalRequest, ...], validation_yaml: bytes, *,
                  max_total_bytes: int, max_review_bytes: int,
                  budget: GenerationBudget, profile_yaml: bytes = b"") -> TransformationBatch:
    """Bind exact per-input canonical identities and final validation bytes."""
    try:
        budget.check("transformation batch preparation")
        if type(requests) is not tuple or not 2 <= len(requests) <= DEFAULT_MAX_INPUT_COLUMNS:
            raise ValueError
        if (type(validation_yaml) is not bytes or type(profile_yaml) is not bytes
                or type(max_total_bytes) is not int or max_total_bytes < 1):
            raise ValueError
        total = len(validation_yaml) + len(profile_yaml) + sum(len(part.payload) for request in requests
                                          for part in request.parts)
        if total > max_total_bytes:
            raise TransformationLimitError(InputDimension.TOTAL_BYTES, total,
                max_total_bytes, "batch_input_run")
        # Local import avoids the profile loader's preparation dependency cycle.
        from test_data_agent.io.transformation_batch_profile import BatchProfile
        profile = (BatchProfile.model_validate(_load_private_yaml(profile_yaml, max_total_bytes))
                   if profile_yaml else None)
        resolve_input_limit(InputDimension.TOTAL_BYTES,
            profile.resource_limits if profile else None, os.environ).check(max_total_bytes, requested=True)
        canonical = tuple(_canonical_request(request, max_total_bytes=max_total_bytes,
            max_review_bytes=max_review_bytes, budget=budget) for request in requests)
        spec = load_generation_policy_yaml(validation_yaml, max_bytes=max_total_bytes, budget=budget)
        names = [next(part.name for part in request.parts if part.kind == "source")
                 for request in canonical]
        if len(set(names)) != len(names) or set(names) != {entity.name for entity in spec.entities}:
            raise ValueError
        # Artifact indices follow request order, so confirmation must bind it too.
        material = json.dumps({"version": 1, "inputs": list(zip(names,
            (request.snapshot_sha256 for request in canonical), strict=True)),
            "validation": hashlib.sha256(validation_yaml).hexdigest(),
            "profile": hashlib.sha256(profile_yaml).hexdigest()},
            sort_keys=True, separators=(",", ":")).encode()
        return TransformationBatch(canonical, validation_yaml,
            hashlib.sha256(b"transformation-batch-v1\0" + material).hexdigest(), profile_yaml)
    except (TransformationLimitError, GenerationLimitError):
        raise
    except (ValueError, TypeError, AttributeError, StopIteration):
        pass
    raise TransformationBatchError("invalid transformation batch") from None


def execute_batch(batch: TransformationBatch, *, expected_snapshot_sha256: str,
                  max_total_bytes: int, max_review_bytes: int, max_output_bytes: int,
                  budget: GenerationBudget, receipt_path: Path | None = None) -> tuple[CsvTransformationResult, ...]:
    """Validate linked final rows before returning any candidate output."""
    try:
        canonical = prepare_batch(batch.requests, batch.validation_yaml,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget,
            profile_yaml=batch.profile_yaml)
        if not hmac.compare_digest(canonical.snapshot_sha256, expected_snapshot_sha256):
            raise ValueError
        if receipt_path is not None:
            from test_data_agent.io.transformation_batch_receipt import verify_batch_receipt
            verify_batch_receipt(canonical, receipt_path, max_total_bytes=max_total_bytes,
                                 max_review_bytes=max_review_bytes, budget=budget)
        if type(max_output_bytes) is not int or max_output_bytes < 1:
            raise ValueError
        from test_data_agent.io.transformation_batch_profile import BatchProfile
        profile_settings = (BatchProfile.model_validate(_load_private_yaml(canonical.profile_yaml, max_total_bytes))
                            if canonical.profile_yaml else None)
        resolve_input_limit(InputDimension.OUTPUT_BYTES,
            profile_settings.resource_limits if profile_settings else None, os.environ).check(
                max_output_bytes, requested=True)
        spec = load_generation_policy_yaml(canonical.validation_yaml,
            max_bytes=max_total_bytes, budget=budget)
        domains: dict[str, tuple[str, list[tuple[str, str]]]] = {}
        domain_arities: dict[str, int] = {}
        component_types: dict[tuple[str, int | None], tuple[str, str | None, str | None]] = {}
        bindings = {}
        for request in canonical.requests:
            budget.check("transformation batch preflight")
            policy = load_behavior_policy_yaml(next(part.payload for part in request.parts
                if part.kind == "policy"), max_bytes=max_total_bytes, budget=budget)
            profile = DatasetProfile.model_validate_json(next(part.payload for part in request.parts
                if part.kind == "evidence"))
            field_types = {(entity.name, item.name): item.data_type.value
                           for entity in profile.entities for item in entity.fields}
            for domain in policy.domains:
                # Compare only this domain's concrete CSV, not unrelated field maps.
                mapping_parts = sorted((part.name, hashlib.sha256(part.payload).hexdigest())
                    for part in request.parts if part.kind == "mapping"
                    and isinstance(domain.mapping, CsvMapping) and part.name == domain.mapping.path)
                identity = (domain.mapping.model_dump_json(), mapping_parts)
                if domain.name in domains and domains[domain.name] != identity:
                    raise ValueError
                domains[domain.name] = identity
                domain_arities[domain.name] = (len(domain.mapping.source_columns)
                    if isinstance(domain.mapping, CsvMapping) else len(domain.mapping.entries[0].original))
            for decision in policy.fields:
                action = decision.behavior
                if isinstance(action, (SynthesizeAction, PreserveAction)):
                # Independent actions retain existing synthesis/preservation gates.
                    continue
                if not isinstance(action, (SubstituteAction, ReplaceTextAction)):
                    raise ValueError
                # Source-free fallback still passes unconditional final FK checks.
                # Preservation requires the verified common receipt at execution.
                if action.unmatched.action != "reject" and not isinstance(action.unmatched, (SynthesizeAction, PreserveAction)):
                    raise ValueError
                # Unlinked fields reuse the existing inline/CSV/literal engine.
                # Relationship fields must still resolve to a common domain below.
                if not isinstance(action.mapping, DomainMapping):
                    continue
                component = (action.mapping.name, action.mapping.component)
                signature = (field_types[(decision.entity, decision.field)],
                    decision.decimal_type.model_dump_json() if decision.decimal_type else None,
                    decision.temporal_type.model_dump_json() if decision.temporal_type else None)
                if component in component_types and component_types[component] != signature:
                    raise ValueError
                component_types[component] = signature
                bindings[(decision.entity, decision.field)] = component
        composite_links: dict[tuple[str, str, str], dict[int, tuple[str, str]]] = {}
        composite_types: dict[tuple[str, str, str], str] = {}
        scalar_relationships = []
        for relationship in spec.relationships:
            if relationship.status == "rejected":
                continue
            parent = bindings[(relationship.parent_entity, relationship.parent_field)]
            child = bindings[(relationship.child_entity, relationship.child_field)]
            if parent != child:
                raise ValueError
            if domain_arities[parent[0]] == 1:
                scalar_relationships.append(relationship)
                continue
            key = (relationship.parent_entity, relationship.child_entity, parent[0])
            component_index = parent[1]
            if component_index is None or component_index in composite_links.setdefault(key, {}):
                raise ValueError
            relationship_type = relationship.relationship_type.value
            if key in composite_types and composite_types[key] != relationship_type:
                raise ValueError
            composite_types[key] = relationship_type
            composite_links[key][component_index] = (relationship.parent_field, relationship.child_field)
        for key, components in composite_links.items():
            if set(components) != set(range(domain_arities[key[2]])):
                raise ValueError
        results = []
        rows_by_entity: dict[str, list[dict[str, Any]]] = {}
        remaining = max_output_bytes
        entities = {entity.name: entity for entity in spec.entities}
        for request in canonical.requests:
            budget.check("transformation batch execution")
            if remaining < 1:
                raise TransformationLimitError(InputDimension.OUTPUT_BYTES,
                    max_output_bytes + 1, max_output_bytes, "batch_output_run")
            try:
                result = _replace_csv_snapshot(request, max_total_bytes=max_total_bytes,
                    max_review_bytes=max_review_bytes, max_output_bytes=remaining, budget=budget,
                    batch_receipt=(canonical, receipt_path) if receipt_path is not None else None)
            except TransformationLimitError as error:
                # Report the shared run counter, not this input's remaining slice.
                # Session/profile ceiling diagnostics retain their own identity.
                if error.origin != "output_run":
                    raise
                raise TransformationLimitError(InputDimension.OUTPUT_BYTES,
                    max_output_bytes - remaining + error.amount,
                    max_output_bytes, "batch_output_run") from None
            remaining -= len(result.csv_bytes)
            name = next(part.name for part in request.parts if part.kind == "source")
            types = {item.name: item.data_type for item in entities[name].fields}
            rows_by_entity[name] = []
            for row in result.rows:
                budget.check("transformation batch final row")
                rows_by_entity[name].append({column: None if value is None else
                    normalize_csv_scalar(value, types[column])
                    for column, value in zip(result.columns, row, strict=True)})
            results.append(result)
        budget.check("transformation batch validation")
        for key, components in composite_links.items():
            parent_entity, child_entity, _ = key
            ordered = [components[index] for index in range(len(components))]
            parents = set()
            for parent_row in rows_by_entity[parent_entity]:
                budget.check("transformation composite parent")
                values = tuple(parent_row[field] for field, _ in ordered)
                # Closed non-null tuple acceptance; no new implicit null equivalence.
                if None in values or values in parents:
                    raise ValueError
                parents.add(values)
            children = set()
            for child_row in rows_by_entity[child_entity]:
                budget.check("transformation composite child")
                values = tuple(child_row[field] for _, field in ordered)
                if None in values or values not in parents:
                    raise ValueError
                if composite_types[key] == "one_to_one" and values in children:
                    raise ValueError
                children.add(values)
        scalar_spec = spec.model_copy(update={"relationships": scalar_relationships})
        if (validate_schema(rows_by_entity, spec) or validate_relationships(rows_by_entity, scalar_spec)
                or validate_constraints(rows_by_entity, spec)):
            raise ValueError
        budget.check("transformation batch complete")
        return tuple(results)
    except (TransformationLimitError, GenerationLimitError):
        raise
    except (ValueError, TypeError, AttributeError, KeyError, StopIteration):
        pass
    raise TransformationBatchError("invalid transformation batch") from None


def review_batch(batch: TransformationBatch, *, max_total_bytes: int,
                 max_review_bytes: int, budget: GenerationBudget) -> bytes:
    """Bounded value-free common review; never approval or execution authority."""
    try:
        canonical = prepare_batch(batch.requests, batch.validation_yaml,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes, budget=budget,
            profile_yaml=batch.profile_yaml)
        if not hmac.compare_digest(batch.snapshot_sha256, canonical.snapshot_sha256):
            raise ValueError
        spec = load_generation_policy_yaml(canonical.validation_yaml,
            max_bytes=max_total_bytes, budget=budget)
        input_indices = {next(part.name for part in request.parts if part.kind == "source"): index
                         for index, request in enumerate(canonical.requests)}
        payload = json.dumps({"schema_version": "0.1", "status": "review_only",
            "snapshot_sha256": canonical.snapshot_sha256,
            "input_count": len(canonical.requests), "relationship_count": len(spec.relationships),
            "approved": False, "preservation_supported": True,
            "public_execution_supported": False,
            "linked_domain_semantics": "ordered_tuple",
            "inputs": [{"index": index, "snapshot_sha256": request.snapshot_sha256,
                        "local_plan": json.loads(request.review)}
                       for index, request in enumerate(canonical.requests)],
            "relationships": [{"parent_input": input_indices[item.parent_entity],
                "parent_field": item.parent_field, "child_input": input_indices[item.child_entity],
                "child_field": item.child_field} for item in spec.relationships]},
            sort_keys=True, separators=(",", ":")).encode()
        if type(max_review_bytes) is not int or len(payload) > max_review_bytes:
            raise ValueError
        budget.check("transformation batch review")
        return payload
    except (TransformationLimitError, GenerationLimitError):
        raise
    except (ValueError, TypeError, AttributeError):
        pass
    raise TransformationBatchError("invalid transformation batch review") from None


@contextmanager
def temporary_batch_publication(batch: TransformationBatch, *, expected_snapshot_sha256: str,
                                max_total_bytes: int, max_review_bytes: int,
                                max_output_bytes: int, budget: GenerationBudget,
                                receipt_path: Path | None = None) -> Iterator[Path]:
    """Fictional isolated acceptance only; validate before one directory rename."""
    results = execute_batch(batch, expected_snapshot_sha256=expected_snapshot_sha256,
        max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
        max_output_bytes=max_output_bytes, budget=budget, receipt_path=receipt_path)
    if any(result.provenance is None for result in results):
        raise TransformationBatchError("invalid transformation batch") from None
    artifacts = []
    remaining = max_output_bytes
    for index, (request, result) in enumerate(zip(batch.requests, results, strict=True)):
        budget.check("transformation batch output")
        policy = load_behavior_policy_yaml(next(part.payload for part in request.parts
            if part.kind == "policy"), max_bytes=max_total_bytes, budget=budget)
        payload, suffix = result.csv_bytes, "csv"
        if isinstance(policy.output, (SqlOutput, ParquetOutput)):
            source = next(part for part in request.parts if part.kind == "source")
            reader = source_reader(source, policy, budget=budget)
            reader.fieldnames = validate_csv_headers(reader.fieldnames)
            originals = (tuple(None if row[name] == policy.csv_nulls.input_token else row[name]
                               for name in result.columns) for row in reader)
            if tuple(reader.fieldnames) != result.columns:
                raise TransformationBatchError("invalid transformation batch output") from None
            if remaining < 1:
                raise TransformationLimitError(InputDimension.OUTPUT_BYTES,
                    max_output_bytes + 1, max_output_bytes, "batch_bundle_run")
            try:
                if isinstance(policy.output, SqlOutput):
                    payload = render_transformation_sql(result, policy.output,
                        max_bytes=remaining, budget=budget, source_rows=originals)
                    suffix = "sql"
                else:
                    payload = render_transformation_parquet(result, policy.output,
                        max_bytes=remaining, budget=budget, source_rows=originals)
                    suffix = "parquet"
            except TransformationLimitError as error:
                raise TransformationLimitError(InputDimension.OUTPUT_BYTES,
                    max_output_bytes - remaining + error.amount,
                    max_output_bytes, "batch_bundle_run") from None
            except GenerationLimitError:
                raise
            except (ValueError, TypeError, OverflowError):
                raise TransformationBatchError("invalid transformation batch output") from None
        remaining -= len(payload)
        artifacts.append((f"input-{index}.{suffix}", payload))
    manifest = json.dumps({"schema_version": "0.1", "status": "closed_batch_completed",
        "snapshot_sha256": expected_snapshot_sha256,
        "origin": "transformed_mixed",
        "privacy_notice": "Mixed-origin output may retain source information; not anonymized.",
        "provenance": [asdict(result.provenance) for result in results if result.provenance is not None],
        "artifacts": [name for name, _ in artifacts]},
        sort_keys=True).encode()
    size = len(manifest) + sum(len(payload) for _, payload in artifacts)
    if size > max_output_bytes:
        raise TransformationLimitError(InputDimension.OUTPUT_BYTES, size,
            max_output_bytes, "batch_bundle_run")
    # No caller-controlled destination or retained artifact in this closed adapter.
    with TemporaryDirectory(prefix="apa-fictional-batch-") as temporary:
        destination = Path(temporary).resolve() / "bundle"
        staging = make_staging_directory(destination)
        for name, payload in artifacts:
            budget.check("transformation batch publication")
            atomic_write_bytes(staging / name, payload)
        atomic_write_bytes(staging / "manifest.json", manifest)
        budget.check("transformation batch publication")
        publish_directory(staging, destination)
        yield destination


def _publish_retained_test_batch(batch: TransformationBatch, destination: Path, *,
                                expected_snapshot_sha256: str, max_total_bytes: int,
                                max_review_bytes: int, max_output_bytes: int,
                                budget: GenerationBudget, receipt_path: Path | None = None) -> bytes:
    """Unregistered fictional retained-output candidate; return value-free manifest only."""
    from test_data_agent.io.path_policy import open_regular_file
    from test_data_agent.io.transformation_publish import _publish_test_artifacts

    with temporary_batch_publication(batch, expected_snapshot_sha256=expected_snapshot_sha256,
            max_total_bytes=max_total_bytes, max_review_bytes=max_review_bytes,
            max_output_bytes=max_output_bytes, budget=budget, receipt_path=receipt_path) as bundle:
        artifacts = []
        consumed = 0
        for path in sorted(bundle.iterdir()):
            budget.check("transformation batch retained publication")
            with open_regular_file(path) as handle:
                payload = handle.read(max_output_bytes - consumed + 1)
            consumed += len(payload)
            if consumed > max_output_bytes:
                raise TransformationLimitError(InputDimension.OUTPUT_BYTES, consumed,
                    max_output_bytes, "batch_bundle_run")
            artifacts.append((path.name, payload))
        manifest = next(payload for name, payload in artifacts if name == "manifest.json")
        _publish_test_artifacts(destination, tuple(artifacts), budget,
                                max_output_bytes=max_output_bytes)
    return manifest
