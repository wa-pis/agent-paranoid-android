"""Source adapters that normalize profiles and specs into DatasetProfile and DatasetSpec."""

from test_data_agent.adapters.csv_file import (
    csv_file_to_dataset_profile,
    csv_file_to_dataset_spec,
    csv_profile_to_dataset_profile,
    csv_profile_to_dataset_spec,
)
from test_data_agent.adapters.json_profile import (
    json_payload_to_dataset_profile,
    json_payload_to_dataset_spec,
    load_json_dataset_profile,
    load_json_dataset_spec,
)
from test_data_agent.adapters.legacy_generation import (
    generation_spec_to_dataset_spec,
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
    multi_table_generation_spec_to_dataset_spec,
)
from test_data_agent.adapters.parquet_dataset import (
    parquet_file_to_dataset_profile,
    parquet_file_to_dataset_spec,
)
from test_data_agent.adapters.trino_profile import (
    trino_profile_to_dataset_profile,
    trino_profile_to_dataset_spec,
)

__all__ = [
    "csv_file_to_dataset_profile",
    "csv_file_to_dataset_spec",
    "csv_profile_to_dataset_profile",
    "csv_profile_to_dataset_spec",
    "generation_spec_to_dataset_spec",
    "json_payload_to_dataset_profile",
    "json_payload_to_dataset_spec",
    "legacy_profile_to_dataset_profile",
    "legacy_profile_to_dataset_spec",
    "load_json_dataset_profile",
    "load_json_dataset_spec",
    "multi_table_generation_spec_to_dataset_spec",
    "parquet_file_to_dataset_profile",
    "parquet_file_to_dataset_spec",
    "trino_profile_to_dataset_profile",
    "trino_profile_to_dataset_spec",
]
