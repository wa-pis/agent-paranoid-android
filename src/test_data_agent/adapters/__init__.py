"""Source adapters that normalize profiles and specs into DatasetProfile and DatasetSpec."""

from test_data_agent.adapters.csv_file import (
    csv_file_to_dataset_profile,
    csv_file_to_dataset_spec,
    csv_profile_to_dataset_profile,
    csv_profile_to_dataset_spec,
    dataset_profile_from_csv_file,
    dataset_spec_from_csv_file,
)
from test_data_agent.adapters.csv_folder import (
    csv_folder_to_dataset_profile,
    csv_folder_to_dataset_spec,
    dataset_profile_from_csv_folder,
    dataset_spec_from_csv_folder,
)
from test_data_agent.adapters.json_profile import (
    json_payload_to_dataset_profile,
    json_payload_to_dataset_spec,
    load_json_dataset_profile,
    load_json_dataset_spec,
    load_profile_or_spec,
)
from test_data_agent.adapters.legacy_generation import (
    generation_spec_to_dataset_spec,
    legacy_profile_to_dataset_profile,
    legacy_profile_to_dataset_spec,
    multi_table_generation_spec_to_dataset_spec,
)
from test_data_agent.adapters.parquet_dataset import (
    dataset_profile_from_parquet,
    dataset_spec_from_parquet,
    parquet_file_to_dataset_profile,
    parquet_file_to_dataset_spec,
)
from test_data_agent.adapters.trino_profile import (
    dataset_profile_from_trino_profile,
    dataset_spec_from_trino_profile,
    trino_profile_to_dataset_profile,
    trino_profile_to_dataset_spec,
)

__all__ = [
    "csv_file_to_dataset_profile",
    "csv_file_to_dataset_spec",
    "csv_folder_to_dataset_profile",
    "csv_folder_to_dataset_spec",
    "csv_profile_to_dataset_profile",
    "csv_profile_to_dataset_spec",
    "dataset_profile_from_csv_file",
    "dataset_profile_from_csv_folder",
    "dataset_profile_from_parquet",
    "dataset_profile_from_trino_profile",
    "dataset_spec_from_csv_file",
    "dataset_spec_from_csv_folder",
    "dataset_spec_from_parquet",
    "dataset_spec_from_trino_profile",
    "generation_spec_to_dataset_spec",
    "json_payload_to_dataset_profile",
    "json_payload_to_dataset_spec",
    "legacy_profile_to_dataset_profile",
    "legacy_profile_to_dataset_spec",
    "load_json_dataset_profile",
    "load_json_dataset_spec",
    "load_profile_or_spec",
    "multi_table_generation_spec_to_dataset_spec",
    "parquet_file_to_dataset_profile",
    "parquet_file_to_dataset_spec",
    "trino_profile_to_dataset_profile",
    "trino_profile_to_dataset_spec",
]
