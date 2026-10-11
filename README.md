# TB · 训练工作台

**把题库、题解、代码编辑、本地评测和训练记录放在一个工作台里。**

TB 面向算法竞赛训练，支持牛客、Codeforces、AtCoder 和洛谷。题库与题解随安装包提供，训练记录留在本机；公开账号同步、机器翻译和共享排行榜按需联网。

**最新正式版：[TB v0.10.1](https://github.com/3097729287/acm-algo-trainer/releases/tag/v0.10.1)（2026-10-11）。** 官方 AC 自动同步排行榜，支持检查、下载和安装软件更新。

[下载最新版](https://github.com/3097729287/acm-algo-trainer/releases/latest) · [项目主页](https://3097729287.github.io/acm-algo-trainer/) · [使用说明](docs/usage.md) · [开发与构建](docs/development.md) · [English](README.en.md) · [反馈问题](https://github.com/3097729287/acm-algo-trainer/issues)

![TB 训练工作台](docs/assets/workbench.png)

## 开始使用

Windows 10/11 64 位推荐下载 [TB-Setup-0.10.1-win64.exe](https://github.com/3097729287/acm-algo-trainer/releases/download/v0.10.1/TB-Setup-0.10.1-win64.exe) 并安装，包含 Python 运行时、C++ 编译器和离线 WebView2 安装组件。已有安装请先退出 TB，再安装到原目录。

[便携版 TB-0.10.1-win64.zip](https://github.com/3097729287/acm-algo-trainer/releases/download/v0.10.1/TB-0.10.1-win64.zip) 需要完整解压，系统须已有 WebView2；不要只复制一个 EXE。发布页同时提供 `SHA256SUMS.txt` 与 `BUILD-INFO.json`，用于核对下载文件和构建信息。

选择题目，加入“我的训练”，在编辑器里写 C++。“运行样例”检查公开样例，“提交”（Ctrl+Enter）通过已连接的原站账号在后台提交，结果显示在 TB 内。首次官方提交先按 [浏览器连接说明](docs/usage.md#练习) 加载随包扩展，并在日常浏览器登录对应平台。确认官方 AC 后自动同步排行榜。

## v0.10.1 中的功能

- **官方 AC 排行榜**：自动补传已保存的历史官方回执，按原题去重，提供北京时间日榜、周榜和总榜。样例通过不计入；仅同步身份、昵称和成绩摘要，不上传代码、Cookie 或翻译密钥。服务当前依赖客户端回执，尚无独立原站防作弊认证。
- **软件自动更新**：默认启动时和运行期间每天检查 GitHub 正式版；在“偏好设置 → 更新 → 软件版本更新”手动检查、下载并选择“保存并安装更新”。安装前保存草稿、在线备份 SQLite，并校验 SHA-256；原地安装后自动重开。官方提交或模拟赛进行中须先完成当前任务。v0.10.1 修复系统代理共享 GitHub 查询额度耗尽时的检查失败。
- **图文与训练界面**：内置 958 道题和题面、796 份题解、376 篇基础讲义；配图离线可读、点击放大。待办与目标汇入“我的训练”，模拟赛采用紧凑布局，题面支持独立 14–32px 字号。

详见 [v0.10.1 更新说明](docs/releases/0.10.1.md)。

## 工作台里有什么

| 功能 | 行为 |
| --- | --- |
| 题库与题解 | v0.10.1 内置 958 道题、796 份题解、376 篇基础讲义，使用 SQLite 存储；不依赖开发者的归档目录 |
| 练习与模拟赛 | 单题、综合与专项训练；比赛中隐藏知识点，结束后复盘 |
| 代码与记录 | 自动保存草稿、提交代码与结果；训练进度由实际提交产生 |
| 知识清单 | 分组标题、层级缩进、连接线和覆盖统计，支持搜索与键盘操作 |
| 成长与能力 | 能力参考、推荐题目和每日任务卡片；奖励按不同题目的实际通过计算 |
| 公开账号 | 同步支持平台的公开资料和通过记录，注明数据来源 |
| 题面翻译 | DeepSeek、火山方舟及自定义兼容 API，支持连接测试，保护代码、公式和样例 |
| 共享排行榜 | 阿里云 API 地址为 `https://47.82.84.74`，已部署；官方 AC 自动同步，按北京时间统计日榜、周榜与总榜 |
| 软件更新 | 启动与每日检查、下载进度、SHA-256 校验、保存草稿和数据库备份、原地安装与重开 |

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

当前仓库为 `3097729287/acm-algo-trainer`，主产品为 TB。正式版源码可从对应 [Release 标签](https://github.com/3097729287/acm-algo-trainer/tree/v0.10.1) 获取。
