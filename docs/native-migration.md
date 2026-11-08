# ToBe Rust 迁移进度

2026-11-09，内部验证编号 `2.0.0-alpha.3`。当前源码接通 **42/136** 项原有接口，**135 项 Rust 自动检查通过**，另有 1 项显式联网检查默认跳过。最新一批实现真实目标训练，新增三个接口；完整功能、正式账号和发行验收仍在继续。

工作区 `开发/tb-tauri-complete-20261108`，分支 `feature/tauri-complete-20261108`。已合入共享草稿范围修复 `c852e411` / `e1704a89`、冻结比赛历史、公开资源接线和目标训练，并同步冻结的 1.6.10 源码 `6ddfbdf7`（本分支合并 `7b282da2`）。当前运行输入、瘦 seed、原生索引、新独立包和实际窗口证据以 `docs/verification/native-source1610-20261109.json` 为准；正式用户版仍由主线验收和发布。

## 源码、数据和独立包

| 对象 | 当前事实 |
| --- | --- |
| 当前源码和新编译二进制 | 42/136 项接线，135 项 Rust 检查；接口的 `partial` 表示仅完成部分业务范围。 |
| 当前公开 seed / 派生索引 | 冻结 1.6.10 瘦 seed 441,696,256 字节、SHA-256 `567286a56e7e84f7a26344056496e980a82206db9fd7e6654e78f3a8d1df9290`；13,480 个原始身份、13,466 条展示、14,182 个别名、480 篇讲义及 635 个题单。新索引 92,934,144 字节，包含全部 13,466 份复习知识投影。 |
| 最新已制作的独立包 | `临时验证/Rust本地测试/1.6.10同步-20261109/ToBe-Rust.exe`，实际构建来源 `ff0115755b99c419832a7df3da155bfec5b13a94`，**42 项接口 / 135 项检查**；原有 36/92 历史包保留。 |
| 上述独立包体积 | 10 个已逐文件校验的运行文件，共 584,323,337 字节；包括仅含 endpoint 的公共资源配置。外部 C++ / Python 运行工具未打入包。 |
| 正式用户版 | 继续由主线发布原架构；本分支没有启动、替换或升级正常安装，也没有切换真实个人数据入口。 |

本轮只制作一次有效瘦库独立包，完整包也通过真实窗口回归。源码合入、数据、测试二进制与包分别记录；不把这份部分功能包当作完整 Rust 版或正式发行。

## 当前已实现的范围

- 版本化 Tauri IPC、请求编号、令牌、账号归属与统一错误；保留原 React 页面，IPC 失败不转入旧 HTTP 后端，也不重放写请求。运行时没有 Python 后端或 sidecar。
- 只读公共目录、题面、普通／详细题解、讲义、Wiki、公开题单和原身份别名。公共目录在构建时编译，运行时按需解压；Python 只作为构建工具或独立测试 oracle。
- 普通训练、真实正式提交历史的读取与首次通过日期、连续天数、提交筛选、历史代码、独立草稿、模板、默认代码、自建题单及跨日时长。自建题单保留 UUID、删除墓碑、原添加时间和一次真实创建行为。
- 复习按实际官方回执调度，保留次日 WA 触发、保守能力下界、间隔、失败和辅助标记、预算、取消恢复、绑定回执与一次奖励账本。普通和复习草稿分别保存；样例通过不完成正式复习，也不生成官方 AC。
- 已结束／已取消比赛的冻结历史、真实计分、缺题标记、考场草稿只读及取消考场草稿恢复。删除后的已完成重现赛继续保留原展示资格证据。只清理有完整证明、无任何草稿／提交／题单／复习等证据的旧版自动加入标记，事务失败整体回滚。
- 目标保存、归档和实际分配，保留原创建时间、归档身份、每天固定题目、别名去重和真实首次正式 AC 进度。最近公开赛事生成原有 `practice_sets`，刷新不更换 ID 或复活手动撤下的题。多目标共享实际复习后剩余分钟；已有采纳学习主线时不额外分配旧目标行。目标容量和题量仍只是安排，不表示获得评级、奖项或经验授权。
- 本地学习规划的共享预算、候选方案、采纳、调整、更换主线、推迟、阅读、原理检查、模板实现证据、跨周归档和旧计划查看。阅读只推进阅读，答对原理题只推进原理阶段；完整正式学习证据尚待迁移。
- C++17 / Python 3 本地样例和自测、异步队列、真实进程限制、取消、关闭恢复及结果写入重试。编译执行不占用数据库或 WebView 锁。输出仅代表样例或自测，不生成官方成绩和授权。
- 固定版本 clang-format / Ruff 格式化，保留 UTF-16 修改位置、源摘要、语言和比赛保护；格式化不执行代码，不改写草稿。
- 本地日志导出与 SQLite 在线副本校验，保留已提交 WAL、未知表和必要历史，拒绝覆盖已有目标。账号关联信息尚未迁移，导出仍标记部分完成。
- 真实 Tauri 全屏状态读写。无宿主的 CLI 明确报告窗口不可用；其它 WebView 无权调用本地数据接口。

