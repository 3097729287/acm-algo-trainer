# TB · 训练工作台

TB 将题库、图文题解、C++ 编辑、本地评测和训练记录放在同一个工作台，支持 Codeforces、AtCoder、牛客和洛谷。账号数据存放在与排行榜共用的服务端 MySQL，本机 SQLite 保存工作副本和待同步记录。

<!-- release-status:start -->
**当前正式版为 v1.1.0。** 本版把 1.0.19/1.0.20 的本地功能、题库补充和本轮界面调整一并交付；[GitHub 发布页](https://github.com/3097729287/acm-algo-trainer/releases/tag/v1.1.0)提供安装包、便携版、增量更新和校验清单。
<!-- release-status:end -->

[项目主页](https://3097729287.github.io/acm-algo-trainer/) · [使用说明](docs/usage.md) · [1.1.0 更新说明](docs/releases/1.1.0.md) · [开发与构建](docs/development.md) · [English](README.en.md)

![TB 训练工作台](docs/assets/workbench.png)

## 安装与更新

Windows 10/11 x64。[安装包](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.1.0/TB-Setup-1.1.0-win64.exe)包含 C++ 编译器和离线 WebView2 组件；[便携版](https://github.com/3097729287/acm-algo-trainer/releases/download/v1.1.0/TB-1.1.0-win64.zip)需要完整解压。

保存草稿、退出 TB 后安装到原目录，个人数据库和导入内容保留。跨电脑使用同一账号时，各电脑应升级到同一新版；浏览器扩展也应重新加载随包版本。自动更新先保存草稿、在线备份 SQLite、校验 SHA-256，再替换程序；进行中的提交或模拟赛结束后继续。实际增量包、扩展 ZIP、`BUILD-INFO.json`、`RELEASE-MANIFEST.json` 与 `SHA256SUMS.txt` 以发布页为准。

## v1.1.0

- **称号与成长：** 累计 AC 保留 1–2000 题的 12 档目标，500、750、1000、1500、2000 题改奖永久称号；连续训练 30、90、180、365、730 天改奖称号，最高目标为两年。自动佩戴最高 AC 与最高连续训练称号；旧版已发经验保留，不追扣或重复发放。
- **成就提示：** 新达成卡片显示边框，鼠标经过或键盘聚焦该卡片才标为已读；已读状态随账号同步。点击顶部段位经验框直接打开训练概览，最高已达成 AC 成就带奖杯，另显示下一个目标；每日任务提示只留在顶部，我的训练显示未完成待办提示。
- **账号与排行：** 成长页集中展示用户名、公开 ID、勋章、账号管理、CF/AtCoder 公开评分和翻译 API。排行榜展示称号、等级、段位与排位分；公开 ID 不采用登录号。当天登录零题也入榜，零题不领取名次奖励。
- **操作与响应：** 比赛列表增加“开始比赛”以启动重现赛；推荐题整行可进入单题。训练、键盘和快捷操作合并。比赛列表每页 40 场，工作区没有变化时复用已有对象；隐藏窗口暂停常规数据和目标轮询，恢复时刷新。后台会话检查、上传与软件自动更新继续运行。
- **数据同步：** 训练、完整提交代码、草稿、目标、每日题单、经验账本、收藏和账号偏好跨电脑恢复。同一账号只保留一个有效会话；另一台登录后，联网旧设备约三秒内检测失效。首次合并有备份，冲突草稿另存。
- **加载与内容：** 题库紧凑响应、缓存序列化结果、编辑器按需加载、后台限量读取题面与缩短个人数据锁，减少等待。现有 929 道带默认题解的题目均有详细版，包括牛客周赛 162–165 全部 26 题；本批为 XCPC 与蓝桥杯新增 120 组两版题解，覆盖 98 道不同题目；续写补齐 2026 四川省赛 C、D、G、H 和秦皇岛邀请赛 A、B、H，[完成与待补清单](docs/editorial-content-20261016.md)。

公共库包含 **5795 道题：5622 可见、173 隐藏；2215 份题面、929 份默认题解、929 份详细题解、376 篇讲义**。没有题面或题解的其他条目不代表可以离线阅读；原站暂时拒绝访问时保留缓存、草稿和重试入口。

新增自动比赛限于指定系列：牛客周赛、小白月赛、练习赛、挑战赛；洛谷入门赛、基础赛、月赛 Div.2；CF Div.2/3/4；AtCoder ABC/ARC。XCPC 与蓝桥杯继续保留。超范围或既无可用题面样例也无题解的自动条目隐藏，个人训练和代码不删除；既有题目的官方难度与标签也会刷新，未知评级不编造。

[账号与同步](docs/accounts.md) · [架构](docs/architecture.md) · [1.0.19 内容记录](docs/releases/1.0.19.md) · [1.0.20 同步与性能记录](docs/releases/1.0.20.md) · [已发布 1.0.18](docs/releases/1.0.18.md)

## 数据与服务

公共题库以 `data/library/` 的 JSON 文本进入 git，打包时重建 `data/library.sqlite3`。个人记录、库工作副本和设置分开保存在 `state/`，安装包不会覆盖个人库。题解与配图存储在 SQLite，运行不依赖开发者的归档目录。

账号快照通过 HTTPS 同步完整个人代码和引用题目的轻量资料、已缓存题面；站点 Cookie、翻译密钥、DPAPI 密文和机器配置保留本机。换电脑后须分别完成原站登录及翻译密钥配置。快照具有版本检查、校验和容量限制，网络失败保留本机未上传记录。

账号、数据库和排行榜共用现有服务器。`005_account_state.sql` 和 `006_public_progress.sql` 已在原 MySQL 上部署；2026-10-16 公网 HTTPS 健康检查确认共享服务 1.1.0、账号同步协议 1、单设备会话及公开成长协议 1。客户端已于 2026-10-18 发布并在本机完成升级。应用保留 Python 本机 API 与 Node.js 共享服务，没有改写为 Go。[服务部署](server/leaderboard/README.md)。

## 开发

需要 Python 3.13、Node.js 24 和支持 C++17 的编译器。桌面依赖见 `backend/requirements.txt`。

```powershell
$env:TB_OFFLINE = "1"
python backend/backend.py --offline --state-dir .backups/dev-state
# 另一个终端
cd frontend
npm ci
npm run dev
```

本机 API 默认为 `127.0.0.1:18765`，前端开发服务默认为 `127.0.0.1:5173`。`frontend/` 负责界面，`backend/` 管理本机数据和评测，`desktop/` 承载 WebView2 与浏览器连接，`server/leaderboard/` 管理账号、同步和排行。

```powershell
python scripts/check.py
cd frontend
npm run build
npm run test:ui
npm run test:compilers
```

发布必须先同步源码、版本与文档，再从同一提交构建和打标签；还须完成隔离安装、升级与迁移检查。详见[开发与发布检查](docs/development.md)。

[贡献说明](CONTRIBUTING.md) · [MIT](LICENSE) · [第三方许可](THIRDPARTY.md)
