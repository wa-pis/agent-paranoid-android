"""Fictional previews never receive verified-edition publishing authority."""

import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts import cloudflare_previews as preview

SHA = "a" * 40


def metadata():
    return {
        "id": 123,
        "status": "completed",
        "conclusion": "success",
        "event": "pull_request",
        "path": ".github/workflows/docs.yml",
        "repository": preview.REPOSITORY,
        "head_repository": "fictional/contribution",
        "head_sha": SHA,
    }


def pull():
    return {
        "number": 42,
        "state": "open",
        "head_sha": SHA,
        "head_repository": "fictional/contribution",
        "base_repository": preview.REPOSITORY,
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("id", 124),
        ("status", "in_progress"),
        ("event", "push"),
        ("path", ".github/workflows/other.yml"),
        ("repository", "fictional/other"),
        ("head_sha", "main\ninjected=value"),
        ("head_repository", None),
        ("conclusion", "unknown"),
    ],
)
def test_unrelated_or_unfinished_source_rejected(key, value):
    with pytest.raises(ValueError, match="completed repository"):
        preview.preview_source({**metadata(), key: value}, [pull()], 123)


@pytest.mark.parametrize(
    "key,value",
    [
        ("state", "closed"),
        ("head_sha", "b" * 40),
        ("number", True),
        ("base_repository", "fictional/other"),
        ("head_repository", "fictional/other"),
    ],
)
def test_current_open_pr_association_is_required(key, value):
    with pytest.raises(ValueError, match="one open PR"):
        preview.preview_source(metadata(), [{**pull(), key: value}], 123)


def test_ambiguous_pr_associations_are_rejected():
    with pytest.raises(ValueError, match="one open PR"):
        preview.preview_source(metadata(), [pull(), {**pull(), "number": 43}], 123)


@pytest.mark.parametrize(
    "conclusion,success", [("success", True), ("failure", False), ("cancelled", False)]
)
def test_fork_source_is_bound_to_authenticated_base_and_exact_head(conclusion, success):
    selected = preview.preview_source(
        {**metadata(), "conclusion": conclusion}, [pull()], 123
    )
    assert (selected.commit, selected.number, selected.success) == (SHA, 42, success)


@pytest.fixture
def site(tmp_path):
    identity = {
        "package_version": "1.7.0rc1",
        "package_commit": "b" * 40,
        "documentation_revision": SHA,
        "status": "PR preview / not stable",
    }
    for name in preview.PREVIEW_FILES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "<html>PR preview / not stable: fictional</html>"
            if name.endswith(".html")
            else '{"docs": []}'
        )
    (tmp_path / "documentation.json").write_text(json.dumps(identity))
    return tmp_path


def test_prepare_preserves_bytes_and_adds_only_noindex_headers(site):
    files = {
        p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()
    }
    preview.prepare_preview(site, SHA)
    assert all((site / name).read_bytes() == value for name, value in files.items())
    assert "noindex, nofollow" in (site / "_headers").read_text()


@pytest.mark.parametrize(
    "key,value",
    [
        ("status", "Maintained stable guidance"),
        ("documentation_revision", "b" * 40),
        ("documentation_revision", SHA + "+dirty"),
    ],
)
def test_false_release_labels_and_revisions_never_publish(site, key, value):
    path = site / "documentation.json"
    identity = json.loads(path.read_text())
    path.write_text(json.dumps({**identity, key: value}))
    with pytest.raises(ValueError, match="exact PR head"):
        preview.prepare_preview(site, SHA)
    assert not (site / "_headers").exists()


def test_backend_rejected_before_headers(site):
    (site / "_worker.js").write_text("fictional forbidden backend")
    with pytest.raises(ValueError, match="backend"):
        preview.prepare_preview(site, SHA)
    assert not (site / "_headers").exists()


