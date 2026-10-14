# 为 TB 贡献

请在 Issue 中描述使用场景、版本、复现步骤和实际结果。界面问题注明窗口尺寸、主题和字号；题库问题附原题 URL。不要提交个人数据库、API Key、Cookie 或草稿。

应用代码在 `frontend/`、`backend/`、`desktop/`；共享服务在 `server/leaderboard/`。修改前阅读 [架构](docs/architecture.md)，按 [开发说明](docs/development.md) 运行相应检查。存储和安装修改须验证新安装与升级保留记录；官方适配使用本地页面夹具验证表单和编译器，不需要提交真实账号。

题解可用 Markdown 作为交换格式，导入时正文和关联讲义进入 SQLite。提供来源 URL、完整题意、解法、代码和实际验证记录。公共题库不携带作者的个人训练状态。使用 `scripts/import_library.py` 导入，再运行完整性检查与 `python scripts/library_seed.py export`，提交 `data/library/` 文本源。`data/library.sqlite3` 是构建产物，不进入 git。

提交 PR 时写清触发问题、最终行为和实测范围。每次准备发布新版本，必须一起更新实际源码、`VERSION`、前端与扩展版本、中英文 README、相关使用说明、项目主页和发布说明。按对应源码核对功能与题库统计，按发布资产核对下载文件名、链接和升级方式；历史发布记录保留当时版本事实。

先把源码与文档提交推送到 GitHub，再发布由同一提交构建的资产；发布标签和 `BUILD-INFO.json` 必须指向构建提交。不能只上传安装包、便携包或增量包而保留旧源码与 README。源码领先正式版时，分别标明源码版本与已发布版本，下载入口只指向已发布资产。完整流程见[发布同步检查](docs/development.md#发布同步检查)。
