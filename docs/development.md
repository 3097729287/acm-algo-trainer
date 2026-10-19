# 开发、验证与构建

源码 v1.1.4 正在验证与打包；当前正式版仍为 1.1.3，共享服务沿用 1.1.2 与协议 1。

## 1.1.4 发布检查

必须在移除开发机 MSYS/GCC PATH、含中文和空格的临时目录验证随包编译器，并核对宿主 DLL 搜索目录恢复。`--package-check` 对四站实际公共题面与参考代码运行样例，不向原站提交。检查 CE/ERROR 诊断、不同输入不复用结果，以及编译缓存随代码与编译器变化失效；保留 Job 时间、内存、输出及子进程限制。

运行完整 `python scripts/check.py`、前端 build 和 app、workspace-decorations、workbench、statement-format、replay-layout、rankings、webview-loading、issues、compilers、external-browser、official-sites 测试。回归覆盖 JSON 导出只读与敏感表排除、首次注册指引及重看、已领取任务提示清除、真实语言控件、样例原换行和公式、25–100% 不透明度及大小屏布局。

发布须固定已推送的干净提交；从该提交构建种子、程序、安装器、v1.1.3 增量与来源清单。全新安装、升级、原生窗口、更新助手与旧更新器实际应用必须通过。共享服务不升级，继续为 1.1.2 / 协议 1。另行续写内容与个人数据库不混入公共构建。


当前客户端正式版为 [v1.1.3](releases/1.1.3.md)，共享服务沿用 1.1.2 与协议 1。

## 1.1.3 验证范围

运行 `python scripts/check.py`、前端 build，以及 `tests/app.mjs`、`tests/workspace-decorations.mjs`、`tests/workbench.mjs`、`tests/replay-layout.mjs`、`tests/rankings.mjs`、`tests/webview-loading.mjs`。新增回归覆盖周日 AC 在周一收录、原日期保留、重复回执、未知题延迟回填、账号切换、四类目标比赛、重启及手动清空、本人缓存裁剪与移除收件箱 API。UI 检查整行点击、未完成目标提示、倒序轮次、透明度及 1024–2048 宽度的顶部时钟。

共享服务本版无修改，继续使用 1.1.2 与协议 1。安装、升级、更新器重启及 1.1.2 增量仍须在隔离目录执行；打包固定于已推送提交，续写题解和用户个人库不得混入。

## 1.1.2 发布检查

运行 `python scripts/check.py`、前端 build，以及 `tests/app.mjs`、`tests/workbench.mjs`、`tests/rankings.mjs`、`tests/workspace-decorations.mjs`、`tests/replay-layout.mjs`、`tests/external-browser.mjs` 与 `tests/webview-loading.mjs`。`python desktop/tests/managed_login.py` 使用隔离无头浏览器和合成会话验证关闭、重启；不访问真实 OJ。共享服务运行 SQLite 与独立 MySQL 的协议套件，包含并发抢昵称和快照版本确认。

恢复副本按五分钟限频，升级和云端替换仍独立备份。不要把该优化改成异步未提交写入。昵称迁移前备份同一 MySQL，在 API 停止时应用 `007` 并运行 `scripts/migrate-nicknames.mjs`，冲突中止而不自动改名。

发布使用固定、已推送提交的独立工作树，避免正在续写的公共内容改变包内库存；题库、前端、安装器、增量包、来源清单和标签须来自同一提交。完成全新安装、完整升级、更新器重启和上一正式版增量应用后再公开资产。



## 1.1.1 发布检查

本版使用可见浏览器适配层，不再分发浏览器扩展 ZIP。版本同步仍包含保留的扩展源码清单，以便历史 fixture 使用；实际安装包与资产清单不包含扩展。运行 scripts/check.py、前端构建、tests/external-browser.mjs、tests/workspace-decorations.mjs、tests/app.mjs 和 tests/rankings.mjs；从最终已推送提交重新构建公共题库、安装包、便携版及上一正式版增量包，并完成隔离全新安装、升级和草稿保留验证。

需要 Python 3.13、Node.js 24，评测需要支持 C++17 的 g++。本机 API 和 SQLite 使用 Python 标准库；桌面构建依赖 `backend/requirements.txt`。独立共享服务使用 Node.js 与 mysql2，生产账号和学习数据保存在与排行榜共用的 MySQL。

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

