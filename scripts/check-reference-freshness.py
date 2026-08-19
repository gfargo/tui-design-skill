#!/usr/bin/env python3
"""Audit version-sensitive framework references for staleness and dead links.

Reads the explicit inventory in scripts/reference-inventory.json and, for each
entry, either compares a pinned framework version against that framework's
primary package registry ("pinned_version") or checks that a cited source
link still resolves ("source_link"). This script never edits skill content or
the inventory; it only reports what a human should review. Network or parse
failures are reported as "unknown", not "stale"/"broken", so a transient
outage or a scraper-hostile 403 does not fail CI on its own.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = REPO_ROOT / "scripts/reference-inventory.json"
USER_AGENT = "tui-design-skill-reference-freshness-audit (+https://github.com/gfargo/tui-design-skill)"
GITHUB_BLOB_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$")
VERSION_RE = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?")
GRANULARITY_LENGTH = {"major": 1, "minor": 2, "patch": 3, "exact": 3}
REVIEW_STATUSES = {"stale", "broken"}


class AuditError(RuntimeError):
    """A structural problem with the inventory or script usage, not a per-entry finding."""


def http_get_json(url: str, timeout: float) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def go_module_escape(module: str) -> str:
    # https://go.dev/ref/mod#module-proxy: uppercase letters are escaped as "!lowercase".
    return re.sub(r"[A-Z]", lambda match: "!" + match.group(0).lower(), module)


def fetch_go_proxy_latest(registry: dict[str, Any], timeout: float) -> str:
    module = go_module_escape(registry["module"])
    data = http_get_json(f"https://proxy.golang.org/{module}/@latest", timeout)
    return str(data["Version"])


def fetch_crates_io_latest(registry: dict[str, Any], timeout: float) -> str:
    data = http_get_json(f"https://crates.io/api/v1/crates/{registry['crate']}", timeout)
    return str(data["crate"]["max_stable_version"])


def fetch_pypi_latest(registry: dict[str, Any], timeout: float) -> str:
    data = http_get_json(f"https://pypi.org/pypi/{registry['package']}/json", timeout)
    return str(data["info"]["version"])


def fetch_npm_latest(registry: dict[str, Any], timeout: float) -> str:
    data = http_get_json(f"https://registry.npmjs.org/{registry['package']}/latest", timeout)
    return str(data["version"])


REGISTRY_FETCHERS = {
    "go_proxy": fetch_go_proxy_latest,
    "crates_io": fetch_crates_io_latest,
    "pypi": fetch_pypi_latest,
    "npm": fetch_npm_latest,
}


def parse_version(value: str) -> tuple[int, int, int]:
    text = value.strip()
    if text[:1] in ("v", "V"):
        text = text[1:]
    match = VERSION_RE.match(text)
    if not match:
        raise AuditError(f"cannot parse version: {value!r}")
    major, minor, patch = (int(group) if group is not None else 0 for group in match.groups())
    return (major, minor, patch)


def version_slice(version: tuple[int, int, int], granularity: str) -> tuple[int, ...]:
    length = GRANULARITY_LENGTH.get(granularity)
    if length is None:
        raise AuditError(f"unknown granularity: {granularity!r}")
    return version[:length]


def github_blob_to_raw(url: str) -> str:
    """Rewrite a github.com blob URL to raw.githubusercontent.com.

    GitHub's web frontend can 403 well-behaved automated requests regardless
    of whether the file exists; the raw content host does not and gives a
    clean 200/404 distinction, so link checks use it when possible.
    """
    match = GITHUB_BLOB_RE.match(url)
    if not match:
        return url
    owner, repo, ref, path = match.groups()
    path = path.split("#", 1)[0].split("?", 1)[0]
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


def evaluate_pinned_version(entry: dict[str, Any], timeout: float) -> tuple[str, str]:
    registry = entry.get("registry") or {}
    fetcher = REGISTRY_FETCHERS.get(registry.get("type"))
    if fetcher is None:
        raise AuditError(f"{entry.get('id')}: unknown registry type {registry.get('type')!r}")
    try:
        latest_raw = fetcher(registry, timeout)
    except AuditError:
        raise
    except Exception as exc:  # noqa: BLE001 - any fetch/network failure is inconclusive, not a hard error
        return "unknown", f"could not fetch latest version ({registry.get('type')}): {exc}"

    pinned_raw = entry.get("pinned_version")
    if not isinstance(pinned_raw, str) or not pinned_raw:
        raise AuditError(f"{entry.get('id')}: pinned_version must be a non-empty string")
    granularity = entry.get("granularity", "minor")

    try:
        pinned = parse_version(pinned_raw)
        latest = parse_version(latest_raw)
        matches = version_slice(pinned, granularity) == version_slice(latest, granularity)
    except AuditError as exc:
        return "unknown", str(exc)

    if matches:
        return "current", f"pinned {pinned_raw} matches latest {latest_raw} ({granularity})"
    return "stale", f"pinned {pinned_raw} — latest is {latest_raw} ({granularity})"


def evaluate_source_link(entry: dict[str, Any], timeout: float) -> tuple[str, str]:
    url = entry.get("url")
    if not isinstance(url, str) or not url:
        raise AuditError(f"{entry.get('id')}: url must be a non-empty string")
    check_url = github_blob_to_raw(url)
    request = urllib.request.Request(check_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if 200 <= response.status < 400:
                return "ok", f"HTTP {response.status}"
            return "unknown", f"HTTP {response.status} (inconclusive)"
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            return "broken", f"HTTP {exc.code}"
        return "unknown", f"HTTP {exc.code} (may be automated-request blocking, not necessarily broken)"
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return "unknown", f"network error: {exc}"


def load_inventory(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read inventory {path}: {exc}") from exc
    references = data.get("references")
    if not isinstance(references, list) or not references:
        raise AuditError(f"{path} must contain a non-empty 'references' list")
    seen: set[str] = set()
    for entry in references:
        entry_id = entry.get("id") if isinstance(entry, dict) else None
        if not isinstance(entry_id, str) or not entry_id:
            raise AuditError("every reference entry needs a non-empty string id")
        if entry_id in seen:
            raise AuditError(f"duplicate reference id: {entry_id!r}")
        seen.add(entry_id)
        if entry.get("kind") not in ("pinned_version", "source_link"):
            raise AuditError(f"{entry_id}: kind must be 'pinned_version' or 'source_link'")
    return references


def run_audit(references: list[dict[str, Any]], timeout: float) -> list[dict[str, Any]]:
    results = []
    for entry in references:
        if entry["kind"] == "pinned_version":
            status, detail = evaluate_pinned_version(entry, timeout)
        else:
            status, detail = evaluate_source_link(entry, timeout)
        results.append({**entry, "status": status, "detail": detail})
    return results


def render_report(results: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    by_framework: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        by_framework.setdefault(result["framework"], []).append(result)

    for framework in sorted(by_framework):
        lines.append(f"== {framework} ==")
        for result in by_framework[framework]:
            label = "pinned version" if result["kind"] == "pinned_version" else "source link"
            target = result.get("claim") or result.get("url")
            lines.append(f"[{result['status']}] {label}: {target}")
            lines.append(f"    {result['detail']}")
        lines.append("")

    total = len(results)
    needs_review = [result for result in results if result["status"] in REVIEW_STATUSES]
    unknown = [result for result in results if result["status"] == "unknown"]
    lines.append(f"{total} checked; {len(needs_review)} need review; {len(unknown)} inconclusive.")
    if needs_review:
        lines.append("Needs review:")
        for result in needs_review:
            lines.append(f"  - [{result['status']}] {result['id']} ({result['file']}): {result['detail']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY), help="path to reference-inventory.json")
    parser.add_argument("--output", help="optional path to write the full JSON report")
    parser.add_argument("--timeout", type=float, default=15.0, help="per-request network timeout in seconds")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        references = load_inventory(Path(args.inventory))
        results = run_audit(references, args.timeout)
    except AuditError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(render_report(results))
    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")

    return 1 if any(result["status"] in REVIEW_STATUSES for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
