# TB · 训练工作台

**把题库、题解、代码编辑、本地评测和训练记录放在一个工作台里。**

TB 面向算法竞赛训练，支持牛客、Codeforces、AtCoder 和洛谷。题库与题解随安装包提供，训练记录留在本机；公开账号同步、机器翻译和共享排行榜按需联网。

**最新正式版：[TB v1.0.14](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.0.14)（2026-10-14）。** 修复每日目标独立计数、原站提交验证和题面加载，支持文件增量更新。

**当前源码：v1.0.15，已完成本地构建与验证，尚未发布 GitHub Release。** 本仓库包含官网回执同步、训练统计、模拟赛与题库扩充的后续改动，详见 [1.0.15 源码更新说明](docs/releases/1.0.15.md)。下方安装包仍为已发布的 1.0.14。

[下载最新版](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [项目主页](https://3097729287.github.io/acm-algo-trainer/) · [使用说明](docs/usage.md) · [开发与构建](docs/development.md) · [English](README.en.md) · [反馈问题](https://github.com/3097729287/acm-algo-trainer/issues)

![TB 训练工作台](docs/assets/workbench.png)

## 开始使用

Windows 10/11 64 位推荐下载 [TB-Setup-1.0.14-win64.exe](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.0.14/TB-Setup-1.0.14-win64.exe) 并安装，包含 Python 运行时、C++ 编译器和离线 WebView2 安装组件。已有安装请先退出 TB，再安装到原目录。

[便携版 TB-1.0.14-win64.zip](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.0.14/TB-1.0.14-win64.zip) 需要完整解压，系统须已有 WebView2；不要只复制一个 EXE。发布页同时提供 1.0.13 → 1.0.14 增量包、`RELEASE-MANIFEST.json`、`SHA256SUMS.txt` 与 `BUILD-INFO.json`，用于更新、核对下载文件和构建信息。

选择题目，加入“我的训练”，在编辑器里写 C++。“运行样例”检查公开样例，“提交”（Ctrl+Enter）通过已连接的原站账号在后台提交，结果显示在 TB 内。首次官方提交先按 [浏览器连接说明](docs/usage.md#练习) 加载随包扩展，并在日常浏览器登录对应平台。确认官方 AC 后自动同步排行榜。

## 最新正式版 v1.0.14

- **每日目标与经验**：每个目标的当天题单独立保存、独立计数并加入“我的训练”；每日经验按当天 AC 的不同原题计算，旧题当天重新 AC 也计入，首次 AC 奖励不重复发放。
- **原站提交与题面修复**：四站提交验证与账号登录分开处理，复用现有浏览器会话；修复旧回执阻塞后续提交、空样例导致题面缺失等问题。人工验证仍在原站完成，受理不明的请求不自动重发。
- **文件增量更新**：在“偏好设置 → 更新 → 软件版本更新”检查和下载，再选择“保存并替换更新”。更新前保存草稿、在线备份 SQLite 并校验 SHA-256，只替换变化文件；漏装版本沿已发布增量包逐步更新，不重复下载编译器与 WebView2。官方提交或模拟赛进行中须先完成当前任务。
- **随包内容**：正式版 1.0.14 包含 958 道题和题面、796 份默认题解、1 份详细题解、376 篇基础讲义；配图离线可读、点击放大。

详见 [v1.0.14 更新说明](docs/releases/1.0.14.md)。

## 当前源码 v1.0.15 的新增内容

- **官网回执同步**：按已配置账号同步 Codeforces 官方提交记录；浏览器扩展读取本人记录并观察 AtCoder、牛客和洛谷的回执。题库中能匹配到的原题按平台和提交编号去重，保留原始提交时间；未取得源码时明确标记。
- **提交接续**：准备超时或需要验证时打开本次提交页并尝试预填代码，由用户完成原站验证与提交，TB 继续检测结果，不重复发送代码。
- **训练与比赛**：顶部显示今日 AC，成长页显示总做题数；全局提交记录过滤运行与样例。比赛名称自然排序、重现赛可搜索；已结束模拟赛可单条或批量删除，保留代码、草稿与 AC。内置题单升级后，每日目标仍通过原题 URL 识别原任务。
- **公共题库**：随源码提供 1,982 道题和题面，保留 796 份默认题解、1 份详细题解和 376 篇基础讲义。公开同步会继续增加本机题库；部分比赛题单仍待核验，覆盖情况见 `backend/resources/*-coverage.json`，不将已收录题目视为所有比赛的完整题单。

## 工作台里有什么（当前源码）

| 功能 | 行为 |
| --- | --- |
| 题库与题解 | 1,982 道题、796 份默认题解、1 份详细题解和 376 篇基础讲义，使用 SQLite 存储；不依赖开发者的归档目录 |
| 练习与模拟赛 | 单题、综合、专项与重现赛；比赛中隐藏知识点，结束后复盘或删除比赛记录 |
| 代码与记录 | 自动保存草稿、提交代码与结果；正式提交历史与工作台样例运行分开显示 |
| 知识清单 | 分组标题、层级缩进、连接线和覆盖统计，支持搜索与键盘操作 |
| 成长与能力 | 今日 AC、总做题数、能力参考、推荐题目和每日任务；每日目标独立计数 |
| 公开账号 | 同步支持平台的公开资料和通过记录，注明数据来源 |
| 题面翻译 | DeepSeek、火山方舟及自定义兼容 API，支持连接测试，保护代码、公式和样例 |
| 共享排行榜 | 阿里云 API 地址为 `https://47.82.84.74`，已部署；官方 AC 自动同步，按北京时间统计日榜、周榜与总榜 |
| 软件更新 | 启动与每日检查、增量下载、SHA-256 校验、保存草稿和数据库备份、替换变化文件与重开 |

新同步的公开题可能尚无题解。只有内置或导入了题解的题目显示“可读题解”。本题的基础讲解只关联自己的讲解章节及明确引用，不会把同标签的全部讲义列出来。

## 项目结构

```text
frontend/           React 界面，独立开发与构建
backend/            本机 HTTP API、SQLite 存储、训练与评测服务
backend/resources/  标准知识点和公开来源配置
desktop/           桌面窗口及官方提交适配
data/              library/ 文本源与重建出的公共 library.sqlite3
server/leaderboard/ Node.js + MySQL + Redis 共享排行服务
scripts/           内容导入、检查与构建
packaging/         Windows 安装程序
docs/              使用、架构、开发与迁移说明
```

前后端通过 `/api` 通信。后端不要求界面文件即可启动；开发时 Vite 代理 API，桌面版由宿主组合已构建的界面与本机服务。

## 数据与升级

内置题库以文本源 `data/library/`（JSON）进入 git，`data/library.sqlite3` 是其构建产物：首次启动缺失时自动重建，打包与离线检查也会补齐（`scripts/library_seed.py export|build` 手动导出/重建）。运行时数据位于 `state/`：题库工作副本、个人训练数据库和设置文档数据库彼此独立。升级更新公共题库，保留个人记录、身份、加密配置和用户导入内容；写入前会备份已有题库。

0.5 版本的 SQLite 个人记录直接沿用，JSON 配置在首次使用时迁入 SQLite，源文件保留。安装程序可显式导入旧 DSH 安装的记录。详见 [数据与迁移](docs/architecture.md#数据与迁移)。

## 开发

需要 Python 3.13、Node.js 24 和可用的 C++ 编译器。

```powershell
$env:TB_OFFLINE = "1"
python backend/backend.py --offline --state-dir .backups/dev-state
# 另一个终端
cd frontend
npm ci
npm run dev
```

后端默认 `127.0.0.1:18765`，前端默认 `127.0.0.1:5173`。桌面开发另装 `backend/requirements.txt` 中的依赖，构建界面后运行 `python desktop/launch.py`。完整命令见 [开发说明](docs/development.md)。

```powershell
python scripts/check.py
cd frontend
npm run build
npm run test:ui
npm run test:compilers
```

[排行榜部署](server/leaderboard/README.md) · [贡献说明](CONTRIBUTING.md) · [MIT](LICENSE) · [第三方许可](THIRDPARTY.md)

当前仓库为 `3097729287/acm-algo-trainer`，主产品为 TB。已发布的 1.0.14 源码见对应 [Release 标签](https://github.com/3097729287/acm-algo-trainer/tree/v1.0.14)。每次发布必须同步源码、中英文 README 和相关文档，标签与构建提交一致；详见[发布同步检查](docs/development.md#发布同步检查)。
