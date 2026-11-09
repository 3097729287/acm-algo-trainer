# Reviewed Hubei H / P10865 counting identity

The complete original-source comparison in
`content-updates/20261109-new-xcpc-hubei/source-review.json#existingEquivalentTasks`
binds Gym 105139 H (official original PDF page 11) to Luogu P10865. This fix
recognizes that exact pair only. Matching titles, adjacent IDs and unreviewed
metadata do not establish a shared question.

Counting key: `luogu.com.cn/problem/P10865`. Native key aliases:

- `luogu.com.cn/problem/P10865`
- `codeforces.com/gym/105139/problem/H`

The native IDs remain `luogu-training-P10865` and
`remote:codeforces:105139::H`. Their original URLs, source records, drafts,
submission records and native URL index are retained. `canonical_url` and
`TrainingService._identity_map` still represent native navigation/submission
identity. Catalogue responses separately expose `questionKey`,
`questionAliasKeys` and `questionAliasIds` on the pair's two entries.

Official solved totals, first-AC milestones, learning/ability evidence,
recommendations, unsolved-paper selection, goal allocation and new custom-list
additions use the shared question key. The old local-sample/official boundary
is unchanged. The pair also shares the live-contest history lock, preventing
its other native entry from exposing the old solution during an exam.

New first-AC XP is granted once under the counting key. Existing positive XP
under either old native key is retained without a difference payment. If both
were previously paid, both amounts remain in the historical total; no rows are
deleted or rewritten. Only an already-zero, unrated award can receive the
existing later-rating top-up, once across the pair. Acknowledged ranking event
IDs for either old key prevent duplicate delivery. The Node service applies
the same exact identity to its own earliest-first-AC projection and rewards.

This does not deduplicate native contest slots. Hubei A–L still has twelve
slots, H keeps the CF ID and URL, and a new official H receipt within this
contest's window earns the normal slot score even after a prior Luogu AC.

Validation:

- 84 targeted tests passed, including 12 new pair/history regressions, plus
  existing official reward, catalogue, goal/list, ability, replay, partial
  replay and ranking tests.
- `scripts/verify_hubei_question_identity_20261109.py` opened the exact final
  1,101,402,112-byte public source read-only. It copied thirteen public rows and
  22 referenced resources to a disposable 7,995,392-byte fixture. No personal
  database or installed application was opened.
- All thirteen native entries resolve independently, while their counting
  identities represent twelve questions. An old Luogu AC excludes both
  entries from new-question selection. The production replay preview and
  start retain all twelve Hubei slots and H's original CF problem response.
- A generated old Luogu receipt plus its 200-XP award, followed by a generated
  official CF H receipt five minutes into the replay, yields one accepted
  contest slot, one global solved question, `newProblem=false`, and exactly the
  same old 200-XP ledger. Drafts, the old source receipt and cached two-key
  public history remain equal. This exercises receipt handling with generated
  history; it is not a real official submission or an official-AC claim.
- Original source database size and modification time remain equal. All
  disposable fixture files were removed. The proof contains only public source
  digests and generated-history results.

Receipts and cleanup preflight are in
`docs/verification/hubei-question-identity-20261109/`.
