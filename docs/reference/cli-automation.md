# CLI Automation And JSON

Every core command accepts `--json`. Success writes one versioned
`CliSuccessResponse` to stdout and leaves stderr empty:

```json
{
  "schema_version": "1.0",
  "ok": true,
  "command": "test-data-agent demo",
  "exit_code": 0,
  "status": "succeeded",
  "artifacts": ["out/demo"],
  "result": null
}
```

Validation failures use the same envelope with exit code `1` and status
`validation_failed`. Artifact paths appear only after publication. Human
summaries and progress never share stdout with the JSON document.

`doctor --json` returns typed local statuses including `available`,
`not_installed`, `failed`, and `skipped`. A successful local smoke does not
claim that remote credentials or services are available.

## Agent JSON Contract

Use JSON output when invoking the review flow from automation:

```bash
test-data-agent agent-plan data/example_dataset --workspace out/agent --json
test-data-agent agent-review out/agent --json
test-data-agent agent-status out/agent --json
test-data-agent agent-approve out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256" --json
```

Planning and approval return an `AgentResult`; advisor request returns an
`AdvisorRequest` or `AdvisorExchange`; advisor apply and status return an
`AgentWorkspaceStatus`; review returns an `AgentReviewReport`. These versioned
contracts never include source or generated rows.

`AgentReviewReport` contains field metadata, relationships, privacy safety
flags, plan/current fingerprints, and `generation_performed: false`. It omits
distribution values. Completed results add an approval receipt tied to the
exact reviewed fingerprint.

Known failures also write one versioned JSON document to stdout when `--json`
is present:

```json
{
  "schema_version": "1.0",
  "ok": false,
  "error": {
    "code": "invalid_arguments",
    "message": "the following arguments are required: --workspace",
    "command": "test-data-agent agent-plan",
    "exit_code": 2,
    "retryable": false,
    "help": "test-data-agent agent-plan --help"
  }
}
```

Clients must branch on `error.code`, not message text. Stable codes and process
exit behavior are listed in [CLI Errors And Exit Codes](cli-errors.md).
