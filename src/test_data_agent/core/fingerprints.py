"""Canonical metadata fingerprints shared by services and adapters."""

import hashlib
import json

from pydantic import BaseModel

from test_data_agent.core.dataset import DatasetProfile, DatasetSpec


def model_fingerprint(model: BaseModel) -> str:
    payload = model.model_dump(mode="json")

    # Compatibility: keep previous fingerprints stable for persisted contracts when
    # the newly added local_category_fields feature is absent from external payloads.
    if isinstance(model, (DatasetProfile, DatasetSpec)):
        payload = dict(payload)
        if payload.get("local_category_fields", None) == []:
            payload.pop("local_category_fields", None)
    if isinstance(model, DatasetProfile):
        if payload.get("has_unmodeled_expressions") is None:
            payload.pop("has_unmodeled_expressions", None)
        # Unspecified carries no new evidence; preserve pre-metadata plan hashes.
        for entity in payload["entities"]:
            for field in entity["fields"]:
                if field.get("unique_ratio_kind") == "unspecified":
                    field.pop("unique_ratio_kind")

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(canonical).hexdigest()

