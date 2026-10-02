from types import SimpleNamespace
from types import ModuleType
from pathlib import Path
import sys
import logging

import pytest

from test_data_agent.trino_auth import TrinoAuthConfig
from test_data_agent.trino_auth import bounded_oauth_session
from test_data_agent.trino_config import TrinoConfigurationError
from test_data_agent.trino_work_budget import DEFAULT_QUERY_WORK_LIMITS, QueryWorkBudget, QueryWorkBudgetExceeded


@pytest.mark.parametrize("url", [
    "http://fictional.test/token", "https://elsewhere.test/token",
    "https://fictional.test:444/token", "https://user:fictional@fictional.test/token",
    "https://fictional.test/token#fragment", "https://fictional.test:bad/token",
])
def test_oauth_direct_token_adapter_rejects_unapproved_origin(url: str) -> None:
    import requests
    session = bounded_oauth_session(host="fictional.test", port=443, request_timeout=1, budget=None)
    with session, pytest.raises(TrinoConfigurationError) as caught:
        # The driver calls response.connection.send directly for token polling.
        session.get_adapter(url).send(SimpleNamespace(url=url))
    assert url not in str(caught.value)
    assert caught.value.__context__ is None
    assert isinstance(session, requests.Session)


def test_oauth_direct_token_adapter_bounds_timeout_and_detaches_errors(monkeypatch) -> None:
    import requests
    options = []
    def send(adapter, request, **kwargs):
        options.append(kwargs)
        raise requests.ConnectionError("fictional-token-url")
    # HTTP dependency stub only; product guards execute unchanged, no network.
    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", send)
    session = bounded_oauth_session(host="fictional.test", port=443, request_timeout=2, budget=None)
    with session, pytest.raises(TrinoConfigurationError) as caught:
        session.get_adapter("https://fictional.test").send(
            SimpleNamespace(url="https://fictional.test/token"), verify=False, timeout=999,
        )
    assert options[0]["verify"] is True
    assert all(0 < value <= 1 for value in options[0]["timeout"])
    assert session.trust_env is False
    assert caught.value.__context__ is None
    assert "fictional-token-url" not in str(caught.value)


def test_oauth_direct_token_adapter_rejects_expired_deadline(monkeypatch) -> None:
    session = bounded_oauth_session(host="fictional.test", port=443, request_timeout=-1, budget=None)
    with session, pytest.raises(TrinoConfigurationError, match="deadline"):
        session.get_adapter("https://fictional.test").send(SimpleNamespace(url="https://fictional.test/token"))


def test_oauth_direct_token_adapter_obeys_shared_invocation_budget() -> None:
    clock = [0.0]
    budget = QueryWorkBudget(DEFAULT_QUERY_WORK_LIMITS, monotonic_clock=lambda: clock[0])
    session = bounded_oauth_session(host="fictional.test", port=443, request_timeout=300, budget=budget)
    clock[0] = DEFAULT_QUERY_WORK_LIMITS.max_invocation_seconds + 1
    with session, pytest.raises(QueryWorkBudgetExceeded):
        session.get_adapter("https://fictional.test").send(SimpleNamespace(url="https://fictional.test/token"))


@pytest.mark.parametrize("method,constructor", [("basic", "BasicAuthentication"), ("jwt", "JWTAuthentication")])
def test_runtime_authentication_never_stores_secret(method, constructor) -> None:
    config = TrinoAuthConfig(method=method, secret_env="FICTIONAL_AUTH")
    driver = SimpleNamespace(**{constructor: lambda *args: args})
    result = config.build(driver_auth=driver, environ={"FICTIONAL_AUTH": "fictional-secret"},
                          username="fictional", http_scheme="https")
    assert result[-1] == "fictional-secret"
    assert "fictional-secret" not in repr(config)
    with pytest.raises(TrinoConfigurationError):
        config.build(driver_auth=driver, environ={}, username="fictional", http_scheme="https")
    with pytest.raises(TrinoConfigurationError):
        config.build(driver_auth=driver, environ={}, username="fictional", http_scheme="http")


def test_oauth_never_uses_driver_default_redirect() -> None:
    driver = SimpleNamespace(OAuth2Authentication=lambda **kwargs: kwargs)
    config = TrinoAuthConfig(method="oauth2")
    with pytest.raises(TrinoConfigurationError, match="trusted local"):
        config.build(driver_auth=driver, environ={}, username="fictional", http_scheme="https")
    def handler(url: str) -> None:
        return None
    assert config.build(driver_auth=driver, environ={}, username="fictional", http_scheme="https",
                        oauth_redirect=handler) == {"redirect_auth_url_handler": handler}