def test_missing_russian_search_rejected_before_upload(site):
    (site / "ru/search.html").unlink()
    with pytest.raises(ValueError, match="bilingual"):
        preview.prepare_preview(site, SHA)


@pytest.fixture
def public(site, monkeypatch):
    base = "https://fictional.pages.dev/"
    responses = {
        name: (site / name).read_bytes()
        for name in (*preview.PREVIEW_FILES, "documentation.json")
    }
    requests = []

    def download(url):
        name = url.removeprefix(base)
        requests.append(name)
        return responses[name]

    monkeypatch.setattr(preview, "download", download)
    monkeypatch.setattr(
        preview,
        "urlopen",
        lambda *a, **k: nullcontext(
            SimpleNamespace(url=base, headers={"X-Robots-Tag": "noindex, nofollow"})
        ),
    )
    return base, responses, requests


def test_public_verification_checks_both_languages_search_and_exact_identity(
    site, public
):
    base, _, requests = public
    preview.verify_preview(site, base, SHA)
    assert set(requests) == {*preview.PREVIEW_FILES, "documentation.json"}


@pytest.mark.parametrize("name", preview.PREVIEW_FILES)
def test_changed_entry_or_search_is_rejected(site, public, name):
    base, responses, _ = public
    responses[name] = b"fictional corruption"
    with pytest.raises(ValueError, match="differs"):
        preview.verify_preview(site, base, SHA)


def test_public_preview_must_remain_noindex(site, public, monkeypatch):
    base, _, _ = public
    monkeypatch.setattr(
        preview,
        "urlopen",
        lambda *a, **k: nullcontext(SimpleNamespace(url=base, headers={})),
    )
    with pytest.raises(ValueError, match="noindex"):
        preview.verify_preview(site, base, SHA)


def test_source_and_publisher_have_separate_credentials_and_code():
    source = yaml.load(
        Path(".github/workflows/docs.yml").read_text(), Loader=yaml.BaseLoader
    )["jobs"]["preview"]
    assert source["if"] == "github.event_name == 'pull_request'"
    assert source["permissions"] == {"contents": "read"}
    assert "environment" not in source
    assert "secrets." not in json.dumps(source)
    setup_uv = next(
        step
        for step in source["steps"]
        if step.get("uses", "").startswith("astral-sh/setup-uv@")
    )
    assert setup_uv["with"]["enable-cache"] == "false"
    assert setup_uv["with"]["prune-cache"] == "true"
    checkout = next(
        s for s in source["steps"] if s.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha }}"
    workflow = yaml.load(
        Path(".github/workflows/cloudflare-previews.yml").read_text(),
        Loader=yaml.BaseLoader,
    )
    assert set(workflow["on"]) == {"workflow_run"}
    jobs = workflow["jobs"]
    assert (
        "environment" not in jobs["inspect"]
        and "environment" not in jobs["source-failure"]
    )
    publisher = jobs["publish"]
    assert publisher["environment"] == "cloudflare-pages-preview"
    assert publisher["permissions"]["contents"] == "read"
    assert publisher["permissions"]["statuses"] == "write"
    for name in ("inspect", "publish"):
        checkout = next(
            s
            for s in jobs[name]["steps"]
            if s.get("uses", "").startswith("actions/checkout@")
        )
        assert checkout["with"]["ref"] == "${{ github.sha }}"
    receivers = [s for s in publisher["steps"] if "secrets." in json.dumps(s)]
    assert len(receivers) == 1
    assert receivers[0]["id"] == "deploy"
    assert receivers[0]["with"]["workingDirectory"] == "cloudflare-upload"
    assert "--branch=pr-" in receivers[0]["with"]["command"]
    assert "CLOUDFLARE_PAGES_PREVIEW_PROJECT" in receivers[0]["with"]["command"]
    assert '[[ "$CF_PROJECT" != "$NORMAL_PROJECT" ]]' in json.dumps(publisher).replace(
        '\\"', '"'
    )
