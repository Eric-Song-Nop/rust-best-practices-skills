# Chapter 9 - Sharing and concurrency

## Choose access and ownership separately

Prefer ordinary borrowing and ownership when they express the required lifetime.
Use `Rc` for shared ownership within one thread, `Arc` for shared ownership that
must cross threads, and interior mutability when mutation through shared access
is part of the design. These are different capabilities, not a ranking from fast
to slow. `&T` can permit interior mutation; it is not universally immutable data.

Cloning `Rc` or `Arc` shares the allocation rather than cloning `T`, but updates
reference counts. `Arc` uses atomic reference counting; it does not make arbitrary
inner state thread-safe. Avoid unnecessary clone/drop pairs in hot paths and
inspect actual ownership lifetimes before changing them.
See [`Rc`](https://doc.rust-lang.org/std/rc/struct.Rc.html) and
[`Arc`](https://doc.rust-lang.org/std/sync/struct.Arc.html).

## Use accurate Send and Sync bounds

For these standard types with their default allocators, the relevant conditions
are below. `Send` means a value can be transferred across threads; `Sync` means
shared references can be transferred. Neither promises lock-free execution.
See [`Send`](https://doc.rust-lang.org/std/marker/trait.Send.html),
[`Sync`](https://doc.rust-lang.org/std/marker/trait.Sync.html), and each wrapper's
trait implementations.

| Type | `Send` condition | `Sync` condition |
| --- | --- | --- |
| `&T` | `T: Sync` | `T: Sync` |
| `&mut T` | `T: Send` | `T: Sync` |
| `Box<T>` | `T: Send` | `T: Sync` |
| `Rc<T>` | No | No |
| `Arc<T>` | `T: Send + Sync` | `T: Send + Sync` |
| `Cell<T>` | `T: Send` | No |
| `RefCell<T>` | `T: Send` | No |
| `Mutex<T>` | `T: Send` | `T: Send` |
| `RwLock<T>` | `T: Send` | `T: Send + Sync` |

In particular, `&mut T` can be `Send`; exclusivity does not prohibit transferring
a borrow to a scoped thread. These positive assertions compile:

```rust
use std::cell::{Cell, RefCell};
use std::sync::{Arc, Mutex};

fn require_send<T: Send>() {}
fn require_sync<T: Sync>() {}

require_send::<&mut String>();
require_sync::<&mut String>();
require_send::<Cell<String>>();
require_send::<RefCell<String>>();
require_sync::<Mutex<Cell<u32>>>();
require_send::<Arc<Mutex<String>>>();
```

`Arc` does not turn `RefCell` into thread-safe shared state:

```rust,compile_fail
use std::cell::RefCell;
use std::sync::Arc;
fn require_send<T: Send>() {}
require_send::<Arc<RefCell<u32>>>();
```

## Cell is not limited to Copy types

`Cell<T>` supports non-`Copy` values. `get` requires `T: Copy`; `set`, `replace`,
and `into_inner` do not. `take` requires `Default`. It does not provide a general
shared-reference method that borrows its inner `T`. Use it when replacement or
value transfer matches the operation, not as a universal faster `RefCell`.
See [`Cell`](https://doc.rust-lang.org/std/cell/struct.Cell.html).

```rust
use std::cell::Cell;
let slot = Cell::new(String::from("old"));
let previous = slot.replace(String::from("new"));
assert_eq!(previous, "old");
assert_eq!(slot.take(), "new");
slot.set(String::from("final"));
assert_eq!(slot.into_inner(), "final");
```

This still does not allow copying a `String` out through `get`:

```rust,compile_fail
use std::cell::Cell;
let slot = Cell::new(String::from("owned"));
let _ = slot.get();
```

`RefCell` provides runtime-checked borrows. `borrow`/`borrow_mut` can panic on a
conflict; `try_borrow`/`try_borrow_mut` expose failure. These checks may optimize
away in a particular context, but that is not an API guarantee. Prefer a narrower
borrow scope or split ownership when it naturally removes the need for interior
mutability. Do not remove meaningful reentrancy checks without replacing their
contract. See [`RefCell`](https://doc.rust-lang.org/std/cell/struct.RefCell.html).

## Use scoped parallelism when borrowing is enough

Disjoint work can borrow data without adding `Arc` or a lock:

```rust
let mut values = [1_u32, 2, 3, 4];
std::thread::scope(|scope| {
    let (left, right) = values.split_at_mut(2);
    scope.spawn(move || {
        for value in left { *value *= 2; }
    });
    scope.spawn(move || {
        for value in right { *value *= 2; }
    });
});
assert_eq!(values, [2, 4, 6, 8]);
```

This demonstrates safe lifetimes, not that spawning threads for four elements is
fast. Measure task granularity, scheduling, synchronization, cache-line sharing,
and concurrency under the intended workload.
See [`thread::scope`](https://doc.rust-lang.org/std/thread/fn.scope.html).

For shared mutation, select a lock or other synchronization protocol from the
actual access pattern. `RwLock` is not automatically faster than `Mutex`.
Do not weaken atomic ordering without proving the synchronization protocol.
Prefer a simple correct design over a speculative lock-free replacement.
See [`Mutex`](https://doc.rust-lang.org/std/sync/struct.Mutex.html),
[`RwLock`](https://doc.rust-lang.org/std/sync/struct.RwLock.html), and
[atomic ordering](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html).

## Treat async suspension as a lifetime boundary

Read the runtime's task requirements. A future's `Send` constraints depend on
state held across suspension and the spawning API; not every future must be
`Send` or `'static`. Do not add `Arc` merely because code is async. Avoid holding
a blocking lock guard, broad mutable borrow, or large retained buffer across
`.await` unless that is deliberate and safe for the executor and protocol.
Account for cancellation, backpressure, wakeups, and retained task state.
`Pin` is about a value's movement contract, not automatic allocation or thread
safety. See [`Future`](https://doc.rust-lang.org/std/future/trait.Future.html) and
[`Pin`](https://doc.rust-lang.org/std/pin/index.html).
