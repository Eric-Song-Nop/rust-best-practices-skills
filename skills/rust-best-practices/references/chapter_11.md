# Chapter 11 - Compiler and interpreter hot paths

Use this chapter for interpreters, parsers, query engines, codecs, and similar
systems that repeatedly interpret descriptors or execute planned operations.
It is not a requirement to add a planner to ordinary application code.

## Optimize one meaningful operation across its boundaries

Trace an operation from input representation through decoding, access, execution,
and completion. Count repeated decoding, lookups, validation, temporary owners,
stack or buffer round-trips, result wrapping, and dispatch. A cheaper helper can
leave the dominant redundant work untouched.

Choose a coherent operation-level transformation: direct destination access,
scoped slot admission, fused passes, preserved continuation positions, compact
execution descriptors, or a different ownership boundary. These are alternatives
to evaluate, not features to implement all at once. Keep the existing execution
model unless changing it has a stronger justified opportunity; no stack-to-register
migration or additional planner is mandatory.

Permit replacing helper APIs and dataflow when they force duplicated work.
Preserve correctness invariants, not historical call boundaries. Prefer a small
mechanism that serves meaningful operations over a growing catalog of narrow
patterns that each add guards and completion machinery.

## Move only the right work earlier

Separate stages and established facts:

| Stage | Useful work | Limits |
| --- | --- | --- |
| Build time | Generate tables and exhaustiveness/consistency checks | Does not know arbitrary runtime input |
| Compile/load/plan time | Decode stable operands, validate control flow, determine static effects | Must charge planning and metadata cost; untrusted serialized input still needs validation |
| Dynamic admission | Resolve current storage, types, overlap, owner, generation, capacity | Valid only until its specified invalidators |
| Execution/commit | Use admitted access and preserve effects | Must not replay already performed effects on fallback |

For an interpreter, compile-time can mean compilation of guest input at runtime,
not compilation of the Rust engine. State which one is meant. A guest compiler's
verified descriptor does not automatically become a fact known to LLVM; design
the consumer so it actually avoids re-decoding or revalidating immutable facts.

Keep descriptors immutable after publication or provide versioning/invalidation.
Validate the real emitted representation, including canonical dumps or equivalent
structural tests. Do not certify only a hand-built test descriptor while the
production compiler emits a different form.

## Let proofs change the consumer

A useful admitted access carries a borrow, resolved slot, decoded operand, or
other capability the consumer can use directly. Passing a typed handle into the
same generic helper that repeats all lookups may improve safety without reducing
work. Check which checks and ownership operations actually survive.

Hoist immutable facts out of repeated execution. Admit dynamic facts once per
valid operation or region rather than checking them at each helper boundary.
Keep necessary checks when storage can move, IDs can be recycled, a callback can
mutate state, or the operation can reenter. Do not extend a proof beyond its
validity scope simply because its type still exists.

Use safe borrowing, split access, typed storage, and explicit ownership transfer.
Do not weaken identity or generation semantics, introduce unchecked accesses, or
assume a marker erases a runtime bounds check. See
[proof lifetimes](chapter_07.md) and [data representation](chapter_10.md).

## Preserve observable effects and completion state

Before a speculative path commits, either establish all facts needed to proceed
or specify its continuation after partial execution. On a miss, preserve the
state that the generic path expects, including owned operands. After observable
work, resume at the correct point rather than restarting an operation.

For language engines, include evaluation order, numeric conversion, signed zero,
NaN, overflow, getters, proxies, callbacks, exception positions, source locations,
resource release, and suspend/resume state as required by the language contract.
For other engines, enumerate their corresponding effects instead of borrowing a
JavaScript-specific checklist blindly.

Avoid materializing a generic intermediate only to decode and consume it again.
A direct destination or completion interface can delete that round-trip. Preserve
the required release order and error behavior; postponing drops or collection is
not an equivalent optimization merely because the final numeric result matches.

## Verify coverage and net benefit

Test the compiler/planner, admission, execution, and completion together.
Differential tests must cover actual hits, deliberate misses, invalidation,
overlap, boundary sizes, and failures. Measure rejection reasons separately from
final timing. A fast-path implementation with no representative hits is not a
completed performance result.

Compare the changed operation and real applications. Include planning/startup,
metadata memory, code size, miss cost, and cleanup. Use infrastructure-only and
cumulative baselines when necessary to isolate those costs. Do not infer an
application speedup from a dispatch-count reduction or a single arithmetic loop.

Choose acceptance criteria from the workload and hard constraints. Pursue a
higher-upside boundary change when repeated narrow changes fail to remove enough
work; do not respond only by adding more conservative checks around the same
costly path. At the same time, retain the generic semantics for cases the new
path does not handle. Use [performance reporting](performance-report.md) to
separate the structural hypothesis from the observed outcome.
