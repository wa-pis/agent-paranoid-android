"""Bind untrusted static previews to current PR heads without executing their code."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from scripts.cloudflare_documentation import (
    HEADERS,
    IDENTITY_FIELDS,
    REPOSITORY,
    static_payload,
)
from scripts.verify_documentation import DOCUMENTATION_USER_AGENT, download

PREVIEW_FILES = (
    "index.html",
    "ru/index.html",
    "search.html",
    "ru/search.html",
    "search/search_index.json",
)


@dataclass(frozen=True)
class PreviewSource:
    run_id: int
    commit: str
    number: int
    success: bool


def preview_run(metadata: dict[str, Any], run_id: int) -> str:
    expected = {
        "id": run_id,
        "status": "completed",
        "event": "pull_request",
        "path": ".github/workflows/docs.yml",
        "repository": REPOSITORY,
    }
    sha = metadata.get("head_sha")
    if (
        type(run_id) is not int
        or run_id <= 0
        or any(metadata.get(k) != v for k, v in expected.items())
        or not isinstance(sha, str)
        or not re.fullmatch(r"[0-9a-f]{40}", sha)
        or not isinstance(metadata.get("head_repository"), str)
        or not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", metadata["head_repository"]
        )
        or metadata.get("conclusion")
        not in {
            "success",
            "failure",
            "cancelled",
            "timed_out",
            "action_required",
            "neutral",
            "stale",
        }
    ):
        raise ValueError("preview requires a completed repository Documentation PR run")
    return sha


def preview_source(
    metadata: dict[str, Any], pulls: list[dict[str, Any]], run_id: int
) -> PreviewSource:
    sha = preview_run(metadata, run_id)
    matches = [
        p
        for p in pulls
        if p.get("state") == "open"
        and p.get("head_sha") == sha
        and p.get("base_repository") == REPOSITORY
        and p.get("head_repository") == metadata.get("head_repository")
    ]
    if (
        len(matches) != 1
        or type(matches[0].get("number")) is not int
        or matches[0]["number"] <= 0
    ):
        raise ValueError(
            "preview requires one open PR at the exact current source head"
        )
    return PreviewSource(
        run_id, sha, matches[0]["number"], metadata["conclusion"] == "success"
    )


def preview_identity(root: Path, sha: str) -> dict[str, str]:
    identity = json.loads((root / "documentation.json").read_text())
    if (
        not re.fullmatch(r"[0-9a-f]{40}", sha)
        or set(identity) != set(IDENTITY_FIELDS)
        or identity.get("documentation_revision") != sha
        or identity.get("status") != "PR preview / not stable"
        or not isinstance(identity.get("package_commit"), str)
        or not re.fullmatch(r"[0-9a-f]{40}", identity["package_commit"])
        or not isinstance(identity.get("package_version"), str)
        or not re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+(?:rc[0-9]+|\.dev[0-9]+)?",
            identity["package_version"],
        )
    ):
        raise ValueError("preview identity must label the exact PR head as not stable")
    for name in PREVIEW_FILES:
        if not (root / name).is_file():
            raise ValueError(
                "preview requires bilingual navigation and edition-local search"
            )
    for name in ("index.html", "ru/index.html"):
        if "PR preview / not stable" not in (root / name).read_text():
            raise ValueError("preview must retain its visible not-stable label")
    return identity


def prepare_preview(root: Path, sha: str) -> None:
    static_payload(root)
    preview_identity(root, sha)
    (root / "_headers").write_text(HEADERS)


def verify_preview(root: Path, url: str, sha: str) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".pages.dev")
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("preview requires an HTTPS Cloudflare Pages deployment URL")
    base = url.rstrip("/") + "/"
    expected = preview_identity(root, sha)
    if json.loads(download(base + "documentation.json")) != expected:
        raise ValueError(
            "public preview identity differs from the retained PR artifact"
        )
    for name in PREVIEW_FILES:
        if (
            hashlib.sha256(download(base + name)).digest()
            != hashlib.sha256((root / name).read_bytes()).digest()
        ):
            raise ValueError("public preview differs from its retained PR artifact")
    with urlopen(
        Request(base, headers={"User-Agent": DOCUMENTATION_USER_AGENT}), timeout=20
    ) as response:
        if (
            urlsplit(response.url).scheme != "https"
            or "noindex" not in response.headers.get("X-Robots-Tag", "").lower()
        ):
            raise ValueError("public preview must remain HTTPS and noindex")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "source"):
        item = sub.add_parser(command)
        item.add_argument("--metadata", type=Path, required=True)
        item.add_argument("--run-id", type=int, required=True)
        if command == "source":
            item.add_argument("--pulls", type=Path, required=True)
    for command in ("prepare", "verify"):
        item = sub.add_parser(command)
        item.add_argument("site", type=Path)
        item.add_argument("--sha", required=True)
        if command == "verify":
            item.add_argument("--url", required=True)
    args = parser.parse_args()
    if args.command == "run":
        print(
            "source_sha="
            + preview_run(json.loads(args.metadata.read_text()), args.run_id)
        )
    elif args.command == "source":
        selected = preview_source(
            json.loads(args.metadata.read_text()),
            json.loads(args.pulls.read_text()),
            args.run_id,
        )
        print(
            f"source_sha={selected.commit}\npr_number={selected.number}\nsource_success={str(selected.success).lower()}"
        )
    elif args.command == "prepare":
        prepare_preview(args.site, args.sha)
    else:
        verify_preview(args.site, args.url, args.sha)
        print(
            "Verified labelled, noindex bilingual PR preview at its exact source head"
        )


if __name__ == "__main__":
    main()
