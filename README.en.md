# TB · Training Workbench

TB combines a problem library, illustrated editorials, C++ editing, local sample judging and personal training records for Codeforces, AtCoder, Nowcoder and Luogu. Account data and rankings share the existing server-side MySQL database; local SQLite retains a durable working copy and pending changes.

<!-- release-status:start -->
**Source v1.1.3 is being validated and packaged; stable downloads remain v1.1.2.** [Changes](docs/releases/1.1.3.md).
<!-- release-status:end -->

[Usage](docs/usage.md) · [1.1.2 release notes](docs/releases/1.1.2.md) · [Build instructions](docs/development.md) · [中文](README.md)

![TB workbench](docs/assets/workbench.png)

## Install and upgrade

Windows 10/11 x64. The [installer](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.1.2/TB-Setup-1.1.2-win64.exe) includes the compiler and offline WebView2 runtime. Extract the complete [portable archive](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.1.2/TB-1.1.2-win64.zip).

Save drafts, close TB and update the existing directory. Personal databases and imported content remain intact. Upgrade each computer to the same current release and log in in the dedicated submission browser when using v1.1.2. Automatic updates wait for saved drafts and active submissions/mocks, make online SQLite backups, verify SHA-256 and replace program files. Available deltas, `BUILD-INFO.json`, `RELEASE-MANIFEST.json` and `SHA256SUMS.txt` are listed on the release page.

## Version 1.1.3 (in preparation)

- Move the clock to the top bar and today's goal questions into the training list. Goal management uses one compact row.
- Add goal questions to Daily Tasks with a pending indicator. Newly discovered Div.3, ABC, Nowcoder weekly and Luogu basic/monthly events follow active goal requirements.
- Match actual owner submissions, preserve original acceptance dates and deduplicate historical results.
- Apply translucent surfaces across pages, reduce dividers, remove the standalone milestone and editorial inbox, open problems from the whole row, and sort numbered events newest first.

[Scope and details](docs/releases/1.1.3.md). This build retains 960 editorial pairs; parallel editorial additions remain separate.

## Version 1.1.2

- Replay contests submit through original-site forms and attach official receipts to the running contest. Long task IDs fit; deleting a replay removes training entries introduced only by it while preserving code and results.
- Remember the dedicated browser and locally encrypted sessions. Authenticated revision checks avoid downloading unchanged learning snapshots.
- Reduce full-database copies on autosave and keep remove/clear actions visible on smaller screens.
- Nicknames are unique; standings omit public IDs. Consistent status chips, progress cards and adjustable panel opacity make the workspace more useful.

[Details and a sample screen](docs/releases/1.1.2.md). The fixed build retains 960 editorial pairs; ongoing editorial additions remain separate.

## Version 1.1.1

- Visible browser submission replaces the silent transport. TB opens an original-site form in a dedicated Edge/Chrome profile, fills code, clicks once per explicit intent and follows that attempt's receipt. No browser extension is required. Log in once in that profile; verification stays with the source site.
- Startup validates a saved session through the authenticated state request, avoids replacing unchanged personal tables, and coalesces slow login requests. Authentication and cross-device takeover checks remain in place.
- Standings use compact framed rows, inline public IDs and small summary cards. Zero-solve users have no medal placeholder. Calendar summary values align across font sizes.
- Optional outlined, aurora and blueprint panels, static backgrounds, local background images and a training clock. The growth page includes a real daily leaderboard preview. Background images stay on the device.
- Duplicate account-settings entry removed; software-version labels use the software updater instead of an old catalogue cache.

[1.1.1 notes](docs/releases/1.1.1.md) · [Browser submission](docs/browser-preparation.md) · [Site adapter boundary](docs/site-adapters.md)

## Training and current library

