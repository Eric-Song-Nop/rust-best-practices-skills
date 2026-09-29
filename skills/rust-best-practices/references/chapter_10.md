# Chapter 10 - Data representation

## Inspect the whole representation

Start with sizes, alignments, cardinality, ownership, access patterns, and lifetime.
Account for container capacity and metadata as well as payload. Measure using the
actual target; pointer widths and ABI differ. `size_of` is a useful observation,
not a guarantee that the same layout holds across targets or compiler versions.
See [type layout](https://doc.rust-lang.org/reference/type-layout.html).

An array is inline storage, not inherently stack storage: it can be a field of
a heap allocation or reside in static storage. A `Vec` owns a separate element
buffer; the `Vec` value itself can also live in different places. Large inline
values may create stack pressure or copies, depending on placement and generated
code. Do not classify all arrays as stack allocations or all ownership transfers
as heap copies.

`Box::new(large_value)` does not guarantee that no large stack temporary is
materialized. Optimizations may remove one, but stack-constrained code should
use an allocation/construction path with an understood peak and verify the target.
For an initialized byte buffer, this avoids writing a large array expression:

```rust
let buffer: Box<[u8]> = vec![0_u8; 64 * 1024].into_boxed_slice();
assert_eq!(buffer.len(), 64 * 1024);
assert!(buffer.iter().all(|&byte| byte == 0));
```

This is not a universal allocator-failure or stack-usage guarantee.
See [`Vec` guarantees](https://doc.rust-lang.org/std/vec/struct.Vec.html#guarantees).

## Choose allocation lifetime and reuse deliberately

Remove allocations by consuming owned values, writing into existing destinations,
streaming, or sharing immutable data when the contract allows. Reserve capacity
from known bounds or a measured distribution; excessive reservation raises peak
and retained memory. Reusing storage can avoid allocations while retaining much
more memory than the steady-state payload needs.

`SmallVec` stores up to its configured inline capacity inside the container and
can spill to a heap allocation when that capacity is exceeded. It does not choose
storage merely because a type or const array is "large." Increasing inline
capacity also enlarges every container and can increase movement and stack use.
Use the actual length distribution and spill behavior before adopting it.
See the [SmallVec documentation](https://docs.rs/smallvec/latest/smallvec/).

Arenas and pools can improve locality and amortize allocation, but they change
retention and cleanup boundaries. Account for fragmentation, high-water capacity,
reuse, destructor timing, and stale identities. Interning adds lookup and table
lifetime costs; it is valuable only when reuse pays for them. Do not delay release
or change collection semantics just to hide allocation costs in a benchmark.

## Optimize for access, not only byte count

For arrays of heterogeneous records, compare inline enums, boxed rare payloads,
separate typed storage, and hot/cold field separation. Inline enums can be widened
by their largest variants and alignment; boxing can shrink each slot but add
allocations and pointer chasing. Inspect the actual layout, including any niche
optimization, rather than assuming tag and payload sizes.

Array-of-structs favors accesses that need one record's fields together.
Structure-of-arrays can favor dense scans over a few fields. Either can be wrong
for a different workload. A smaller representation can still introduce extra
loads, decoding, or scattered accesses. `repr(C)` and packed layouts are not
universal performance annotations and can add constraints or alignment hazards.
Do not add unsafe access to compensate for a speculative layout.

Separate typed arenas can prevent category mistakes and reduce oversized shared
slots. A typed ID does not by itself validate an index, owner, or generation.
Preserve required identity width and reuse semantics. Compact handles or offsets
need explicit range limits and overflow behavior, not silent narrowing.
See [proof-carrying interfaces](chapter_07.md).

## Measure memory dimensions separately

Record live payload, allocated capacity, allocator overhead where available,
retained caches, temporary planning/collection storage, and process RSS or device
heap observations separately. Peak memory must come from simultaneous usage; do
not add peaks measured at different times and call that an observed process peak.
Report allocation count and bytes separately from allocation latency.

For embedded deployments, account for text/flash size, RAM, stack peaks, allocator
availability, and worst-case latency on the device. Host measurements and
cross-compilation do not establish device behavior. A capacity reduction may be
valuable without speeding up execution; label the outcome precisely.

For concurrency, investigate cache-line sharing only with relevant evidence and
target details. Padding can reduce contention while increasing memory; it is not
a substitute for identifying which state different workers actually touch.
