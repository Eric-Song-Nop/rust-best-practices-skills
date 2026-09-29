---
name: rust-best-practices
description: >
  Write, review, and optimize Rust with explicit ownership, accurate language
  semantics, and evidence-driven performance decisions. Use this skill when:
  (1) implementing or refactoring Rust,
  (2) designing ownership, error, or concurrency boundaries,
  (3) investigating runtime, allocation, or code-size costs,
  (4) building performance-sensitive libraries, interpreters, or embedded systems,
  (5) reviewing Rust tests, documentation, or performance claims.
license: MIT
compatibility: Follow the project's Rust toolchain and MSRV. Bundled examples target Rust 1.85+ and edition 2021; validation requires Python 3.10+ and rustdoc.
metadata:
  author: Eric-Song-Nop
  version: "2.0.0"
  upstream: apollographql/skills
allowed-tools: Bash(cargo:*) Bash(rustc:*) Bash(rustdoc:*) Bash(rustfmt:*) Bash(python3:*) Read Write Edit Glob Grep
---

# Rust Best Practices

Build correct, maintainable Rust. For performance work, optimize the work that
survives compilation and the resources that matter to the actual workload.
This fork replaces the original handbook-derived rules; see the
[maintenance guide](README.md) for scope and validation.

## Start with the project

Read repository instructions, the affected implementation and callers, manifests,
lockfile, toolchain, target configuration, and relevant tests. Establish the MSRV
(minimum supported Rust version), edition, feature combinations, deployment
hardware, and resource constraints. Do not upgrade dependencies or the toolchain
just to use a preferred lint, API, or syntax.

Separate the requested outcome: correctness, maintainability, API design,
performance, or a combination. Do not label an idiomatic rewrite a speedup.
Use project-specific contracts over generic preferences. Preserve a safe-Rust
boundary; this skill does not introduce `unsafe` to obtain an optimization.
A dependency's safe API may internally use unsafe code: that is distinct from
permission to add unsafe code to the project.

## Load the relevant references

Read the chapters needed for the task, not the entire bundle by default.
For performance changes, read chapter 3 plus the relevant implementation topics.
For ordinary edits, use the affected topic and the project's normal checks;
a benchmark campaign is not a prerequisite for fixing a typo or clarifying an API.

| Task | Reference |
| --- | --- |
| Ownership, moves, iteration, numeric semantics | [1. Ownership and expressions](references/chapter_01.md) |
| Toolchains, feature matrices, Clippy | [2. Tooling and lints](references/chapter_02.md) |
| Finding opportunities and validating gains | [3. Performance workflow](references/chapter_03.md) |
| Failures, invariants, transactional mutation | [4. Errors and commit boundaries](references/chapter_04.md) |
| Behavioral, differential, and compile-fail tests | [5. Testing](references/chapter_05.md) |
| Generics, trait objects, inlining, generated code | [6. Dispatch and code generation](references/chapter_06.md) |
| Typestate, validation, proof lifetime | [7. Proof-carrying interfaces](references/chapter_07.md) |
| Comments, contracts, reviews, evidence | [8. Documentation](references/chapter_08.md) |
| Cells, reference counting, threads, async | [9. Sharing and concurrency](references/chapter_09.md) |
| Allocation, layout, locality, embedded memory | [10. Data representation](references/chapter_10.md) |
| Compiler-planned execution and runtime operations | [11. Compiler and interpreter hot paths](references/chapter_11.md) |
| Recording a performance experiment | [Performance report template](references/performance-report.md) |

## Non-negotiable correctness constraints

Preserve specified results and observable behavior: evaluation order, arithmetic
and overflow semantics, errors and their timing, externally visible mutation,
resource release, cancellation, identity, generation checks, and aliasing rules.
Apply the relevant subset to the project; do not invent guest-language or
real-time requirements for unrelated code.

Distinguish malformed external input, recoverable failure, optimization misses,
and internal invariant violations. Keep required validation on untrusted paths.
Do not replace checks with `debug_assert!` when release correctness needs them,
or silently change panic, allocation-failure, or drop behavior.

A source-level proof, a compiler optimization, and a measured speedup are three
different claims. A private constructor can enforce an invariant without making
LLVM eliminate a later branch. A type marker does not establish the identity or
current generation of a runtime object by itself.

## Performance workflow

1. **Define the operation and objective.** Identify the real caller and workload,
   its frequency and input distribution, and the latency, throughput, memory,
   startup, or code-size objective. Inspect evidence where available. An explicit
   structural cost model is enough to propose an experiment; measurement is
   required to claim a gain, not to obtain permission to explore a better design.
2. **Account for work.** Write a before/after ledger of lookups, decoding, checks,
   allocations, copies, reference-count changes, synchronization, dispatches,
   and result materialization. Include guards, misses, metadata, setup, and cleanup.
   Prefer eliminating repeated work over adding another narrowly guarded path.
3. **Change the right boundary.** Permit replacing helpers, ownership interfaces,
   data layouts, or execution boundaries. Correctness contracts are constraints;
   historical abstractions are not. Choose a coherent high-upside change rather
   than accumulating independent micro-optimizations or speculative infrastructure.
4. **Implement and test the contract.** Make static facts explicit where possible.
   Admit dynamic facts at the widest valid scope, carry the useful capability,
   and invalidate it correctly. Test success, miss, error, and invalidation paths.
5. **Inspect and measure proportionately.** For a hot-path cost claim, inspect the
   relevant optimized generated code. Compare fixed-work baseline and candidate
   runs under matching conditions, then check representative workloads and affected
   resource budgets. Keep diagnostic instrumentation out of timing runs unless it
   is part of the shipped configuration.
6. **Report the result precisely.** Separate semantic correctness, work removed,
   generated-code changes, and measured outcomes. State unmeasured dimensions and
   uncertainty. Keep, revise, or remove the change against the project's objective,
   not an arbitrary universal percentage threshold.

An infrastructure-only change may be valuable without improving speed; label it
as such. A local regression can be an acceptable documented tradeoff when the
whole-workload objective improves within hard budgets. Do not retain unsuccessful
complexity indefinitely under a performance label.

## Decision rules, not syntax rankings

Choose borrowing, moving, or cloning from the required ownership transition.
`Copy` is not a universal cheapness threshold, and moving is not cloning.
Choose iteration style for semantics and clarity, then inspect code generation
where it matters. Do not rank `.iter()` above `.into_iter()`, `.sum()` above
`.fold()`, or iterator chains above equivalent loops by spelling alone.

Choose dispatch at the call site. Neither generics nor `dyn Trait` guarantees the
best overall performance. Treat inlining, boxing, small-vector storage, caching,
and structure-of-arrays as hypotheses with workload-dependent tradeoffs.
Clippy is a source of diagnostics, not a profiler or authority over measured
layout decisions.

## Deliver the work

Use repository checks and supported target/feature combinations. Report exactly
which commands ran and their results; disclose unavailable tools and skipped
checks. Do not claim benchmarks, code-generation inspection, or target-device
validation that did not run. Do not manufacture timings from source reasoning.

In reviews, prioritize correctness and high-impact costs before style. Give the
specific location, failure or cost mechanism, proposed change, and supporting
proof or evidence. Mark an unmeasured performance concern as a hypothesis rather
than a demonstrated regression. Keep follow-up work focused on the objective.
