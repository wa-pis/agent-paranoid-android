"""Only fictional static assets and public source-run metadata cross this boundary."""

import hashlib
import json
from dataclasses import asdict

import pytest

from scripts import cloudflare_documentation as cf


def metadata():
    return {
        "id": 123,
        "head_sha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
        "event": "push",
        "head_branch": "main",
        "path": ".github/workflows/docs.yml",
        "repository": cf.REPOSITORY,
        "head_repository": cf.REPOSITORY,
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("id", 124),
        ("conclusion", "failure"),
        ("status", "in_progress"),
        ("event", "pull_request"),
        ("head_branch", "feature"),
        ("path", ".github/workflows/other.yml"),
        ("repository", "fictional/other"),
        ("head_repository", "fictional/fork"),
        ("head_sha", "main\ninjected=value"),
    ],
)
def test_source_run_rejects_untrusted_provenance(key, value):
    run = {**metadata(), key: value}
    with pytest.raises(ValueError, match="successful main"):
        cf.source_run(run, 123)


def test_source_run_binds_exact_successful_commit():
    assert asdict(cf.source_run(metadata(), 123)) == {"run_id": 123, "commit": "a" * 40}


@pytest.fixture
def site(tmp_path):
    root = tmp_path / "site"
    (root / "downloads").mkdir(parents=True)
    identity = {
        "package_version": "1.6.0",
        "package_commit": "a" * 40,
        "documentation_revision": "b" * 40,
        "status": "Maintained stable guidance",
    }
    (root / "index.html").write_text("<h1>Fictional handbook</h1>")
    hashes = {}
    for name in cf.EXPORT_NAMES:
        data = b"fictional static artifact"
        (root / "downloads" / name).write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    (root / "documentation.json").write_text(json.dumps(identity))
    (root / "downloads/documentation.json").write_text(
        json.dumps(
            {
                **identity,
                "chapters": ["index.md"],
                "sha256": hashes,
                "index_sha256": hashlib.sha256(
                    (root / "index.html").read_bytes()
                ).hexdigest(),
            }
        )
    )
    return root


def test_preparation_preserves_every_asset_byte_and_adds_only_transport_headers(site):
    original = {
        p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()
    }
    result = cf.prepare(site)
    assert result.editions == 1
    assert result.files == len(original) + 1
    assert all((site / name).read_bytes() == data for name, data in original.items())
    headers = (site / "_headers").read_text()
    assert 'Content-Disposition: attachment; filename="handbook.html"' in headers
    assert "/downloads/handbook\n" in headers  # Pages strips .html on serving.
    assert "/versions/*/downloads/handbook\n" in headers
    assert "X-Robots-Tag: noindex, nofollow" in headers


@pytest.mark.parametrize(
    "name", ["_worker.js", "functions", "_headers", "wrangler.toml"]
)
def test_backend_or_host_configuration_is_rejected_before_mutation(site, name):
    (site / name).write_text("fictional forbidden deployment input")
    with pytest.raises(ValueError, match="deployment or backend"):
        cf.prepare(site)
    if name != "_headers":
        assert not (site / "_headers").exists()


def test_symlinks_never_escape_static_payload(site, tmp_path):
    outside = tmp_path / "outside"
    outside.write_text("fictional unrelated file")
    (site / "linked").symlink_to(outside)
    with pytest.raises(ValueError, match="symbolic links"):
        cf.prepare(site)
    assert not (site / "_headers").exists()


@pytest.mark.parametrize("limit", ["MAX_FILES", "MAX_FILE_BYTES"])
def test_asset_limits_fail_before_mutation(site, monkeypatch, limit):
    monkeypatch.setattr(cf, limit, 1)
    with pytest.raises(ValueError, match="asset limits"):
        cf.prepare(site)
    assert not (site / "_headers").exists()


