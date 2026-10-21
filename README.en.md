# TB · Training Workbench

TB combines a problem library, illustrated editorials, a C++ editor, local judging and training records for Codeforces, AtCoder, Nowcoder and Luogu. SQLite preserves local work; the account service synchronizes learning data between computers.

<!-- release-status:start -->
**Source version 1.2.1 is not yet published.** Release validation is in progress. Public downloads remain on [v1.1.5](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.1.5). [1.2.1 changes and validation](docs/releases/1.2.1.md).
<!-- release-status:end -->

[Website](https://3097729287.github.io/acm-algo-trainer/) · [Usage](docs/usage.md) · [Development](docs/development.md) · [中文](README.md)

![TB workbench](docs/assets/workbench.png)

## Install and upgrade

Windows 10/11 x64. The [installer](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.1.5/TB-Setup-1.1.5-win64.exe) includes the C++ compiler and offline WebView2 runtime. Fully extract the [portable archive](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.1.5/TB-1.1.5-win64.zip) before running it. Release pages include checksums and supported incremental updates.

Save drafts and exit TB before installing into the existing directory. Personal databases, source code and imported content are preserved. The updater saves work, takes online SQLite backups and verifies SHA-256 before replacement. Keep the same TB version on your computers. Original-site login uses TB's dedicated browser profile; no extension is required.

## Changes in 1.2.1

- A settings home opens detailed categories and remembers the category and scroll position when you leave and return. Similar interaction/navigation controls are merged. Translation API settings move here. Click the top-right avatar to choose or remove its image.
- Global and per-page opacity supports **0–100%**, with always-visible page controls and a reset-all action. Minimal, outlined, aurora and blueprint styles have distinct surfaces.
- Both problems and contests support nested folders: platform, series, contest; XCPC additionally groups event type, year, event and warm-up/main round. Existing metadata supplies categories and dates; unknown years remain unknown.
- A narrower sidebar has a collapsed knowledge drawer with a smooth transition. Unsubmitted problems use a grey dot. Mock setup, rankings and submission history remove repetitive text and put necessary explanations in tooltips.
- Daily tasks, achievements and the clock move to the bottom-right status bar. Top and bottom bars hide during practice. The top shows daily AC and hearts received today; AC color strengthens with the count. Hearts reset by the Beijing calendar date.
- **King starts at ability score 2200.** Existing ability evidence is reclassified without changing XP or records. The guided tour highlights real controls and waits for you to open a problem and return before continuing through the workflow.

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
