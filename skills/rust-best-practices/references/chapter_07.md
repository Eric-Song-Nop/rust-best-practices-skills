# Chapter 7 - Proof-carrying interfaces

## State exactly what is known

Distinguish three facts:

| Fact | Example | Appropriate enforcement |
| --- | --- | --- |
| Static construction fact | A required field was supplied | Types and private constructors |
| Dynamic fact valid for a scope | A mutable slot exists in this storage now | Checked admission returning a scoped borrow |
| Mutable external fact | A handle still names the same generation | Revalidation or an enforced invalidation protocol |

A marker such as `Validated<T>` does not make its validation static. The check may
still happen at runtime. Its benefit can be preventing misuse and repeated checks
within a valid scope. A zero-sized marker does not imply the entire wrapper,
state transition, or generated execution path is zero-cost.

## Store the valid state's actual payload

Prefer a representation that does not need to express an invalid state after
transition. Here, the named builder carries a `Named(String)`, not an
`Option<String>` plus a marker and a later unwrap:

```rust
mod building {
    pub struct Missing;
    pub struct Named(String);
    pub struct Builder<N> { name: N }

    impl Builder<Missing> {
        pub fn new() -> Self { Self { name: Missing } }
        pub fn name(self, name: String) -> Builder<Named> {
            Builder { name: Named(name) }
        }
    }
    impl Builder<Named> {
        pub fn build(self) -> String { self.name.0 }
    }
}

let name = building::Builder::new().name(String::from("Ada")).build();
assert_eq!(name, "Ada");
```

The missing state has no `build` method. A self-contained invalid-use test:

```rust,compile_fail
struct Missing;
struct Named(String);
struct Builder<N> { name: N }
impl Builder<Named> {
    fn build(self) -> String { self.name.0 }
}
let missing = Builder { name: Missing };
let _ = missing.build();
```

Keeping `Option` can still be appropriate when optionality exists in that state.
The mistake is claiming a runtime check disappeared merely because the API has
a typestate parameter. Verify code generation separately.
See the [typestate discussion in the Embedded Rust Book](https://docs.rust-embedded.org/book/static-guarantees/typestate-programming.html).

## Carry a capability instead of a detached assertion

A checked index wrapped in a newtype does not automatically belong to the next
slice it is used with. Prefer a capability tied to the actual storage when its
lifetime fits the operation. This function admits a window once, then returns
access to that exact window:

```rust
fn window_mut<T>(values: &mut [T], start: usize, len: usize) -> Option<&mut [T]> {
    let end = start.checked_add(len)?;
    values.get_mut(start..end)
}

let mut values = [1_u32, 2, 3, 4];
{
    let window = window_mut(&mut values, 1, 2).unwrap();
    for value in window {
        *value += 10;
    }
}
assert_eq!(values, [1, 12, 13, 4]);
assert!(window_mut(&mut values, usize::MAX, 2).is_none());
```

The returned borrow ties access to the storage and enforces exclusivity for its
lifetime. It does not certify unrelated indexing. Iteration and the safe slice API
express the access pattern without introducing unchecked code.
See [slice operations](https://doc.rust-lang.org/std/primitive.slice.html).

A live element borrow prevents resizing the vector through its owner:

```rust,compile_fail
let mut values = vec![1_u32];
let slot = values.get_mut(0).unwrap();
values.push(2);
*slot = 3;
```

## Record the proof's lifetime and invalidators

For every reusable proof, specify its producer, established facts, subject
identity, consumers, lifetime, and invalidators. Explain why each invalidator is
prevented or detected. Private fields prevent arbitrary construction by clients;
they do not prove that every internal constructor or mutation preserves the fact.

A typed arena ID can prevent mixing cell IDs with shape IDs while still needing
bounds, owner, and generation checks. A borrow lifetime alone does not prevent
mutation through interior mutability, callbacks, or external resources. Do not
cache a fact across such changes without the corresponding protocol.

Do not revalidate immutable facts on every operation after successful admission.
Also do not hoist a dynamic check past an operation that can invalidate it.
Use split borrows, narrower interfaces, and operation-scoped access to widen the
valid proof scope where possible. A useful proof changes the consumer interface
so it can use what has been established instead of starting another lookup.

## Keep the machinery proportional

Typestate is useful for protocol transitions, staged construction, and validated
execution interfaces. An ordinary enum can be simpler for runtime-selected
states. Avoid generic state combinations that duplicate large implementations
without deleting work. No unsafe conversion is required merely because two
states have different payload types; use explicit state-specific payloads,
associated types, or separate structs as appropriate.

For performance, distinguish API safety, represented state, eliminated dynamic
work, and measured gain. A better type boundary can be valuable before it speeds
anything up, but it must not be presented as a speedup without evidence.
