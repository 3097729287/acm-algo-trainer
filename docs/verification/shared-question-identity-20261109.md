湖北 2024 Gym105139H / 洛谷 P10865 共享服务去重修复，基线 ae5df344，独立工作区。

开始前完整阅读设计理念并检查现有 identity、计数、奖励、原事件存储和临时构建：没有可删除的废弃文件或重复资源；原始收据、既有测试及结算历史均继续使用并保留。此次替换了排名与霸榜中直接 COUNT 全部平台行的旧查询片段，复用同一个精确身份投影，不增加平行存储或复制原稿。

与 Python/Rust 维护代理约定：全局 question identity=`luogu.com.cn/problem/P10865`；别名仅此键与 `codeforces.com/gym/105139/problem/H`。各字符串的 SHA-256 对应既有 problem_key。导航、原站提交、比赛字母/槽位继续保留原平台身份。

本次不改数据库 schema、不迁移或归并原事件行、不更改旧 accepted_at/received_at，不撤回既有排名奖励、霸榜历史或背景库存。排名、将来结算的排名 XP、将来结算的霸榜先选两别名的实际最早原事件，再按日/周范围过滤。任一别名已有排名排除记录也适用于同题，防止通过另一平台恢复被排除成绩。团队仍从原始 AC 和验证后的 native receipt 在真实比赛窗口计分，不采用全局首次日期替代本场通过时间；原 H 题位保持。重现赛背景新奖励不允许同题两个别名冒充两道不同赛题，已发背景不改。

共享服务没有独立的每题首次 XP 发放台账；个人首次 XP/学习记录由 Python 真实 journal 与成长实现维护，另由内容修复代理处理。此处负责共享排名、排名结算奖励及服务自己的奖励入口，不能从共享 COUNT 推测或改写个人提交历史。

同题证据为 `content-updates/20261109-new-xcpc-hubei/source-review.json#existingEquivalentTasks`（原审查文件 SHA-256 `fe07c8939c76f408492d04da53deb1cd4c156b262588aa623b53ff453095dce6`），官方 15 页原题书第 11 页 H，PDF SHA-256 `925611a43f223d1489a315b8e7ebecf0f202abd51f5f50aec5033549f9012282`；对应归档洛谷 JSON SHA-256 `13a6510c78182dd7c09eaa4bf51b9e0d91fb4cd8e621c9e4406524f37faee245`。未复制原件。

旧重现赛 `p:` 标识曾使用完整原题 URL 的 SHA，本次同时识别已核的两个原 URL `https://www.luogu.com.cn/problem/P10865`、`https://codeforces.com/gym/105139/problem/H` 与新的 question-key SHA；不把任意 URL、同名标题或相邻题号并入同题。后台按“今日”删除排名时也先选全局首次，不会因今天重过镜像而把过去的真实首 AC 排除。

实际验证：

- 完整 SQLite 服务测试 143 项：142 通过、1 项原有跳过、0 失败。
- 全新独立 MySQL 8.0.27 的旧完整协议、团队与新增同题测试合计 62 项全部通过。随机 loopback 端口 13791；每个新增夹具建库前比较 `@@datadir` 与本次全新 nonce 目录。结束前再次验证 datadir、实际 server PID 与启动父进程/程序路径，确认 0 个临时 schema 后正常 SHUTDOWN；未连接正常 MySQL 或私有卷。
- 最终补充已有旧背景奖励可读取/可打开的证据后，SQLite/MySQL 各 5 项目标组合再次全部通过。五项覆盖精确 pair、双向上传与跨日跨周最早日期、legacy 两哈希与历史排名奖励完整保留、未来排名 XP/霸榜不膨胀、12 槽团队 fixture 保留 H 原 CF URL与窗口计分、canonical LG 新客户端与 native 收据兼容，以及旧完整 URL/新 question hash 的背景证据去重。
- 团队用的是明确注入的 12 槽 HTTP fixture；未声称修改了正式 team-contests 选题册或在原站正式提交。native-only 行是隔离已验证回执表夹具，未冒称本次调用外部原站核验。
- SQLite 夹具原来只把 SELECT 当作读语句，现同时支持实际 WITH 读查询；没有放松 SQL 断言。MySQL 的同题方案直接在实际共享 HTTP 和真实 MySQL SQL 引擎中通过。
- 早期 MySQL 合并检查漏置明确 fixture 模式环境变量而被门禁拒绝；补上后 62 项通过，门禁未移除。E 盘中文路径上的此旧 MySQL 启动即退出，因此依 root 授权改用全新 C 盘 ASCII 临时路径，非迁移已有数据。

原始日志与隔离实例所有权/正常关闭回执在忽略区 `.backups/question-identity-verification`。部署需要更新五个引用模块并加入 `src/question-identities.mjs`；没有 SQL 数据迁移。本批仅隔离本机测试，不部署或访问正常账号。
