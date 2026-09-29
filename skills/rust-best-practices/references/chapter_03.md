# Chapter 3 - Performance workflow

## Define success before polishing code

Name the operation and deployment objective: request latency, completed work per
second, startup, memory peak, binary size, or another concrete budget. Identify
representative inputs, frequency, miss distribution, and important adversarial
cases. Separate hard constraints from negotiable tradeoffs.

Read the implementation and build configuration. Use existing profiles and
measurements where available, but allow structural hypotheses before a full
profile exists. Repeated decoding, construction of immediately discarded values,
or redundant validation can justify an experiment. They do not justify a speedup
claim. Favor opportunities that remove substantial recurring work over repeated
low-upside syntax changes.

Keep the process proportional. A small allocation fix may need a focused test
and allocation measurement. A new interpreter execution path needs coverage,
miss-cost analysis, and representative execution results. Do not mandate every
tool and benchmark for every edit.

## Write a work ledger

For the same logical operation, account for before/after:

| Cost | Questions |
| --- | --- |
| Computation and checks | Which decoding, hashing, type, bounds, identity, or generation checks survive? |
| Ownership and memory | Which allocations, byte copies, clones, drops, and reference-count operations survive? |
| Execution | Which calls, dispatches, loads, stores, and synchronization remain? |
| Added machinery | What do planning, guards, misses, metadata, invalidation, and cleanup cost? |

This is a hypothesis about work, not an instruction-count measurement. Confirm
important claims in optimized code and measurements. Source-level `Result`,
`match`, or helper counts do not establish machine-code costs.

Estimate opportunity size without presenting it as a prediction. Under the
simplified Amdahl model, removing half of a component responsible for 30% of time
reduces total time by 15%, not 50%. Real interactions can change that result.
Account for preparation amortization and short-lived workloads as well as hot
steady state. Reject a cache or fast path whose admission and maintenance consume
the benefit on the intended workload.

## Use evidence that answers the question

A CPU profile locates sampled execution; an allocation profile locates memory
activity. Neither substitutes for the other. Flamegraph width represents the
aggregated sample weight under the selected event, not per-call cost or elapsed
chronology. CPU samples do not by themselves explain I/O waits or queueing.
See the [flamegraph author's explanation](https://www.brendangregg.com/flamegraphs.html).

Inspect optimized assembly or IR for a concrete question: did a check disappear,
did a value spill, did a call inline, or did text size expand? Examine the actual
caller and build, not only an isolated example. Hardware counters can distinguish
changed instruction counts from cycles, branch behavior, or cache activity;
interpret them with the target CPU's event definitions. Do not assert a cache or
branch-prediction problem merely from a flamegraph or a large Rust function.

Use tools that match the environment: the project's benchmark harness first,
then available sampling, allocation, code-size, or counter tools. Installing a
new tool is not itself progress. Retain raw results and tool versions.
See [rustc code-generation options](https://doc.rust-lang.org/rustc/codegen-options/index.html).

## Compare like with like

Record baseline and candidate commits, compiler/LLVM versions, lockfile and input
hashes, feature flags, profiles, target, allocator, and relevant environment.
Build both artifacts before timing. Do not overlap compilation or other heavy
work with a timing run. Interleave or randomize paired baseline/candidate runs,
use independent process runs when appropriate, and report spread and uncertainty
rather than selecting the best run.

Hold logical work constant. Adaptive scores, fixed-duration loops, and changed
warm-up can execute different amounts of work; keep their official scores but
also compare fixed-work runs. Preserve observable outputs. Use `black_box` where
needed to discourage unwanted optimization, understanding that it is a best-effort
optimization barrier, not a proof that the benchmark represents production.
See [`black_box`](https://doc.rust-lang.org/std/hint/fn.black_box.html).

Separate setup/compile/plan time, execution, teardown, allocation, and retained
memory. When a phase can move work elsewhere, also measure the combined path.
For services, include realistic concurrency and queueing; for devices, test the
target before claiming target gains. For percentile claims, use enough samples
and describe the sampling method.

Measure fast-path hits, misses, non-applicable cases, and end-to-end workloads.
Collect rejection reasons in a diagnostic run when they explain coverage. Avoid
adding permanent per-operation instrumentation just to support an experiment.
For a substantial optimization framework, compare the original implementation,
infrastructure-only state, enabled candidate, and cumulative stack when those
separate builds are needed to isolate cost. A disabled runtime flag may retain
code-layout and metadata costs and is not automatically the original baseline.

## Decide without overstating

Use absolute values, units, relative differences, sample counts, and uncertainty.
There is no universal 5% acceptance threshold: a small robust high-frequency gain
can matter, and a large noisy microbenchmark result can be irrelevant. Improved
instruction counts are not necessarily reduced wall time. Reduced live bytes are
not necessarily reduced peak capacity or RSS.

If executable code and execution configuration are identical, do not attribute
noise to a generated-code optimization. Configuration, input, and external
library differences must still be controlled before drawing that conclusion.
Separate these outcomes: correctness improvement, maintainability improvement,
work removed, code-generation change, measured gain, and inconclusive result.

Keep a local regression only as an explicit tradeoff against the actual objective
and hard budgets. Validate cumulative changes against the original baseline, not
just favorable adjacent commits. Remove failed experiments unless their separate
non-performance value is stated. Use the
[report template](performance-report.md) for substantial experiments, pruning
sections that do not apply rather than inventing data.
