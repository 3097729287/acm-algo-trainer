Rust 排行榜与互动客户端的独立实现基于 29e1fd59；正式 Python 程序、安装包和共享服务器不随本批修改。

开始前已完整阅读 `E:\项目\ToBe\设计理念.md`。检查 `backend-rust` 中已有模块、引用、临时构建及共享服务夹具：当前没有排行榜或社交客户端，也没有可删除的废弃实现、重复资源或临时产物。Python 实现仍用于正式版及协议对照，全部保留。采用稀疏独立工作区，未复制公共大资源、个人库、登录信息或密钥。

真实协议基准为 `backend/leaderboard.py`、`backend/training.py:979–1082`、`backend/gameplay.py`、`server/leaderboard/src/api.mjs`、`social.mjs`、`social-store.mjs`、`training-list-likes.mjs`、`duel-community.mjs`。社交及题单点赞的正式 JSON 回执没有 owner，客户端必须以同一认证上下文校验 `/v1/profile`，校验实际收件人和请求标识，并拒绝切号后的迟到响应；不伪造服务回执，也不因此更改正式服务。

真实输入计时沿用 React 的 `usePresence.js` 与 `userInput.js`：只有鼠标、键盘、触摸等真实输入刷新计时；300 秒后发送 `idle`。客户端不能把心跳或读取排行榜算作输入。服务排除 idle 用户，现有 `PresenceLabel.css` 对离线显示红色。

本模块交付不等于 Rust 全部路由迁移完成。账号授权及实际路由由集成代理接入；同步采用本机只读准备、无数据库锁的网络阶段、短事务提交三个阶段，公共成长资料必须由真实成长实现提供。

`AuthContext<'a>` 只借用账号管理器的 `{ owner, endpoint, bearer, admin }`，没有 Debug/Serialize。缓存仅保留 bearer 的 SHA-256 会话标识，响应和日志不返回标识或令牌。`still_current: &dyn Fn() -> bool` 必须为快速 lease/epoch 检查；构造请求前、联网后、缓存提交前和本机事务提交前均检查，变化返回 `409 OWNER_CHANGED`。账号层在退出、替换或失效时还须调用 `invalidate_owner`，并执行外层 owner/请求 token 门禁。

`new(Duration)` 创建独立 blocking HTTP 客户端：总超时上限 60 秒、连接最多 3 秒、禁止重定向、禁用自动重试；回环 HTTP 绕过系统代理，远端自定义 HTTPS 保留系统代理。头像响应上限 16,065,568 字节、社交 4 MiB、其余 256 KiB。头像缓存总数据最多 32 MiB/100 项，15 秒重新核验；元资料认证缓存 15 秒，按 owner/endpoint/登录会话隔离。榜单 8 秒刷新，按同一 owner/endpoint/登录会话/周期/北京时间隔离，只保留真实成功数据。乱序读取不能覆盖已确认的点赞和更新的头像。

公开方法表如下。除构造、清缓存和三阶段同步外，统一返回 `Result<serde_json::Value, ApiError>`，最后两个参数固定为 `now: DateTime<Utc>, still_current: &dyn Fn() -> bool`。

| 本机路由 | 模块方法及其余参数 | 真实共享接口 |
| --- | --- | --- |
| GET leaderboard / rankings | `rankings(&AuthContext, period: &str, now, guard)` | GET /v1/leaderboard?period=... |
| GET leaderboard/avatar | `avatar(&AuthContext, user_id: &str, expected_hash: &str, now, guard)` | GET /v1/avatars/{uuid} |
| GET social | `social(&AuthContext, now, guard)` | GET /v1/social |
| POST social/comments、likes、read | `social_write(&AuthContext, action: &str, body: &Value, now, guard)` | POST /v1/social/{action} |
| GET training-list-likes | `list_likes(&AuthContext, ids: &[String], now, guard)` | GET /v1/training-list-likes?id=... |
| POST training-list-likes | `list_like(&AuthContext, body: &Value, now, guard)` | POST /v1/training-list-likes |
| POST presence | `presence(&AuthContext, body: &Value, now, guard)` | POST /v1/presence |

