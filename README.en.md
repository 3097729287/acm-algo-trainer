# TB · Training Workbench

TB brings competitive programming problems, editorials, C++ editing, local sample judging and training records into one desktop workspace. It supports Nowcoder, Codeforces, AtCoder and Luogu. Bundled content and personal records work locally; public account sync, translation and shared rankings use the network as needed.

**Latest stable release: [TB v1.0.14](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.0.14), released on October 14, 2026.** It fixes independent daily-goal counts, original-site submission verification and statement loading, with file delta updates.

**Current source: v1.0.15, built and validated locally; no GitHub Release has been published for this version.** It adds official receipt synchronization, training statistics, contest improvements and more bundled problems. See the [1.0.15 source update notes](docs/releases/1.0.15.md). Downloads below remain on the published 1.0.14 release.

[Download latest](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [Website](https://3097729287.github.io/acm-algo-trainer/) · [中文](README.md) · [Usage](docs/usage.md) · [Development](docs/development.md) · [Report an issue](https://github.com/3097729287/acm-algo-trainer/issues)

![TB workbench with problem, editor and illustrated editorial](docs/assets/workbench.png)

## Install and start

For Windows 10/11 x64, download [TB-Setup-1.0.14-win64.exe](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.0.14/TB-Setup-1.0.14-win64.exe). The installer includes Python, a C++ toolchain and an offline WebView2 installer. Exit TB before manually upgrading into the existing directory.

Extract the entire [portable ZIP](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.0.14/TB-1.0.14-win64.zip); it requires an existing WebView2 runtime. The release also includes the 1.0.13 → 1.0.14 delta package, `RELEASE-MANIFEST.json`, `SHA256SUMS.txt` and `BUILD-INFO.json`.

Choose a problem, add it to your training and write C++. **Run samples** tests public examples. **Submit** (Ctrl+Enter) sends code through your connected original-site account in the background and shows the result in TB. For first use, load the bundled Edge/Chrome browser extension and sign in to the platform in your regular browser; see [browser setup](docs/usage.md#练习).

## Latest stable release: v1.0.14

- Each daily goal keeps and counts its own assigned problems. Daily XP counts distinct problems accepted that day, including previously solved problems, without repeating first-AC rewards.
- Submission verification is separate from account login and reuses existing browser sessions. Fixes cover stale receipts blocking later submissions and statements with empty sample input. Users complete site verification themselves; uncertain requests are never resent automatically.
- Updates use verified file deltas, preserving drafts and databases without downloading the compiler or WebView2 again. Skipped versions follow available intermediate delta packages.
- The published 1.0.14 bundle contains 958 problems and statements, 796 default editorials, 1 detailed editorial and 376 foundation lessons.

See the [v1.0.14 release notes](docs/releases/1.0.14.md).

## Additions in the current v1.0.15 source

- Synchronize Codeforces official submissions for the configured account and receive personal submission records through the browser extension for Codeforces, AtCoder, Nowcoder and Luogu. Records matching bundled or locally known problems retain their original timestamps and are deduplicated by platform and submission ID. Missing submitted code is labeled explicitly.
- If submission preparation times out or verification is required, open the relevant browser page and try to prefill the code. The user completes verification and submits through the original form while TB continues watching for the result without resending code.
- Show today's AC count and total solved problems; keep sample runs out of global submission history. Search naturally sorted contest names and delete finished mock-contest records while preserving drafts, code and AC progress. Daily goals retain their original tasks when bundled problem IDs change.
- Bundle 1,982 problems and statements, 796 default editorials, 1 detailed editorial and 376 foundation lessons. Public synchronization may add more problems locally. Some contest rosters remain unverified; coverage reports live in `backend/resources/*-coverage.json`.

## Workbench features (current source)

| Feature | Behavior |
| --- | --- |
| Bundled content | 1,982 problems and statements, 796 default editorials, 1 detailed editorial and 376 foundation lessons in SQLite; illustrations work offline and open at full size |
| Training and mock contests | Single-problem, mixed, focused and replay contests; topics and editorials stay hidden until review; finished contest records can be deleted |
| Code and records | Saved drafts, code and results; official submission history is separate from workbench sample runs; independent statement font size from 14 to 32px |
| Knowledge and growth | Today's AC count, total solved problems, hierarchical knowledge coverage, recommendations, independent daily goals and achievements |
| Public accounts and translation | Public account synchronization; DeepSeek, Volcengine Ark and compatible custom translation APIs, with connection tests and code/math/sample preservation |
| Official AC rankings | Historical saved official receipts are uploaded automatically; each canonical problem counts once, with daily, weekly and total rankings in Beijing time |
| Software updates | Startup and daily checks, file delta downloads, SHA-256 verification, draft saving, online SQLite backups, changed-file replacement and restart |

Newly discovered public problems may have no editorial. Foundation links come from the current problem and explicit references, rather than every lesson sharing a tag.

The deployed ranking service is at `https://47.82.84.74`. It receives identity/nickname, problem hashes, acceptance times and difficulty; code, drafts, translation keys and site cookies stay local. Sample passes do not count. The service relies on client receipts and does not independently certify official-site results against cheating.

Use **Preferences → Updates → Software updates** for manual checks or to disable automatic checks. After downloading, choose **Save and replace update** (保存并替换更新). Active official submissions and contests must finish first. Versions from 1.0.13 use delta packages; older clients complete their initial upgrade through their existing installer flow. A failed delta restores the previous program files.

## Data and development

Upgrades preserve personal records, identity, encrypted settings and local imports. Runtime data lives in `state/`; do not distribute a used installation as a public package. Legacy JSON settings migrate once to SQLite without deleting the originals. See [data and migration](docs/architecture.md#数据与迁移).

`frontend/` contains React, `backend/` owns local HTTP and SQLite, `desktop/` owns the native shell and site adapters, and `server/leaderboard/` contains the Node.js/MySQL/Redis ranking service. Public library JSON lives in `data/library/`; the bundled SQLite database is rebuilt when missing.

Use Python 3.13, Node.js 24 and a C++17 compiler:

```powershell
$env:TB_OFFLINE = "1"
python backend/backend.py --offline --state-dir .backups/dev-state
# In another terminal
cd frontend
npm ci
npm run dev
```

The backend defaults to `127.0.0.1:18765`, the frontend to `127.0.0.1:5173`. For desktop development, install `backend/requirements.txt`, build the frontend and run `python desktop/launch.py` with disposable state. See [development and validation](docs/development.md).

The repository is `3097729287/acm-algo-trainer`; published source is available at the [v1.0.14 tag](https://github.com/3097729287/acm-algo-trainer/tree/v1.0.14). Each release must synchronize source, both READMEs and affected documentation; the release tag must identify the build commit. See the [release synchronization checklist](docs/development.md#发布同步检查).

Application source is MIT licensed. See [contributing](CONTRIBUTING.md), [third-party notices](THIRDPARTY.md), [compiler sources](TOOLCHAIN-SOURCES.md) and [ranking deployment](server/leaderboard/README.md).
