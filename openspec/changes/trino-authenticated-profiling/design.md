# Design

Existing implementation: `trino_auth.py`, `trino_config.py`, connection adapters,
`tests/test_trino_auth.py` and `tests/test_trino_oauth_cli.py`. Start by verifying
these paths. The following invariants apply to any demonstrated gap; they are
not a proposal to replace or narrow the existing supported methods.

Keep public configuration serializable without credentials. Prefer a separate
injected credential provider/auth object with repr disabled, rather than adding a
printable password field to the existing dataclass. Environment parsing must
reject partial mode/user/password settings and credential-bearing URLs.

Create the driver's auth object at the connection boundary. Require HTTPS and
verified certificates for basic auth, including trusted-local deployments;
existing insecure overrides must not permit sending a password over HTTP.

Classify failures from known typed driver/status data, never by returning or
parsing arbitrary backend messages. Detach original exceptions where user-facing
errors cross boundaries. Apply the same factory to query profiling and MCP.
