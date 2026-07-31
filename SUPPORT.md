# Support

Agent Paranoid Android is maintained on a best-effort basis. The supported
runtimes, optional extras, and compatibility commitments are documented in the
[runtime and integration support policy](docs/reference/support-policy.md).

## Where To Ask

- Use GitHub Issues for reproducible bugs and focused feature requests.
- Use the documentation and `test-data-agent doctor` for installation and
  optional-extra diagnostics.
- Use the private process in [SECURITY.md](SECURITY.md) for vulnerabilities,
  unsafe data disclosure, unrestricted SQL, or secret exposure.

Include the package version, Python version, platform, installed extras, exact
command, expected behavior, and a minimal synthetic reproduction. Maintainers
may close requests that cannot be reproduced, are outside the documented
support policy, or require access to production data.

Never attach production rows, raw PII, credentials, audit keys, provider
responses containing sensitive data, or internal infrastructure details.

## Response Expectations

There is no guaranteed response time or private consulting service. Security
reports and regressions that could copy source rows, expose sensitive values,
or bypass read-only SQL controls receive priority. Other issues are handled as
maintainer capacity permits.