## 公开资源缓存接线

固定 SHA-256、MIME、长度和受信任地址的公开图片／PDF／附件先在服务锁外下载，再进入题面或题解业务。公共 seed 保持只读，缓存单独保存，兼容原 SQLite 缓存格式；流式写入临时文件并验证后，再在事务中写 SQLite blob。失败的临时文件自动回收，错误或超长正文不进入缓存。

原源连接失败可使用受信任的国内回退；保持 Windows TLS 证书验证，不跟随重定向，不携带账号 token、Cookie 或个人数据库信息。单份资源最多 32 MiB、全进程最多 4 个并行下载；单次读取最多准备 256 份、合计 128 MiB 远端资源，超出时明确失败并保留个人记录。已缓存资源可离线读取。

题面、译文、原 PDF、附件、题解方法、详细题解和讲义读取都使用相同校验路径；`library/asset` 同样验证内嵌与缓存字节摘要。网络等待不持有 catalogue/library/personal 锁；下载失败不会提前开启复习、标记看过题解或保存代码。样例运行只需要文本样例和限制，不等待无关图片或 PDF。

## 明确保留的迁移保护

进行中比赛的创建、到期和结算、私人题目目录叠加、完整正式学习证据、真实账号登录／DPAPI／分块同步、原站浏览器和新官方回执、成长授权、社交／排行／团队／对战协议、更新与安装恢复仍有未迁移业务。对应接口或事实存在时明确返回 `MIGRATION_PENDING`、比赛冲突或具体资源错误，不隐藏旧记录或把它们当作空数据。

普通工作区允许已完成比赛、既有官方历史和有效活动目标；目标遇到私人账号事实或进行中比赛时继续保护，损坏的目标记录明确报错并保留原值。无法识别的重现赛来源也继续保护。完整规划的刷新／变更仍拒绝未迁移的官方、复习、比赛、目标和私人题目事实。CLI 和诊断页的 `authenticated=false` 只是隔离本地身份，不授予正式账号、经验、排名、库存或共享服务权限。

## 当前验证

135 项 Rust 检查包括 9 项目标业务边界、8 项资源模块检查和 8 项资源服务集成检查。目标覆盖同日固定、别名重复修复、实际证据、共享预算、采纳主线、跨日重开和失败整体回滚；资源覆盖首读下载、离线重开、损坏、错误账号与令牌、失败时个人日志不变，以及网络等待期间其它读取。工作区排他锁保持启用。

