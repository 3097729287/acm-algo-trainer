# 开发、验证与构建

## 1.3.4 构建与验证

1.3.4 已正式发布。构建与标签为 `61ebe19e213d4daa113482332e5a9239caaf1d59` / `v1.3.4`，发布源码来自 `release/1.3.4` 的独立干净工作副本；后续 `a5f8e19` 仅适配测试断言。已发布运行代码不含后续背包 DP 实验室改动，保留原题单。[发布与下载](releases/1.3.4.md)。

575 项后端检查、前端构建及交互回归、四站公开赛程、6000 题雷达、原生窗口、C++/Python、新装/卸载、1.3.3 升级与实际增量器全部通过。[GitHub 检查](https://github.com/3097729287/acm-algo-trainer/actions/runs/39747568470) 的前端、后端与共享服务均通过。两版独立安装和数据隔离通过，本机 8 个个人库在线备份及升级前后表和结构核对通过。未进行真实原站代码提交，共享服务与账号协议不变。

## 1.3.3 构建与验证

1.3.3 已正式发布，构建与标签提交为 `84fa8d5830f0ee79abbe4356447a900c6f3e62ca`。本次包含预置中文题面、统一知识点及掌握度 v3、完整赛事目录、重现赛选择、设置内各页指引与独立管理员安装包；另调整按钮、间距、圆角、图标、分页和视觉对齐。[最终验证与下载](releases/1.3.3.md)。

验证覆盖题量折减、父子知识点覆盖、别名筛选、分类保全、预置译文绑定与不可变内容、管理员角色及普通版接口拒绝；前端包含账号隔离、首次注册总览、各页目录、雷达到题库、工作台中文切换、四种训练、叶子选题和五窗口布局。所有测试使用隔离状态，不发送真实原站代码。完整后端、最终安装与增量结果在发布说明记录；共享服务协议和数据库不变。

普通包使用既有 `build/assemble/installer`；先完成其构建来源信息，再执行 `python scripts/build_release.py admin-assemble --stage <同一stage>` 与 `admin-installer`，后者使用相同的 `--inno`、`--webview2` 参数。管理员 EXE 为 `TB管理员版.exe`，Inno AppId、安装目录、快捷方式与普通版分开。两版分别验证新装/卸载、隔离状态及普通版拒绝管理接口，再发布同一源码提交的资产。管理员包不含预设密码或学习进度。

## 1.3.2 构建与验证

1.3.2 已正式发布，构建提交与标签为 `3107e20837b47021777f642b648a1aa47b238279` / `v1.3.2`。[GitHub CI](https://github.com/3097729287/acm-algo-trainer/actions/runs/39667115294) 的前端、后端与共享服务检查均通过。版本、双语 README、主页、使用说明、掌握度模型与架构说明随本次源码提交。`knowledge_mastery.py` 的纯函数与集成回归覆盖题库扩容无影响、样本不足、未知难度、独立性、失败、运行/CE 排除与别名去重。模拟赛回归包含全模式原站提交上下文与罚时、锁和正式回执关联。

完整后端 532 项、前端 build、主界面、真实隔离 API E2E、工作台、五窗口模拟赛、时长与目录、排名、同步状态和掌握度回归已通过。设置动画另核对恐龙边界折返、灯泡亮度范围、气球时长、不同建筑及视觉布局；检查发现并修复 tooltip 的 Esc 被页面全局快捷键提前捕获的问题。最终原生窗口、导出、安装/卸载、完整升级、更新助手及 1.3.0 / 1.3.1 两条实际增量均通过。8 个 GitHub 资产的字节与 SHA-256 已核对；本机 8 个 SQLite 数据库及 3 个普通快捷方式保持，分发文件逐一核验。[发布与校验](releases/1.3.2.md)。

前端新增目录选择、排序方向、掌握度合并及含义对应成就图标。`node tests/ui-v131.mjs` 扩展验证圆角裁剪、每题边框、目标移动、同步槽位、底部顺时针经验环、设置返回与提示，以及父知识点证据去重；`node tests/revision-flows.mjs` 验证时长和手动保留，`node tests/mock-layout.mjs` 在五种窗口检查选题浮层真实命中和切题草稿。发布检查使用新建 staging 与临时数据库，1.3.0 / 1.3.1 增量分别调用原版更新器，标签与构建信息须对应已推送提交。无共享服务变更。

## 1.3.1 构建与验证

1.3.1 已正式发布，固定构建提交 `7ab050ae0add7356a5f3b63d2b6a9e8f498b3a0c`。[发布记录](releases/1.3.1.md)。后端 525 项、前端回归、原生恢复、安装/卸载、完整升级、更新助手和两条实际增量均通过。本机 8 个数据库及快捷方式核对保留。[GitHub CI](https://github.com/3097729287/acm-algo-trainer/actions/runs/39650917032) 的前端与共享服务已通过；后端工作流汇总状态以链接为准。本机后端完整 525 项已通过。新增 `node tests/ui-v131.mjs` 和 `node tests/revision-flows.mjs` 覆盖搜索栏、筛选浮层、可修改快捷键、透明度、模拟赛四模式、账号立即显示和渲染错误恢复。`python desktop/tests/webview_resources_native.py --rounds 0` 在隔离原生窗口验证最小化、覆盖层及真实测试渲染进程退出后的草稿恢复。

后端偏好协议新增受限 `shortcuts` 映射，云端仍沿用私有偏好文档，无服务端 schema 变更。运行完整 `python scripts/check.py`、前端构建和相关回归；固定干净已推送提交后构建，标签与 BUILD-INFO 保持一致。发布前完成原生检查、管理员隔离、安装/卸载、完整升级与旧更新器实际应用增量，所有状态位于临时目录。

## 1.3.0 构建与验证

1.3.0 已正式发布，固定构建提交 `8922ffbc144402adf01b6367a9f68775e1461b77`。[交付与验证](releases/1.3.0.md) · [GitHub CI](https://github.com/3097729287/acm-algo-trainer/actions/runs/39622874758)。GitHub CI 的全部测试步骤成功；Windows runner 仍在收尾，工作流汇总状态以链接为准。随包双语言、管理员隔离、原生窗口、全新安装/卸载、完整升级、更新助手和 1.2.1 实际增量均通过；本机 8 个数据库已在线备份并验证表与 schema 保留。后续发布状态文档可领先构建提交，程序与标签身份保持不变。

新功能回归为 `python -m unittest discover -s backend -p test_v130.py`、`node tests/ui-v130.mjs` 和 `node tests/account-sync-status.mjs`；其余前后端回归继续执行。测试使用临时 SQLite 与合成回执，不向真实账号提交。

先运行 `python scripts/fetch_python_runtime.py <空目录>`，校验官方 CPython 3.13.16 的固定 SHA-256，再向 `scripts/build_release.py assemble` 传入 `--python-source <目录>`。运行时安装到 `_internal/python3`，本次 C++ 工具链不变，增量包显式包含新增 Python 字节与许可证。`--package-check` 同时验证随包 C++ 与 Python 样例。

发布 1.3.0 前完成源代码、双语 README、VERSION、扩展清单、主页、用法与本说明的同步，先推送再构建。全新安装、旧版升级和增量实际应用必须在隔离目录验证。管理员须核对独立路径、普通版接口拒绝、等级/段位可编辑和勋章授权不修改用户记录。共享服务保持 1.2.1，无服务端表迁移。


## 1.2.1 发布验证

1.2.1 已正式发布，构建提交 `173b23094256fc52d727c01bc4aeec69d87b9486`。[完整验证记录](releases/1.2.1.md) · [通过的 GitHub CI](https://github.com/3097729287/acm-algo-trainer/actions/runs/39555071361)。后端 512 项、共享服务 SQLite/MySQL 各 33 项、前端、原生安装和两条增量路径均已通过。除既有构建和安装检查外，执行 `node tests/ui-redesign.mjs` 与 `node tests/ui-social.mjs`，覆盖设置返回位置、真实引导流程、四种风格、0% 透明度、抽屉、深层文件夹、底栏和今日爱心。后端检查包含透明度保存后重启读取，以及 2199/2200 的段位边界。桌面原生检查使用新的两级设置入口。

本次只更改门槛，不迁移个人提交和经验。服务升级复用备份、指纹核对与同库切换，验证 todayLikes 按北京时间归零、累计总数保留。GitHub 源码须先推送，资产从固定干净提交构建，再验证标签与来源清单。服务运行包从干净检出准备；发布前确认 shell 文件为 LF，禁止直接复制含 CRLF 的工作目录脚本。以下为旧版验证记录。

## 1.2.0 构建、本机交付与服务部署

v1.2.0 已完成构建、本机替换和共享服务部署；GitHub 公开资产尚未发布，公开下载继续指向 v1.1.5。构建源码为 `54798667ac8dee3d4006ce43cd56f8e573da26bf`，本机 `VERSION`、构建信息及服务器版本已核对。[本版说明](releases/1.2.0.md)分别记录功能、隔离安装、本机替换与服务核验。

本轮公共种子经 `scripts/check.py` 核对为 5819 题、2422 份题面、1302 份默认题解、1302 份详细题解和 376 篇讲义。公共文本源、重建后的 SQLite 与构建信息须一致；不混入个人工作库。按 2026-10-22 用户更新，后续新增题解的题目难度小于等于 2200（含 2200），未知先核验；原有全部题解、图片和记录继续参与正常打包与迁移。[题解政策](editorial-policy.md)。

已完成的功能验证基线为后端 511 项、共享服务 SQLite/API/HTTP 33 项与隔离 MySQL 33 项；前端 build、app、workbench、catalog-activity、workspace-decorations、issues、ui-social 及真实隔离 API E2E 通过。新增检查覆盖列表位置、静止鼠标滚动、透明表头、爱心失败回滚与每日唯一、100 条以上全部已读、公开活动不含已读状态、大通知响应、头像范围、固定段位色和二级设置布局。测试不使用生产账号试交。

版本文件、双语 README、主页和公共种子已随构建源码提交并推送，`BUILD-INFO.json`、来源清单和资产 SHA-256 对应同一来源。实际验证已通过：原生 WebView 全屏与 JSON 导出、干净 PATH 下四站本地样例、全新安装/卸载、1.1.5 → 1.2.0 安装升级、重启设置与缓存保留、更新助手正常关窗重启，以及旧 1.1.5 增量器应用后保留身份、草稿和训练。本机更新前在线备份，更新后个人表与 schema 一致、程序文件 SHA-256 一致，快捷方式保留，日常工作区保持关闭。

服务已先备份原 MySQL，再在原数据卷应用 `008_social.sql` 并部署 1.2.0 API。HTTPS 确认 `socialProtocol: 1`；原 15 表指纹一致，仅新增两个互动表，配置和数据卷保留，SQL 备份通过 gzip 与 SHA-256 校验。状态协议和公开成长协议保持 1。公开文档仅记结果，生产数据、备份和统计留在私有运维记录。

7 组额外 UI 套件已通过。测试提交 `a2cb9170297e314b8c2f1d5beb9875ed2a601d74` 仅修正工作台字号输入的渲染等待，本地复跑通过，运行时字节及构建身份保持 `5479866`。远端 CI 结果单独记录，以工作流结果为准。公开资产与正式下载入口仍保持 v1.1.5，公开发布时再核对标签和资产。

## 1.1.5 发布检查

1.1.5 已发布。必须在英文 Windows CI 验证中文/空格工作目录，并保留工具链干净 PATH、DLL 搜索路径恢复及 Job 限制。前端与后端完整工作流验证现行 UI、四站实际语言控件和被拦截的原生提交；不向用户账号测试提交。安装与 v1.1.4 增量须在隔离目录实际应用。

## 1.1.4 发布检查

必须在移除开发机 MSYS/GCC PATH、含中文和空格的临时目录验证随包编译器，并核对宿主 DLL 搜索目录恢复。`--package-check` 对四站实际公共题面与参考代码运行样例，不向原站提交。检查 CE/ERROR 诊断、不同输入不复用结果，以及编译缓存随代码与编译器变化失效；保留 Job 时间、内存、输出及子进程限制。

运行完整 `python scripts/check.py`、前端 build 和 app、workspace-decorations、workbench、statement-format、replay-layout、rankings、webview-loading、issues、compilers、external-browser、official-sites 测试。回归覆盖 JSON 导出只读与敏感表排除、首次注册指引及重看、已领取任务提示清除、真实语言控件、样例原换行和公式、25–100% 不透明度及大小屏布局。

发布须固定已推送的干净提交；从该提交构建种子、程序、安装器、v1.1.3 增量与来源清单。全新安装、升级、原生窗口、更新助手与旧更新器实际应用必须通过。共享服务不升级，继续为 1.1.2 / 协议 1。另行续写内容与个人数据库不混入公共构建。


此节记录 1.2.0 当时的交付状态；当前正式下载与本机版本为 [1.3.4](releases/1.3.4.md)，共享服务为 1.2.1，账号与公开成长协议仍为 1。

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

API 的可选参数见 `python backend/backend.py --help`。历史 [v1.1.0](releases/1.1.0.md) 的源码标签、`BUILD-INFO.json` 与已发布资产均指向 `474d347b34fbd3815072d78ceed41c6abec18f72`；该版 `005` 账号同步与 `006` 公开成长迁移已完成。当前公开下载为 v1.3.4；本次构建和交付见本页首节，以下版本章节为历史记录。

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

## 本轮检查

1.3.4 已正式发布。新增 `test_reviews.py` 覆盖次日时区、逐轮草稿、语言与重启、独立性、失败反馈、简单题豁免、预算和回执关联。`test_catalog_identity.py` 核对原题去重且同名异题保留；`test_contest_calendar.py` 覆盖四站过滤、时区、非阻塞缓存与离线。`test_foundation_extraction.py` 确认旧内容不变与新增正文、图片和关联一致。

前端 `radar-performance.mjs` 使用 6000 题、500 条证据测量首屏和连续二级切换；`ui-v131.mjs` 同时验证首次题解宽度、直接下一题和保存失败屏障、比赛日历与用户/管理员入口。工作台、模拟赛和引导回归同时通过；后续算法实验室在独立开发分支验证。每个依赖 Vite 预构建缓存的浏览器回归顺序运行，避免改版本时多个开发服务器同时重写缓存。

算法实验室已接入开发主应用，仅保留背包 DP；课程与跟做检查已完成。另一会话的基础补齐已完成，全库逐篇精修和阅读复核尚未完成，联合发布继续等待；不能以 task_complete 或最终答复替代需求完成核对。`frontend/npm run build:lab` 仍生成内联 JS/CSS 的 HTML 和可分享 ZIP；`npm run test:lab` 检验核心模型、五题的原题样例与独立枚举、实际 C++17，以及解压后断网的 `file://` 应用。`ui-v131.mjs` 检验主应用单课入口、固定翻页及跟做进入真实工作台流程。入口为 `frontend/standalone/`，共享课程在 `src/pages/algorithm-lab/`；独立输出到 `TB/版本/算法实验室体验版`。详见[教学创作流程](algorithm-lab-authoring.md)。

## 发布同步检查

每次发布都必须把实际源码和文档作为同一版本交付，不能只上传发布包。

1. 统一 `VERSION`、`frontend/package.json`、`frontend/package-lock.json` 和 `desktop/browser_extension/manifest.json` 的版本；核对安装程序与扩展构建使用该版本。
2. 同步 `README.md`、`README.en.md`、相关使用/架构说明、`docs/index.html` 和 `docs/releases/<版本>.md`。逐项核对真实功能、题库统计、下载文件名、源码标签、升级方式和已知限制。源码领先正式版时明确标注源码版本及“尚未正式发布”，保留已发布版本的下载链接；正式发布时再一起更新正式版入口。
3. 运行相关后端、前端、浏览器与共享服务检查；将发布源码、公共题库文本源和文档一起提交并推送到 GitHub。检查提交内容不含个人状态、凭据、Cookie、恢复备份或本机绝对路径。
4. 从确认过的提交构建安装版、便携版，生成 `RELEASE-MANIFEST.json`、`SHA256SUMS.txt` 与记录准确提交的 `BUILD-INFO.json`。现行可见浏览器入口不分发扩展包，保留扩展源码仅供历史 fixture。根据上一正式版文件清单生成增量包，并在隔离状态完成新安装、升级、个人数据保留及增量替换验证。构建后源码若有改动，重新提交并构建受影响资产。
5. 发布标签指向构建提交，发布说明与 README 描述同一版本；核对 GitHub 上的源码、版本号、下载链接和资产哈希后完成发布。不要移动已有正式版标签或把尚未发布的版本写成最新正式版。
6. 更新指定本地项目目录的当前记录，写清源码提交、GitHub 同步结果、已发布/未发布状态、检查结果和实际启动入口。仅更新源码或文档时，明确说明本次未重新打包。

## 1.0.19 内容与加载检查

`python scripts/measure_loading.py --output build/loading.json` 使用临时离线状态记录首次启动、重启、题库、工作台、题面和题解耗时，不读取个人数据。`node frontend/tests/loading.mjs` 须在 frontend 目录改用 `node tests/loading.mjs`，检查在途请求合并及写后刷新；`node tests/latest-editorials.mjs` 实际渲染本批 71 题的公式和配图。后端覆盖重启复用、导入/WAL 失效、单题知识增量、并发、令牌替换与讲义关系批量读取。

10 月 16 日为 134 场已有默认题解的比赛补写 727 份详细版，原有 82 份保留。1.1.0 发布时公共库为 5795 题、2215 份题面、929 份默认题解、929 份详细题解和 376 篇讲义；1.1.1 与当前 1.1.3 固定发布包为 960 组双版。应用可见性策略后为 5622 可见、173 隐藏。后续源码与本机题库追加见[内容记录](editorial-content-20261016.md)。统计核对要区分固定发布包、当前源码库存、可见题目与有题面数量；新发布必须从对应源码重建公共库。

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

2026-10-16 的 1.0.20 服务先行迁移已完成在线备份、原 MySQL 卷增量升级及 API/Caddy 更新。健康检查确认账号协议 1 与单设备会话；账号、官方 AC、奖励、快照和会话前后核对一致。隔离安装与本机替换核对程序文件及个人数据库保留；具体生产统计、备份和本机入口保留在私有记录。后续版本的独立构建和交付状态见本页首节；本段仅记录当时的服务迁移。

## 1.1.0 发布检查

1.1.0 当时的源码、安装器默认版本、前端和浏览器扩展均使用 1.1.0，公共库包含 929 份详细题解；以前的 1.0.20 包不具备该批全部内容。`006_public_progress.sql` 于 2026-10-16 在原 MySQL 完成生产部署，确认账号同步协议 1、单设备会话及公开成长协议 1。原表、卷、compose 配置及账号快照保留，在线备份已在受控位置核验；迁移前后账号、官方 AC、奖励、快照和会话一致，逐项统计保留在私有运维记录。

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

2026-10-19 XCPC 与蓝桥杯收尾快照：当时源码与本机题库含 2398 份题面、1262 份默认题解和 1262 份详细题解。XCPC 与蓝桥杯本任务累计新增 453 组双版，覆盖 408 道不同题目；已核定且低于 2200 分的范围已补齐，遗漏 0；907 个未评级 XCPC 条目及 1 个蓝桥杯条目待核验，已有题解全部保留。[逐题范围与检查](editorial-content-20261016.md)。

2026-10-19 新比赛内容追加已纳入 v1.2.0 实际构建公共种子：5819 题、2422 份题面、1302 组双版题解。29 道新增题的独立验证及归档副本复跑通过；16 份整场文档格式检查、58 次 Markdown 代码一致性检查、104 篇实际阅读器渲染、1991 个公式及 13 项导入检查通过。原 1262 组及个人数据全部保留。新条目对应已有题解另有 11 组；旧发布包固定库存不回写。[范围、备份与证据](recent-contest-editorials-20261019.md)。
