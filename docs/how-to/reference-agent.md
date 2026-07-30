# Run The Reference Agent

[`examples/reference_agent.py`](https://github.com/wa-pis/agent-paranoid-android/blob/main/examples/reference_agent.py)
is a runnable application-layer example built only from the public Python API.
It demonstrates the complete review-first flow without a provider SDK,
credentials, or network access.

The included `BaselineAdvisorClient` is a deterministic safe stand-in. It
returns the baseline `DatasetSpec` unchanged. Replace only its `complete`
method with a provider-specific structured-output call described in the
[Advisor API](../reference/advisor.md).

To use the included OpenAI adapter instead, install only its optional extra:

```bash
python3 -m pip install "agent-paranoid-android[openai]"
export OPENAI_API_KEY="<read from your secret manager>"
```

Do not put the key in source files, command arguments, fixtures, logs, or
workspace artifacts.

## 1. Plan And Propose

From a repository checkout:

```bash
python3 examples/reference_agent.py plan \
  tests/fixtures/example_dataset \
  --workspace out/reference-agent \
  --count 25 \
  --seed 12345
```

For a real OpenAI proposal, add `--advisor openai`. The default model is
`gpt-5.6`; use `--model` to select another model available to your project:

```bash
python3 examples/reference_agent.py plan \
  tests/fixtures/example_dataset \
  --workspace out/openai-agent \
  --count 25 \
  --seed 12345 \
  --advisor openai
```

This profiles the source, builds a safe advisor exchange, persists the
validated proposal, and stops with:

```json
{
  "phase": "awaiting_approval",
  "approval_required": true,
  "next_action": "review_and_approve"
}
```

No `generated/` folder exists at this point.

## 2. Review

Inspect these files:

- `out/reference-agent/profile.json`: safe metadata, not source rows;
- `out/reference-agent/dataset_spec.yaml`: exact proposed generation contract;
- `out/reference-agent/advisor_review.json`: fingerprint-bound request and
  proposal.

Read the current fingerprint without changing the workspace:

```bash
python3 examples/reference_agent.py status out/reference-agent
```

Record `review.current_spec_sha256` only after reviewing
`dataset_spec.yaml`. If the spec changes, run `status` again and review the new
hash.

## 3. Approve And Generate

Pass the exact reviewed fingerprint:

```bash
python3 examples/reference_agent.py approve \
  out/reference-agent \
  --reviewed-spec-sha256 <review.current_spec_sha256>
```

A stale or different hash fails before generation. A successful approval runs
deterministic generation, validation, and source-row reuse checks. The
manifest reports:

```json
{
  "synthetic": true,
  "source_rows_copied": false
}
```

The example never auto-approves, sends source rows to a model, or returns
dataset rows in its JSON status output.

The OpenAI request uses separate developer and user roles for trusted policy
and untrusted metadata, requests a structured `AdvisorProposal`, sets
`store=False`, and rejects incomplete responses. The package validates the
proposal again before writing it to the workspace.
