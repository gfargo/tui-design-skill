import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts/check-samples.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_samples", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


samples_tool = load_module()

REFERENCE = """# Reference

```go check=go/hello
package main

func main() {}
```

An unmarked fence is ignored:

```go
this is not checked
```

- A list item with an indented fence:
  ```rust check=rust/clap
  struct Cli {
      verbose: bool,
  }

  // In main:
  let cli = Cli { verbose: true };
  ```
"""


class CheckSamplesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.reference = self.root / "reference.md"
        self.reference.write_text(REFERENCE, encoding="utf-8")
        self.harness_root = self.root / "samples"
        for harness in ("go", "rust"):
            (self.harness_root / harness).mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, relative, text):
        path = self.harness_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def samples(self):
        return samples_tool.collect_samples([self.reference])

    def errors(self):
        placeholders = samples_tool.collect_placeholders(self.harness_root)
        return samples_tool.verify(self.samples(), placeholders, self.harness_root)

    def use_both_samples(self):
        self.write("go/main.go.tmpl", "<<sample go/hello>>\n")
        self.write(
            "rust/src/main.rs.tmpl",
            '<<sample rust/clap until="// In main">>\n\nfn main() {\n    <<sample rust/clap from="let cli">>\n}\n',
        )

    def test_marked_fences_are_collected_and_unmarked_fences_ignored(self):
        samples = self.samples()
        self.assertEqual(sorted(samples), ["go/hello", "rust/clap"])
        self.assertEqual(samples["go/hello"].line, 3)
        self.assertNotIn("not checked", "".join(sample.text for sample in samples.values()))

    def test_indented_fence_content_is_dedented(self):
        self.assertTrue(self.samples()["rust/clap"].text.startswith("struct Cli {\n    verbose: bool,"))

    def test_consistent_harness_verifies_and_renders_with_reindented_splits(self):
        self.use_both_samples()
        self.write("rust/Cargo.toml", "[package]\n")
        self.assertEqual(self.errors(), [])
        out = self.root / "out"
        source_map = samples_tool.render(self.samples(), out, harness_root=self.harness_root)
        self.assertEqual(
            (out / "rust/src/main.rs").read_text(),
            "struct Cli {\n    verbose: bool,\n}\n\nfn main() {\n    let cli = Cli { verbose: true };\n}\n",
        )
        self.assertTrue((out / "rust/Cargo.toml").is_file())
        self.assertFalse((out / "go/main.go.tmpl").exists())
        self.assertIn("go/hello  ", "\n".join(source_map))
        self.assertTrue(any(line.endswith("rust/src/main.rs:6-6") for line in source_map), source_map)

    def test_marked_sample_without_a_template_is_an_error(self):
        self.write("go/main.go.tmpl", "<<sample go/hello>>\n")
        errors = self.errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("rust/clap is not used by any *.tmpl file", errors[0])

    def test_marked_sample_without_a_harness_directory_is_an_error(self):
        (self.harness_root / "rust").rmdir()
        self.write("go/main.go.tmpl", "<<sample go/hello>>\n")
        self.assertIn("has no harness directory", " ".join(self.errors()))

    def test_placeholder_for_unknown_or_foreign_sample_is_an_error(self):
        self.use_both_samples()
        self.write("go/extra.go.tmpl", "<<sample go/missing>>\n<<sample rust/clap>>\n")
        errors = " ".join(self.errors())
        self.assertIn("unknown sample go/missing", errors)
        self.assertIn("belongs to another harness than go", errors)

    def test_option_that_matches_nothing_is_an_error(self):
        self.use_both_samples()
        self.write("go/extra.go.tmpl", '<<sample go/hello drop="fmt.Println">>\n')
        self.assertIn("drop='fmt.Println' matches no line of go/hello", " ".join(self.errors()))

    def test_drop_removes_matching_lines(self):
        placeholder = samples_tool.parse_placeholder('<<sample go/hello drop="func main">>', Path("t.tmpl"), 1)
        self.assertEqual(samples_tool.select_lines(self.samples()["go/hello"], placeholder), ["package main"])

    def test_invalid_placeholder_option_is_rejected(self):
        with self.assertRaises(samples_tool.SampleError):
            samples_tool.parse_placeholder('<<sample go/hello after="x">>', Path("t.tmpl"), 1)

    def test_duplicate_and_invalid_ids_are_rejected(self):
        self.reference.write_text(REFERENCE + "\n```go check=go/hello\n```\n", encoding="utf-8")
        with self.assertRaisesRegex(samples_tool.SampleError, "duplicate sample id go/hello"):
            self.samples()
        self.reference.write_text("```go check=Hello\n```\n", encoding="utf-8")
        with self.assertRaisesRegex(samples_tool.SampleError, "invalid sample id"):
            self.samples()

    def test_unclosed_marked_fence_is_rejected(self):
        self.reference.write_text("```go check=go/hello\npackage main\n", encoding="utf-8")
        with self.assertRaisesRegex(samples_tool.SampleError, "never closed"):
            self.samples()

    def test_build_products_are_not_copied(self):
        self.use_both_samples()
        self.write("rust/target/debug/junk", "x")
        out = self.root / "out"
        samples_tool.render(self.samples(), out, ["rust"], harness_root=self.harness_root)
        self.assertFalse((out / "rust/target").exists())
        self.assertFalse((out / "go").exists())

    def test_repository_markers_match_the_harness_templates(self):
        samples, placeholders = samples_tool.load()
        self.assertGreater(len(samples), 0)
        self.assertEqual({placeholder.id for placeholder in placeholders}, set(samples))


if __name__ == "__main__":
    unittest.main()
