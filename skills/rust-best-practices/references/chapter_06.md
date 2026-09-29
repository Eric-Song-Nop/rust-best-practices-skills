# Chapter 6 - Dispatch and code generation

## Choose dispatch at the actual boundary

Generics and argument-position `impl Trait` normally allow monomorphization for
concrete types. This can expose operations to inlining and specialization, but
multiple instantiations can increase code size and compilation cost. It does not
guarantee inlining or that all validation disappears.

`dyn Trait` expresses runtime type erasure through a pointer. It can reduce
implementation duplication and help separate large shared code from small
specialized wrappers. Its calls can require indirect dispatch and inhibit some
optimizations; the compiler can also devirtualize calls in some contexts. Compare
the actual call site and binary, not a universal static-versus-dynamic ranking.
See [generics](https://doc.rust-lang.org/book/ch10-01-syntax.html) and
[trait objects](https://doc.rust-lang.org/reference/types/trait-object.html).

Dynamic dispatch does not inherently allocate. Borrowed `&dyn Trait` and
`&mut dyn Trait` do not require `Box`, and a trait object is not restricted to
heterogeneous collections. Use owning pointers only when ownership requires them.
Conversely, generics do not prevent heap allocation inside the implementation.

```rust
trait Checksum {
    fn checksum(&self, bytes: &[u8]) -> u64;
}

struct ByteSum;
impl Checksum for ByteSum {
    fn checksum(&self, bytes: &[u8]) -> u64 {
        bytes.iter().map(|&byte| u64::from(byte)).sum()
    }
}

fn static_call<C: Checksum>(checker: &C, bytes: &[u8]) -> u64 {
    checker.checksum(bytes)
}
fn erased_call(checker: &dyn Checksum, bytes: &[u8]) -> u64 {
    checker.checksum(bytes)
}

assert_eq!(static_call(&ByteSum, &[1, 2, 3]), 6);
assert_eq!(erased_call(&ByteSum, &[1, 2, 3]), 6);
```

This example establishes equivalent results, not a performance comparison.
An enum with a `match` is another representation for a closed set of alternatives;
it can still require runtime dispatch. Consider representation size, branch
behavior, and extensibility rather than assuming it is automatically faster.

## Check dyn compatibility precisely

Use the current [Rust Reference](https://doc.rust-lang.org/reference/items/traits.html#dyn-compatibility)
for the project's compiler. Do not summarize the rules as only "no generic
methods" or "methods cannot mention `Self`." A method explicitly requiring
`Self: Sized` can be excluded from trait-object dispatch without making the whole
trait incompatible. `Self: Sized` on the trait itself is different. Associated
items, receivers, and return types have additional rules.

```rust
trait Label {
    fn label(&self) -> &str;
    fn duplicate(&self) -> Self
    where
        Self: Sized;
}

impl Label for String {
    fn label(&self) -> &str { self.as_str() }
    fn duplicate(&self) -> Self { self.clone() }
}

let value = String::from("ready");
let object: &dyn Label = &value;
assert_eq!(object.label(), "ready");
assert_eq!(value.duplicate(), value);
```

## Control specialization and code growth

Keep generic parameters where specialization removes meaningful work. A small
generic adapter around a larger non-generic implementation can bound duplication.
For a runtime or embedded system, track text size and target instruction-cache
constraints as well as direct-call costs. Do not propagate a new type parameter
through an entire system without identifying the operations it improves.

`#[inline]`, `#[inline(always)]`, `#[inline(never)]`, and `#[cold]` express
optimization intent; none is a universal speed recipe. Inlining can expose
constants and eliminate calls, but can also grow hot code and live ranges.
Outline rare diagnostics when it helps, without losing the intended error or
source position. See [codegen attributes](https://doc.rust-lang.org/reference/attributes/codegen.html).

## Inspect the generated implementation

Ask a specific question: which check, call, copy, reference-count operation,
spill, or reload should vanish? Inspect the optimized caller and relevant
callees with the actual target, feature set, and profile. For a library target,
this command emits assembly; select the real package when needed:

```sh
cargo rustc --lib --release -- --emit=asm
```

Use `--bin` for the relevant executable instead. Account for cross-crate and
link-time optimization; intermediate assembly may not be the final linked code.
Keep an inspectable build close to the measured artifact. Do not change inlining
just to expose a symbol and then treat that artifact as production evidence.
See [`cargo rustc`](https://doc.rust-lang.org/cargo/commands/cargo-rustc.html).

Follow with representative measurements. Fewer source branches or instructions
are evidence about work, not sufficient proof of fewer cycles or lower latency.
Do not put architecture-specific assembly snapshots behind a universal CI gate
unless the project intentionally pins that compiler/target contract.
