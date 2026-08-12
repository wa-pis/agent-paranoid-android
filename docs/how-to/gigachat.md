# Use The GigaChat Advisor

GigaChat is an experimental, explicit advisor for the existing review-first
agent workflow. It can propose bounded `DatasetSpec` changes, but it cannot
profile a source, approve a spec, generate rows, write SQL, or access MCP.

The adapter uses the official `gigachat` Python SDK directly. GigaChain and
LangChain are not required for this single structured request.

!!! note "Release status"

    The adapter is included in stable `1.1.0` through the explicit `gigachat`
    extra.

## Install The Stable Release

Create an isolated environment and pin the exact stable release:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install "agent-paranoid-android[gigachat]==1.1.0"
test-data-agent doctor --require-extra gigachat
```

Doctor uses a local fake transport. It does not read credentials, obtain an
access token, or contact GigaChat.

## Configure Authentication

Choose exactly one authentication mode. Keep the value in a secret manager or
private process environment; never put it in a command argument, configuration
file, agent workspace, shell transcript, test fixture, or issue.

### Authorization Key

Use the authorization key from the GigaChat API project together with its
matching scope:

```bash
export GIGACHAT_CREDENTIALS='<authorization-key-from-secret-manager>'
export GIGACHAT_SCOPE='GIGACHAT_API_PERS'
unset GIGACHAT_ACCESS_TOKEN
```

Supported scopes are:

- `GIGACHAT_API_PERS` for individual access;
- `GIGACHAT_API_B2B` for prepaid business access;
- `GIGACHAT_API_CORP` for pay-as-you-go business access.

The SDK exchanges the authorization key for an access token in memory.

### Pre-Obtained Access Token

Alternatively, use one short-lived access token and no authorization key:

```bash
export GIGACHAT_ACCESS_TOKEN='<short-lived-access-token>'
export GIGACHAT_SCOPE='GIGACHAT_API_PERS'
unset GIGACHAT_CREDENTIALS
```

The official API documentation currently describes access tokens as valid for
30 minutes. Obtain a fresh test token immediately before a manual smoke; do not
send it through chat or commit it.

See the official
[authorization](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api)
and [SDK](https://developers.sber.ru/docs/ru/gigachat/guides/using-sdks)
documentation for account setup.

## Configure Certificate Trust

TLS verification is mandatory. The API and authorization endpoints are fixed
to the official HTTPS services and cannot be overridden. If the operating
system trust store does not contain the required CA certificates, point to a
reviewed readable PEM bundle:

```bash
export GIGACHAT_CA_BUNDLE_FILE='/absolute/path/to/trusted-ca-bundle.pem'
```

There is no insecure-disable option. Configuration such as
`GIGACHAT_VERIFY_SSL_CERTS=false`, a custom base URL, or a client certificate
fails locally before a provider request.

## Run The Synthetic Workflow

Use only the checked-in fictional fixture for the first call. Choose a new
workspace path for each run:

```bash
test-data-agent agent-plan tests/fixtures/example_dataset \
  --workspace out/gigachat-agent \
  --count 25 \
  --seed 12345 \
  --format csv

test-data-agent agent-review out/gigachat-agent
test-data-agent agent-advise out/gigachat-agent --provider gigachat
test-data-agent agent-review out/gigachat-agent
```

`agent-advise` makes one bounded external request. It writes a validated
`advisor_review.json` and proposed `dataset_spec.yaml`, then stops. It does not
create `generated/`.

Review the changed spec and record the new fingerprint printed by the second
`agent-review`. Only then approve deterministic local generation:

```bash
REVIEWED_SPEC_SHA256='<sha256-from-the-second-agent-review>'
test-data-agent agent-approve out/gigachat-agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256"
```

Use `--model MODEL` only for a reviewed provider model override. Omitting it
uses the adapter default, `GigaChat`.

After the run, remove secrets from the process environment:

```bash
unset GIGACHAT_CREDENTIALS GIGACHAT_ACCESS_TOKEN GIGACHAT_SCOPE
unset GIGACHAT_CA_BUNDLE_FILE
```

## Provider Boundary

GigaChat receives one non-streaming structured request containing:

- package-owned instructions in a system message;
- safe profile metadata and the baseline spec in a separate user message;
- the strict `AdvisorProposal` JSON Schema.

It does not receive source or generated rows, database credentials, exact
locally preserved category values, their reverse mappings, source free text,
or MCP responses. Exact approved local enums are replaced with field-scoped
synthetic labels before serialization. Entity and field names remain untrusted
metadata and may still reveal internal schema vocabulary, so treat the exchange
as confidential.

The default request ceilings are 4 MiB input, 1 MiB response content, 4,096
output tokens, 15 seconds per attempt, and no retries. The request disables
streaming and provider storage. Invalid, filtered, incomplete, oversized, or
schema-invalid output fails before the workspace changes.

GigaChat structured output is currently beta. When it emits schema defaults in
place of nested immutable values, the adapter may replace an identity-matched
invalid `dataset_spec` with the exact fingerprint-bound local baseline. No
provider-proposed dataset change survives that fallback. The result still must
pass the normal Pydantic, fingerprint, privacy, and advisor-contract checks
before a review is written; every other invalid response fails closed.

## Cost And Testing

A real `agent-advise` call consumes provider quota and may be billable. Normal
unit, package, doctor, and release tests use synthetic data and local fake
transports; they never require a GigaChat credential or network access. Run a
live smoke only as an explicit manual check with a disposable test credential
and the fictional fixture above.

For bounded error guidance, see [Troubleshooting](../operations/troubleshooting.md).
