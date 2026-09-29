#!/usr/bin/env python3
"""Check bundle structure and execute its Rust examples without third-party packages."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

SKILL = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^(`{3,}|~{3,})(.*)$")
LINK = re.compile(r"\[[^\]\n]+\]\(([^)\s]+)\)")
RUST_FLAGS = {"rust", "compile_fail", "no_run", "should_panic"}
OTHER_LANGUAGES = {"sh", "shell", "bash", "text", "toml", "yaml", "json", "python", "markdown"}


@dataclass(frozen=True)
class Block:
    line: int
    info: str
    code: str

    @property
    def is_rust(self) -> bool:
        return self.info.split(",", 1)[0].strip() == "rust"


def parse_markdown(text: str) -> tuple[list[Block], str]:
    """Parse the bundle's explicit, unindented fenced blocks and outside prose."""
    blocks: list[Block] = []
    prose: list[str] = []
    opening: tuple[str, str, int] | None = None
    code: list[str] = []
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if opening is None:
            if match:
                fence, info = match.groups()
                info = info.strip()
                if not info:
                    raise ValueError(f"line {number}: code fence needs an explicit language")
                if info.split(",", 1)[0].strip() != "rust" and info not in OTHER_LANGUAGES:
                    raise ValueError(f"line {number}: unsupported code-fence language: {info}")
                opening = (fence, info, number)
                code = []
            else:
                prose.append(line)
        else:
            fence, info, start = opening
            if (match and match[1][0] == fence[0]
                    and len(match[1]) >= len(fence) and not match[2].strip()):
                block = Block(start, info, "\n".join(code) + "\n")
                if block.is_rust:
                    flags = {part.strip() for part in info.split(",")}
                    unknown = flags - RUST_FLAGS
                    if unknown:
                        raise ValueError(f"line {start}: unsupported Rust flags: {sorted(unknown)}")
                    if "compile_fail" in flags and flags & {"no_run", "should_panic"}:
                        raise ValueError(f"line {start}: incompatible Rust test flags")
                blocks.append(block)
                opening = None
            else:
                code.append(line)
    if opening:
        raise ValueError(f"line {opening[2]}: unclosed code fence")
    return blocks, "\n".join(prose)


def anchors(prose: str) -> set[str]:
    result: set[str] = set()
    counts: dict[str, int] = {}
    for line in prose.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        slug = re.sub(r"[^\w\- ]", "", match[1].lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def check_links(path: Path, prose: str, repository: Path) -> None:
    """Validate local inline-link destinations; external URLs are not fetched."""
    repository = repository.resolve()
    for raw in LINK.findall(prose):
        target = urlsplit(raw)
        if target.scheme or target.netloc:
            continue
        destination = (path.parent / unquote(target.path)).resolve() if target.path else path.resolve()
        if not destination.is_relative_to(repository):
            raise ValueError(f"{path}: local link escapes repository: {raw}")
        if not destination.exists():
            raise ValueError(f"{path}: missing local link target: {raw}")
        if target.fragment and destination.suffix == ".md":
            _, target_prose = parse_markdown(destination.read_text(encoding="utf-8"))
            if unquote(target.fragment) not in anchors(target_prose):
                raise ValueError(f"{path}: missing local heading: {raw}")


def check_frontmatter(text: str) -> None:
    """Check this bundle's required fields, not the full YAML/Agent Skills spec."""
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md needs YAML frontmatter")
    header = match[1]
    patterns = {
        "name": r"^name: rust-best-practices$",
        "description": r"^description: >\n(?:  .+\n)+",
        "license": r"^license: MIT$",
        "compatibility": r"^compatibility: .+$",
        "metadata": r"^metadata:$",
        "author": r"^  author: .+$",
        "version": r'^  version: "\d+\.\d+\.\d+"$',
        "tools": r"^allowed-tools: .+$",
    }
    for label, pattern in patterns.items():
        if not re.search(pattern, header, re.MULTILINE):
            raise ValueError(f"SKILL.md missing or malformed {label}")


def rust_examples(blocks: list[Block]) -> str:
    """Use the source fences directly, adding a safe-Rust constraint to each test."""
    parts = []
    for block in blocks:
        if block.is_rust:
            parts.append(
                f"## Source line {block.line}\n\n```{block.info}\n"
                f"# #![forbid(unsafe_code)]\n{block.code}```\n"
            )
    return "\n".join(parts)


def validate_structure(skill: Path) -> tuple[list[tuple[Path, list[Block]]], int]:
    check_frontmatter((skill / "SKILL.md").read_text(encoding="utf-8"))
    documents = sorted(skill.rglob("*.md"))
    if not documents:
        raise ValueError("no Markdown documents found")
    parsed = []
    examples = 0
    for path in documents:
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            raise ValueError(f"{path}: missing final newline")
        if any(line.rstrip() != line for line in text.splitlines()):
            raise ValueError(f"{path}: trailing whitespace")
        blocks, prose = parse_markdown(text)
        check_links(path, prose, skill.parents[1])
        examples += sum(block.is_rust for block in blocks)
        parsed.append((path, blocks))
    if not examples:
        raise ValueError("no Rust examples found; refusing an empty validation pass")
    return parsed, examples


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static-only", action="store_true", help="check structure only; explicitly skip Rust execution")
    parser.add_argument("--rustdoc", default="rustdoc", help="rustdoc executable for the selected toolchain")
    args = parser.parse_args()
    try:
        parsed, count = validate_structure(SKILL)
        print(f"Structure OK: {len(parsed)} Markdown files, {count} Rust examples.", flush=True)
        if args.static_only:
            print("Rust examples NOT executed (--static-only).")
            return 0
        rustdoc = shutil.which(args.rustdoc)
        if rustdoc is None:
            raise ValueError("rustdoc unavailable; install/select the documented toolchain or explicitly use --static-only")
        subprocess.run([rustdoc, "--version"], check=True, timeout=30)
        with tempfile.TemporaryDirectory(prefix="rust-skill-tests-") as directory:
            for path, blocks in parsed:
                examples = rust_examples(blocks)
                if not examples:
                    continue
                generated = Path(directory) / path.name
                generated.write_text(examples, encoding="utf-8")
                for optimization in ("0", "3"):
                    print(f"Testing {path.relative_to(SKILL)} (opt-level={optimization})", flush=True)
                    subprocess.run(
                        [rustdoc, "--test", str(generated), "--edition=2021",
                         "-C", f"opt-level={optimization}", "-C", "overflow-checks=yes",
                         "-C", "debug-assertions=yes", "--test-args=--test-threads=1"],
                        check=True, timeout=120,
                    )
        print(f"All {count} Rust examples passed at opt-level 0 and 3.")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(f"Validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
