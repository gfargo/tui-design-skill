from __future__ import annotations

import http.server
import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts/check-reference-freshness.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_reference_freshness", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        if self.path == "/ok":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        elif self.path == "/redirect-to-ok":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
        elif self.path == "/gone":
            self.send_response(410)
            self.end_headers()
        elif self.path == "/forbidden":
            self.send_response(403)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - silence default access log
        pass


class ReferenceFreshnessUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), _FixtureHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def base_url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_parse_version_handles_prefix_and_missing_components(self) -> None:
        self.assertEqual(self.module.parse_version("v2.0.8"), (2, 0, 8))
        self.assertEqual(self.module.parse_version("8"), (8, 0, 0))
        self.assertEqual(self.module.parse_version("0.30.2"), (0, 30, 2))

    def test_parse_version_rejects_garbage(self) -> None:
        with self.assertRaises(self.module.AuditError):
            self.module.parse_version("not-a-version")

    def test_version_slice_granularities(self) -> None:
        version = (2, 1, 8)
        self.assertEqual(self.module.version_slice(version, "major"), (2,))
        self.assertEqual(self.module.version_slice(version, "minor"), (2, 1))
        self.assertEqual(self.module.version_slice(version, "patch"), (2, 1, 8))
        self.assertEqual(self.module.version_slice(version, "exact"), (2, 1, 8))

    def test_github_blob_urls_rewrite_to_raw_and_drop_fragment(self) -> None:
        rewritten = self.module.github_blob_to_raw(
            "https://github.com/charmbracelet/bubbletea/blob/v2.0.8/tea.go#L10"
        )
        self.assertEqual(rewritten, "https://raw.githubusercontent.com/charmbracelet/bubbletea/v2.0.8/tea.go")

    def test_non_github_urls_are_unchanged(self) -> None:
        url = "https://ratatui.rs/recipes/apps/spawn-vim/"
        self.assertEqual(self.module.github_blob_to_raw(url), url)

    def test_evaluate_pinned_version_reports_current(self) -> None:
        entry = {
            "id": "fixture-current",
            "pinned_version": "2.0.8",
            "granularity": "major",
            "registry": {"type": "fixture"},
        }
        with self._patched_fetcher(lambda registry, timeout: "v2.0.9"):
            status, detail = self.module.evaluate_pinned_version(entry, timeout=1.0)
        self.assertEqual(status, "current")
        self.assertIn("2.0.8", detail)

    def test_evaluate_pinned_version_reports_stale(self) -> None:
        entry = {
            "id": "fixture-stale",
            "pinned_version": "0.30.2",
            "granularity": "minor",
            "registry": {"type": "fixture"},
        }
        with self._patched_fetcher(lambda registry, timeout: "0.31.0"):
            status, detail = self.module.evaluate_pinned_version(entry, timeout=1.0)
        self.assertEqual(status, "stale")
        self.assertIn("0.31.0", detail)

    def test_evaluate_pinned_version_fetch_failure_is_unknown_not_a_hard_error(self) -> None:
        def raise_network_error(registry, timeout):
            raise OSError("boom")

        entry = {
            "id": "fixture-unreachable",
            "pinned_version": "1.0.0",
            "granularity": "major",
            "registry": {"type": "fixture"},
        }
        with self._patched_fetcher(raise_network_error):
            status, detail = self.module.evaluate_pinned_version(entry, timeout=1.0)
        self.assertEqual(status, "unknown")
        self.assertIn("boom", detail)

    def test_evaluate_pinned_version_rejects_unknown_registry_type(self) -> None:
        entry = {
            "id": "fixture-bad-registry",
            "pinned_version": "1.0.0",
            "granularity": "major",
            "registry": {"type": "does-not-exist"},
        }
        with self.assertRaises(self.module.AuditError):
            self.module.evaluate_pinned_version(entry, timeout=1.0)

    def test_evaluate_source_link_ok_and_broken_and_ambiguous(self) -> None:
        ok_status, _ = self.module.evaluate_source_link({"id": "ok", "url": self.base_url("/ok")}, timeout=5.0)
        self.assertEqual(ok_status, "ok")

        redirect_status, _ = self.module.evaluate_source_link(
            {"id": "redirect", "url": self.base_url("/redirect-to-ok")}, timeout=5.0
        )
        self.assertEqual(redirect_status, "ok")

        broken_status, _ = self.module.evaluate_source_link({"id": "gone", "url": self.base_url("/gone")}, timeout=5.0)
        self.assertEqual(broken_status, "broken")

        # A 403 is treated as inconclusive: scraper-hostile sites return it for live links too.
        ambiguous_status, detail = self.module.evaluate_source_link(
            {"id": "forbidden", "url": self.base_url("/forbidden")}, timeout=5.0
        )
        self.assertEqual(ambiguous_status, "unknown")
        self.assertIn("403", detail)

    def test_evaluate_source_link_network_error_is_unknown(self) -> None:
        status, detail = self.module.evaluate_source_link(
            {"id": "unreachable", "url": "http://127.0.0.1:1/never"}, timeout=1.0
        )
        self.assertEqual(status, "unknown")
        self.assertIn("network error", detail)

    def test_load_inventory_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(
                json.dumps(
                    {
                        "references": [
                            {"id": "dup", "framework": "X", "kind": "source_link", "file": "f.md", "url": "https://example.com"},
                            {"id": "dup", "framework": "X", "kind": "source_link", "file": "f.md", "url": "https://example.com"},
                        ]
                    }
                )
            )
            with self.assertRaises(self.module.AuditError):
                self.module.load_inventory(path)

    def test_load_inventory_rejects_unknown_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(
                json.dumps(
                    {"references": [{"id": "a", "framework": "X", "kind": "not-a-kind", "file": "f.md"}]}
                )
            )
            with self.assertRaises(self.module.AuditError):
                self.module.load_inventory(path)

    def test_real_inventory_file_loads_and_is_internally_consistent(self) -> None:
        references = self.module.load_inventory(REPO_ROOT / "scripts/reference-inventory.json")
        self.assertGreaterEqual(len(references), 1)
        for entry in references:
            if entry["kind"] == "pinned_version":
                self.assertIn(entry["registry"]["type"], self.module.REGISTRY_FETCHERS)

    def _patched_fetcher(self, fetcher):
        return mock.patch.dict(self.module.REGISTRY_FETCHERS, {"fixture": fetcher})


class ReferenceFreshnessCliTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), _FixtureHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def base_url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def write_inventory(self, directory: Path, urls: list[str]) -> Path:
        path = directory / "inventory.json"
        path.write_text(
            json.dumps(
                {
                    "references": [
                        {
                            "id": f"link-{index}",
                            "framework": "Fixture",
                            "kind": "source_link",
                            "file": "fixture.md",
                            "url": url,
                        }
                        for index, url in enumerate(urls)
                    ]
                }
            )
        )
        return path

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], text=True, capture_output=True, check=False
        )

    def test_cli_exits_zero_when_everything_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory = self.write_inventory(Path(directory), [self.base_url("/ok")])
            completed = self.invoke("--inventory", str(inventory))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("[ok]", completed.stdout)

    def test_cli_exits_one_and_writes_json_report_when_a_link_is_broken(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory = self.write_inventory(Path(directory), [self.base_url("/ok"), self.base_url("/gone")])
            output = Path(directory) / "report.json"
            completed = self.invoke("--inventory", str(inventory), "--output", str(output))
            self.assertEqual(completed.returncode, 1, completed.stderr)
            report = json.loads(output.read_text())
        statuses = {entry["status"] for entry in report}
        self.assertIn("broken", statuses)

    def test_cli_exits_two_on_malformed_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            path.write_text(json.dumps({"references": []}))
            completed = self.invoke("--inventory", str(path))
        self.assertEqual(completed.returncode, 2)
        self.assertIn("error:", completed.stderr)

    def test_cli_rejects_non_positive_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory = self.write_inventory(Path(directory), [self.base_url("/ok")])
            completed = self.invoke("--inventory", str(inventory), "--timeout", "0")
        self.assertEqual(completed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
