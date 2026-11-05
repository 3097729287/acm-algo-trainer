# ToBe Rust 重构进度

2026-11-06，内部测试编号 `2.0.0-alpha.3`。**按用户最新要求，Tauri + Rust 仅在本地测试；正式更新继续采用原有 React + Python 架构及既有打包流程。架构切换须等待用户新的明确指示。** 正式 `VERSION` 仍为 1.6.1，本目录不能替换正式安装。

源码：`E:\项目\ToBe\开发\tb-tauri-rust`；分支：`refactor/tauri-rust-20261105`；基于前端提交 `9d5fcd83`，已纳入设置碎裂修订 `1e9861e2` 以及日历任务、杯子触地与连接恢复修订 `0f6524c7`。正式源码在 `开发/tb-learning-summary-20261105` 继续独立更新，后续修订仍需逐项迁入本测试分支；不复制正在修改中的文件。

## 已实现

- React 与原有产品页面保留。公共 `request(path, body, token)` 在 Tauri 内走 IPC，浏览器开发继续使用原 HTTP。IPC 失败不回退 HTTP、不重放写请求。
- 版本化请求、请求编号、查询参数、账号归属、会话令牌和统一错误，定义于 `api/ipc.schema.json`。
- 从原后端 AST 生成 **134 个方法与路径组合**的迁移清单及个人 SQLite 表结构；`python scripts/native_contract.py --check` 检查遗漏。
- Rust 核心库与 Tauri 2 宿主已构建；运行时没有 Python 后端、Python sidecar 或本机 HTTP API 进程。
- Rust 只读访问现有 13,417 道题、题面、讲义、题单、资源和 Wiki；分页查询避免一次局部读取载入全库。
- 新增只读公共目录索引，按旧实现的真实去重、别名及展示规则生成：13,403 条展示记录、14,119 个历史／远程别名、480 篇讲义、635 个公开题单。13,417 是原始题库行数，展示数差异来自既有规则，未删除原始题目。
- 索引由 `scripts/build_native_catalog.py` 在构建时编译公共内容。完整目录、紧凑目录、题面补丁和资源按需解压；已有资源复用原库，额外内嵌公共资源按 SHA-256 去重保存并在读取时核验。运行程序不调用 Python，也不访问私有账号缓存。
- 原有偏好读取、初始代码模板读取／保存／选择、自建模板读取／保存、Wiki 和普通草稿保存已接入，保留版本冲突、删除墓碑和原语言键。
- 接入原 React 的题库／普通训练工作区、题目、题解／关联讲义、阅读队列、公开题单、提交记录筛选及历史代码读取。新增偏好保存、时长心跳去重和有效学习区间合并；前台时长不冒充掌握证据。
- 新增本地学习规划：推荐起点、共享周预算、1–5 条主线、待采纳方案、显式采纳、调整时间、更换主线、推迟、换题、困难诊断、阅读完成、原理检查、模板实现证据、跨周归档和停滞提示。已读、历史删除墓碑及版本冲突继续保留；旧计划按当时数据查看。
- 阅读只推进阅读阶段，正确回答只推进原理阶段；模板通过按实际辅助标记区分跟练和独立实现。正式解题、延迟复习及比赛证据的完整推导仍待迁移，相关历史存在时先拒绝规划刷新／变更，不把其当作空记录。
- 规划、归档和训练辅助标记在同一 SQLite 保存点中提交，后续保存失败全部回滚；重复刷新不更换版本。规划读取已有紧凑目录，避免加载完整题面投影。
- 任务接续提示放在工作区上方的紧凑行，修复原先作为横排子项占掉一列、挤窄任务主内容的问题；不增加新的提示文案。
- 账号接口只提供隔离验证环境的令牌，`authenticated=false`，不表示真实账号已迁移。
- SQLite 在线备份形成新副本，包含已提交 WAL、未知表和历史记录；校验副本完整性与逻辑指纹，拒绝覆盖已有目标。源库不执行模式变更，公共库不覆盖个人库。缺少必要字段的旧模式明确阻止迁移。

实时迁移状态来自 Rust `api/capabilities`：原有接口接线 **30 / 134**，另有 7 个新诊断／题库读取接口。`partial` 标识只完成部分范围的接口，账号引导不计入已迁移业务接口。接线数量不代表完整功能验收。

当前工作区支持普通本地训练。有正式提交事实、活动目标、复习状态或任何比赛历史时，相关工作区和训练操作先返回 `MIGRATION_PENDING`，不隐藏记录，也不在拒绝前修改训练。私人题面目录叠加、比赛／复习草稿上下文及未迁移的学习写入同样明确拒绝。原站远程图片／PDF 下载尚未接入，缺少缓存时返回资源错误，不伪造内容。

从诊断页点击“打开本地测试工作区”可进入原 React。该入口只使用显式本地测试身份和隔离状态，不代表注册账号登录，也不授予共享服务的经验、排名或库存。

`learning-summary/refresh` 和规划写入目前支持没有正式提交、复习调度、比赛、活动目标和私人题目事实的本地测试状态。含这些未迁移事实时返回 `MIGRATION_PENDING` 并保留原数据；正在比赛时调整规划返回冲突。综合检验试卷的启动、正式判题及完整能力模型仍未接入。独立本地导航不再等待尚未迁移的成长接口，浏览器正式入口保持原有逻辑。

