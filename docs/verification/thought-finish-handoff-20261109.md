# 思维对决交接（2026-11-09）

范围是独立分支 `finish/thought-20261109`，基于 `5ca1f752`。本分支没有部署服务、改普通程序、改普通账号配置或重新发布 1.6.11 应用。国内更新新桥与团队训练由各自分支负责。先读设计理念和当前 AGENTS；清理检查见同目录 `thought-finish-cleanup-20261109.json`，此新工作树没有可删的旧构建或重复源码。

## 服务必须合入的内容

| 路径（相对仓库） | 作用 |
| --- | --- |
| `server/leaderboard/src/pk-judge.mjs` | 固定 prompt／JSON 规则，HTTPS 端点校验、桌面同款非思考选项、45 秒总期限、取消、128 KiB 响应限制、永久与暂时错误分类 |
| `server/leaderboard/src/thought-duels.mjs` | 关闭时释放租约并保留答卷、旧工作防覆盖、单次结算、每场／每日持久预算与额度等待恢复 |
| `server/leaderboard/src/server.mjs` | 将裁判配置、超时、预算环境字段接入真实服务启动 |
| `server/leaderboard/mysql/021_thought_judge_budget.sql` | 仅新增 `pk_judge_usage(usage_day,calls)`，幂等、不清零、不改已有 ledger／奖励／答卷 |
| `server/leaderboard/compose.pk.yaml` | 现有 PK overlay 增加超时和预算映射；沿用当前其他 overlay，不丢失原有服务配置 |

生产依赖未增加。`package.json` 只扩充测试命令，SQLite fixture 与测试文件不属于生产运行需求。已有 017 表和完整 `thought-problems.json` 仍是必要基础，不能只复制一个新 judge 文件。应从审核后的完整提交构建共享服务，并记录该提交，不能只以未变化的服务版本号判断源码。

## 配置字段（不含实际服务值）

| 字段 | 处理 |
| --- | --- |
| `PK_AI_ENDPOINT`、`PK_AI_MODEL` | 复用 TB 提供商所需的最小非秘密字段；端点为完整 HTTPS Chat Completions 路径 |
| `PK_AI_KEY_FILE` 或 `PK_AI_KEY` | 优先服务端私有 secret 文件；已有 `_FILE` 优先于直接 key，不能只增加 key 而忽略正在生效的 `_FILE` |
| `PK_AI_TIMEOUT_MS` | 单次总期限，默认 45000 ms，允许收紧，硬上限 45000 ms |
| `PK_AI_MATCH_CALL_LIMIT` | 默认 4，合法 1–4，包含第一次和重试 |
| `PK_AI_DAILY_CALL_LIMIT` | 默认全服务每天 100，合法 1–10000，北京时间日界；多个实例须一致 |
| `PK_MATCH_ENABLED`、`PK_THOUGHT_MODE_ENABLED` | 两个开关必须同时明确开启；凭据传输工具不会修改开关 |

费用护栏不是只存进程内存：每次裁判请求前，`pk_lobby` 锁下原子消耗当天额度。失败／取消／重启不返还，重复交卷不会重新消耗。日额度不足时答卷保持真实待裁判状态，每 60 秒再检查；额度上调或跨日后继续，等待时不伪造评分或加减积分。每进程最多 2 个在途任务，每次输出上限 6000 tokens；每日上限限制请求次数，不承诺具体货币费用。所有配置变动只属于 PK 字段，保留现有数据库、排行、下载、账号与其他 secret 字段。

## 本机配置到 SSH stdin

用户已明确允许复用 TB 的本机 AI 配置。确切来源：`E:\项目\ToBe\版本\最新版\程序\state\tb-documents.sqlite3` 的 `documents` 表，行键 `translation-settings.json`。需要 `provider`、`model`、`baseUrl` 和 DPAPI `protectedKey`；不调用会回退到其他项目 `.dsh` 的凭据探测。普通程序、配置行和账号状态保持只读。

`scripts/tb_thought_provider_stdin.py` 已提供最小输送端：

```text
python scripts/tb_thought_provider_stdin.py
python scripts/tb_thought_provider_stdin.py --ssh-argv <已审阅的无密钥argv.json> --apply
```

第一条仅检查本机存在性并输出字段名，不解密、不连接 SSH。第二条仅在内存 DPAPI 解密，将 `PK_AI_ENDPOINT`、`PK_AI_MODEL`、`PK_AI_KEY` 的 JSON 发到审核过的 `ssh` 子进程 stdin，捕获而不回显任何远端 stdout／stderr；凭据不进入 argv、文件、日志或公开产物。argv JSON 必须以 `ssh`／`ssh.exe` 开头，后面是当前 TB 服务的主机别名和已审核的私有配置接收程序；该文件自身不能含凭据。工具不附带、不执行远端 env 修改器，本轮仅运行过第一条。

