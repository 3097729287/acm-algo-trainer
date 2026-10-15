# TB · 训练工作台

TB 将题库、题解、C++ 编辑、本地评测和训练记录放在同一个工作台，支持 Codeforces、AtCoder、牛客和洛谷。个人训练与草稿保存在本机。

**版本：[TB v1.0.18](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.0.18) · 2026-10-15。** 源码、程序、前端与浏览器扩展同版；标签与 BUILD-INFO 标识实际构建提交。发布资产公开前属于尚未正式发布的源码准备阶段，此时正式版仍为 v1.0.17，请使用“下载最新正式版”入口；资产公开后以 v1.0.18 发布页为准。

[下载最新正式版](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [项目主页](https://3097729287.github.io/acm-algo-trainer/) · [使用说明](docs/usage.md) · [开发与构建](docs/development.md) · [English](README.en.md)

![TB 训练工作台](docs/assets/workbench.png)

## 安装与更新

Windows 10/11 x64 使用 `TB-Setup-1.0.18-win64.exe`，含 C++ 编译器与离线 WebView2 组件。便携版为 `TB-1.0.18-win64.zip`，请完整解压。保存草稿、退出 TB 后安装到原目录，个人数据库与导入内容保留。

1.0.17 提供 `TB-Update-1.0.17-to-1.0.18-win64.zip` 增量包；更早版本可沿增量链更新或使用完整安装包。另有浏览器扩展 ZIP、`RELEASE-MANIFEST.json`、`SHA256SUMS.txt` 与 `BUILD-INFO.json`。更新后重新加载随包浏览器扩展。

## v1.0.18 的改动

- 每次启动强制检查正式版，登录前也能更新；发现新版后自动下载、校验并安装，无需确认。草稿保存、数据库备份和提交/模拟赛等待完成后自动继续；每日检查开关只控制运行期间的额外检查。
- 我的训练删除分组下拉与平台分类；题库保留七项分类。最低难度、最高难度、提交结果与缩短后的搜索框放在同一行，窄窗口自动换行。
- 每日任务移入顶部独立弹窗，显示领取进度与可领取提示；领取经验后仍可按 Esc 关闭。更新通知新增一键已读，保留通知与题目链接。
- 等级称号改为算法实践、状态建模、构造与证明、复杂度掌控等技术主题；经验与段位规则保留。活动通过数采用数字与细进度条，保留五档颜色。
- 多目标周计划只显示一份。同类比赛取最高周题量与最高练习范围，给出未通过的建议题目；各目标的每日题单和完成进度继续独立保存。
- 自动新增仅覆盖牛客、洛谷、AtCoder 已结束比赛；CF 普通赛只补已指定题解的 31 场赛事，另收录 2017 年起的新 XCPC。160 场旧条目退出公共选题，旧安装中的题目与个人记录保留。
- 规范中文赛事名称并区分地点、赛段与镜像。核对 63 场原始比赛日期，纠正把镜像上传或重放时间当赛事日期的情况；日期不明时只显示已核实年份。
- 保留 295 场、3580 道 CF Gym XCPC 题，其中 284 场提供独立的 Gym 整场 1–5 级难度。新增 439 道有依据的单题估分、172 道具体知识标签；估分与整场等级分别展示。

公共题库共 **5782 道题、600 场比赛**，保留 **2202 份题面、796 份默认题解、1 份详细题解、376 篇讲义**。291 题采用官方 rating，1929 题为标明来源的估算，3562 题仍缺少可靠单题评级。知识点来自已有原站/镜像资料及对应公开题解的明确技术词，自动匹配不冒充算法复验。新增 Gym 题面按需联网缓存，不保证全部离线可读。

[更新说明](docs/releases/1.0.18.md) · [赛事核对报告](backend/resources/contest-audit-1.0.18.json) · [评级依据](backend/resources/xcpc-rating-audit.json) · [知识依据](backend/resources/xcpc-knowledge-audit.json)

## 工作台里有什么

| 功能 | 行为 |
| --- | --- |
| 题库与题解 | 5,782 道题、2,202 份内置题面、796 份默认题解、1 份详细题解和 376 篇基础讲义，使用 SQLite 存储；不依赖开发者的归档目录 |
| 练习与模拟赛 | 单题、综合、专项与重现赛；比赛中隐藏知识点，结束后复盘或删除比赛记录 |
| 代码与记录 | 自动保存草稿、提交代码与结果；正式提交历史与工作台样例运行分开显示 |
| 知识清单 | 分组标题、层级缩进、连接线和覆盖统计，支持搜索与键盘操作 |
| 成长与能力 | 今日 AC、总做题数、能力参考、推荐题目和每日任务；每日目标独立计数 |
| 公开账号 | 同步支持平台的公开资料和通过记录，注明数据来源 |
| 题面翻译 | DeepSeek、火山方舟及自定义兼容 API，支持连接测试，保护代码、公式和样例 |
| 共享排行榜 | 阿里云 API 地址为 `https://47.82.84.74`，已部署；官方 AC 自动同步，按北京时间统计日榜、周榜与总榜 |
| 软件更新 | 每次启动强制检查并自动安装、增量下载、SHA-256 校验、保存草稿和数据库备份、替换变化文件与重开 |

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

当前仓库为 `3097729287/acm-algo-trainer`，主产品为 TB。1.0.16 对应源码见 [版本标签](https://github.com/3097729287/acm-algo-trainer/tree/v1.0.16)。每次发布同步源码、中英文 README 和相关文档，标签与构建提交一致；详见[发布同步检查](docs/development.md#发布同步检查)。