def test_certificate_references_resolve_only_at_runtime(tmp_path: Path) -> None:
    driver = SimpleNamespace(CertificateAuthentication=lambda cert, key: (cert, key))
    config = TrinoAuthConfig(method="certificate", certificate_env="FICTIONAL_CERT", key_env="FICTIONAL_KEY")
    certificate, key = tmp_path / "cert.pem", tmp_path / "key.pem"
    certificate.write_text("fictional certificate placeholder", encoding="utf-8")
    key.write_text("fictional key placeholder", encoding="utf-8")
    environ = {"FICTIONAL_CERT": str(certificate), "FICTIONAL_KEY": str(key)}
    assert config.build(driver_auth=driver, environ=environ, username="fictional",
                        http_scheme="https") == (environ["FICTIONAL_CERT"], environ["FICTIONAL_KEY"])
    assert str(tmp_path) not in repr(config)
    with pytest.raises(TrinoConfigurationError, match="missing or invalid"):
        config.build(driver_auth=driver, environ={"FICTIONAL_CERT": str(certificate)},
                     username="fictional", http_scheme="https")
    key.unlink()
    with pytest.raises(TrinoConfigurationError, match="missing or unreadable") as caught:
        config.build(driver_auth=driver, environ=environ,
                     username="fictional", http_scheme="https")
    assert str(key) not in str(caught.value)


@pytest.mark.parametrize("method,module,constructor", [
    ("kerberos", "requests_kerberos", "KerberosAuthentication"),
    ("gssapi", "requests_gssapi", "GSSAPIAuthentication"),
])
def test_optional_integrated_authentication_is_mutual_and_non_delegating(
    method, module, constructor, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Isolated dependency stub, not a product-policy monkeypatch or live driver.
    monkeypatch.setitem(sys.modules, module, ModuleType(module))
    driver = SimpleNamespace(**{constructor: lambda **kwargs: kwargs})
    assert TrinoAuthConfig(method=method).build(driver_auth=driver, environ={},
                                              username="fictional", http_scheme="https") == {
        "mutual_authentication": 1, "delegate": False,
    }


def test_driver_auth_error_is_detached_and_value_free() -> None:
    def broken(token):
        raise RuntimeError(token)
    driver = SimpleNamespace(JWTAuthentication=broken)
    config = TrinoAuthConfig(method="jwt", secret_env="FICTIONAL_TOKEN")
    with pytest.raises(TrinoConfigurationError) as caught:
        config.build(driver_auth=driver, environ={"FICTIONAL_TOKEN": "fictional-secret"},
                     username="fictional", http_scheme="https")
    assert "fictional-secret" not in str(caught.value)
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None


@pytest.mark.parametrize("method,kwargs", [
    ("none", {"secret_env": "FICTIONAL"}),
    ("jwt", {"certificate_env": "FICTIONAL"}),
    ("certificate", {"secret_env": "FICTIONAL"}),
])
def test_conflicting_auth_references_reject(method, kwargs) -> None:
    with pytest.raises(TrinoConfigurationError):
        TrinoAuthConfig(method=method, **kwargs).build(
            driver_auth=None, environ={}, username="fictional", http_scheme="https",
        )


def test_unknown_auth_method_does_not_reflect_input() -> None:
    with pytest.raises(TrinoConfigurationError) as caught:
        TrinoAuthConfig.from_env({"TRINO_AUTH_METHOD": "fictional-untrusted-input"})
    assert "fictional-untrusted-input" not in str(caught.value)


@pytest.mark.parametrize("logger_name", ["trino.auth", "urllib3.connectionpool"])
def test_oauth_diagnostics_are_value_free_before_driver_constructor(
    caplog: pytest.LogCaptureFixture, logger_name: str,
) -> None:
    def constructor(**kwargs):
        logging.getLogger(logger_name).debug("nextUri %s", "fictional-secret-token-url")
        return kwargs
    driver = SimpleNamespace(OAuth2Authentication=constructor)
    with caplog.at_level(logging.DEBUG, logger=logger_name):
        TrinoAuthConfig(method="oauth2").build(
            driver_auth=driver, environ={}, username="fictional", http_scheme="https",
            oauth_redirect=lambda url: None,
        )
    assert "fictional-secret-token-url" not in caplog.text
    assert "authentication diagnostic suppressed" in caplog.text