因此支持“DPAPI 内存解密 → SSH stdin → 私有 env／secret”的路径，但 root 必须先核对实际服务的配置组织与接收程序：仅更新这三个 PK 配置的实际存储（优先将 key 写入私有 secret 文件，并仅修改相应 `_FILE` 指针），原样保留其他 env 字段；保持私有权限且运行账号可读。完整 env 展开与真实 JSON 不得回显。不能用本机验证回执推断已经向服务器复制或已开放功能。

## 部署顺序及验证边界

1. 保留当前生产运行源码／配置与在线 SQL 备份，完成已有恢复演练；关闭 PK 两个开关。按既有维护流程取得所有旧表的行数和内容指纹，避免并发写入干扰比较。
2. 合入审核后的完整服务提交，沿用当前服务构建和 overlay 链。若 017 未存在先执行 017，再执行 021。执行前后用 `scripts/audit-preserved-data.mjs` 核对旧表全量指纹：新增计数表可以为空，重跑必须保留已存在的计数。不要清空任何 `pk_`、账号、排行、奖励或下载表。
3. 审核最小私有配置变更后，使用 stdin 输送；不要修改普通桌面配置或账号状态。先确认 `_FILE`／直接 key 的实际优先级、私有文件读取权限与全服务预算一致。
4. 对独立 MySQL 测试实例可执行 `node --test tests/thought-budget-mysql.test.mjs`（显式设置 `TB_MYSQL_TEST_PORT`）。本机该项明确跳过；后续经 root 审核，已经在服务器 MySQL 8.4.11 的全新随机 schema 内用 `scripts/verify-thought-isolated-mysql.mjs` 完成真实 017／021 保全、重复幂等、预算并发／重启／跨日及超额无假赛果验收，新 schema 已清理。见 [只读审计与隔离回执](thought-production-readonly-audit-20261109.md)。这不是生产迁移或全部 MySQL 测试套件已执行。
5. 重建并切换共享服务，检查健康、原有账号／排行接口与本人 PK 状态，再明确开启两个 PK 开关。以临时账号做有界实际环境验证，不用真实玩家答卷冒充测试。检查对局和 `pk_judge_usage` 只增加预期次数，日志仅出现脱敏代码和数字状态。
6. 回退时关闭两个开关并保留所有表、计数、答卷与历史，不能用清空预算或恢复旧快照来重复消费。失败对局只展示明确失败，日额度等待没有伪造结果。

服务侧修复可独立部署。客户端的 `backend/thought_duel.py`（同账号切换服务／会话后拒绝旧响应）与 `frontend/src/components/ThoughtBattle.jsx`（明确的历史响应隔离、额度恢复等待文案）需要后续桌面版重新打包才进入普通程序。1.6.11 当前已发布应用字节不变；旧客户端仍能使用原有对局协议，但不会显示新增等待文案。本轮不负责打包该客户端更新。

## 已执行验证

- 真提供商只调用 1 次，3.350 秒：两个临时玩家和一个临时旁观账号，公开题目，99／39 分；四次重复交卷只结算一次，答卷、真实裁决和积分经重启保留。原回执保存在 `.backups/thought-live-20261109/case-8478bf574ed3/result.json`，同目录公开脱敏副本为 `thought-live-provider-20261109.json`。此真实验证发生在新增日预算之前；最终日预算由下述严格离线测试验证，没有为重复验收再次消费提供商额度。
- 最终共享服务：159 项，157 通过、2 明确跳过、0 失败；其中裁判／恢复／预算专项 25 项全部通过。新增 MySQL 跳过与旧服务中的既有跳过均保留原因。
- Python 中转／账号相关 29 项通过；真实 React＋共享 HTTP 的思维用例通过（fixture 裁判，和上面的真实 AI 回执分开表述），含额度等待／恢复、迟到草稿／历史响应、六维评分与窄屏。前端生产构建通过。
- 附带跑的旧 `gameplay-owner-races.mjs` 在未修改的贴纸 fixture 找不到“贴纸”按钮处失败；没有调整贴纸产品，也不将该旧通用测试记为通过。Vite 的未解析 `virtual:material-review` 扫描警告没有阻止本轮思维专项或生产构建。
- 后续实际 `5ca1f752` 基线对照在同一“贴纸”断言失败，相关三文件与思维分支 SHA 相同，确定为已有 fixture 缺 `.app-statusbar`。服务器的独立随机 MySQL schema 七项验收通过；全部源候选与临时 schema 已按校验清理，无孤儿容器，生产源码／PID／配置保持原样。失败与成功证据均保留。

独立源码提交和分支推送完成后由 root 决定后续集成／部署。本页的生产配置步骤仍未执行，没有传输 AI 凭据、改生产 env、重启服务或启动普通程序；后续 SSH 只进行只读审计及 root 审核允许的新随机 schema 隔离验收。