API 的可选参数见 `python backend/backend.py --help`。当前正式版为 [v1.1.0](releases/1.1.0.md)，源码标签、`BUILD-INFO.json` 与已发布资产均指向提交 `474d347b34fbd3815072d78ceed41c6abec18f72`。原服务器的 `005` 账号同步与 `006` 公开成长资料迁移均已完成，公网 HTTPS 已确认服务 1.1.0；本机客户端已升级，8 个个人数据库和 3 个快捷方式均已核对保留。

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
$tbVersion = (Get-Content VERSION).Trim()
python scripts/build_release.py build --stage "build/$tbVersion"
python scripts/build_release.py assemble --stage "build/$tbVersion" --compiler-source <compiler目录>
python scripts/build_release.py installer --stage "build/$tbVersion" --inno <ISCC.exe> --webview2 <离线WebView2安装程序>
```

`TB新版.exe --package-check <报告路径>` 在隔离状态下检查内置题解和真实 C++ 评测；`--native-check` 检查实际桌面界面；`--serve-check` 启动检查服务，到同名 `.stop` 文件出现时停止。通过 `TB_STATE_DIR` 指定一次性状态，验证时设置 `TB_OFFLINE=1`。生产安装包不得包含这些测试产生的数据。

真实安装与升级检查使用独立 AppId，不修改日常安装、快捷方式或个人状态；在 `build/release-check-current-*` 保留报告与隔离数据。验证当前桌面版本的升级时，使用旧版公共安装目录作为输入，检查会排除其个人状态：

```powershell
python scripts/check_current_release.py --stage "build/$tbVersion" --legacy-package <旧版公共安装目录> --inno <ISCC.exe> --webview2 <离线WebView2安装程序>
```

`scripts/check_release.py` 保留为 0.5 迁移检查，需要对应旧版安装脚本（`--legacy-iss`）。`scripts/check_update_helper.py` 检查自动更新助手，须配合可丢弃程序与状态使用。

1.0.18 自动更新回归须覆盖关闭每日检查后仍立即执行启动检查、登录前更新、无确认自动安装、草稿屏障、进行中任务结束后自动重试、损坏下载拒绝安装以及其他账号数据库/WAL 备份。测试指定本地更新源，不查询或安装真实发布资产。

安装程序按相同 AppId 升级，只覆盖程序和公共种子库。完成后验证旧草稿、提交代码、身份、模拟赛和经验值仍在；发布前准备 `SHA256SUMS.txt`、`BUILD-INFO.json` 与文件清单，并核对下载资产和对应源码。构建工具不会覆盖已有 staging；重复构建使用新的空目录。

## 发布同步检查

每次发布都必须把实际源码和文档作为同一版本交付，不能只上传发布包。

1. 统一 `VERSION`、`frontend/package.json`、`frontend/package-lock.json` 和 `desktop/browser_extension/manifest.json` 的版本；核对安装程序与扩展构建使用该版本。
2. 同步 `README.md`、`README.en.md`、相关使用/架构说明、`docs/index.html` 和 `docs/releases/<版本>.md`。逐项核对真实功能、题库统计、下载文件名、源码标签、升级方式和已知限制。源码领先正式版时明确标注源码版本及“尚未正式发布”，保留已发布版本的下载链接；正式发布时再一起更新正式版入口。
3. 运行相关后端、前端、浏览器与共享服务检查；将发布源码、公共题库文本源和文档一起提交并推送到 GitHub。检查提交内容不含个人状态、凭据、Cookie、恢复备份或本机绝对路径。
4. 从确认过的提交构建安装版、便携版和浏览器扩展，生成 `RELEASE-MANIFEST.json`、`SHA256SUMS.txt` 与记录准确提交的 `BUILD-INFO.json`。根据上一正式版文件清单生成增量包，并在隔离状态完成新安装、升级、个人数据保留及增量替换验证。构建后源码若有改动，重新提交并构建受影响资产。
5. 发布标签指向构建提交，发布说明与 README 描述同一版本；核对 GitHub 上的源码、版本号、下载链接和资产哈希后完成发布。不要移动已有正式版标签或把尚未发布的版本写成最新正式版。
6. 更新指定本地项目目录的当前记录，写清源码提交、GitHub 同步结果、已发布/未发布状态、检查结果和实际启动入口。仅更新源码或文档时，明确说明本次未重新打包。

## 1.0.19 内容与加载检查

`python scripts/measure_loading.py --output build/loading.json` 使用临时离线状态记录首次启动、重启、题库、工作台、题面和题解耗时，不读取个人数据。`node frontend/tests/loading.mjs` 须在 frontend 目录改用 `node tests/loading.mjs`，检查在途请求合并及写后刷新；`node tests/latest-editorials.mjs` 实际渲染本批 71 题的公式和配图。后端覆盖重启复用、导入/WAL 失效、单题知识增量、并发、令牌替换与讲义关系批量读取。

10 月 16 日为 134 场已有默认题解的比赛补写 727 份详细版，原有 82 份保留。1.1.0 使用的公共源与 SQLite 为 5795 题、2215 份题面、960 份默认题解、960 份详细题解、376 篇讲义；应用可见性策略后为 5622 可见、173 隐藏。XCPC 与蓝桥杯累计完成 127 道不同题目、含镜像 151 组两版题解，2026 四川省赛和秦皇岛邀请赛的已筛选范围均已补齐，蓝桥杯 2026 初赛 B 组八题已全部补齐，国赛 B 组 A–I 九题已补双版题解（J 题等待题面更正），武汉邀请赛的已筛选六题已补齐；当前待补范围见[内容记录](editorial-content-20261016.md)。统计核对要区分库存、可见题目与有题面数量；必须重新从当前公共源构建，不能复用尚未包含这批内容的旧 1.0.20 包。

## 1.0.20 同步与性能检查

同步回归必须使用本机隔离账号服务及临时个人数据库，覆盖登录恢复失败不进入空工作区、两设备接管、慢上传期间心跳撤销、旧会话迟到写入拒绝、三方修改与删除、草稿冲突留存、XP/成就重放幂等、公开账号绑定隔离、偏好迁移和另一电脑缺公共题目 ID 的继续练习。不得用生产用户验证登录或向真实原站提交测试代码。

```powershell
$env:TB_OFFLINE = "1"
python -m unittest discover -s backend -p "test_account_sync.py"
python -m unittest discover -s backend -p "test_sync_independent_review.py"
python -m unittest discover -s backend -p "test_account_preferences.py"
cd server/leaderboard
$env:NODE_OPTIONS = "--max-old-space-size=64"
npm test
# 仅对已显式配置的可丢弃本机 MySQL 实例运行；配置变量见 tests/mysql.test.mjs
npm run test:mysql
```

本轮在隔离 MySQL 8.0.27、回环随机端口与 Node 64 MiB 堆限制下通过 22 项真实数据库测试，包含大压缩源码快照、005 迁移重入、并发 CAS、单会话与零题登录榜。实例正常 shutdown，未操作系统 MySQL 服务或用户数据库。共享服务另以 SQLite 测试适配器验证高密度 JSON 在解析前拒绝、20 MiB 超限请求、快照限并发和心跳可用；不能用 SQLite 测试替代真实 MySQL 协议验证。

前端新增 `node tests/account-sync-status.mjs`、`node tests/background-statement.mjs`、`node tests/training-overview.mjs`，分别验证待同步/失效、题面后台读取和 XP/AC 成就展示，运行目录为 `frontend/`。其他既有发布检查继续执行，最终通过情况以构建报告为准。

体积测量比较同一题库的 UTF-8 完整与紧凑响应（约 12.68 → 7.98 MB）和构建入口 JS（约 1.419 → 0.863 MB，编辑器约 560 KB 按需加载）；耗时测量须记录机器、冷/热缓存与历史条数。重点覆盖有大量官方回执的成长统计、并发题面失败、锁等待和账号切换后的后台服务释放，避免只测空账号。

本机进程样本约 70% 的私有内存属于 WebView。当前保留 Python 本机后端与 Node.js 共享服务，优化重复数据、缓存、锁和任务生命周期；换为 Go 不能直接消除 WebView 占用，尚未实施语言迁移。

## 1.0.20 服务先行迁移

生产现有数据卷必须保留，先在线备份 MySQL，再执行幂等的 `mysql/005_account_state.sql` 与运行时替换，检查健康响应含 `accountStateProtocol: 1` 后再安装或分发客户端。部署脚本只收拢旧会话，不改身份、历史 AC 或角色；已有云端状态后旧协议客户端会收到 426 升级提示。详见[完整步骤与回滚](../server/leaderboard/README.md#1020-同步上线)。

发布包不含个人数据，但运行时账号同步会上传个人代码；不要沿用“只上传成绩摘要”的整体隐私描述。Cookie、翻译密钥、DPAPI 密文和机器设置仍不上传。数据库备份须按个人数据保护，首次合并前保留本机 SQLite 在线备份和冲突记录。

2026-10-16 已完成生产在线备份、原 MySQL 卷上的增量迁移及 API/Caddy 更新。公网健康检查确认 `version: 1.0.20`、`accountStateProtocol: 1`、`singleSession: true`；143 个身份、3 个账号、164106 条官方 AC 记录及指纹、4 笔共 400 XP 的奖励前后一致。每个账号最多保留一个会话。日常客户端已升级至 1.0.20：安装器退出码为 0，4526 个文件符合包清单，首次启动前核对 8 个原数据库的全部表与模式不变，3 个快捷方式不变。正式下载链接仍指向 v1.0.18，尚未推送源码或公开发布资产。公开发布前仍须完成上方发布同步检查。

## 1.1.0 发布检查

源码、安装器默认版本、前端和浏览器扩展均使用 1.1.0。发布包重新构建当前 960 份详细题解的公共库；以前的 1.0.20 包不具备这次全部内容。`006_public_progress.sql` 已于 2026-10-16 13:51（北京时间）在原 MySQL 上完成生产部署；公网 HTTPS 确认服务 1.1.0、账号同步协议 1、单设备会话及公开成长协议 1。原表、卷、compose 覆盖配置及账号快照保留，在线备份已在受控位置核验。前后 143 个身份、3 个账号、164107 条官方 AC 及指纹、4 笔共 400 XP 奖励和 3 个会话完全一致；账号快照与登录日期各 1 条，同账号多会话为 0。

成就回归覆盖旧 XP 不追扣、退休目标不再发奖、称号零 XP 一次领取、1000 天旧记录兼容两年目标、自动佩戴最高两枚、双机已读并集与公开摘要缓存失效。排行榜另测旧版缺资料、零 AC 登录、已认证摘要更新、拒绝非法字段、真实 MySQL JOIN，以及关闭后定时器不再访问 SQLite。测试始终使用临时个人库与本机服务。

```powershell
$env:TB_OFFLINE = "1"
$env:PYTHONPATH = "backend;backend/common;desktop"
python -m unittest test_achievement_rewards test_account_preferences test_leaderboard_lifecycle
python scripts/check.py
cd frontend
npm run build
node tests/progress-v110.mjs
node tests/ranking-public-progress.mjs
```

已完成源码全套 461 项检查，后续增量升级与构建元数据的 17 项定向检查也全部通过。前端构建、12 项界面检查、训练概览、隐藏/恢复轮询及 3 种偏好同步场景通过；覆盖顶部直接概览、成就 hover/focus 独立已读、称号样式、账号/翻译入口、比赛分页与直接重现赛。常规界面数据和目标轮询在隐藏窗口暂停，恢复可见立即读取状态与待处理结果；后台会话心跳、上传、任务和软件自动更新继续运行。无变化工作区保持对象引用，提交或同步后的更新仍会刷新。

数学标题、Markdown 和讲义阅读器按需加载。当前构建主入口 871.12 → 423.61 KB，首屏另有 8.90 KB JSX runtime，编辑器约 560 KB 按需读取；比较时须计算所有首屏块，不能只报入口当总下载量。WebView Normal/Low 与取消请求头订阅的三轮隔离测量见[发布说明](releases/1.1.0.md#响应与加载)。它验证最小化时草稿和计时器继续执行，不使用 Suspend；真实 Windows WebView 的 7 项官方流程和 8 项静默流程 fixture 也已通过，未向真实原站提交。v1.1.0 的全新安装、完整升级、更新器重启和增量包验证均已通过。

旧版增量更新器不接受根目录新增 `BUILD-INFO.json` 和 `SOURCE-MANIFEST.json`。构建包在 `resources/` 放置两份权威副本；面向旧客户端的增量清单省略这两个根路径，经原有资源白名单交付。冻结程序通用启动入口跳过更新助手，在普通启动及隔离发布探针前校验版本、40 位提交号与来源清单 SHA-256，再原子恢复根目录信息；大小有界、拒绝符号链接及 junction、失败回滚并留日志。新版白名单仅增加这两个根文件供后续升级使用。`test_update_patch` 与 `test_release_metadata` 的 17 项定向检查覆盖旧版路径兼容、幂等、非法资源拒绝、回滚和个人状态字节/修改时间不变；正式旧版 EXE 的完整增量升级还须由构建探针验证。

2026-10-18 发布切换已完成：两份 README、主页、usage/accounts/architecture/development 与本版说明均显示 v1.1.0 为当前正式版。`v1.1.0` 标签和 `BUILD-INFO.json` 指向 `474d347b34fbd3815072d78ceed41c6abec18f72`；GitHub 发布页的 9 个资产名称、大小和 SHA-256 与本地清单逐项一致。下一版仍须在构建提交、标签和发布页之间执行同样的对应检查。