## 验证

- 49 项 Rust 检查：中文与空草稿、UTF-8 大小、账号与令牌隔离、模板冲突／语言／墓碑、异常旧记录、已提交／未提交 WAL、未知表、迁移目标竞争、拒绝覆盖、时长合并／跨日／去重、偏好合并、学习 CAS、公共资源完整性以及规划阶段与异常记录保护。
- 19 项与旧 Python 实现的真实对照：初始代码、自建模板、Wiki 目录／正文、语言选择及删除后的目录。使用临时状态，不使用个人数据。
- 第二组 52 项旧实现对照及边界场景覆盖完整／紧凑目录、普通训练、偏好、时长、历史、提交分页／搜索／别名、题面资源及公开题单；另外验证比赛历史、私有目录和拒绝写入的 3 项迁移边界。结果记录在 `.backups/native-phase2-parity.json`。
- 第三组 52 项学习规划对照及边界场景覆盖全部 22 个专题的共享预算、候选顺序、阅读／原理／模板阶段、更换主线、历史、跨周、方案与错误处理；额外 3 项检查验证保存失败时回滚归档和辅助标记，以及不误删正式解题证据。结果在 `.backups/native-learning-parity.json`。
- 原生 Tauri/WebView2 实测：React 加载、真实 IPC、13,417 道题总数、真实题面；原 React 的代码保存和刷新恢复，以及“安排学习 → 阅读完成 → 答错／答对原理检查 → 取消时间修改 → 更换主线 → 查看旧计划 → 刷新恢复”。保留宽窄窗口截图和页面异常检查。
- React 正式构建与 IPC 序列化／错误／账号切换／重复读取合并检查。

证据：开发工作区 `.backups/native-parity.json`、`.backups/native-phase2-parity.json`、`.backups/native-learning-parity.json`、`.backups/native-tests-phase3.log`、`.backups/native-window/result.json` 及截图；独立打包运行证据在 `.backups/native-window-packaged`。最终检查结果以本轮本地测试记录为准。

## 剩余工作

1. 私有题目目录叠加、导入、动态更新与远程资源下载。
2. 训练、复习、比赛、原站回执和完整提交历史。
3. 学习主线、周计划、掌握证据与历史计划的逐项等价迁移。
4. 账号、DPAPI 凭据、离线恢复、分块同步和冲突合并。
5. 能力、经验、每日任务、成就与库存授权；不用客户端生成结果代替可信事实。
6. 有限资源的本地运行器、C++／Python 工具链、原站浏览器及原生窗口生命周期。
7. 排行榜、社交、贴纸和对战协议适配，更新、备份、安装与升级恢复。
8. 相同题库、工具链、账号操作链下的速度、全部进程内存、安装体积与升级临时空间对比。

正式更新继续使用原架构；本地测试不触发正式更新、部署、数据入口切换或发布。云端保持原协议，未修改线上数据。

## 性能口径

完整功能兼容后，启动和常用操作应更快，硬盘与内存占用应更小。当前主 EXE 约 16 MiB，另含 WebView2Loader、现有题库、公共目录索引及 Wiki，**不等于完整新版本安装体积**。实际字节数见测试包 `BUILD-INFO.json`。

原生测试记录启动、IPC P50／P95 和宿主／WebView 进程内存。诊断页面工作量小于正式 ToBe，不能直接比较为性能提升比例；完整功能对比通过前不宣称整体资源目标达标。

## 开发与运行

Rust／Cargo 缓存位于 `E:\项目\ToBe\公共工具\Rust`，未修改全局 PATH。系统 MSVC 安装被自动审批拦截后，已用便携 Rust GNU 和现有 MinGW 完成原生构建；使用本机 WebView2。

```powershell
cd E:\项目\ToBe\开发\tb-tauri-rust
python scripts/native_contract.py --check
python scripts/build_native_catalog.py
powershell -NoProfile -File scripts/native.ps1 -Action test
node frontend/tests/native-transport.mjs
python scripts/native_parity.py
python scripts/native_phase2_parity.py
python scripts/native_learning_parity.py
cd frontend
npm run build
cd ..
powershell -NoProfile -File scripts/native.ps1 -Action desktop
node frontend/tests/native-window.mjs
```

`native.ps1 -Action dev` 运行已构建前端的开发宿主，不启动 Python。直接运行源码编译的 EXE 时，将 `TB_NATIVE_SOURCE_ROOT` 设为源码根目录；打包候选默认使用 EXE 同目录资源。

`scripts/package_native_candidate.ps1` 默认生成 `E:\项目\ToBe\临时验证\Rust本地测试\2.0.0-alpha.3`，逐文件校验 SHA-256，附构建信息；已有目标拒绝覆盖。测试包的数据库和 WebView 配置位于自身 `state/native-migration-sandbox`，不打开正式账号或浏览器配置，不替换正常快捷方式。`-VerifyOnly` 只核验已生成的文件。

迁移工具：`target/debug/tobe-core.exe migrate SOURCE DESTINATION`，只生成新副本。完整业务验收尚未完成，不能据此将副本切为正式数据入口。
