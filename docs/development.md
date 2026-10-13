# 开发、验证与构建

需要 Python 3.13、Node.js 24，评测需要支持 C++17 的 g++。API 和数据库只依赖 Python 标准库；桌面构建依赖 `backend/requirements.txt`。

```powershell
$env:TB_OFFLINE = "1"
python backend/backend.py --offline --state-dir .backups/dev-state
# 独立终端
cd frontend
npm ci
npm run dev
```

Vite 默认代理 `127.0.0.1:18765`；改变后端地址时设置 `TB_API_URL`。构建后的界面可通过 `--frontend frontend/dist` 与本机服务组合。桌面开发先安装依赖并构建界面，在仓库根目录使用隔离状态启动：

```powershell
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
$env:TB_OFFLINE = "1"
$env:TB_STATE_DIR = "$PWD/.backups/desktop-dev-state"
python desktop/launch.py
```

API 的可选参数见 `python backend/backend.py --help`。当前正式版为 [v0.10.1](releases/0.10.1.md)，准确的发布源码以对应 Git 标签为准。

```powershell
python scripts/check.py
cd frontend
npm run build
npm run test:ui
npm run test:compilers
npm run test:model
npm run test:math
npm run test:workbench
npm run test:e2e
node tests/software-updates.mjs
cd ../server/leaderboard
npm test
```

检查使用临时目录和离线模式；端到端检查启动独立 API 与 Vite，并验证真实 SQLite 题解读取。浏览器默认用系统 Edge；CI 使用已安装的 Playwright Chromium。截图保存在被忽略的 `frontend/tests/screenshots/`。

## 本地更新记录

每次版本或 PR 更新，都同步到用户指定的本地项目目录，并覆盖维护当前更新记录，写清提交、状态、验证结果、当前源码位置和实际启动入口。未合并的 PR、已合并的源码、本地构建和正式发布分别标明；仅源码更新须注明尚未打包。

本地只保留最新版完整可运行程序和当前开发所需内容，不保留历史 EXE、发布包、重复源码快照或旧构建目录。清理前核实源码已保存在 GitHub，保全未上传提交和修改；当前开发工作副本仍需保留。

新程序须完成隔离验证。旧程序保存并正常关闭后，使用 SQLite 在线备份迁入并核对个人数据，更新最新版快捷方式，再删除被替代的程序。训练记录、草稿、身份、设置和用户导入内容不属于可删除的历史版本。

## 导入公共题库

```powershell
python scripts/import_library.py --archive <包含题解目录的数据根> --output data/library.sqlite3
python scripts/library_seed.py export   # sqlite -> data/library/*.json
python scripts/check.py --library-only
```

导入只读源归档，清除分发库的个人状态，保存可移植题解、题面、图片和精确讲义关系。生成前保留原库备份；不要将个人工作数据库替换为公共库。

`data/library.sqlite3` 不进入 git，git 管理的是其文本源 `data/library/*.json`。改完题库后运行 `export` 提交文本源；clone 或打包时 `data/library.sqlite3` 缺失会自动由文本源重建（`scripts/library_seed.py build` 可手动触发）。

新增详细版写入 `data/library/detailed_solutions.json`：每条记录使用 `problem_id`、`markdown`、`source_path`、`images`，与默认版的记录格式一致。`problem_id` 必须对应已有题目，`source_path` 只保存可移植的来源说明；运行时只读数据库。不要覆盖 `solutions.json`。补写后执行 `python scripts/library_seed.py build`、`python scripts/check.py` 和 `node frontend/tests/detailed-solutions.mjs`（在 `frontend` 目录运行时使用 `node tests/detailed-solutions.mjs`）。详细版须针对本题解释读者卡点，包含必要的样例推演与正确性说明，不由默认版机械扩写或自动改名生成。

## Windows 安装包

先构建前端，再在新的空 staging 目录进行构建。编译器目录必须包含完整 `ucrt64` 树；与分发二进制对应的源代码、许可证和构建配方也要提供。

```powershell
python -m pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
python scripts/build_release.py build --stage build/0.10.1
python scripts/build_release.py assemble --stage build/0.10.1 --compiler-source <compiler目录>
python scripts/build_release.py installer --stage build/0.10.1 --inno <ISCC.exe> --webview2 <离线WebView2安装程序>
```

`TB新版.exe --package-check <报告路径>` 在隔离状态下检查内置题解和真实 C++ 评测；`--native-check` 检查实际桌面界面；`--serve-check` 启动检查服务，到同名 `.stop` 文件出现时停止。通过 `TB_STATE_DIR` 指定一次性状态，验证时设置 `TB_OFFLINE=1`。生产安装包不得包含这些测试产生的数据。

真实安装与升级检查使用独立 AppId，不修改日常安装、快捷方式或个人状态；在 `build/release-check-current-*` 保留报告与隔离数据。验证当前桌面版本的升级时，使用旧版公共安装目录作为输入，检查会排除其个人状态：

```powershell
python scripts/check_current_release.py --stage build/0.10.1 --legacy-package <旧版公共安装目录> --inno <ISCC.exe> --webview2 <离线WebView2安装程序>
```

`scripts/check_release.py` 保留为 0.5 迁移检查，需要对应旧版安装脚本（`--legacy-iss`）。`scripts/check_update_helper.py` 检查自动更新助手，须配合可丢弃程序与状态使用。

安装程序按相同 AppId 升级，只覆盖程序和公共种子库。完成后验证旧草稿、提交代码、身份、模拟赛和经验值仍在；发布前准备 `SHA256SUMS.txt`、`BUILD-INFO.json` 与文件清单，并核对下载资产和对应源码。构建工具不会覆盖已有 staging；重复构建使用新的空目录。
