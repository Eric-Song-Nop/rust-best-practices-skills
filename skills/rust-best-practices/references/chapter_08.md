# Chapter 8 - Documentation

## Document the contract where it is used

Use `///` for an item's documentation and `//!` for its enclosing module or
crate. Explain behavior, inputs, results, errors, panics, resource ownership,
and concurrency or cancellation requirements when relevant. Include enough
rationale to prevent misuse; "why" is not forbidden in public API documentation.
See [documentation comments](https://doc.rust-lang.org/reference/comments.html#doc-comments).

Use local comments for non-obvious invariants, proof boundaries, evaluation order,
and optimization constraints. A long but necessary explanation is better than
a short misleading one. Extract a helper when its contract improves the code,
not to obey a comment-length limit. Conversely, do not leave a wall of narrative
that merely repeats each statement.

Comments, tests, and design documents can all become stale. Update the relevant
ones with the implementation. Move broad design rationale into a versioned
record, but keep the local invariant and link close to its consumer. Do not
remove a safety or correctness explanation just because the syntax looks clear.

## Make performance statements auditable

Distinguish an intended effect from a measured one. A useful record identifies
the operation, before/after work, compiler and target, workload, result, and
limitations. Avoid timeless claims such as "this always vectorizes" or "generics
have no cost." A code-generation observation applies to the inspected build.

For a reusable proof, document:

```text
Established fact:
Subject and identity:
Producer and required validation:
Consumers:
Validity scope and invalidating operations:
How invalidation is prevented or detected:
Required behavior on miss or error:
Generated-code evidence, if inspected:
```

For a measured implementation choice, link a concise
[performance report](performance-report.md). Keep explanatory comments about
necessary behavior even when a benchmark report is available; timing data is not
a substitute for semantic reasoning.

## Write examples that can be checked

Use self-contained executable Rust examples for behavior. Use `compile_fail` to
show an invalid API operation and `no_run` only when execution requires an
external environment. Label genuine pseudocode `text`; do not write incomplete
Rust and present it as a working example.

The bundled validator executes Rust fences directly from these Markdown files,
so the examples are the tested source rather than copies in a disconnected test
crate. Negative examples establish compilation failure, not necessarily an exact
diagnostic; add targeted UI tests when that distinction matters.
See [rustdoc documentation tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html).

Use the repository's documentation checks. Enable lints such as missing docs or
broken intra-doc links when they fit its public API policy; do not impose a
project-wide lint migration in a small change. Ordinary Markdown links are not
all checked by rustdoc, so validate local links separately.
See [rustdoc lints](https://doc.rust-lang.org/rustdoc/lints.html).

## Keep reviews and maintenance actionable

For a finding, provide a location, the violated contract or plausible cost,
consequences, and a concrete correction. Mark measured regressions, code-derived
facts, and unmeasured hypotheses differently. Avoid large style-only rewrites
inside a performance experiment because they obscure attribution.

Track substantial deferred work with an issue or versioned task reference when
available. A local TODO can state a concrete condition for removal; do not invent
an issue number to satisfy a format rule or require a remote issue for every
minor note. Follow the project's tracking convention.

For this fork, keep the entry point and references consistent, retain upstream
license attribution, bump versions required by repository CI, and re-run example
validation after edits. Source links explain language and library contracts;
performance recommendations remain workload-dependent decisions.
