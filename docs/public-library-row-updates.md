# Public library row updates

The compact installer can keep an approved installed `data/library.sqlite3` and
its seed identity file. Both files are pinned by full SHA-256 in the existing
installer's anchors. They are excluded from replacements; the complete installer
continues to contain the latest complete public seed.

A release-owned `resources/public-library-update.json` identifies a gzip SQLite
payload by compressed and expanded length and SHA-256. The payload contains only
changed public rows and new resources, and is bounded to 32 MiB compressed and
64 MiB expanded. Approved bases may have different public content: the builder
includes the union of rows needed by any base. Every changed problem carries its
complete target course links. Complete target course membership prevents the
partial input from accidentally retiring unchanged courses.

Pictures already embedded in an approved base are recovered from that same
read-only file and checked by digest, MIME and length. Their bytes are not sent
again. Other existing content-addressed resources are reused. Source JSON and
the installed base are unchanged.

The runtime uses the existing `LibraryDatabase.merge_seed` conflict rules and
required recovery snapshot. Personal drafts and submissions are outside the
payload. Locally edited explanations, fetched statements and custom links retain
the same behavior as a complete seed merge. The composition digest makes a
second startup idempotent. Unknown bases, corrupt transports and missing reused
resources stop before a private library merge. Unrecognized existing cache files
are preserved; a distinct verified cache file is used instead.

Validation on 2026-11-09: 47 targeted checks pass, including original compact
installer recovery, base tampering, complete versus partial merges, multiple
released base contents, local explanations, course deletion, inline image reuse
and cache filename collisions. A pre-existing merge bug was also fixed: parsing
one fetched statement must not replace the table-wide saved-row lookup and
overwrite subsequent fetched overrides. The new two-path regression fails on
the prior implementation and passes on the fix. Two actual released 1.6.9 public
seed layouts produce the same eleven checked tables and 6,441 resource identities
as a full merge, including independent local explanation and draft fixtures.
The 1.6.9 to frozen 1.6.10 content prototype is
about 1.05 MB. This is a content transport measurement, not a claim that the
whole user-visible update meets the one-minute goal. The new path is not yet on
the stable channel.
