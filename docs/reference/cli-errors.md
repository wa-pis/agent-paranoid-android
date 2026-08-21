# CLI Errors And Exit Codes

Without `--json`, expected failures use concise stderr text and include a
recovery command when one is available. User-controlled values, provider
responses, source literals, and credentials are bounded or omitted.

| Code | Meaning |
| --- | --- |
| `0` | The command completed successfully. Running without a command also returns `0`. |
| `1` | Dataset validation failed. This can be intentional for negative datasets. |
| `2` | Arguments, input, paths, safety checks, resources, or configuration prevented completion. |
| `69` | An optional dependency or external service is unavailable. |
| `70` | An unexpected internal error occurred. Use `--debug` only when technical details are safe to display. |
| `74` | The operating system could not complete an I/O operation. |
| `130` | The user cancelled with Ctrl+C; catchable staging and rollback completed first. |

Stable JSON error codes are `invalid_arguments`, `input_not_found`,
`invalid_path`, `invalid_input`, `configuration`, `missing_dependency`,
`external_service`, `io_failure`, `internal_error`, and `cancelled`.

## Interrupted Agent Approval

Use `agent-status` to inspect a workspace without changing it. If approval was
interrupted after the generated bundle was committed, status reports
`recovery_required` and provides the exact recovery command:

```bash
test-data-agent agent-recover out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256"
```

Recovery revalidates the checkpoint, fingerprints, manifest, generated rows,
validation report, and source-row non-reuse before publishing missing
completion metadata. It never regenerates rows.

See [Troubleshooting](../operations/troubleshooting.md) for source-specific
diagnostics and recovery steps.
