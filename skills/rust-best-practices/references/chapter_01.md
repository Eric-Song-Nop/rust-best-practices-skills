# Chapter 1 - Ownership and expressions

## Choose the required ownership transition

Use `&T` for shared access, `&mut T` for exclusive access, and `T` when the callee
must own or consume the value. For read-only text and sequences, `&str` and `&[T]`
usually express the contract better than `&String` and `&Vec<T>`. Accept the
concrete collection when its capacity or collection-specific operations matter.

A move transfers ownership; it does not call `Clone`. Moving a `Vec` or `String`
does not inherently copy the heap elements. A large inline value can still
require data movement if the compiler cannot eliminate it. Borrowing adds a
reference and may change optimization opportunities. Do not choose either from
a fixed 24-byte or 512-byte rule: representation, ABI, inlining, and use matter.
See the [ownership chapter](https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html)
and [`Vec` guarantees](https://doc.rust-lang.org/std/vec/struct.Vec.html#guarantees).

`Copy` permits implicit duplication and excludes types with `Drop`; it is not a
promise that duplication is cheap. Derive it when duplication matches the API's
semantics. Large arrays can implement `Copy`. Changing a public type's `Copy`
contract is an API decision, not just a local optimization.
See [`Copy`](https://doc.rust-lang.org/std/marker/trait.Copy.html).

Use `clone()` for genuinely independent ownership. Inspect the implementation:
a string clone, a reference clone, and an `Arc` clone have different costs.
Do not introduce cloning merely to preserve an unsuitable helper signature.
Taking ownership, splitting borrows, or returning the unconsumed input on failure
can be the better interface. Do not remove observable custom `Clone` or `Drop`
behavior while making that change.

```rust
fn append_owned(mut values: Vec<String>, value: String) -> Vec<String> {
    values.push(value);
    values
}

let original = vec![String::from("first")];
let result = append_owned(original, String::from("second"));
assert_eq!(result, ["first", "second"]);
```

Use `Cow` when a concrete API benefits from borrowing on one path and owning on
another. Its enum representation and possible allocation remain relevant; it is
not a default remedy for unclear ownership. Read [`Cow`](https://doc.rust-lang.org/std/borrow/enum.Cow.html).

## Iterate according to ownership and effects

`values.iter()` yields references; `values.iter_mut()` yields exclusive
references. `Vec<T>::into_iter()` consumes the vector and yields owned elements
without requiring `T: Clone` or `T: Copy`. Other types have their own
`IntoIterator` implementations; do not generalize vector semantics to all types.
See [`IntoIterator`](https://doc.rust-lang.org/std/iter/trait.IntoIterator.html).

Use a loop when control flow and side effects are clearer that way. Use iterator
adapters when they express the transformation clearly. A `for` loop itself uses
`IntoIterator`; these are not competing execution engines. Lazy evaluation is
not a guarantee of machine-code loop fusion or vectorization.

Avoid intermediate collection when the consumer can stream the same work.
Keep a collection when it enables reuse, sorting, random access, batching, or a
required effect boundary. Moving collection or cloning later can change when
errors, allocation, and side effects occur. Check those semantics before fusing.

Implementing both `Copy` and `Iterator` is legal, but usually surprising for a
stateful cursor: advancing a copy does not advance the original. Prefer an
explicit cursor-cloning contract or an `IntoIterator` descriptor when independent
iteration is intended. Do not turn that API preference into a false language rule.

## Preserve arithmetic semantics

Use `.sum()` to communicate summation, not because `fold` closures are opaque to
the optimizer. Primitive `Sum` implementations use folding in the
[standard-library implementation](https://doc.rust-lang.org/src/core/iter/traits/accum.rs.html);
this implementation detail is not a promise about arbitrary `Sum` types.

Do not move an initial accumulator outside a reduction, reassociate floating
point, substitute fused operations, or reorder checked arithmetic without a
semantic justification. Here, moving the initial value changes the answer:

```rust
let values = [1e16_f64, -1e16];
let sequential = values.iter().copied().fold(1.0, |acc, x| acc + x);
let moved_initial = values.iter().copied().sum::<f64>() + 1.0;
assert_eq!(sequential, 0.0);
assert_eq!(moved_initial, 1.0);
```

Specify checked, wrapping, saturating, or ordinary arithmetic from the contract.
Test signed zero, NaN, infinities, overflow, and empty reductions where relevant.
Do not make results depend accidentally on debug versus release overflow checks.
See [operator semantics](https://doc.rust-lang.org/reference/expressions/operator-expr.html).

## Abstract shared meaning, not matching text

Extract a helper when it provides a useful contract or centralizes the same
invariant. Keep a little duplication when paths have different ownership,
evaluation order, or performance requirements. An occurrence count is a heuristic,
not a gate. A helper taking more mode flags can indicate the wrong boundary.

For hot code, check whether extraction changes inlining, live values, or error
transport. Conversely, do not insist on one giant function: cold-path extraction
can improve clarity and code layout. Compare the resulting implementation,
not the apparent number of function calls in the source.
