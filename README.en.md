# TB · Training Workbench

TB brings competitive programming problems, editorials, C++ editing, local sample judging and training records into one desktop workspace. It supports Nowcoder, Codeforces, AtCoder and Luogu. Bundled content and personal records work locally; public account sync, translation and shared rankings use the network as needed.

**Latest stable release: [TB v0.10.1](https://github.com/3097729287/acm-algo-trainer/releases/tag/v0.10.1), released on October 11, 2026.**

[Download latest](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [Website](https://3097729287.github.io/acm-algo-trainer/) · [中文](README.md) · [Usage](docs/usage.md) · [Development](docs/development.md) · [Report an issue](https://github.com/3097729287/acm-algo-trainer/issues)

![TB workbench with problem, editor and illustrated editorial](docs/assets/workbench.png)

## Install and start

For Windows 10/11 x64, download [TB-Setup-0.10.1-win64.exe](https://github.com/3097729287/acm-algo-trainer/releases/download/v0.10.1/TB-Setup-0.10.1-win64.exe). The installer includes Python, a C++ toolchain and an offline WebView2 installer. Exit TB before manually upgrading into the existing directory.

Extract the entire [portable ZIP](https://github.com/3097729287/acm-algo-trainer/releases/download/v0.10.1/TB-0.10.1-win64.zip); it requires an existing WebView2 runtime. The release also includes `SHA256SUMS.txt` and `BUILD-INFO.json`.

Choose a problem, add it to your training and write C++. **Run samples** tests public examples. **Submit** (Ctrl+Enter) sends code through your connected original-site account in the background and shows the result in TB. For first use, load the bundled Edge/Chrome browser extension and sign in to the platform in your regular browser; see [browser setup](docs/usage.md#练习).

## Features in v0.10.1

| Feature | Behavior |
| --- | --- |
| Bundled content | 958 problems and statements, 796 editorials and 376 foundation lessons, stored in SQLite; illustrations work offline and open at full size |
| Training and mock contests | Single-problem, mixed and focused practice; contest topics and editorials stay hidden until review; compact training and contest layouts |
| Code and records | Saved drafts, submission code and results; independent statement font size from 14 to 32px |
| Knowledge and growth | Hierarchical knowledge coverage, concept search, recommendations, daily tasks and achievements |
| Public accounts and translation | Public account synchronization; DeepSeek, Volcengine Ark and compatible custom translation APIs, with connection tests and code/math/sample preservation |
| Official AC rankings | Historical saved official receipts are uploaded automatically; each canonical problem counts once, with daily, weekly and total rankings in Beijing time |
| Software updates | Startup and daily checks, download progress, SHA-256 verification, draft saving, online SQLite backups, installation in place and restart |

Newly discovered public problems may have no editorial. Foundation links come from the current problem and explicit references, rather than every lesson sharing a tag.

The deployed ranking service is at `https://47.82.84.74`. It receives identity/nickname, problem hashes, acceptance times and difficulty; code, drafts, translation keys and site cookies stay local. Sample passes do not count. The service relies on client receipts and does not independently certify official-site results against cheating.

Use **Preferences → Updates → Software updates** for manual checks or to disable automatic checks. After downloading, choose **Save and install update**. Active official submissions and contests must finish first. v0.10.1 retries a direct HTTPS check when a shared proxy exhausts GitHub's API quota. See the [release notes](docs/releases/0.10.1.md).

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

The repository is `3097729287/acm-algo-trainer`; stable source is available at the [v0.10.1 tag](https://github.com/3097729287/acm-algo-trainer/tree/v0.10.1). Application source is MIT licensed. See [contributing](CONTRIBUTING.md), [third-party notices](THIRDPARTY.md), [compiler sources](TOOLCHAIN-SOURCES.md) and [ranking deployment](server/leaderboard/README.md).
