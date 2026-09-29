# Chapter 5 - Testing

## Test a contract, not an assertion count

Give each test a clear scenario and meaningful failure output. Several assertions
can express one contract: a failed insertion returns its input, leaves storage
unchanged, and does not release either value early. Splitting that contract just
to enforce one assertion per test hides relationships and repeats setup.

Use unit tests for internal invariants, integration tests for externally visible
behavior, and documentation tests for examples. Keep the actual action and
important expected behavior readable. Use shared fixtures when they remove noise,
not abstractions that compute expected results using the implementation under test.
See [test organization](https://doc.rust-lang.org/book/ch11-03-test-organization.html).

## Cover ownership and state transitions

Test success, absence, rejection, failure, aliasing where supported, and resource
release. This small test checks failure ownership and drop timing together:

```rust
use std::cell::Cell;

struct Tracked<'a>(&'a Cell<usize>);
impl Drop for Tracked<'_> {
    fn drop(&mut self) {
        self.0.set(self.0.get() + 1);
    }
}

fn replace_at<T>(slots: &mut [T], index: usize, incoming: T) -> Result<T, T> {
    match slots.get_mut(index) {
        Some(slot) => Ok(std::mem::replace(slot, incoming)),
        None => Err(incoming),
    }
}

let drops = Cell::new(0);
let mut slots = [Tracked(&drops)];
let incoming = Tracked(&drops);
let rejected = match replace_at(&mut slots, 2, incoming) {
    Err(value) => value,
    Ok(_) => panic!("out-of-range replacement unexpectedly succeeded"),
};
assert_eq!(drops.get(), 0);
assert_eq!(slots.len(), 1);
drop(rejected);
assert_eq!(drops.get(), 1);
drop(slots);
assert_eq!(drops.get(), 2);
```

This does not prove arbitrary panic safety. Add targeted panic/cancellation tests
where the contract requires them. Use bounded deterministic fault injection for
fallible operations rather than relying on actual machine exhaustion.

## Validate optimized paths against a reference

For substantial optimizations, compare reference and candidate outputs and
observable state, not merely a checksum or final scalar. Include errors and their
positions/timing, mutation order, ownership, and identity when those are part of
the system's contract. Cover realistic fast-path hits and deliberate misses.
A test suite that always falls back does not test the optimized path.

Use a deterministic corpus plus generated or property-based cases when the state
space warrants them. Record seeds, keep minimized failures, and compare against
an independent reference where possible. Include empty and boundary sizes,
overlap, stale handles, invalidation, capacity changes, and reentrancy when relevant.
For numeric transformations, cover the specified overflow behavior, signed zero,
NaN, infinities, and evaluation order. Decide whether equality is numerical,
bitwise, or semantic before selecting assertions.

Test the real compiler/planner and emitted representation when a runtime fast
path depends on them. Hand-constructing an optimized operation alone does not
show that production compilation reaches it. Diagnostic coverage counters can
verify that intended paths run; keep them separate from final timing builds.

## Compile examples and invalid uses

Ordinary Rust fences in this bundle are self-contained executable examples.
`rust,compile_fail` fences check invalid usage. Pair negative examples with valid
ones so an unrelated broken setup cannot supply the only evidence. A generic
compile failure is weaker than a test asserting the expected compiler diagnostic;
use the project's UI-test framework when the exact reason is part of the claim.

Use `no_run` for real examples that must compile but cannot safely execute in the
test environment. Label genuine pseudocode `text`. Do not hide broken Rust behind
`ignore`. The bundle's validator rejects ignored Rust snippets and runs ordinary
examples in both unoptimized and optimized builds.
See [rustdoc tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html).

## Keep snapshots and benchmarks in their roles

Use reviewed snapshots for generated structure, bytecode, diagnostics, or public
output when that structure is the contract. Redact only genuinely irrelevant
nondeterminism; do not redact the behavior being tested. Never accept refreshed
snapshots as proof that changed semantics are correct. Prefer direct assertions
for simple values and relationships.

Correctness tests are not timing benchmarks. Allocation-count tests need a
controlled scope; test harness activity can allocate too. Avoid flaky wall-clock
thresholds in ordinary unit tests. Run documentation tests explicitly when a
chosen test runner does not execute them. Use project CI and the
[performance workflow](chapter_03.md) for their respective evidence.
