"""Public host verification is bound to a retained fictional build artifact."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from scripts import verify_documentation as published

BASE = "https://fictional.invalid/en/1.7.0rc1/"
IDENTITY = {
    "package_version": "1.7.0rc1",
    "package_commit": "a" * 40,
    "documentation_revision": "b" * 40,
    "status": "Release candidate / not stable",
}


@pytest.fixture
def publication(monkeypatch):
    entry = b"<html>Fictional edition</html>"
    files = {name: ("fictional " + name).encode() for name in published.EXPORT_NAMES}
    manifest = {
        **IDENTITY,
        "chapters": ["index.md", "ru/index.md"],
        "index_sha256": hashlib.sha256(entry).hexdigest(),
        "sha256": {
            name: hashlib.sha256(payload).hexdigest() for name, payload in files.items()
        },
    }
    responses = {
        "": entry,
        "documentation.json": json.dumps(IDENTITY).encode(),
        "downloads/documentation.json": json.dumps(manifest).encode(),
        **{"downloads/" + name: payload for name, payload in files.items()},
    }
    requests = []

    def download(url):
        assert url.startswith(BASE)
        path = url.removeprefix(BASE)
        requests.append(path)
        return responses[path]

    monkeypatch.setattr(published, "download", download)
    return manifest, responses, requests


def test_public_edition_compares_retained_identity_chapters_and_every_file(publication):
    manifest, _, requests = publication
    published.verify_edition(BASE, IDENTITY, manifest)
    assert set(requests) == {
        "",
        "documentation.json",
        "downloads/documentation.json",
        *("downloads/" + name for name in published.EXPORT_NAMES),
    }
    assert not any("versions/" in path for path in requests)


@pytest.mark.parametrize("name", published.EXPORT_NAMES)
def test_each_changed_download_is_rejected(publication, name):
    manifest, responses, _ = publication
    responses["downloads/" + name] = b"fictional changed artifact"
    with pytest.raises(ValueError, match="hash mismatch"):
        published.verify_edition(BASE, IDENTITY, manifest)


def test_changed_download_and_its_hosted_hash_cannot_redefine_the_build(publication):
    manifest, responses, _ = publication
    changed = copy.deepcopy(manifest)
    responses["downloads/handbook.pdf"] = b"fictional changed PDF"
    changed["sha256"]["handbook.pdf"] = hashlib.sha256(
        responses["downloads/handbook.pdf"]
    ).hexdigest()
    responses["downloads/documentation.json"] = json.dumps(changed).encode()
    with pytest.raises(ValueError, match="retained build"):
        published.verify_edition(BASE, IDENTITY, manifest)


@pytest.mark.parametrize("change", ["chapters", "source", "revision", "entry"])
def test_public_manifest_cannot_replace_build_provenance(publication, change):
    manifest, responses, _ = publication
    changed = copy.deepcopy(manifest)
    if change == "chapters":
        changed["chapters"] = ["index.md"]
    elif change == "source":
        changed["package_commit"] = "c" * 40
    elif change == "revision":
        changed["documentation_revision"] = "d" * 40
    else:
        changed["index_sha256"] = "0" * 64
    responses["downloads/documentation.json"] = json.dumps(changed).encode()
    with pytest.raises(ValueError, match="retained build"):
        published.verify_edition(BASE, IDENTITY, manifest)


def test_host_injection_is_not_silently_exempted_from_entry_hash(publication):
    manifest, responses, _ = publication
    responses[""] += b"<script>fictional host injection</script>"
    with pytest.raises(ValueError, match="entry page"):
        published.verify_edition(BASE, IDENTITY, manifest)


@pytest.mark.parametrize(
    "change",
    [
        "missing_file",
        "extra_file",
        "bad_hash",
        "missing_entry_hash",
        "missing_chapters",
        "duplicate_chapter",
        "bad_chapter",
        "identity",
    ],
)
def test_incomplete_retained_evidence_fails_before_network(publication, change):
    manifest, _, requests = publication
    if change == "missing_file":
        del manifest["sha256"]["site.zip"]
    elif change == "extra_file":
        manifest["sha256"]["other.zip"] = "0" * 64
    elif change == "bad_hash":
        manifest["sha256"]["site.zip"] = "wrong"
    elif change == "missing_entry_hash":
        del manifest["index_sha256"]
    elif change == "missing_chapters":
        manifest["chapters"] = []
    elif change == "duplicate_chapter":
        manifest["chapters"].append("index.md")
    elif change == "bad_chapter":
        manifest["chapters"] = [{}]
    else:
        manifest["package_commit"] = "c" * 40
    with pytest.raises(ValueError, match="retained build manifest"):
        published.verify_edition(BASE, IDENTITY, manifest)
    assert not requests


def test_dirty_build_cannot_be_publicly_verified(publication):
    manifest, _, requests = publication
    expected = {**IDENTITY, "documentation_revision": "b" * 40 + "+dirty"}
    manifest.update(expected)
    with pytest.raises(ValueError, match="uncommitted"):
        published.verify_edition(BASE, expected, manifest)
    assert not requests


def test_cli_edition_mode_requires_local_manifest_without_claiming_promotion(
    publication, tmp_path, monkeypatch, capsys
):
    manifest, _, _ = publication
    path = tmp_path / "documentation.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(
        "sys.argv",
        [
            "verify_documentation",
            "--url",
            BASE,
            "--expected-json",
            json.dumps(IDENTITY),
            "--edition-manifest",
            str(path),
        ],
    )
    assert published.main() == 0
    assert "promotion is not verified" in capsys.readouterr().out


def test_download_identifies_verifier_without_changing_timeout_or_payload(monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace

    def open_request(request, *, timeout):
        assert request.full_url == BASE
        assert request.get_header("User-agent") == published.DOCUMENTATION_USER_AGENT
        assert timeout == 20
        return nullcontext(SimpleNamespace(url=BASE, read=lambda limit: b"fictional"))

    monkeypatch.setattr(published, "urlopen", open_request)
    assert published.download(BASE) == b"fictional"
