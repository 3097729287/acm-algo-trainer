# ToBe Rust 重构进度

2026-11-05，开发候选 `2.0.0-alpha.1`。**这是可运行的迁移验证程序，尚未完成完整 ToBe 功能重构，不能替换 1.6.1 正式版。**

源码：`E:\项目\ToBe\开发\tb-tauri-rust`；分支：`refactor/tauri-rust-20261105`；基于当前前端提交 `9d5fcd83`。原工作区中尚未提交的场景交互代码另行保留，没有混入重构提交。

## 已实现

- React 与原有产品页面保留。公共 `request(path, body, token)` 在 Tauri 内走 IPC，浏览器开发继续使用原 HTTP。IPC 失败不回退 HTTP、不重放写请求。
- 版本化请求、请求编号、查询参数、账号归属、会话令牌和统一错误，定义于 `api/ipc.schema.json`。
- 从原后端 AST 生成 **134 个方法与路径组合**的迁移清单及个人 SQLite 表结构；`python scripts/native_contract.py --check` 检查遗漏。
- Rust 核心库与 Tauri 2 宿主已构建；运行时没有 Python 后端、Python sidecar 或本机 HTTP API 进程。
- Rust 只读访问现有 13,417 道题、题面、讲义、题单、资源和 Wiki；分页查询避免一次局部读取载入全库。
- 原有偏好读取、初始代码模板读取／保存／选择、自建模板读取／保存、Wiki 和普通草稿保存已接入，保留版本冲突、删除墓碑和原语言键。
- 账号接口只提供隔离验证环境的令牌，`authenticated=false`，不表示真实账号已迁移。
- SQLite 在线备份形成新副本，包含已提交 WAL、未知表和历史记录；校验副本完整性与逻辑指纹，拒绝覆盖已有目标。源库不执行模式变更，公共库不覆盖个人库。缺少必要字段的旧模式明确阻止迁移。

实时迁移状态来自 Rust `api/capabilities`：原有接口接入 **9 / 134**，另有 7 个新诊断／题库读取接口。比赛、复习草稿上下文仍明确返回 `MIGRATION_PENDING`。接入数量不代表完整功能和全部边界验收。

## 验证

- 24 项 Rust 集成检查：中文与空草稿、UTF-8 大小、账号与令牌隔离、模板冲突／语言／墓碑、异常旧记录、已提交／未提交 WAL、未知表、迁移目标竞争、拒绝覆盖及旧模式保护。
- 19 项与旧 Python 实现的真实对照：初始代码、自建模板、Wiki 目录／正文、语言选择及删除后的目录。使用临时状态，不使用个人数据。
- 原生 Tauri/WebView2 实测：React 加载、真实 IPC、13,417 道题总数、真实题面、普通草稿提交、宽窄窗口截图和页面异常检查。
- React 正式构建与 IPC 序列化／错误／账号切换／重复读取合并检查。

证据：开发工作区 `.backups/native-parity.json`、`.backups/native-window/result.json` 及同目录截图。最终检查结果以本轮更新记录为准。

## 剩余工作

1. 完整题库目录投影、导入、动态更新与资源水合。
2. 训练、复习、比赛、原站回执和完整提交历史。
3. 学习主线、周计划、掌握证据与历史计划的逐项等价迁移。
4. 账号、DPAPI 凭据、离线恢复、分块同步和冲突合并。
5. 能力、经验、每日任务、成就与库存授权；不用客户端生成结果代替可信事实。
6. 有限资源的本地运行器、C++／Python 工具链、原站浏览器及原生窗口生命周期。
7. 排行榜、社交、贴纸和对战协议适配，更新、备份、安装与升级恢复。
8. 相同题库、工具链、账号操作链下的速度、全部进程内存、安装体积与升级临时空间对比。

云端保持原协议；未部署服务、未修改线上数据、未公开发布。是否同时重写云端以用户后续答复为准，桌面迁移独立推进。

## 性能口径

完整功能兼容后，启动和常用操作应更快，硬盘与内存占用应更小。当前主 EXE 约 15.3 MiB，另含 WebView2Loader、现有题库及 Wiki，**不等于完整新版本安装体积**。

原生测试记录启动、IPC P50／P95 和宿主／WebView 进程内存。诊断页面工作量小于正式 ToBe，不能直接比较为性能提升比例；完整功能对比通过前不宣称整体资源目标达标。

## 开发与运行

Rust／Cargo 缓存位于 `E:\项目\ToBe\公共工具\Rust`，未修改全局 PATH。系统 MSVC 安装被自动审批拦截后，已用便携 Rust GNU 和现有 MinGW 完成原生构建；使用本机 WebView2。

```powershell
cd E:\项目\ToBe\开发\tb-tauri-rust
python scripts/native_contract.py --check
powershell -NoProfile -File scripts/native.ps1 -Action test
node frontend/tests/native-transport.mjs
python scripts/native_parity.py
cd frontend
npm run build
cd ..
powershell -NoProfile -File scripts/native.ps1 -Action desktop
node frontend/tests/native-window.mjs
```

`native.ps1 -Action dev` 运行已构建前端的开发宿主，不启动 Python。直接运行源码编译的 EXE 时，将 `TB_NATIVE_SOURCE_ROOT` 设为源码根目录；打包候选默认使用 EXE 同目录资源。

`scripts/package_native_candidate.ps1` 生成单独候选目录，逐文件校验 SHA-256，附构建信息；已有目标拒绝覆盖。候选的数据库和 WebView 配置位于自身 `state/native-migration-sandbox`，不打开正式账号或浏览器配置，不替换正常快捷方式。

迁移工具：`target/debug/tobe-core.exe migrate SOURCE DESTINATION`，只生成新副本。完整业务验收尚未完成，不能据此将副本切为正式数据入口。