@pytest.mark.parametrize(
    "name", ["index.html", "downloads/handbook.pdf", "downloads/handbook.html"]
)
def test_corruption_never_redefines_manifest_or_writes_headers(site, name):
    (site / name).write_bytes(b"fictional corruption")
    with pytest.raises(ValueError, match="retained manifest"):
        cf.prepare(site)
    assert not (site / "_headers").exists()


@pytest.mark.parametrize(
    "url",
    [
        "http://test.pages.dev/",
        "https://user:password@test.pages.dev/",
        "https://test.pages.dev.attacker.invalid/",
        "https://test.pages.dev/?token=x",
    ],
)
def test_public_url_guard_precedes_all_network_and_artifact_access(
    site, monkeypatch, url
):
    def forbidden(*args):
        pytest.fail("invalid deployment URL must fail before verification")

    monkeypatch.setattr(cf, "verify", forbidden)
    with pytest.raises(ValueError, match="HTTPS Cloudflare"):
        cf.verify_public(site, url)


def test_public_verification_covers_each_retained_edition_and_alias_gate(
    site, monkeypatch
):
    import shutil

    version = site / "versions/1.6.0"
    version.mkdir(parents=True)
    for name in ("documentation.json", "index.html"):
        shutil.copyfile(site / name, version / name)
    shutil.copytree(site / "downloads", version / "downloads")
    calls = []
    monkeypatch.setattr(
        cf, "verify", lambda url, identity: calls.append(("alias", url))
    )
    monkeypatch.setattr(
        cf,
        "verify_edition",
        lambda url, identity, manifest: calls.append(("edition", url)),
    )
    monkeypatch.setattr(
        cf, "verify_attachment", lambda url: calls.append(("attachment", url))
    )
    assert cf.verify_public(site, "https://fictional.pages.dev/") == 2
    assert ("alias", "https://fictional.pages.dev/") in calls
    for suffix in ("", "versions/1.6.0/"):
        assert ("edition", "https://fictional.pages.dev/" + suffix) in calls
        assert (
            "attachment",
            "https://fictional.pages.dev/" + suffix + "downloads/handbook.html",
        ) in calls


@pytest.mark.parametrize(
    "disposition", [None, "inline", 'attachment; filename="wrong.html"']
)
def test_html_response_requires_real_attachment_header(monkeypatch, disposition):
    from email.message import Message
    from types import SimpleNamespace
    from contextlib import nullcontext

    headers = Message()
    if disposition:
        headers["Content-Disposition"] = disposition
    response = SimpleNamespace(
        url="https://fictional.pages.dev/downloads/handbook", headers=headers
    )
    monkeypatch.setattr(cf, "urlopen", lambda *args, **kwargs: nullcontext(response))
    with pytest.raises(ValueError, match="HTTPS attachment"):
        cf.verify_attachment(response.url)


def test_parallel_workflow_never_uses_pr_code_or_production_branch():
    from pathlib import Path
    import yaml

    data = yaml.load(
        Path(".github/workflows/cloudflare-docs.yml").read_text(),
        Loader=yaml.BaseLoader,
    )
    assert set(data["on"]) == {"workflow_dispatch"}
    job = data["jobs"]["parallel"]
    assert job["if"] == "github.ref == 'refs/heads/main'"
    steps = job["steps"]
    checkout = next(
        step for step in steps if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "${{ github.sha }}"
    deploy = next(step for step in steps if step.get("id") == "deploy")
    assert "--branch=migration-${{ inputs.source_run_id }}" in deploy["with"]["command"]
    assert "--branch=main" not in deploy["with"]["command"]
    assert deploy["with"]["workingDirectory"] == "cloudflare-upload"
    secret_receivers = [
        step for step in steps if "CLOUDFLARE_API_TOKEN" in json.dumps(step)
    ]
    assert {step["id"] for step in secret_receivers} == {"create", "deploy"}
    create = next(step for step in steps if step.get("id") == "create")
    assert create["if"] == "inputs.create_project"
    assert (
        data["on"]["workflow_dispatch"]["inputs"]["create_project"]["default"]
        == "false"
    )
    assert all(step["uses"] == deploy["uses"] for step in secret_receivers)
