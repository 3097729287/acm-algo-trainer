# Pure Rust account chunk protocol

Base `60fd850d`; isolated worktree `tb-rust-account-chunks-20261109`. This delivers
the pure module described by `docs/native-account-chunks-contract.md`. It does
not activate an account, replace the Python application, publish a cloud root,
or claim that the account endpoints have been implemented.

The design document was read in full and cleanup checked before editing. The
fresh checkout had no obsolete Rust chunk implementation or owned build files
to delete. Existing vault, transport, journal, Python reference implementation,
and the pending metadata research remain in use. See `cleanup.json` for hashes.
Build output and large in-memory boundary tests use the C: temporary target;
there is no new large seed, archive fixture, live-account read, or app launch.

After the tests, nine generated Python bytecode files (448951 bytes) were
identified in this new checkout. Automatic approval review rejected their
removal with only `blocked by policy`; nothing was deleted and that path was
not retried by another method. They remain ignored, outside the commit. The
test helper now suppresses future bytecode creation. See
`generated-bytecode-preserved.json` for the actual cleanup outcome.

## Module contract

`backend-rust/src/account_chunks.rs` implements all agreed entry points:
`encode`, `from_wire`, `to_wire`, `code_reference`, `write_blob`, `read_blob`,
`pack_state`, `unpack_state`, `canonicalize_state`, and `read_code`.

`ObjectKind`, `ChunkObject`, `Canonicalized`, `Unpacked`, and the fixed `TABLES`
are public. `CodeReference` has validated private fields and public `root()`,
`sha256()`, `bytes()`, and `offset()` getters; it cannot be deserialized as an
already trusted reference. Parsing a serialized reference is the only public
constructor. An absent offset is zero, as in the old three-field references.

Wire GET objects have exactly `kind/data/children`; upload objects add exactly
`hash`, which must match the expected identity. The actual compressed bytes,
sorted unique lowercase child hashes, payload limit, and object digest are
checked both after a wire read and when a callback supplies a cached object.
`from_wire` receives a parsed `Value`; it does not claim to detect duplicate
keys in the original HTTP JSON text. Raw transport parsing stays with the
coordinator. Table primary-key duplication is checked explicitly.

The caller injects synchronous store/load closures. There is no HTTP client,
database, token, global cache, owner lookup, or persistent lock in this module.
Callbacks must use the coordinator's owner-scoped cache and epoch checks.
Callbacks propagate their original errors. A partial immutable cache write
cannot produce a returned root or outgoing state after an error; publication
and missing/upload receipts remain the coordinator's responsibility. In
particular, outgoing cloud-only cold-code links are retained without fetching
them; only the authenticated upload layer can confirm their remote presence.

Validated data failures use non-retryable `ACCOUNT_CHUNK_INVALID` (503), capacity
failures use `ACCOUNT_CHUNK_LIMIT` (413), and neither sets uncertainty. A corrupt
graph is not reclassified as a network interruption or an offline lease.

## Preserved semantics and limits

- All 17 tables, primary keys, table iteration order, month prefixes, one- or
  two-digit hash buckets, row grouping order, and stable restored row ordering
  follow the Python implementation. True integer IDs are required for the two
  integer-key tables; bool and `1.0` do not become an integer primary key. Other
  primary keys remain strings, including an empty draft context. Unknown row
  columns are retained; unknown tables and missing/null/duplicate primary keys
  fail closed.
- The sole legacy duplicate exception is `account_preferences` /
  `learning-summary-v1`: all duplicate rows and their order remain in the
  returned state and `duplicate_learning_summary` is set. The module neither
  chooses one nor runs a lossy repair.
- Limits remain 64 KiB decompressed node, 66 KiB compressed payload, 256 child
  dependencies, 128 concat parts, depth 24, 128 MiB per blob, 4 MiB manifest,
  4096 bucket entries per table, and 512 MiB expanded table bytes. The latter
  counter excludes profile/manifest bytes just as the existing Python reader;
  these retain their own 128 MiB / 4 MiB bounds. Shared parts are read for each
  occurrence, and non-payload dependency links are not mistaken for content.
- Gzip member CRCs, concatenated members, and Python-compatible zero padding
  are handled with a bounded expansion. Invalid gzip, extra garbage, excessive
  expansion, missing parts, wrong cached identities, and excessive depth fail.
- A strict older-than-30-days cutoff archives source bytes. Equal-to-cutoff,
  new, and invalid-date rows stay inline. Existing immutable refs are reused;
  matching fetched code and unfetched code with a known ref yield the same
  outgoing representation. Only the returned projection changes. Input state
  and actual local source strings remain intact, including interrupted writes.
- Code archives preserve month/hash grouping, sorted submission IDs, 64 KiB
  grouping, and standalone large files. References and reads enforce 262144
  bytes, offset, exact slice SHA256, and strict UTF-8. Code links inside
  submission conflicts remain reachable dependencies.

## Compatibility evidence

The test-only helper `backend-rust/tests/support/account_chunks_oracle.py`
imports the actual `backend/account_chunks.py` and `account_sync.py`, builds a
synthetic in-memory SQLite service, and calls the real old `canonicalize`,
`pack`, `get`, `read_blob`, and `submission_code`. Graph storage asserts that no
personal database lock is held; any HTTP request fails the test. The helper is
not imported or invoked by production Rust.

`python-bidirectional.json` records 17 tables, 75 old Python graph objects, 73
new Rust graph objects, nine code files read in both directions, and 4103
finite float vectors. All Unicode, controls, integer boundaries, negative
zero, small/large exponent forms, parse-to-bits, and re-encode bytes agree.

The default serde_json parser initially changed
`1.2345678901234567e+30` by one f64 ULP. `float-counterexample.json` records the
observed exact bit patterns. With the coordinator's explicit agreement the
existing dependency now enables `float_roundtrip`; package versions and
`Cargo.lock` are unchanged. The module additionally uses Python's exponent
presentation thresholds and signs for canonical encoding.

New Rust gzip bytes differ from Python's compressor for this fixture. The old
root `c2a819a16fdf2736ff255a52604c13b48a9c8abf6ea98be069ff1ccfa634135c`
is retained and verified as supplied. New gzip has its own honest root
`35bd2088b4f2a5668f84060f450492110c7d4a6c1da8c0658a3829757594555f`.
No old object is relabeled, recompressed under its old hash, or silently
substituted. Both Python and Rust read the other compressor's objects.

The independent tests also exercise malformed manifests, rows, code refs,
wire fields, cache digests, CRC/truncation/padding, concat membership, shared
parts, callback interruption, distinct owner-cache closures, cold references
without downloads, and the legacy summary exception. The explicit large test
actually writes and reads a 128 MiB blob, accepts exactly 512 MiB aggregate
table bytes, and rejects the fifth 128 MiB group. It stores only a small
deduplicated graph and commits no large fixture. It is ignored by the ordinary
fast suite and was run with `--include-ignored` for this delivery.

## Reproduction

Use the prepared MinGW toolchain and C: target, with `TB_NATIVE_TEST_PYTHON`
pointing to the Windows Python test interpreter. Run:

```text
cargo test -p tobe-core --test account_chunks -- --include-ignored
```

`TB_ACCOUNT_CHUNKS_PROOF` optionally selects the public JSON receipt path for
the synthetic bidirectional test. Actual test results and adjacent regressions
are recorded in `validation.json`. Endpoint negotiation, owner/endpoint/epoch
validation, authenticated upload confirmation, CAS, journal apply, account
activation, and actual asynchronous HTTP remain separate integration work.
