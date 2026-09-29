"""Regression tests for the dependency-free bundle checker."""

from pathlib import Path
import tempfile
import unittest

import validate


class ValidationTests(unittest.TestCase):
    def test_extracts_rust_and_preserves_prose(self):
        blocks, prose = validate.parse_markdown("# Heading\n```rust\nassert!(true);\n```\n")
        self.assertEqual(len(blocks), 1)
        self.assertTrue(blocks[0].is_rust)
        self.assertEqual(prose, "# Heading")

    def test_requires_explicit_language(self):
        with self.assertRaisesRegex(ValueError, "explicit language"):
            validate.parse_markdown("```\nx\n```\n")

    def test_rejects_implicit_rust_flags(self):
        with self.assertRaisesRegex(ValueError, "unsupported code-fence language"):
            validate.parse_markdown("```compile_fail\nx\n```\n")

    def test_rejects_unclosed_fence(self):
        with self.assertRaisesRegex(ValueError, "unclosed"):
            validate.parse_markdown("```rust\nx\n")

    def test_rejects_ignored_rust(self):
        with self.assertRaisesRegex(ValueError, "unsupported Rust flags"):
            validate.parse_markdown("```rust,ignore\nx\n```\n")

    def test_rejects_incompatible_flags(self):
        with self.assertRaisesRegex(ValueError, "incompatible"):
            validate.parse_markdown("```rust,compile_fail,no_run\nx\n```\n")

    def test_generated_tests_forbid_unsafe(self):
        blocks, _ = validate.parse_markdown("```rust,compile_fail\nlet x: u8 = false;\n```\n")
        generated = validate.rust_examples(blocks)
        self.assertIn("rust,compile_fail", generated)
        self.assertIn("#![forbid(unsafe_code)]", generated)
        self.assertIn("let x: u8 = false;", generated)

    def test_non_rust_is_not_executed(self):
        blocks, _ = validate.parse_markdown("```sh\necho hi\n```\n")
        self.assertEqual(validate.rust_examples(blocks), "")

    def test_duplicate_headings(self):
        self.assertEqual(validate.anchors("## Same\n## Same"), {"same", "same-1"})

    def test_links_and_missing_anchor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("# Source\n", encoding="utf-8")
            target = root / "target.md"
            target.write_text("# Present\n", encoding="utf-8")
            validate.check_links(source, "[ok](target.md#present)", root)
            with self.assertRaisesRegex(ValueError, "missing local heading"):
                validate.check_links(source, "[bad](target.md#absent)", root)
            with self.assertRaisesRegex(ValueError, "missing local link"):
                validate.check_links(source, "[bad](absent.md)", root)
            with self.assertRaisesRegex(ValueError, "escapes repository"):
                validate.check_links(source, "[bad](../outside.md)", root)

    def test_external_links_are_not_fetched(self):
        validate.check_links(Path("source.md"), "[source](https://example.invalid/x)", Path.cwd())

    def test_frontmatter_is_required(self):
        with self.assertRaisesRegex(ValueError, "frontmatter"):
            validate.check_frontmatter("# No frontmatter\n")


if __name__ == "__main__":
    unittest.main()
