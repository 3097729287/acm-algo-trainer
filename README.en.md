# TB · Training Workbench

TB combines a problem library, editorials, C++ editing, local sample judging and personal training records. It supports Codeforces, AtCoder, Nowcoder and Luogu; personal data stays on your computer.

**[v1.0.18](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.0.18), 2026-10-15.** Application, frontend and extension share this version. The tag and BUILD-INFO identify the actual build commit. Before the assets become public this source is unpublished preparation and v1.0.17 remains stable; use the latest-release link. Once published, the v1.0.18 release is authoritative.

[Latest stable download](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [Usage](docs/usage.md) · [Build instructions](docs/development.md) · [中文](README.md)

![TB workbench](docs/assets/workbench.png)

## Install and upgrade

Windows 10/11 x64: `TB-Setup-1.0.18-win64.exe` includes the compiler and offline WebView2 runtime. Extract the entire `TB-1.0.18-win64.zip` for portable use. Save drafts and close TB before updating the existing directory. Personal databases are never replaced by the public seed.

Assets include the 1.0.17 → 1.0.18 delta, browser-extension ZIP, `RELEASE-MANIFEST.json`, `SHA256SUMS.txt` and `BUILD-INFO.json`. Older installations can follow the existing delta chain or use the full installer. Reload the bundled extension after upgrading.

## Changes in v1.0.18

- Every launch checks for stable updates, including before login, and automatically downloads, verifies and installs a new version without confirmation. Installation waits for draft saving and pending submissions/mocks, then retries automatically. The daily-check preference only affects additional checks while running.
- Removed the group and platform strip from My Training. Difficulty and verdict controls share a compact row with search; the library retains its seven category tabs.
- Daily missions open from the top bar, with claim progress and reward indicators. Notifications support marking all as read without deleting links or history.
- Replaced level titles with algorithm-oriented themes. Activity counts use quieter numeric and bar styles with five intensity bands.
- Multiple goals share one weekly contest plan: each contest family takes its highest workload and practice range, with suggested unsolved questions. Daily goal assignments remain independent.
- New discovery is limited to ended Nowcoder, Luogu and AtCoder contests, the 31 previously selected Codeforces editorial contests, and new XCPC events from 2017 onward. Retired catalogue entries remain available to existing personal history.
- Standardized Chinese contest names and verified 63 original event dates. Mirror upload/replay dates are separated; unknown dates display only the verified event year.
- Retained 295 CF Gym XCPC contests / 3580 problems, including 284 published whole-contest Gym difficulty levels. Added 439 evidence-backed problem estimates and 172 specific knowledge labels.

The public seed contains **5782 problems, 600 contests, 2202 statements, 796 default editorials, one detailed editorial and 376 lessons**. Of the problem ratings, 291 are official and 1929 are clearly marked estimates; 3562 remain unrated. Whole-contest Gym levels are separate from problem ratings. Knowledge metadata uses existing public/mirror evidence and explicit terms in identified public editorials; automatic classification does not claim a reverified algorithm. Newly added Gym statements require an online fetch and are cached after opening.

[Release notes](docs/releases/1.0.18.md) · [Contest audit](backend/resources/contest-audit-1.0.18.json) · [Rating audit](backend/resources/xcpc-rating-audit.json) · [Knowledge audit](backend/resources/xcpc-knowledge-audit.json)

## Data and development

`frontend/` renders the workbench, `backend/` owns the SQLite library and personal records, `desktop/` hosts WebView2 and the browser bridge, and `server/leaderboard/` provides the independent shared service. Public library source lives under `data/library/`; `data/library.sqlite3` is rebuilt from those tracked JSON files. Personal databases, drafts, identity, credentials and cookies are excluded from distributions.

Run `python scripts/check.py`, the frontend build and the relevant Playwright tests before release. Packaged releases require isolated native desktop, C++ judging, fresh-install, upgrade, uninstall retention and actual delta replacement checks. See [architecture](docs/architecture.md), [development](docs/development.md) and [third-party notices](THIRDPARTY.md).
