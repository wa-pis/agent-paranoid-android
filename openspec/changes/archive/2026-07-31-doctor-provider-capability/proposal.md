# Change: doctor-provider-capability

## Why

Importing a provider SDK does not prove that the installed version exposes the
structured response surface required by the bundled advisor adapter.

## What Changes

- Construct and close a local OpenAI SDK client with a non-secret placeholder.
- Verify the structured Responses API and advisor adapter construction.
- Redact failures and provide exact provider-extra reinstall guidance.
- Run the smoke from the isolated OpenAI wheel profile in CI.

## Impact

`doctor --require-extra openai` performs an in-process SDK and adapter check
unless `--skip-smoke` is supplied. It does not read credentials or contact the
provider.
