"""Runtime-only Trino authentication; no secrets in saved configuration."""

from __future__ import annotations

import importlib
import logging
import os
import re
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import urlsplit

from test_data_agent.trino_config import TrinoConfigurationError
from test_data_agent.trino_work_budget import QueryWorkBudget

AuthMethod = Literal["none", "basic", "jwt", "kerberos", "gssapi", "oauth2", "certificate"]
_METHODS = {"none", "basic", "jwt", "kerberos", "gssapi", "oauth2", "certificate"}


def bounded_oauth_session(
    *, host: str, port: int, request_timeout: float, budget: QueryWorkBudget | None,
) -> Any:
    """Guard both ordinary requests and the driver's direct token-adapter sends."""
    import requests

    deadline = time.monotonic() + request_timeout

    class OAuthAdapter(requests.adapters.HTTPAdapter):
        def send(
            self, request: Any, stream: bool = False, timeout: Any = None,
            verify: bool | str = True, cert: Any = None, proxies: Any = None,
        ) -> Any:
            allowed = False
            try:
                endpoint = urlsplit(request.url)
                allowed = (
                    endpoint.scheme == "https" and endpoint.hostname == host.lower()
                    and (endpoint.port or 443) == port
                    and endpoint.username is None and endpoint.password is None
                    and not endpoint.fragment
                )
            except ValueError:
                pass
            if not allowed:
                raise TrinoConfigurationError("OAuth2 transport requires the configured HTTPS Trino origin")
            remaining = deadline - time.monotonic()
            if budget is not None:
                remaining = min(remaining, budget.remaining_invocation_seconds())
            if remaining <= 0:
                raise TrinoConfigurationError("OAuth2 transport deadline exceeded")
            # Requests applies connect/read timeouts separately; split the remaining budget.
            try:
                response = super().send(
                    request, stream=stream, verify=True, cert=cert, proxies=proxies,
                    timeout=(remaining / 2, remaining / 2),
                )
            except requests.RequestException:
                pass
            else:
                if budget is not None:
                    try:
                        budget.check_invocation_deadline()
                    except Exception:
                        response.close()
                        raise
                if time.monotonic() >= deadline:
                    response.close()
                    raise TrinoConfigurationError("OAuth2 transport deadline exceeded")
                return response
            raise TrinoConfigurationError("OAuth2 transport failed")

    session = requests.Session()
    # Do not inherit proxy credentials or netrc secrets from the process environment.
    session.trust_env = False
    adapter = OAuthAdapter()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class _AuthDiagnosticFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Driver diagnostics may contain redirect/token URLs and backend bodies.
        record.msg = "Trino authentication diagnostic suppressed"
        record.args = ()
        record.exc_info = None
        record.exc_text = None
        record.stack_info = None
        return True


def _configure_auth_diagnostics() -> None:
    # The HTTP pool also logs request paths, including OAuth token query strings.
    for name in ("trino.auth", "urllib3.connectionpool"):
        logger = logging.getLogger(name)
        if not any(isinstance(item, _AuthDiagnosticFilter) for item in logger.filters):
            logger.addFilter(_AuthDiagnosticFilter())


@dataclass(frozen=True)
class TrinoAuthConfig:
    method: AuthMethod = "none"
    secret_env: str | None = field(default=None, repr=False)
    certificate_env: str | None = field(default=None, repr=False)
    key_env: str | None = field(default=None, repr=False)

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> TrinoAuthConfig:
        method = environ.get("TRINO_AUTH_METHOD", "none")
        if method not in _METHODS:
            raise TrinoConfigurationError("unsupported Trino authentication method")
        return cls(
            method=cast(AuthMethod, method),
            secret_env=environ.get("TRINO_AUTH_SECRET_ENV"),
            certificate_env=environ.get("TRINO_AUTH_CERTIFICATE_ENV"),
            key_env=environ.get("TRINO_AUTH_KEY_ENV"),
        )

    def build(
        self, *, driver_auth: Any, environ: Mapping[str, str], username: str,
        http_scheme: str, oauth_redirect: Callable[[str], None] | None = None,
    ) -> Any:
        """Resolve runtime secrets and validate before any driver connection."""
        if self.method not in _METHODS:
            raise TrinoConfigurationError("unsupported Trino authentication method")
        if self.method == "none":
            if any((self.secret_env, self.certificate_env, self.key_env)):
                raise TrinoConfigurationError("authentication references require an authentication method")
            return None
        if http_scheme.lower() != "https":
            raise TrinoConfigurationError("Trino authentication requires verified HTTPS")
        if self.method not in {"basic", "jwt"} and self.secret_env is not None:
            raise TrinoConfigurationError("secret reference conflicts with authentication method")
        if self.method != "certificate" and any((self.certificate_env, self.key_env)):
            raise TrinoConfigurationError("certificate references conflict with authentication method")
        try:
            if self.method == "basic":
                return driver_auth.BasicAuthentication(username, self._secret(self.secret_env, environ))
            if self.method == "jwt":
                return driver_auth.JWTAuthentication(self._secret(self.secret_env, environ))
            if self.method == "certificate":
                return driver_auth.CertificateAuthentication(
                    self._credential_file(self.certificate_env, environ),
                    self._credential_file(self.key_env, environ),
                )
            if self.method in {"kerberos", "gssapi"}:
                importlib.import_module("requests_kerberos" if self.method == "kerberos" else "requests_gssapi")
                constructor = driver_auth.KerberosAuthentication if self.method == "kerberos" else driver_auth.GSSAPIAuthentication
                return constructor(mutual_authentication=1, delegate=False)
            if oauth_redirect is None:
                raise TrinoConfigurationError("OAuth2 requires an explicit trusted local redirect handler")
            _configure_auth_diagnostics()
            return driver_auth.OAuth2Authentication(redirect_auth_url_handler=oauth_redirect)
        except TrinoConfigurationError:
            raise
        except Exception:
            pass
        # Detach constructor/import errors which may include secrets or paths.
        raise TrinoConfigurationError("Trino authentication is unavailable or invalid")

    @staticmethod
    def _credential_file(reference: str | None, environ: Mapping[str, str]) -> str:
        value = TrinoAuthConfig._secret(reference, environ)
        if not Path(value).is_file() or not os.access(value, os.R_OK):
            raise TrinoConfigurationError("Trino authentication credential file is missing or unreadable")
        return value

    @staticmethod
    def _secret(reference: str | None, environ: Mapping[str, str]) -> str:
        if reference is None or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", reference) is None:
            raise TrinoConfigurationError("Trino authentication requires a valid runtime secret reference")
        value = environ.get(reference)
        if not value or len(value) > 65536 or "\r" in value or "\n" in value:
            raise TrinoConfigurationError("Trino authentication runtime secret is missing or invalid")
        return value
