"""Offline forecast accuracy and streamed revalidation, using fictional specs only."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from dataset_scale import fixture
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.execution_policy import GenerationExecutionPolicy
from test_data_agent.io.capacity import estimate_dataset_capacity
from test_data_agent.io.scalable_validation import validate_scalable_bundle
from test_data_agent.io.workflows import generate_dataset_bundle


def typed_fixture(count: int) -> DatasetSpec:
    return DatasetSpec.model_validate({
        'schema_version': '1.1',
        'entities': [{'name': 'typed_items', 'row_count': count, 'primary_key': 'synthetic_key', 'fields': [
            {'name': 'synthetic_key', 'data_type': 'integer', 'is_identifier': True},
            {'name': 'amount', 'data_type': 'decimal', 'semantic_type': 'numeric_measure',
             'distribution': {'kind': 'decimal_range', 'precision': 8, 'scale': 2, 'min': '-10.00', 'max': '25.00'}},
            {'name': 'day', 'data_type': 'date',
             'distribution': {'kind': 'date_range', 'min': '2024-01-01', 'max': '2025-01-01'}},
            {'name': 'instant', 'data_type': 'datetime', 'nullable': True, 'null_ratio': .25,
             'distribution': {'kind': 'datetime_range', 'min': '2024-01-01T00:00:00', 'max': '2025-01-01T00:00:00'}},
            {'name': 'label', 'data_type': 'string', 'distribution': {'kind': 'categorical', 'categories': [
                {'value': 'синий, "квадрат"\n', 'count': 3}, {'value': '緑色', 'count': 1}]}},
            {'name': 'long_text', 'data_type': 'string', 'nullable': True, 'null_ratio': .1,
             'distribution': {'kind': 'string_pattern', 'min_length': 80, 'max_length': 120}},
        ]}], 'generation_settings': {'seed': 42}})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, default=10000)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--large-validation', action='store_true')
    parser.add_argument('--legacy', action='store_true')
    args = parser.parse_args()
    if not 10000 <= args.count <= 750000:
        parser.error('rows must be between 10000 and 750000')
    records = []
    cases = [('simple', fixture), ('typed', typed_fixture)]
    for name, build in cases:
        for fmt in ('csv', 'json', 'parquet'):
            data = build(args.count)
            data.generation_settings.output_format = fmt
            if not args.legacy:
                data.generation_settings.execution_policy = GenerationExecutionPolicy(workers=4)
            with tempfile.TemporaryDirectory(prefix='apa-capacity-accuracy-') as temporary:
                root = Path(temporary).resolve()
                forecast = estimate_dataset_capacity(data, calibrate=True, workspace=root, use_cache=False)
                output = root/'generated'
                started = time.monotonic()
                generate_dataset_bundle(data, output_folder=output)
                seconds = time.monotonic()-started
                actual_bytes = sum((output/f'{entity.name}.{fmt}').stat().st_size for entity in data.entities)
                assert forecast.duration_seconds is not None
                size_error = abs(forecast.file_bytes.expected-actual_bytes)/actual_bytes
                time_error = abs(forecast.duration_seconds.expected-seconds)/seconds
                within = (forecast.file_bytes.low <= actual_bytes <= forecast.file_bytes.high
                          and forecast.duration_seconds.low <= seconds <= forecast.duration_seconds.high)
                validate_started = time.monotonic()
                if args.legacy:
                    from test_data_agent.io.commands import validate_dataset_artifacts
                    assert validate_dataset_artifacts(output/'dataset_spec.yaml', output).valid
                else:
                    assert validate_scalable_bundle(data, output).valid
                record = {'case': name, 'format': fmt, 'rows': args.count, 'engine': 'legacy' if args.legacy else 'scalable-v1',
                    'file_bytes': actual_bytes, 'seconds': seconds,
                    'streamed_revalidation_seconds': time.monotonic()-validate_started,
                    'forecast_bytes': forecast.file_bytes.model_dump(),
                    'forecast_seconds': forecast.duration_seconds.model_dump(),
                    'size_relative_error': size_error, 'time_relative_error': time_error,
                    'within_bounds': within,
                    'accepted': within and size_error <= (.4 if fmt == 'parquet' else .25) and time_error <= .4}
                records.append(record)
                args.result.write_text(json.dumps(records, indent=2)+'\n')
                print(json.dumps(record), flush=True)
    if args.large_validation:
        data = fixture(750000)
        data.generation_settings.execution_policy = GenerationExecutionPolicy(workers=4)
        with tempfile.TemporaryDirectory(prefix='apa-large-validation-') as temporary:
            output = Path(temporary).resolve()/'generated'
            generate_dataset_bundle(data, output_folder=output)
            started = time.monotonic()
            assert validate_scalable_bundle(data, output).valid
            records.append({'case': 'large_streamed_validation', 'rows': 750000, 'columns': 25,
                'seconds': time.monotonic()-started, 'distinct_synthetic_keys_verified': True})
            args.result.write_text(json.dumps(records, indent=2)+'\n')
            print(json.dumps(records[-1]), flush=True)
    if not all(record['accepted'] for record in records if 'accepted' in record):
        raise SystemExit('forecast accuracy target unmet; see numeric evidence')


if __name__ == '__main__':
    main()