三阶段同步签名：

```rust
prepare_sync(&self, auth: &AuthContext<'_>, personal: &PersonalStore,
    catalogue: &Catalogue, public_profile: Option<&Value>,
    now: DateTime<Utc>, guard: &dyn Fn() -> bool) -> Result<SyncPlan, ApiError>
execute_sync(&self, auth: &AuthContext<'_>, plan: &SyncPlan,
    now: DateTime<Utc>, guard: &dyn Fn() -> bool) -> Result<SyncReceipt, ApiError>
commit_sync(&self, auth: &AuthContext<'_>, personal: &PersonalStore,
    receipt: SyncReceipt, guard: &dyn Fn() -> bool) -> Result<Value, ApiError>
```

`SyncPlan`/`SyncReceipt` 字段私有、不可从 JSON 反序列化。本机只读阶段仅选真实 submit/AC/official/finished 记录，按规范原题 URL 最早日期去重，复用 `official-v1\0owner\0problemKey` 哈希规则；旧已确认更早日期不覆盖。网络阶段按 100 条上传，空批不发送；核验 profile userId、原样成长资料/头像 hash、processed/scope 和 rewards userId/经验范围。网络阶段不持 SQLite 连接。提交阶段再次核验原 journal 的 user_id/endpoint，以短事务保存原 ranking_receipts、ranking_reward_totals 和成功同步时间，保留草稿和提交原记录。榜单获取失败保留已有同范围真实成绩，明确 status=error；未全部刷新不会写“全部同步成功”的时间。

执行错误不会自动重发写操作。传输中断或成功响应损坏会标记 `uncertain=true`；用户明确重试时，留言复用原 requestId、AC 复用原 eventId，由真实共享服务保证幂等。尚未收到完整同步回执时不伪造本机 receipt，已有远端接受记录可以安全再对账。

2026-11-09 已在独立工作区运行：

- `cargo test -p tobe-core --test leaderboard --offline --locked`：10 项通过。真实 production createApiServer + SQLiteStore、三个经正式 register/login 接口建立的临时账号；包括私人收件箱/回复/已读隔离、社交及题单点赞、错 owner/bearer 拒绝、账号/端点/周期/日期缓存隔离、401 清该会话缓存、头像摘要/格式/删除/15 秒期限、300 秒 idle 与在线人数、禁止重定向、迟到响应拒绝、真实写入后断流不重放、迟到榜单不撤销爱心、101 条真实 journal 首 AC 分为两批、空批不发送、三阶段回执提交及切号拒绝、失败保留原草稿及真实榜单。
- `cargo test -p tobe-core --lib --offline --locked`：22 项通过。第一次检查缺少既有测试要求的 TB_NATIVE_TEST_PYTHON；补上现成 Windows Python 测试解释器后完整通过，未修改测试或生产规则。
- 日志保存在忽略区 `.backups/social-client-verification`。所有网络均为本机随机端口。时间边界以注入测试时间精确推进，不把测试时间推进称作真实等待五分钟；红色离线样式沿用已核对的现有 React CSS，本批未进行新 WebView UI 验收。

集成尚需实际完成：账号管理器持有 owned 会话快照后借出上下文并接上述路由；同步前后只在准备/提交时短持对应 journal 锁；公共成长 DTO 由真实成长实现提供（None 时明确 publicProgressPublished=false）；`leaderboard` 外层可从本机已保存 profile 读取 lastSyncedAt；旧社交操作产生的本地每日任务 action（heart-given/leader-tease）由实际任务实现接续，不能靠 UI 发送标记补写。现有 Service 的 MIGRATION_PENDING 标记没有在本批撤除。
