# First CSV Dataset

This tutorial profiles one CSV file, infers a generation specification,
generates new values, and validates the result.

## Prerequisites

- complete [Installation](installation.md);
- run commands from a clone of this repository so the synthetic fixture below
  is available;
- choose a new output directory.

The fixture contains fictional values and reserved example email domains.

## Generate 25 Rows

```bash
test-data-agent generate-from-csv tests/fixtures/customers.csv \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

Expected summary:

```text
Generated synthetic dataset: out | rows: customers=25 | seed: 12345 | validation: passed | source rows copied: no
```

The exact output path shown in the summary can vary by platform.

## Inspect The Bundle

The command writes:

```text
out/
  customers.csv
  csv_profile.json
  dataset_spec.json
  generation_manifest.json
  validation_report.json
```

Check the manifest before using the data:

```bash
python3 -c "import json; m=json.load(open('out/generation_manifest.json')); print(m['synthetic'], m['source_rows_copied'], m['validation_valid'], m['seed'])"
```

Expected output:

```text
True False True 12345
```

Open `out/customers.csv` and confirm that it contains 25 generated rows plus
the header. Source rows are not shuffled or copied.

## Reproduce The Result

Generate into a different path with the same seed:

```bash
test-data-agent generate-from-csv tests/fixtures/customers.csv \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/repeated/customers.csv
```

The two generated CSV files should match:

```bash
python3 -c "from pathlib import Path; assert Path('out/customers.csv').read_bytes() == Path('out/repeated/customers.csv').read_bytes(); print('deterministic: ok')"
```

## Use Your Own CSV

Replace the fixture path with your file:

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

Treat every source CSV as potentially sensitive. Do not share its contents,
profile artifacts, or command logs until you have reviewed them. The profiler
suppresses raw values for fields detected as sensitive, but ambiguous domain
fields still require human review.

Next, read [Review The Output](review-output.md).
