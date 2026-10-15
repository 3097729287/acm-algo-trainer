# TB · Training Workbench

TB combines competitive programming problems, editorials, C++ editing, local sample judging and personal training records. It supports Codeforces, AtCoder, Nowcoder and Luogu.

**Version: [TB v1.0.17](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.0.17), October 15, 2026.** Source, application and extension share version 1.0.17; the tag and BUILD-INFO identify the build commit. Before its release assets become public this version is not formally released; use the latest-stable download link below.

[Latest stable download](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [Website](https://3097729287.github.io/acm-algo-trainer/) · [中文](README.md) · [Usage](docs/usage.md) · [Development](docs/development.md)

![TB training workbench](docs/assets/workbench.png)

## Install and upgrade

For Windows 10/11 x64 use `TB-Setup-1.0.17-win64.exe`; it includes a C++ compiler and offline WebView2 setup. Extract the entire `TB-1.0.17-win64.zip` for portable use. Save drafts and exit TB before upgrading into the existing directory. Personal databases are preserved.

Assets include a 1.0.16 → 1.0.17 delta, a browser extension ZIP, `RELEASE-MANIFEST.json`, `SHA256SUMS.txt` and `BUILD-INFO.json`. Older versions can follow the existing delta chain or use the full installer. Reload the bundled extension in Edge/Chrome after updating.

## Changes in v1.0.17

- Shared shelves in the competition and problem library pages: All, Nowcoder, Luogu, Codeforces, AtCoder, XCPC history and Lanqiao Group B history. Removed the platform dropdown, exposed difficulty/result filters, and shortened the date-sort label.
- Natural contest-name ordering retains series, year, location and distinct Gym mirrors. Existing task IDs and personal records are preserved.
- Added 5328 tasks from 455 verified ICPC/CCPC Gym rosters. Rechecked all 2202 existing tasks and changed 1003 difficulty values. Reviewed Nowcoder Weekly 165 E/F estimates are approximately 1900/2100.
- Estimates display an approximation sign with source, interval and confidence. Tasks without sufficient evidence remain unrated; statement subjects and zero solves no longer manufacture difficulty values.
- Activity shows only distinct official passes per day, including repeat passes on later days. The calendar and counts use five styles for 0, 1, 2–3, 4–6 and 7+ tasks.

The library contains **7530 tasks across 760 contests**, 2202 bundled statements, 796 default editorials, 1 detailed editorial and 376 lessons. New Gym statements are fetched and cached when opened; they require an accessible original site. 1781 tasks have official or estimated difficulty and 5749 remain unrated. Another 16 online rosters could not be verified; see the [coverage report](backend/resources/cf-xcpc-coverage.json) and [release notes](docs/releases/1.0.17.md).

## Workbench features (current source)

| Feature | Behavior |
| --- | --- |
| Bundled content | 7,530 tasks, 2,202 bundled statements, 796 default editorials, 1 detailed editorial and 376 foundation lessons in SQLite; illustrations work offline and open at full size |
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

The repository is `3097729287/acm-algo-trainer`; versioned source is available at the [v1.0.17 tag](https://github.com/3097729287/acm-algo-trainer/tree/v1.0.17). Each release synchronizes source, both READMEs and affected documentation; the release tag identifies the build commit. See the [release synchronization checklist](docs/development.md#发布同步检查).

Application source is MIT licensed. See [contributing](CONTRIBUTING.md), [third-party notices](THIRDPARTY.md), [compiler sources](TOOLCHAIN-SOURCES.md) and [ranking deployment](server/leaderboard/README.md).
