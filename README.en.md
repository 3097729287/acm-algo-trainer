# TB · Training Workbench

TB brings competitive programming problems, editorials, C++ editing, local judging and training records into one desktop workspace. It supports Nowcoder, Codeforces, AtCoder and Luogu.

[Download](https://github.com/3097729287/acm-algo-trainer/releases) · [中文](README.md) · [Architecture](docs/architecture.md) · [Development](docs/development.md)

![TB workbench](docs/assets/workbench.png)

The Windows installer includes the Python runtime, C++ toolchain and offline WebView2 installer. Extract the entire portable ZIP; it requires an existing WebView2 runtime.

The bundled SQLite library contains 796 editorials and their supporting foundation lessons. It works without the developer's Markdown archive. Newly discovered public problems may have no editorial yet. Foundation links come from the current problem and explicit references, rather than every lesson sharing a tag.

Use **Run samples** to test examples and **Submit** to send code through your connected original-site account in the background. Confirmed official AC receipts drive progress and shared rankings; samples and duplicate problems do not add ranking points.

The API starts independently of the React frontend. `frontend/` contains the UI, `backend/` owns HTTP and SQLite, `desktop/` owns the native shell and official-site adapters, and `server/leaderboard/` contains the Node.js, MySQL and Redis ranking service.

The shared ranking client targets the Aliyun API at https://47.82.84.74/. The service is deployed. Version 0.10.0 synchronizes the first confirmed official AC per canonical problem, including existing local receipts. It sends only identity/nickname, problem hashes, acceptance times and difficulty. Code, drafts, provider keys and site cookies stay local. Translation supports DeepSeek and custom compatible APIs, preserves code/math/examples, and includes a connection test.

Upgrades preserve personal records and identities, encrypted settings and local imports. Legacy JSON settings migrate once to SQLite without deleting the original files. See [usage](docs/usage.md), [migration](docs/architecture.md#数据与迁移), and [contributing](CONTRIBUTING.md).

```powershell
python backend/backend.py --offline
# In another terminal
cd frontend
npm ci
npm run dev
```

The repository URL remains `acm-agent-workflow`; TB is the primary product. Application source is MIT licensed. See [third-party notices](THIRDPARTY.md) for distributed components.

Software updates are checked at startup and daily while running. Settings → Updates supports manual checks, download progress and installation with SHA-256 verification. The installer preserves personal state; TB saves the current draft, creates online SQLite backups, exits normally, installs in place and restarts. Active official submissions and contests must finish first. Stable Windows releases come from this repository only.
