# 1.6.12 review completion and coding pack entrance

Base: `2da2b18f0912b39f1efea250a4478d91e5708806`. This independent change is source-only until the release worktree integrates and rebuilds it. The frozen 2da release output and all prior update proofs remain unchanged.

## Observed cause

`App.progressChanged` applied the fresh workspace after an official result but did not refresh the adopted learning-summary snapshot. `useLearningSummary` refreshed every 30 seconds; its `tb:learning-progress` listener had no dispatch anywhere in the frontend. `nextActionChoices` therefore kept the old pending plan review. Clicking that summary task passed its old `reviewId` through `App.openSummaryTask` to `training/start` as `restoreReviewId`. `ReviewScheduler.set_cancelled` then rejected the already completed review with 409 / “这次复习已经完成”. The same message can be reached by restoration, so it does not establish that the row's minus button failed.

Against unmodified 2da, an isolated synthetic SQLite case confirmed that a fresh AC completed the review, removed it from `workspace.reviews.tasks` and awarded exactly one review reward. Starting the stale review ID produced the reported 409. Removing that completed training row twice succeeded and preserved all submissions. The unmodified frontend model still chose the old pending summary review even with fresh accepted training and no pending review.

## Change

After Workbench progress is applied, App immediately refreshes the adopted summary. If `training/start` receives a completed review ID, it validates problem ownership and acknowledges `reviewAlreadyCompleted` without opening, activating, cancelling or rewarding the completed task. App refreshes the plan and stays out of that stale rewrite. The existing strict scheduler cancellation guard remains intact.

The lower-right gift came from the actual `LearningBrowser` portal's `study-pack-button`, independently of the main footer. That portal now omits the button while any visible problem/coding pane is present. The main footer and reading-only entrance retain their existing behavior. No CSS-only hiding or new interface text was added.

## Validation

- `test_reviews`: 27 passed. The regression removes a completed review twice, repeats both deferred and full `training/start` calls, and compares the completed task, entire submission rows, saved review code and reward totals. It also confirms no reactivation.
- `test_daily_chains` and `test_learning_summary`: 38 passed.
- `node tests/review-completion-app.mjs`: actual App, Workbench and LearningBrowser with explicitly synthetic, intercepted API records; all external traffic blocked. The submission control receives an offline fixture AC, then the top-bar summary advances in **359 ms**, without waiting for the 30-second timer. A second scenario settles the review between painting the shortcut and handling `training/start`; App does not enter the settled rewrite, show the completed-review error or send a completion write. Main pack present, coding pack absent from DOM, reading pack preserved. No browser errors or unknown API routes.
- `npm run build`: passed (the existing large-chunk warning remains).

The full-App receipt is `review-completion-app-20261109.json`. Its unique ignored raw case is `.backups/review-completion-app/1794230776926/`. The first fixture run (`1794230651177`) reached and passed the AC/coding checks, then failed because its own saved synthetic browser restored an open coding tab before the race scenario. That failed receipt and screenshot were preserved; the second case explicitly resets only the synthetic browser position.

These checks do not claim a new real Codeforces submission, live AI call, desktop installation or published release. The normal program and all normal personal databases, credentials and training state were untouched. Source and the frontend must both be rebuilt into the new 1.6.12 candidate; old producer/source metadata cannot be reused as the producer identity for changed app bytes.