本轮新 release CLI 显式指定绝对路径，对照实际旧 Python 实现完成：目标 49 项逐字段及持久化比较和 9 项边界；38 项复习／冻结历史逐字段比较、1 项已确认别名与 5 项边界；普通业务 52+3；本地规划 52+3。随机创建 ID 仅为 oracle 对齐，不改写业务选择或回执。默认跳过的显式 HTTPS 冒烟检查没有计入 135 项；独立资源模块另有 PNG、JPEG 和 PDF 三份真实 HTTPS 下载后离线重读证据。

当前新宿主真实 Tauri/WebView2 回归通过全屏、普通 C++／Python 本地运行、学习任务、复习独立草稿、冻结比赛历史和立即刷新。原图“小月的屏幕”实际解码显示，`library/asset` 返回与画面同一原始字节；页面错误为零。窗口使用的全量 seed 已内嵌该原图，远端首读／离线恢复另由服务与独立传输检查验证。窗口回归和原图显示证据随服务接线回执保留。全部测试使用新建隔离日志，没有发送原站提交，也没有使用或发放真实账号奖励。共享 React 的错误保存、立即刷新和等待时切账号等十项场景见 `review-scope-commit-20261109.json`。冻结比赛 UI 的导航入口只在新建测试 WebView 缓存中显式展示，不修改账号等级。

目标批的同一真实窗口另通过两个目标的 IPC 创建、既有训练表打开目标题目、实际编辑保存、刷新恢复和归档保留草稿；没有为验证重新增加已收起的旧目标编辑器入口。其截图为 `docs/verification/20261109-native-goal-task.png`，完整窗口回执随目标业务 JSON 保留。

冻结 1.6.10 的原稿、补译与知识点实际进入新瘦 seed 和索引，原生投影构建错误为零。新 seed 上重新通过上述 49+9、38+1+5、52+3、52+3 对照与 135 项 Rust 检查。源码宿主与新独立包均通过全套窗口操作；新补的 102992 A 和 105459 B 原稿共五页 PDF、中文及原图实际显示，逐页有文字，公式错误和页面错误为零。三个 PDF 从远端实际进入新隔离缓存；同一日志断网重开后字节摘要、译文与图片一致，缓存和个人逻辑指纹不变。该检查覆盖所列内容，远端总索引的完整逐字节发布核验另由主线保留。

源码接线数量和诊断启动时间不是完整功能验收，也不能用于宣称整体速度、所有进程内存或完整安装体积已经优于现版；这些比较仍待相同题库、工具链和账号操作链下完成。

## 历史验证记录

下表仅是各自提交和各自二进制的历史结果，不能代替当前回归。原证据、必要的历史包与恢复元数据继续保留。

| 阶段 | 当时 Rust 检查 | 历史回执 |
| --- | ---: | --- |
| 格式化 | 51 | `docs/verification/native-format-20261108.json` |
| Windows 进程限制 | 59 | `docs/verification/native-process-20261108.json` |
| 普通样例／自测 | 75 | `docs/verification/native-local-run-20261108.json`、`native-current-20261108.json` |
| 1.6.7 源码与独立包 | 75 | `docs/verification/native-167-20261108.json`、`native-167-packaged-20261108.json` |
| 自建题单／1.6.8 | 85 | `临时验证/Rust本地测试/1.6.8同步-20261109` 的构建和窗口回执 |
| 日志导出／默认代码／公开赛事 | 92 | `docs/verification/native-journal-events-20261109.json`；当时独立包与旧公共源仍保留 |
| 真实全屏 | 94 | `docs/verification/native-fullscreen-20261109.json` |
| 既有正式历史／复习 | 104 | `docs/verification/native-reviews-20261109.json` |
| 冻结比赛历史 | 110 | `docs/verification/native-contest-history-20261109.json` |
| 独立公开资源模块 | 8 项模块检查，非整体验收 | `docs/verification/native-public-assets-module-20261109.json`；该历史回执当时尚未接入 Service |
| 公开资源完整接线 | 126 | `docs/verification/native-public-assets-service-20261109.json` |
| 目标训练／旧 seed | 135 | `docs/verification/native-goals-20261109.json`，当时仍是旧十份后续译文 seed |

