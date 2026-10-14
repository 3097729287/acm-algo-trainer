# TB · 训练工作台

TB 将题库、题解、C++ 编辑、本地评测和训练记录放在同一个工作台，支持 Codeforces、AtCoder、牛客和洛谷。个人训练与草稿保存在本机。

**版本：[TB v1.0.16](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.0.16) · 2026-10-15。** 源码、程序、前端与浏览器扩展统一为 1.0.16；发布资产与标签对应同一构建提交。安装包是否已可下载，以发布页为准。

[下载最新正式版](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [项目主页](https://3097729287.github.io/acm-algo-trainer/) · [使用说明](docs/usage.md) · [开发与构建](docs/development.md) · [English](README.en.md)

![TB 训练工作台](docs/assets/workbench.png)

## 安装与更新

Windows 10/11 x64 使用发布页的 `TB-Setup-1.0.16-win64.exe`，含 C++ 编译器及离线 WebView2 安装组件。便携版为 `TB-1.0.16-win64.zip`，请完整解压。已有版本先保存草稿并退出 TB，再安装到原目录；安装包不会覆盖个人数据库。

发布资产包含 1.0.14 → 1.0.16 增量包、浏览器扩展 ZIP、`RELEASE-MANIFEST.json`、`SHA256SUMS.txt` 和 `BUILD-INFO.json`。本地使用 1.0.15 的用户也可完整安装升级。更新后在 Edge/Chrome 扩展管理中重新加载随包“TB 浏览器连接”。

## v1.0.16 的改动

- 修复 CF 原生提交按钮和表单关联识别，后台等待不再误报未登录。正常准备错误保留重试；只有原站要求验证时转到浏览器人工处理。已发送但回执未确认的请求继续查询，不自动重发。
- 10 级成长体系，每级所需经验为 200、400、600、800、1000、1200、1400、1600、1800 XP，累计 9000 XP 达到 10 级。十种段位有独立图标与颜色，并扩展高难题、千题/万题及长期连续训练称号。
- 10 级自动解锁 TB 排位，顶部与成长页切换为 TB 排位分。按独立首次原站 AC 加分，同题只奖励一次；翡翠及以上需每日完成对应难度题目维持分数，王者星级持续提高。此分数是 TB 的个人训练排位，与原站 rating 和共享过题榜分别显示。
- 顶部独立显示今日 AC，等级栏显示 X/Y XP 或 TB 排位分，删除旧下拉统计方块。账号编辑默认收起。取消牛客、洛谷公开统计账号绑定，原站登录与提交仍支持四个平台。
- 公共题库为 2202 道题及题面、796 份默认题解、1 份详细题解、376 篇基础讲义。全部题目具有知识分类与难度；保留原站评级，762 道使用明确标识的 TB 估算。部分知识分类仅描述题面模型，具体算法未复验。
- 规范 XCPC、周赛、小白月赛和练习赛名称，去掉重复赛事题名前缀，保留原题标题与身份。之后新增题目自动使用相同命名规则。

详见 [v1.0.16 更新说明](docs/releases/1.0.16.md)。

## 工作台里有什么

| 功能 | 行为 |
| --- | --- |
| 题库与题解 | 2,202 道题、796 份默认题解、1 份详细题解和 376 篇基础讲义，使用 SQLite 存储；不依赖开发者的归档目录 |
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

当前仓库为 `3097729287/acm-algo-trainer`，主产品为 TB。1.0.16 对应源码见 [版本标签](https://github.com/3097729287/acm-algo-trainer/tree/v1.0.16)。每次发布同步源码、中英文 README 和相关文档，标签与构建提交一致；详见[发布同步检查](docs/development.md#发布同步检查)。
