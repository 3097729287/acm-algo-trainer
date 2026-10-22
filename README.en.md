# TB · Training Workbench

TB combines a problem library, illustrated editorials, a C++ / Python editor, local judging and training records for Codeforces, AtCoder, Nowcoder and Luogu. SQLite preserves local work; the account service synchronizes learning data between computers.

<!-- release-status:start -->
**[1.3.2 is released](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.3.2).** [Changes, upgrade checks and SHA-256](docs/releases/1.3.2.md).
The source is **1.3.3, not yet released**. Search controls and equal page spacing are under validation; downloads still point to 1.3.2. [Upcoming changes](docs/releases/1.3.3.md).
<!-- release-status:end -->

[Website](https://3097729287.github.io/acm-algo-trainer/) · [Usage](docs/usage.md) · [Development](docs/development.md) · [中文](README.md)

![TB workbench](docs/assets/workbench.png)

## Install and upgrade

Windows 10/11 x64. The [installer](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.3.2/TB-Setup-1.3.2-win64.exe) includes the C++ compiler, Python 3 runtime and offline WebView2 runtime. Fully extract the [portable archive](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.3.2/TB-1.3.2-win64.zip) before running it. Release pages include checksums and supported incremental updates.

Save drafts and exit TB before installing into the existing directory. Personal databases, source code and imported content are preserved. The updater saves work, takes online SQLite backups and verifies SHA-256 before replacement. Keep the same TB version on your computers. Original-site login uses TB's dedicated browser profile; no extension is required.

## Changes in 1.3.3

- Search bars place the direction toggle before filters, with matching default colors. Changing direction alone does not show a filter indicator.
- Uniform spacing on all four workspace edges also applies to large windows. Settings tiles, credits and translation panels fit the available height and preserve their bottom corners.

## Changes in 1.3.2

- Compact navigation removes page breadcrumbs. The uppercase TB mark toggles the sidebar; settings subpages have a return arrow and Escape navigation, tooltips for explanations and solid configuration panels. Sync indicators keep a fixed position.
- Daily goal problems move into My Training. Queue headings align left, outlined themes border individual problems and rounded surfaces clip square overflow. Remove redundant submission symbols and approximate difficulty prefixes.
- Browse contests, replay events and topic selections through nested folders. Parent topics are selectable, active topic filters can be cleared in the header, and ordered lists expose a direction button beside search.
- Mock history appears below setup, newest first. Single problems default to 30/45/60/75 minutes by difficulty; topical and comprehensive durations follow difficulty and problem count. Replays use the original duration; manual values are retained.
- Every timed mode submits through the original-site browser workflow. The problem menu escapes toolbar clipping, timer and finish controls sit at the upper right, and the editor keeps autosave without import/save buttons or a focus outline.
- Knowledge mastery weights judged success, independence, submission stability and difficulty. Fewer than five distinct judged problems or three rated problems displays `?%`. Parent topics deduplicate shared evidence; adding unused catalog problems cannot reduce mastery.
- Compact standings, restored AC colors, larger counters, filled hearts, consistent flame icons, symmetric rank medals and refined avatar frames. XP rings grow clockwise from the bottom. Achievement icons reflect their meaning, goal controls move into the account panel and credits use larger, colored names.
- Each settings tile has a distinct, centered animation suited to its space: a detailed dinosaur turns at the edges, balloons rise through a tall tile, clouds cross a wide tile, varied buildings surround a planet with a slower explosion and rebuilding cycle, and the bulb glows gently.

## Changes in 1.3.1 (released baseline)

- Search and filter share the top bar without covering status controls. Favorites and sorting move into the filter; contests default to a list.
- The AC indicator shows the pre-today baseline and today's count, e.g. `AC:82` or `AC:82+2`. Static sketch flames and decorated rank avatar frames replace the previous artwork. Growth combines account statistics and radar details.
- Four training modes share generate/start controls and direct topic/event selectors. Presets are 1000–1400, 1300–1700, 1600–2000 and 1900–2200. Dropdown popups no longer close before selection.
- Editable keyboard shortcuts support conflict detection and reset. Navigation labels, groups and order share one editor; settings breadcrumbs and Escape return to the settings home.
- Page opacity works at 0–100%, including lists, statements, editor and editorials. Practice fills the client area; the back arrow or Escape restores navigation.
- Wider standings put medals first and interactions last. Your own heart is colored with no self-comment button. The activity section stays present and contains only the current Beijing date. Deletion uses an anchored confirmation.
- Settings tiles fill the available space with refined dinosaur, cloud, bulb and planet animations. Credits are centered and enlarged; notifications no longer include update configuration.
- Account settings display authenticated local identity immediately. Minimize/restore stops changing main WebView visibility. Renderer exits receive bounded recovery and a visible fallback; draft journals remain intact.

## Library and progression

The public seed contains **5,819 problems (5,646 visible, 173 hidden), 2,422 statements, 1,302 default editorials, 1,302 detailed editorials and 376 lectures**. Uncached statements require connectivity. All existing content remains available; new editorial work is limited to known difficulty strictly below 2200. [Editorial policy](docs/editorial-policy.md).

XP levels and skill tiers are independent. Level 5 unlocks placement; at least five distinct, verified, independent first official ACs are required. Ability is the median difficulty of the strongest five. Iron through King starts at **0, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2100 and 2200**. This is a training estimate, not a direct copy of an original-site account rating. [Progression rules](docs/progression.md).

Only official AC receipts count as accepted problems. In 1.3.2 every timed mode submits through the original-site browser; local sample runs and historical local records retain their actual scope. Standings display separate level and ability information, daily hearts and private messages.

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