- **Titles and progress:** twelve cumulative AC milestones from 1 to 2000 problems. Milestones at 500, 750, 1000, 1500 and 2000 award permanent titles instead of new XP. Training streaks of 30, 90, 180, 365 and 730 days also award titles; two years replaces the former 1000-day target. The highest AC title and streak title are equipped automatically. Previously earned XP remains unchanged.
- **Achievement feedback:** newly earned cards remain highlighted until hovered or focused individually. Read acknowledgements synchronize across computers. Clicking the top progress badge opens the training overview directly, with the highest earned AC milestone and the next target. Daily mission indicators stay in the top bar; unfinished training has its own navigation indicator.
- **Account and ranking display:** Growth groups the username, public ID, medals, account management, CF/AtCoder public ratings and translation settings. Rankings show nicknames, titles, level, tier and ranked points; the public ID stays on the account page. Users who log in that Beijing day appear with zero solves when applicable; zero solves earn no placement rewards.
- **Navigation and responsiveness:** contest rows offer a replay start action; recommendation rows open a problem directly. Training, keyboard settings and quick actions are grouped together. Contest lists use 40-item pages and unchanged workspace data keeps its object references. Hidden windows pause regular data and goal polling, then refresh when visible. Session checks, uploads and automatic software updates continue in the background.
- **Synchronization:** training, complete submitted code, drafts, goals, daily assignments, XP ledgers and preferences restore on another computer. A new login revokes the previous device; online clients detect revocation through an approximately three-second heartbeat. Initial merges are backed up and conflicting drafts are retained.
- **Loading and editorials:** compact catalogue payloads, cached response bytes, a lazy editor, bounded background statement fetching and shorter database locks reduce work. All 960 problems with a default editorial now have a detailed version, including all 26 problems in Nowcoder Weekly 162–165. The current XCPC and Lanqiao batch adds 151 editorial pairs covering 127 distinct problems; the selected scope of the 2026 Sichuan provincial contest and Qinhuangdao invitational is now complete, together with all eight problems of the 2026 Lanqiao provincial B paper and A–I of the 2026 national B paper (J awaits corrected constraints), plus all six selected problems of the 2026 Wuhan invitational; [completed and pending content](docs/editorial-content-20261016.md).

The library contains **5795 problems: 5622 visible and 173 hidden**, plus **2215 statements, 960 default editorials, 960 detailed editorials and 376 lessons**. Other entries are not guaranteed to have offline statements or editorials. Source-site failures retain cached content and drafts.

Automatic discovery follows the selected families: Nowcoder Weekly, Beginner, Practice and Challenge; Luogu Introductory, Basic and Monthly Div.2; CF Div.2/3/4; AtCoder ABC/ARC. Existing XCPC and Lanqiao collections remain. Unsupported automatic entries and those without usable statement/samples or an editorial are hidden without deleting personal history. Existing official ratings and tags also refresh; unknown ratings remain unknown.

The inventory below follows the source snapshot being read. The v1.1.2 binary inventory is pinned in BUILD-INFO.json (960 editorial pairs). Later editorial work is not silently substituted into that release.

## Data, services and development

Public library JSON under `data/library/` is tracked in git and rebuilt into `data/library.sqlite3`. Personal databases and credentials are excluded from distributions. Account snapshots include full personal code and referenced problem metadata/cached statements, but exclude site cookies, translation keys, DPAPI ciphertext and machine settings. Configure site login and translation keys separately on each computer.

Migrations `005_account_state.sql`, `006_public_progress.sql` and `007_unique_nicknames.sql` are deployed on the existing server and MySQL database. HTTPS checks on October 19, 2026 confirmed service version 1.1.2, account-state and public-progress protocol 1, single-device sessions, unique nicknames and revision-based snapshot restoration. The v1.1.2 client is published and the local installation has been upgraded. The local backend remains Python and the shared service remains Node.js.

Python 3.13, Node.js 24 and a C++17 compiler are required for development. Run `python scripts/check.py`, the frontend build and relevant Playwright tests. Packaged releases also require isolated desktop, judging, fresh-install, upgrade and retention checks. Source, documentation, release tag and build metadata must agree.

[Accounts and synchronization](docs/accounts.md) · [Architecture](docs/architecture.md) · [Development](docs/development.md) · [Shared service](server/leaderboard/README.md) · [Historical 1.0.19](docs/releases/1.0.19.md) · [Historical 1.0.20](docs/releases/1.0.20.md) · [MIT](LICENSE)
