# Rust best practices - maintained fork

This is an independent rewrite of the `rust-best-practices` skill in
`Eric-Song-Nop/rust-best-practices-skills`. Install this fork's
`skills/rust-best-practices` directory using your agent's skill installer, and keep
its references with it. The skill name and original chapter paths remain stable.
Other Apollo skills in the repository are outside this rewrite's scope.

The skill covers ordinary Rust implementation and review as well as high-performance
safe Rust. It is not specific to one VM, architecture, allocator, or benchmark.
Project semantics, MSRV, supported targets, and resource constraints remain the
source of requirements. Read the [entry point](SKILL.md) for topic routing.

## What changed in version 2.0.0

All nine original chapters and the entry point are rewritten. Two chapters add
[data representation](references/chapter_10.md) and
[compiler/interpreter operations](references/chapter_11.md), plus an adaptable
[performance report](references/performance-report.md).

The rewrite removes several false or overly broad rules:

| Previous problem | Replacement |
| --- | --- |
| `Cell<T>` described as Copy-only | Method-specific bounds and executable non-Copy ownership examples |
| Incorrect unconditional Send/Sync table | Conditional bounds, valid scoped borrowing, and compile-fail coverage |
| Copy-size thresholds and borrowed iteration treated as speed rules | Ownership transitions, representation, and generated-code evidence |
| `.sum()` versus `.fold()` justified by an opaque closure claim | Standard-library implementation reference and a numeric-order counterexample |
| Typestate markers treated as eliminated dynamic checks | State-specific payloads, scoped admission, identity, and invalidation |
| Generics, boxing, and iterators treated as universal winners | Call-site and workload-dependent decisions |
| Blanket panic, lint, comment, and assertion-count rules | Explicit contracts and project-scoped policy |
| Minimal benchmark recipe used as performance acceptance | Fixed-work comparisons, whole-workload costs, uncertainty, and proportionate gates |

The performance workflow permits replacing old helpers and dataflow to delete
work. It does not require preserving every old abstraction, adding a planner,
collecting every metric for every edit, or rejecting every local regression.
It does require honest claims and preservation of the chosen correctness contract.

## Validate this bundle

The examples target Rust 1.85 or later and edition 2021. This is the bundle's
example baseline, not a recommendation to upgrade a consuming project.
Use Python 3.10 or later. The checker needs no Python packages or Cargo crates.
From the repository root:

```sh
python3 -m unittest discover -s skills/rust-best-practices/scripts -p 'test_*.py'
python3 skills/rust-best-practices/scripts/validate.py
```

The second command checks required frontmatter fields, explicit/balanced fences,
local inline links and headings, then extracts the actual Rust examples and runs
rustdoc at optimization levels 0 and 3. Both modes retain overflow checks and
debug assertions; these are example-correctness runs, not production benchmarks.
Each example receives `forbid(unsafe_code)`. Intentional `compile_fail` examples
must fail to compile. Ignored Rust fences and a zero-example bundle are rejected.

Missing rustdoc is a failure, not an automatic skip. For a documented structure-only
check in an environment without Rust, run:

```sh
python3 skills/rust-best-practices/scripts/validate.py --static-only
```

That command explicitly reports Rust execution as skipped. The structure checker
is tailored to this bundle's unindented, explicitly labeled fences and local inline
links; it is not a general Markdown parser or full Agent Skills specification
validator. External URLs are not fetched by this check. Use the repository's skill
format validation as well.

The [Rust skill workflow](../../.github/workflows/rust-skill.yml) runs the checker
and example tests on Rust 1.85.0 and current stable for relevant pull requests.
Do not claim a passing workflow until its actual result is available. These tests
check examples and format; they do not benchmark a downstream application or prove
all performance guidance on every target.

## Maintenance and attribution

Keep the concise entry point consistent with the references. Add primary-source
links for language and library claims. Compile new examples and add a paired valid
case for negative API examples. Re-check target/toolchain-sensitive claims rather
than replacing them with universal thresholds. Bump the skill version and the
plugin version when required by repository CI.

The fork derives from Apollo GraphQL's MIT-licensed skill bundle. The original
[repository license](../../LICENSE) and attribution are retained. This rewrite's
metadata identifies the fork maintainer rather than implying Apollo endorsement.
