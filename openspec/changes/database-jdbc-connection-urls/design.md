# Design: database-jdbc-connection-urls

## Approach

Add one small parser beside each existing database configuration model. The
parsers recognize the official URL shapes and return ordinary validated config
fields. Existing clients remain unaware of JDBC syntax.

Supported endpoint shapes are based on the official
[pgJDBC connection documentation](https://jdbc.postgresql.org/documentation/use/)
and [Trino JDBC documentation](https://trino.io/docs/current/client/jdbc.html):

```text
jdbc:postgresql://db.example.test:5432/app
jdbc:trino://trino.example.test:8443/hive/analytics?SSL=true
```

This is syntax compatibility, not JDBC runtime compatibility. The parser may
use the Python standard library after removing and validating the leading
`jdbc:` marker.

## Data And Contracts

PostgreSQL URL fields:

- required host and database;
- optional validated port, defaulting through the existing config;
- optional `sslmode`, restricted to values already accepted by
  `PostgresConfig`;
- no username, password, `options`, schema/search-path override, certificate
  password, logger setting, or unknown query property.

Trino URL fields:

- required host;
- optional validated port, catalog, and schema; host, port, and TLS normalize
  into `TrinoConfig`, while catalog/schema become request defaults only after
  matching the mandatory catalog/schema allowlists;
- optional `SSL=true`, mapped to the existing verified HTTPS mode;
- no `user`, `password`, access token, impersonation, proxy, path, role,
  session property, extra credential/header, external authentication, TLS
  verification downgrade, or unknown query property.

The implementation SHALL add typed URL inputs to the relevant configuration
facades and documented command/configuration paths. Authentication identity
and secret material continue to come from their existing fields and runtime
environment references.

If URL and component settings are both present, normalization compares only
explicitly supplied values. Equal values are accepted; a mismatch is a fixed
configuration error before client construction. Allowlist and budget settings
are never inferred from the URL.

## Runnable Examples

Extend the existing disposable database examples instead of introducing a
second service setup:

- `examples/local_postgres/run-jdbc.sh OUTPUT` starts the same localhost-only
  synthetic PostgreSQL cluster as `run.sh`, configures its endpoint with a
  placeholder JDBC-style URL, and runs profile, infer, generate, validate, and
  PostgreSQL SQL export.
- `examples/local_trino/run-jdbc.sh OUTPUT` starts the same pinned synthetic
  Trino service as `run.sh`, configures its endpoint/catalog/schema with a
  JDBC-style URL, and runs safe aggregate profiling followed by deterministic
  generation and validation.

The launchers may share private shell/Python helpers with the current examples,
but both remain explicit user-facing entry points. They run from an installed
wheel with the matching optional extra, accept no real credential, use fixed
seeds, clean up disposable services, and fail if output already exists.

Smoke tests SHALL assert successful artifacts, `synthetic: true`,
`source_rows_copied: false`, deterministic repeated output, and absence of the
JDBC URL or endpoint components from profiles, manifests, logs, and errors.
Normal CI uses fake/no-network configuration tests; disposable live examples
remain explicitly gated where the existing PostgreSQL and Trino examples are
gated.

## Failure Modes

- Wrong adapter prefix, missing host/database, invalid port, malformed escape,
  userinfo, fragment, duplicate parameter, or unknown property: reject before
  network access.
- Credential-bearing or session-changing property: reject with a fixed error
  naming only the property class, never its value.
- Conflicting URL and component fields: reject before network access.
- URL parser or validation failure: do not include the URL or backend endpoint
  in human or JSON errors.
- Existing read-only setup, allowlist, or budget failure after normalization:
  preserve current fail-closed client behavior.

## Alternatives

- **Use a Java JDBC bridge:** rejected because the product already has typed
  Python adapters and should not add a JVM or duplicate driver stack.
- **Accept every JDBC property:** rejected because many properties carry
  credentials or alter proxy, identity, SQL path, session, and TLS behavior.
- **Put the whole URL in public artifacts:** rejected because endpoint and
  query parameters are secret-adjacent operational data.
