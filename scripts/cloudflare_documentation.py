"""Validate trusted static documentation artifacts before parallel Pages upload."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from urllib.request import urlopen

from scripts.verify_documentation import EXPORT_NAMES, verify, verify_edition

MAX_FILES = 20_000
MAX_FILE_BYTES = 25 * 1024 * 1024
REPOSITORY = "wa-pis/agent-paranoid-android"
IDENTITY_FIELDS = (
    "package_version",
    "package_commit",
    "documentation_revision",
    "status",
)
RESERVED = {
    "functions",
    "_worker.js",
    "_routes.json",
    "_headers",
    "_redirects",
    "wrangler.toml",
    "wrangler.json",
    "wrangler.jsonc",
    ".env",
    ".dev.vars",
}
# Parallel uploads are never the indexed/canonical publication.
HEADERS = "/*\n  X-Robots-Tag: noindex, nofollow\n\n" + "\n".join(
    f'{path}\n  Content-Disposition: attachment; filename="handbook.html"\n'
    for path in (
        "/downloads/handbook.html",
        "/downloads/handbook",
        "/versions/*/downloads/handbook.html",
        "/versions/*/downloads/handbook",
    )
)


@dataclass(frozen=True)
class SourceRun:
    run_id: int
    commit: str


@dataclass(frozen=True)
class Payload:
    files: int
    total_bytes: int
    editions: int


def source_run(metadata: dict[str, Any], run_id: int) -> SourceRun:
    """Accept only the public, exact main build selected by a trusted operator."""
    expected = {
        "id": run_id,
        "status": "completed",
        "conclusion": "success",
        "event": "push",
        "head_branch": "main",
        "path": ".github/workflows/docs.yml",
        "repository": REPOSITORY,
        "head_repository": REPOSITORY,
    }
    commit = metadata.get("head_sha")
    if (
        type(run_id) is not int
        or run_id <= 0
        or any(metadata.get(key) != value for key, value in expected.items())
        or not isinstance(commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
    ):
        raise ValueError("Cloudflare requires a successful main Documentation push run")
    return SourceRun(run_id, commit)


def local_edition(root: Path) -> None:
    identity = json.loads((root / "documentation.json").read_text())
    manifest = json.loads((root / "downloads/documentation.json").read_text())
    if (
        set(identity) != set(IDENTITY_FIELDS)
        or any(not isinstance(value, str) for value in identity.values())
        or identity["documentation_revision"].endswith("+dirty")
        or any(manifest.get(key) != value for key, value in identity.items())
        or set(manifest.get("sha256", {})) != set(EXPORT_NAMES)
        or not manifest.get("chapters")
    ):
        raise ValueError(
            "documentation edition has incomplete or inconsistent provenance"
        )
    expected = {
        "index.html": manifest.get("index_sha256"),
        **{f"downloads/{name}": manifest["sha256"][name] for name in EXPORT_NAMES},
    }
    for name, digest in expected.items():
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
        ):
            raise ValueError(
                "documentation artifact does not match its retained manifest"
            )


def prepare(root: Path) -> Payload:
    """Check all assets before adding transport headers; never execute site data."""
    if root.is_symlink() or not root.is_dir():
        raise ValueError("documentation payload must be a real directory")
    if not (root / "index.html").is_file():
        raise ValueError("documentation payload is missing its entry page")
    files, total = 0, 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError("documentation payload must not contain symbolic links")
        if path.relative_to(root).parts[0] in RESERVED:
            raise ValueError(
                "documentation payload contains deployment or backend configuration"
            )
        if path.is_file():
            size = path.stat().st_size
            files += 1
            total += size
            if size > MAX_FILE_BYTES or files + 1 > MAX_FILES:
                raise ValueError(
                    "documentation payload exceeds Cloudflare Free asset limits"
                )
        elif not path.is_dir():
            raise ValueError(
                "documentation payload contains a non-static filesystem entry"
            )
    manifests = list(root.glob("**/downloads/documentation.json"))
    if root / "downloads/documentation.json" not in manifests:
        raise ValueError("normal documentation payload is missing its export manifest")
    for manifest in manifests:
        local_edition(manifest.parent.parent)
    headers = HEADERS.encode()
    (root / "_headers").write_bytes(headers)
    return Payload(files + 1, total + len(headers), len(manifests))


def verify_attachment(url: str) -> None:
    with urlopen(url, timeout=20) as response:
        if (
            urlsplit(response.url).scheme != "https"
            or response.headers.get_content_disposition() != "attachment"
            or response.headers.get_filename() != "handbook.html"
        ):
            raise ValueError("standalone HTML must be served as an HTTPS attachment")


def verify_public(root: Path, url: str) -> int:
    """Require the uploaded bytes to match each same-build retained edition."""
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
        raise ValueError("parallel verification requires an HTTPS Cloudflare Pages URL")
    base = url.rstrip("/") + "/"
    identity = json.loads((root / "documentation.json").read_text())
    # Keep the existing stable alias/destination gate in addition to byte equality.
    verify(base, identity)
    manifests = list(root.glob("**/downloads/documentation.json"))
    for manifest_path in manifests:
        edition_root = manifest_path.parent.parent
        relative = edition_root.relative_to(root).as_posix()
        edition_url = base if relative == "." else base + relative + "/"
        expected = json.loads((edition_root / "documentation.json").read_text())
        manifest = json.loads(manifest_path.read_text())
        verify_edition(edition_url, expected, manifest)
        verify_attachment(edition_url + "downloads/handbook.html")
    return len(manifests)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    source = sub.add_parser("source")
    source.add_argument("--metadata", type=Path, required=True)
    source.add_argument("--run-id", type=int, required=True)
    payload = sub.add_parser("prepare")
    payload.add_argument("site", type=Path)
    public = sub.add_parser("verify")
    public.add_argument("site", type=Path)
    public.add_argument("--url", required=True)
    args = parser.parse_args()
    if args.command == "source":
        selected = source_run(json.loads(args.metadata.read_text()), args.run_id)
        print(f"source_sha={selected.commit}")
    elif args.command == "verify":
        print(f"Verified {verify_public(args.site, args.url)} public editions")
    else:
        selected_payload = prepare(args.site)
        print(
            f"Static payload: {selected_payload.files} files, "
            f"{selected_payload.total_bytes} bytes, {selected_payload.editions} editions"
        )


if __name__ == "__main__":
    main()
