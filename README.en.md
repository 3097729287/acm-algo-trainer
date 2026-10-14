# TB · Training Workbench

TB combines competitive programming problems, editorials, C++ editing, local sample judging and personal training records. It supports Codeforces, AtCoder, Nowcoder and Luogu.

**Version: [TB v1.0.16](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.0.16), October 15, 2026.** Source, application and browser extension share the same version. The release tag and BUILD-INFO identify the build commit; asset availability is shown on the release page.

[Latest stable download](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [Website](https://3097729287.github.io/acm-algo-trainer/) · [中文](README.md) · [Usage](docs/usage.md) · [Development](docs/development.md)

![TB training workbench](docs/assets/workbench.png)

## Install and upgrade

For Windows 10/11 x64 use `TB-Setup-1.0.16-win64.exe`; it includes a C++ compiler and offline WebView2 setup. Extract the entire `TB-1.0.16-win64.zip` for portable use. Save drafts and exit TB before upgrading into the existing directory. Personal databases are preserved.

Assets include a 1.0.14 → 1.0.16 delta, a browser extension ZIP, `RELEASE-MANIFEST.json`, `SHA256SUMS.txt` and `BUILD-INFO.json`. Local 1.0.15 users can use the full installer. Reload the bundled extension in Edge/Chrome after updating.

## Changes in v1.0.16

- Fix CF native submit controls and form ownership. Waiting for preparation does not imply logout. Ordinary preparation errors stay retryable; human handoff happens for an actual verification request. An uncertain dispatched request is tracked without resending code.
- Ten progression levels require 200, 400, …, 1800 XP respectively, totaling 9000 XP. Each tier has a distinct icon and color; achievements now extend to harder tasks, 10,000 independent solves and longer training streaks.
- Level 10 unlocks TB ranked points. Independent first official ACs meeting the current difficulty earn points once per original problem. Emerald and higher require daily qualifying solves; missed completed Beijing days deduct points. King stars continue increasing. TB ranked points are personal training scores, separate from official ratings and the shared solve leaderboard.
- Daily AC is a separate topbar item. The level control displays X/Y XP or ranked points; old popup statistics are removed. Account editing is collapsed. Public-statistics binding is limited to CF and AtCoder; all four original-site submission adapters remain available.
- The public library contains 2202 problems and statements, 796 default editorials, 1 detailed editorial and 376 foundation lessons. Every problem has a knowledge classification and practice difficulty; 762 ratings are explicitly marked TB estimates. Some classifications describe statement subjects and do not claim a verified solution algorithm.
- Normalize XCPC and Nowcoder contest names automatically. Remove repeated contest prefixes from problem titles while preserving original titles and identities.

See [v1.0.16 release notes](docs/releases/1.0.16.md).

## Workbench features (current source)

| Feature | Behavior |
| --- | --- |
| Bundled content | 2,202 problems and statements, 796 default editorials, 1 detailed editorial and 376 foundation lessons in SQLite; illustrations work offline and open at full size |
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

The repository is `3097729287/acm-algo-trainer`; versioned source is available at the [v1.0.16 tag](https://github.com/3097729287/acm-algo-trainer/tree/v1.0.16). Each release synchronizes source, both READMEs and affected documentation; the release tag identifies the build commit. See the [release synchronization checklist](docs/development.md#发布同步检查).

Application source is MIT licensed. See [contributing](CONTRIBUTING.md), [third-party notices](THIRDPARTY.md), [compiler sources](TOOLCHAIN-SOURCES.md) and [ranking deployment](server/leaderboard/README.md).
