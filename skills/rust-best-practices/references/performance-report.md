# Performance report template

Use this for a substantial performance change. Remove inapplicable sections and
mark unavailable evidence as unmeasured; do not fill missing values with zero.
For a small change, a compact equivalent in the PR description is sufficient.

## Objective and contract

- Operation, real callers, workload/input distribution, and resource objective.
- Hard budgets and preserved semantics, including ownership and failure behavior.
- Why this change has a meaningful opportunity; alternatives deliberately excluded.

## Implementation and work ledger

| Work per logical operation | Baseline | Candidate | Evidence or hypothesis |
| --- | --- | --- | --- |
| Repeated lookups/checks/decoding | | | |
| Allocations/copies/reference counting | | | |
| Dispatch/result materialization | | | |
| Added guards/misses/metadata/cleanup | | | |

Identify proof producer, subject, validity scope, consumers, and invalidators.
Explain which helper or representation boundary changed and why. Do not turn
source-level operation counts into measured instruction counts.

## Reproduction

Record baseline/candidate SHAs; compiler and LLVM versions; target CPU/OS;
profile, features, codegen flags, allocator, dependency/lockfile hash; benchmark
harness and input hashes; exact build and run commands; warm-up policy; logical
work per run; run ordering; sample count; and relevant load/environment controls.
Keep paths to raw results and inspected code-generation artifacts.

## Correctness and reachability

Record tests actually run and outcomes. Include fast-path hits, intended misses,
errors, invalidation, and observable state/ownership equivalence where relevant.
For planned execution, verify actual emitted descriptors and production reachability.
Explain diagnostic instrumentation and whether it is absent from timing builds.

## Measurements

| Workload or phase | Baseline value/unit | Candidate value/unit | Relative change | Samples and uncertainty |
| --- | --- | --- | --- | --- |
| Target operation | | | | |
| Non-applicable/miss case | | | | |
| Representative application | | | | |
| Startup/planning/teardown | | | | |
| Memory/capacity/peak | | | | |
| Binary or hot text size | | | | |

Separate fixed-work measurements from adaptive scores. Include cumulative and
infrastructure-only comparisons when needed. Distinguish latency from throughput,
cycles from instructions, and live bytes from capacity/RSS. Do not sum separately
observed memory peaks into a claimed simultaneous peak.

## Interpretation and decision

State separately: correctness result, work removed, generated-code observation,
measured outcome, tradeoffs, and unmeasured dimensions. Describe uncertainty and
known confounders. Do not claim a code-generation gain from identical executable
code under the same execution configuration.

Keep, revise, or remove the change against the stated objective. A local regression
requires an explicit overall benefit within hard budgets, not concealment in an
aggregate. An infrastructure or maintainability change without speedup should be
labeled accordingly. Name only the next experiment that resolves the main open
question rather than inventing a long optimization roadmap.
