# TB · Training Workbench

TB combines a problem library, illustrated editorials, a C++ / Python editor, local judging and training records for Codeforces, AtCoder, Nowcoder and Luogu. SQLite preserves local work; the account service synchronizes learning data between computers.

<!-- release-status:start -->
**Source 1.3.0 is not yet published.** [1.2.1 remains the stable download](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.2.1). [Changes and validation](docs/releases/1.3.0.md).
<!-- release-status:end -->

[Website](https://3097729287.github.io/acm-algo-trainer/) · [Usage](docs/usage.md) · [Development](docs/development.md) · [中文](README.md)

![TB workbench](docs/assets/workbench.png)

## Install and upgrade

Windows 10/11 x64. The [installer](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.2.1/TB-Setup-1.2.1-win64.exe) includes the C++ compiler and offline WebView2 runtime. Fully extract the [portable archive](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.2.1/TB-1.2.1-win64.zip) before running it. Release pages include checksums and supported incremental updates.

Save drafts and exit TB before installing into the existing directory. Personal databases, source code and imported content are preserved. The updater saves work, takes online SQLite backups and verifies SHA-256 before replacement. Keep the same TB version on your computers. Original-site login uses TB's dedicated browser profile; no extension is required.

## Changes in 1.3.0

- Unified surfaces remove chrome separators and status icon borders, align values and keep table headers translucent. Problems and personal training use lists; contests have category folders with playable contest rows directly inside them.
- One filter button contains platform/event categories, nested knowledge topics, difficulty, verdicts and saved filters. CF / AC labels are shorter; ACM mirrors belong exclusively to ACM. Problem and contest ordering can be reversed.
- A practice flame counts consecutive Beijing dates with at least one formal submission. Drafts, browsing and sample runs do not count. Yesterday's streak remains while today is still open. Seven animated sizes begin at **1, 2, 4, 7, 15, 30 and 60 days**, then stay capped.
- Click a knowledge-domain radar vertex to drill into its topics, then filter problems. Difficulty estimates cover basic through common graph algorithms. Learning paths provide five stages (ideas, templates, interaction, practice and transfer), a two-pointer demo and candidate problems; editorial curation and per-problem explanations remain explicitly pending.
- Four training modes share green/yellow/red easy, normal and hard presets, defaulting to 0–10000. Topic/event selection moves into filters. Replay difficulty filters the whole event's median, preserving all original tasks and their order.
- A tiled settings home includes animated coffee, balloon, dinosaur, bulb and clouds. Account identity and acknowledgements have separate pages; jiahao27 joins the one-name-per-line credits. Backgrounds support GIF/animated WebP/PNG and timed local playlists. Editorial opacity is independently adjustable. Skill and title medals differ by tier/title. Sync uses a spinner and a transient completion indicator.
- The editor supports C++17 and Python 3, persists language metadata, and runs Python with the existing Windows Job resource limits. An isolated CPython 3.13.16 runtime ships with the app. Native site language controls select Python 3 / PyPy 3 for official submissions.
- Start the separate local administrator workspace with `TB新版.exe --admin` or its shortcut. Change XP level and skill tier and unlock every achievement/title. Its records and browser profile live under `admin-workspace/`; it neither authenticates to the user cloud account nor uploads public standings.
- Official submission opens its own browser window and closes that window after a durable final receipt has been displayed in TB. Login, verification and uncertain/error states remain visible. The guided tour reflects the new workflow.

## Library and progression

The public seed contains **5,819 problems (5,646 visible, 173 hidden), 2,422 statements, 1,302 default editorials, 1,302 detailed editorials and 376 lectures**. Uncached statements require connectivity. All existing content remains available; new editorial work is limited to known difficulty strictly below 2200. [Editorial policy](docs/editorial-policy.md).

XP levels and skill tiers are independent. Level 5 unlocks placement; at least five distinct, verified, independent first official ACs are required. Ability is the median difficulty of the strongest five. Iron through King starts at **0, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2100 and 2200**. This is a training estimate, not a direct copy of an original-site account rating. [Progression rules](docs/progression.md).

Only official AC receipts count as accepted problems. Sample runs retain their actual scope. Replay contests use original-site submissions; generated contests use the indicated local judging scope. Standings display separate level and ability information, daily hearts and private messages.

## Data and development

Account sync preserves training, complete submitted source, drafts, goals, XP, favorites and preferences. Conflicting drafts are retained separately. Site cookies stay local; translation keys use Windows DPAPI. JSON export excludes passwords, cookies and API keys.

```powershell
python backend/backend.py --offline
# In another terminal
cd frontend
npm ci
npm run dev
```

[Accounts](docs/accounts.md) · [Architecture](docs/architecture.md) · [Build and release checks](docs/development.md) · [Earlier releases](https://github.com/3097729287/acm-algo-trainer/releases)
