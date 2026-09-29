# Chapter 2 - Tooling and lints

## Follow the actual build contract

Read `rust-toolchain.toml`, `rust-version`, the edition, Cargo configuration,
workspace settings, and CI before choosing commands. Use the repository's task
runner when it encodes these choices. A modern skill does not authorize an MSRV
increase or dependency update. Record `rustc -Vv` and `cargo -V` for reproducibility.

For a workspace with a committed, current lockfile, a typical starting set is:

```sh
cargo fmt --all -- --check
cargo check --workspace --locked
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
cargo test --workspace --doc --locked
```

These commands are examples, not a replacement for project instructions.
`--all-targets` covers Cargo target kinds, not all hardware targets.
`--all-features` does not test each feature combination, and some features are
mutually exclusive. Test the supported default, minimal, and selected feature
configurations explicitly. Cross-check target-dependent and `no_std` builds when
a change affects them. `cargo check` is not an execution test.
See [Cargo feature guidance](https://doc.rust-lang.org/cargo/reference/features.html).

`--locked` rejects a lockfile change. Diagnose why resolution differs rather than
running `cargo update` to make the failure disappear. If a project deliberately
has no tracked lockfile, follow its resolution policy and pin benchmark inputs
separately. See [`cargo update`](https://doc.rust-lang.org/cargo/commands/cargo-update.html).

Install a missing component for the selected toolchain when authorized; do not
run an unconditional `rustup update`. Check whether optional profiling tools are
available before prescribing or installing them.

## Interpret diagnostics

Clippy identifies patterns worth inspecting; it does not measure their runtime
impact. A `large_enum_variant` warning may justify boxing a cold payload, or a
measured inline representation may be appropriate. A `needless_collect` warning
still requires checking evaluation order and reuse. Do not describe replacing
`clone()` on a `Copy` type with a copy as a demonstrated speedup.

Fix correctness diagnostics. Apply style diagnostics when they improve the code
and fit the repository. Use a narrow, explained lint override for intentional
tradeoffs. Prefer `#[expect(...)]` when the supported compiler has it and the lint
is expected to fire; use `#[allow(...)]` when policy or conditional availability
makes that appropriate. Do not require `expect` on an older MSRV.
See [lint attributes](https://doc.rust-lang.org/reference/attributes/diagnostics.html).

## Configure priorities and inheritance correctly

For a workspace that requires safe Rust, this is an illustrative policy:

```toml
[workspace.lints.rust]
unsafe_code = "forbid"

[workspace.lints.clippy]
all = { level = "warn", priority = -1 }
```

Each member opting into that policy needs:

```toml
[lints]
workspace = true
```

Higher numeric priorities take precedence; give broad groups a lower priority
than individual overrides. Workspace lint declarations are not inherited merely
because the section exists. Do not add a blanket pedantic or nursery policy to
an unrelated change. Verify support in the project's Cargo version.
See [manifest lints](https://doc.rust-lang.org/cargo/reference/manifest.html#the-lints-section).

## Keep validation and performance builds distinct

Use optimized code for performance claims, but inspect the actual profile rather
than trusting the name `release`. Cargo's `bench` profile normally inherits
`release`; a custom production profile may differ. Keep codegen units, LTO,
features, panic strategy, target CPU, allocator, and dependency resolution aligned
between compared builds. Do not apply a universal `target-cpu=native` or LTO
recipe, especially when shipping to different hardware.
See [profiles](https://doc.rust-lang.org/cargo/reference/profiles.html).

Report the exact commands and their outcome. A missing tool is an unrun check,
not a pass. Do not claim that Clippy passing validates performance or that
cross-compilation validates latency, memory use, or behavior on a device.