## 构建与验证入口

Rust/Cargo 位于 `E:\项目\ToBe\公共工具\Rust`，MinGW 位于 `D:\Work\Msys64\ucrt64\bin`，不修改系统 PATH。当前编译目录以 `.backups/native-target.json` 为准，避免在源码盘重复生成产物。

```powershell
cd E:\项目\ToBe\开发\tb-tauri-complete-20261108
python scripts/native_contract.py --check
powershell -NoProfile -File scripts/native.ps1 -Action test -TestPython C:\Users\lenovo\AppData\Local\Programs\Python\Python313\python.exe
powershell -NoProfile -File scripts/native.ps1 -Action build
$nativeTarget = (Get-Content .backups/native-target.json | ConvertFrom-Json).target
$nativeCli = Join-Path $nativeTarget release/tobe-core.exe
python scripts/native_reviews_parity.py --native $nativeCli --output .backups/current-reviews.json
python scripts/native_goals_parity.py --native $nativeCli --output .backups/current-goals.json
python scripts/native_phase2_parity.py --native $nativeCli --output .backups/current-phase2.json
python scripts/native_learning_parity.py --native $nativeCli --output .backups/current-learning.json
npm --prefix frontend run build
powershell -NoProfile -File scripts/native.ps1 -Action desktop
$nativeDesktop = Join-Path $nativeTarget release/tobe-desktop.exe
node frontend/tests/native-window.mjs $nativeDesktop
```

`TB_NATIVE_SOURCE_ROOT` 只为独立开发宿主选择公开资源；`TB_NATIVE_SANDBOX_DIR` 指向新测试状态。真实窗口附加检查分别使用 `TB_NATIVE_TEST_CONTENT1610`、`TB_NATIVE_TEST_GOALS`、`TB_NATIVE_TEST_RUNNER`、`TB_NATIVE_TEST_REVIEWS`、`TB_NATIVE_TEST_CONTEST_HISTORY`、`TB_NATIVE_TEST_ASSETS`。运行器的开发工具路径与测试进程解释器路径分别配置。迁移工具只向新目标生成副本，不把副本切换为正式数据入口。

## 清理记录

每批更新前先检查引用与用途。此前两份被现 seed 和历史包取代的纯公开 SQLite 副本已核对表结构、身份包含关系及个人记录为空后移入回收站，共 2,105,061,376 字节；这不表示释放了同等空间。复习批删除一份无有效输出的 0 字节临时日志；冻结历史批与资源批各移除四份被成功回执取代的失败诊断临时文件，均有逐文件记录。

公开资源批移除重复的题面提前 hydrate 流程和已失效的“下载尚未迁移”错误文字；原始资源统一通过最终校验。清理了本文多组重复“本轮”总览和过期保护描述，必要计数改存上方历史表，原回执与历史包保留。

目标批开始前核对引用，随后用实际业务替换旧的活动目标一律拒绝和空概览占位；保留进行中比赛、账号事实及完整学习证据保护。窗口通过后移除四份被成功结果取代的测试定位失败临时文件，路径、长度、摘要及原因记录在目标回执。未发现需要删除的其它源文件或仍有用途的公共／个人记录；未触碰正常安装、真实个人数据、草稿、提交和学习记录。

1.6.10 同步前核对公共表、身份包含与完整性；确认旧 1,053,859,840 字节源库与保留历史包摘要完全一致后，在自己的开发工作区用新瘦 seed 原位替换，没有再留一份 GB 副本。两个窗口测试目录的八份过期定位诊断在成功后删除；包装来源校验拒绝短提交号产生的一份未完成候选，经核对十个文件全与输入一致且不存在个人状态后清理，校验已提前到复制前。实际路径、摘要和保留来源均见最新回执。正常安装、真实账号及必要历史包没有改动。
