Generate synthetic test data based on a CSV file.

Source:

* input CSV: {input_csv_path}

Requirements:

* row count: {count}
* output format: {csv/json/parquet/sql}
* mode: {valid/mixed/negative/edge/load_test}
* invalid ratio: {invalid_ratio}
* seed: {seed}
* preserve approximate distributions: yes
* include edge cases: yes
* copy source rows: no
* expose PII: no

Use the CSV only for schema inference, aggregate profiling, safe distributions, and masked patterns. Generate fully synthetic data. Validate the output and return:

* CSV profile
* generation specification
* generated dataset
* validation report
