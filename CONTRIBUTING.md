# 为 TB 贡献

请在 Issue 中描述使用场景、版本、复现步骤和实际结果。界面问题注明窗口尺寸、主题和字号；题库问题附原题 URL。不要提交个人数据库、API Key、Cookie 或草稿。

应用代码在 `frontend/`、`backend/`、`desktop/`；共享服务在 `server/leaderboard/`。修改前阅读 [架构](docs/architecture.md)，按 [开发说明](docs/development.md) 运行相应检查。存储和安装修改须验证新安装与升级保留记录；官方适配使用本地页面夹具验证表单和编译器，不需要提交真实账号。

题解可用 Markdown 作为交换格式，导入时正文和关联讲义进入 SQLite。提供来源 URL、完整题意、解法、代码和实际验证记录。公共题库不携带作者的个人训练状态。使用 `scripts/import_library.py` 导入，再运行完整性检查与 `python scripts/library_seed.py export`，提交 `data/library/` 文本源。`data/library.sqlite3` 是构建产物，不进入 git。

提交 PR 时写清触发问题、最终行为和实测范围。更新 README、使用说明或项目主页时，以最新正式 Release 的版本、资产、对应源码和题库统计核对内容；中文与英文说明保持一致，历史发布记录保留当时版本事实。
