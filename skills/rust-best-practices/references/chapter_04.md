# Chapter 4 - Errors and commit boundaries

## Model the failure, not a blanket rule

Use `Result<T, E>` when callers need to handle failure, and `Option<T>` when
absence is sufficient information. Keep an optimization miss distinct from a
semantic error. Do not replace a valid absent state with an invented error merely
to avoid `Option`.

An input error, a temporary resource failure, and a violated internal invariant
need different handling. `expect` can be appropriate for a documented invariant
or initialization failure under the project's panic policy. Prefer an interface
that makes the invalid state unavailable when practical. A blanket prohibition
on `unwrap` must not become silent fallback, swallowed errors, or fabricated
recoverable failures. See the [Rust Book's panic guidance](https://doc.rust-lang.org/book/ch09-03-to-panic-or-not-to-panic.html).

`unreachable!()` still panics if reached; it is not a compiler proof that a branch
cannot execute. `todo!()` and `unimplemented!()` are also panicking placeholders,
not compile-time completeness checks. Do not introduce unchecked operations or
remove release validation to optimize these paths.

## Choose error representations for the boundary

Use a concrete error enum or struct when callers need structured recovery.
`thiserror` is an optional implementation aid, not a requirement for libraries.
A type-erased application error such as `anyhow::Error` can suit orchestration
and diagnostics; binaries can also require typed errors, and private library
layers may intentionally erase them. Decide from the public contract, allocation
budget, `no_std` support, and recovery needs rather than file or crate labels.
See the authors' documentation for [thiserror](https://docs.rs/thiserror/latest/thiserror/)
and [anyhow](https://docs.rs/anyhow/latest/anyhow/).

Use `?` for propagation when it preserves the intended error. Use explicit
matching for recovery or ownership-sensitive transitions. Neither syntax is
inherently faster. Keep successful hot-path representations compact; investigate
large error payloads because they can affect the containing `Result` layout.
Boxing trades size for indirection and possible allocation: measure the actual
success/failure distribution instead of boxing all errors.

Construct expensive diagnostics only on the error path. For example,
`ok_or_else` delays error construction, while `ok_or` evaluates its argument
before the call. A cheap enum value need not be wrapped in a closure.
See [`Option`](https://doc.rust-lang.org/std/option/enum.Option.html).

## Make failure ownership explicit

An API taking an owned input must specify whether failure consumes, returns, or
stores that input. When retry needs the input, returning it can avoid a defensive
clone. Admit access before changing the destination:

```rust
fn replace_at<T>(slots: &mut [T], index: usize, incoming: T) -> Result<T, T> {
    match slots.get_mut(index) {
        Some(slot) => Ok(std::mem::replace(slot, incoming)),
        None => Err(incoming),
    }
}

let mut slots = [String::from("old")];
let incoming = String::from("new");
let returned = replace_at(&mut slots, 5, incoming).unwrap_err();
assert_eq!(returned, "new");
assert_eq!(slots, ["old"]);
let old = replace_at(&mut slots, 0, returned).unwrap();
assert_eq!(old, "old");
assert_eq!(slots, ["new"]);
```

`mem::replace` moves the old value out without dropping it at that point. Its
caller controls subsequent release. That can change observable behavior, so
preserve the required drop order and lifetime rather than treating deferred
release as a free optimization. See [`mem::replace`](https://doc.rust-lang.org/std/mem/fn.replace.html).

## Define admission, execution, and commit

For a speculative optimization, reject inapplicable input before observable
mutation, or provide the explicitly specified rollback/continuation behavior.
Never replay a getter, callback, write, or resource release through fallback after
already performing it. A generic fallback is not a substitute for correct
partial-execution handling.

Document the state after every error, panic, and cancellation point that matters.
Taking a value out with `Option::take`, `Cell::take`, or `mem::take` leaves a
replacement state; consider what observers see during reentrancy or unwinding.
Do not extend mutable borrows or guards across arbitrary callbacks to avoid a
second lookup. See [proof lifetimes](chapter_07.md).

Do not switch panic strategy, suppress destructors, narrow errors, or change
allocation-failure behavior merely to improve timing. Such changes need their
own explicit contract decision. Test both returned values and state/resource
ownership on success and failure; see [testing](chapter_05.md).
