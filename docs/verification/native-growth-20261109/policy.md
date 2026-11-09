# Shared assessment and starter policy

Base `6d3d6ba6`, new isolated growth worktree. The design document was fully read
and cleanup checked before edits (`cleanup.json`). There was no previous native
growth policy or obsolete owned output to delete. Prior rejected cache paths,
normal program files, and real accounts were not touched.

`growth::policy` exports the agreed pure functions:

```rust
validate_experience(&Value, Option<&str>) -> Option<Value>
merge_experience(&Value, &Value) -> Option<Value>
validate_starter(&Value, Option<&str>) -> Option<Value>
merge_starter(&Value, &Value) -> Option<Value>
six_receipt(&Value, &str) -> Option<Value>
```

The module also exposes stable keys, the two exact assessment IDs, the existing
500 XP old gate / 1500 XP level-six constants, and `empty_experience(owner)`.
The pure functions cannot award XP, insert an AC, or change any journal. Owner
checks must use the authenticated workspace owner supplied by the coordinator.

The old experience schema and seen/choice/grant semantics are retained.
Assignments do not inherit another challenge's attempts. A merge unions only
the chosen challenge's attempts, caps at 128, and keeps the winning pass's exact
receipt even at the cap. Grants use the maximum existing amount, never a sum;
different owners cannot merge. The starter curve retains the old lexical
`selectedAt` selection and exact owner check. Six-level receipts parse both a
JSON object and a stored JSON string, preserve old extra metadata, and enforce
the existing 0..1500 integer bound. The legacy policyVersion/version equality
quirk is kept where Python used `== 1`; explicitly checked integer fields never
accept bool or float. Retaining readable old data does not create qualification.

Four Rust tests passed with 954 direct comparisons against the actual Python
functions: 216 experience validations, 169 experience merges, 63 starter
validations, 441 starter merges, and 65 six-level receipts. Fixtures include
invalid/missing fields, foreign owners, separate assignments, lower old grants,
basic/week dates, timezone/naive dates, leap-second/year-zero rejection, capped
attempts, and retained metadata. Source SHA256 values are in `policy-oracle.json`.
The test helper only imports public policy source, suppresses bytecode, and
uses constructed owners; production Rust never invokes it.

```text
cargo test -p tobe-core --test growth_policy
```

Set `TB_NATIVE_TEST_PYTHON` for this test-only oracle, and optionally
`TB_GROWTH_POLICY_PROOF` to save its public count/source receipt. These checks
do not count as experience/challenge endpoints, actual full-template judge
integration, or complete growth/insights API acceptance. Actual XP bookkeeping
and the two full 24-case assessment suites follow in separate natural batches;
`service`, the account merge coordinator, and the native runner remain owned
by the central Rust agent.
