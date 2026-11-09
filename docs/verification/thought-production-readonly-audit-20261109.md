# 思维对决部署前只读复核

本轮仅进行本机源码比对与生产 SSH 只读审计。重新完整阅读设计理念与当前 AGENTS；清理检查确认本范围没有新增可清理的废弃实现，上一轮源码、失败证据、共享依赖及更新基线保留。没有启动普通程序、本机浏览器或 Docker，也没有执行远端建库、DDL、配置写入、重启或部署。下列隔离脚本目前仅通过语法与默认静态方案检查。

## 旧贴纸用例

最小复现命令：在独立的 `5ca1f752` 源码工作树中进入 `frontend`，沿用当前依赖执行 `node tests/gameplay-owner-races.mjs`。原用例先检查 A／B 对局写入的迟到响应，随后第 19–20 行 `choose()` 查询无障碍名称恰为“贴纸”的按钮；本轮附带执行在该处 5 秒超时。

`5ca1f752` 到思维提交 `1a5c4a23` 的 `gameplay-owner-races.mjs`、`gameplay-owner-fixture.jsx`、`StickerCanvas.jsx` 没有差异。静态根因是 fixture 没有 `.app-statusbar` 节点：`StickerCanvas` 的 layout effect 查询该节点，只有找到 `toolbarHost` 才会 portal 渲染“贴纸”按钮。测试 fixture 只创建两个账号按钮、对战入口和并列内容，没有真实主界面的底栏挂载点。该缺口在基线源码中已存在，本轮思维组件只用于传入 `thought` 的另一个模式，旧 fixture 没有传入该属性。

实际 `5ca1f752` 浏览器对照必须等 root 当前完整更新时间测量结束后再跑；此处暂不将静态证据写成已经执行基线。不得因此修改无关贴纸产品。

## 生产现状（只读所得）

- API：`tb-leaderboard-api-1`，`node:24-bookworm-slim`，Node `v24.21.0`，127.0.0.1:8080，healthy；`/opt/tb-leaderboard/runtime` 只读绑定到 `/app`。BUILD-INFO 为服务 1.4.8，来源 `cbd99a58b6abd26c734a7bdf415b6064a9a539ea`。
- MySQL：`tb-leaderboard-mysql-1`，MySQL `8.4.11`，生产 schema `tb_leaderboard`。数据卷为 `tb-leaderboard_mysql_data_swap_enabled`，保持原样；没有改全局／会话以外的设置。
- Redis：`redis:8.4-alpine`；Caddy：`caddy:2.11.6`。没有构建、拉取或删除镜像。
- 审计时服务器剩余 `448221184` 字节。现有 Node 镜像 ID 为 `sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20`；后续仍须动态查询，不据此拉取新镜像。
- 017 的七张 `pk_` 表结构完整：`pk_lobby` 一行；`pk_ratings`、`pk_queue`、`pk_matches`、`pk_members`、`pk_records`、`pk_operations` 均为零行。`pk_judge_usage` 不存在，021 尚未生效。
- 实际 schema 已有团队表，包含 `team_drafts`、`team_native_receipts`，`team_lobby` 一行、所查 `team_rooms`／`team_members`／`team_operations` 为零行。虽然 runtime/mysql 目录只有 001–018，不能据此断言数据库尚未执行 019／020。没有发现独立迁移版本账本，本轮以实际结构而非文件列表判断。
- Node 容器中可见的相关环境字段名只有 `MYSQL_DATABASE`、`MYSQL_HOST`、`MYSQL_PASSWORD_FILE`、`MYSQL_USER`、`NODE_ENV`、`RATE_LIMIT_SALT_FILE`、`READ_ONLY`；不存在任何 `PK_*` 字段。没有读取 `.env`、secret 文件正文或输出字段值。
- SQL 通过现有 `openStore` 正常认证，独立连接设置 `READ ONLY` 事务，只执行版本、information_schema 和 COUNT 查询；没有读取用户行、推进业务维护或运行裁判。
- 已确认 MySQL Unix socket 存在且确为 socket；可在后续审核的隔离容器中只读绑定该 socket。root secret 文件只确认路径存在，没有读取其内容。

生产源文件 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `src/pk-judge.mjs` | `0e0be9182e7d08e74b48af782b3dd32c55d206e83fe83b9e62996bf679b79948` |
| `src/thought-duels.mjs` | `1e30920077f0ac1b642adfb9c1759c1d569733e2d124e3c60f1821ebf18bb85b` |
| `src/server.mjs` | `72f1717f6e5107e8366235e6ce3b8a32d488809ea035bd01b6303e231d0e8572` |

## 供 root 审阅的最小真实 MySQL 隔离验证

脚本：`server/leaderboard/scripts/verify-thought-isolated-mysql.mjs`。默认只打印方案，既不读凭据也不建立 SQL 连接；必须明确提供 `--execute-isolated` 才执行。当前只跑过默认模式与 `node --check`，没有执行数据库分支。

1. 复用现有 Node 镜像，不 build、不 pull。仅将脚本、它列出的 5 个公开 src 文件和 001／004／017／021 四份迁移放入全新候选目录，总源码约 650 KiB，校验 SHA。不要覆盖 runtime；也可放独立容器 tmpfs。脚本在读取 root secret、连接数据库之前检查 `/app` 所在文件系统仍至少余 256 MiB，不足则退出，给 MySQL 字典和日志留余量。
2. 从现有 MySQL 容器动态查询 PID。socket 来源为 `/proc/<pid>/root/var/run/mysqld/mysqld.sock`，再次确认是 socket。启动一个全新、退出即移除的 Node 容器：`--pull=never --network=none --read-only --memory=192m --cpus=.5 --pids-limit=64 --cap-drop=ALL --log-driver=none`。候选源码、现有 runtime、MySQL socket 和已有 TB MySQL root secret 都只读绑定；不复制密码、不向 argv／环境变量传密码，不改任何实际服务容器。运行账号须能读取挂载的私有 secret。
3. 脚本用现有 `/app/node_modules` 的 mysql2，经 Unix socket 正常认证；仅此未来执行步骤会由客户端在内存消费已挂载的 root secret。脚本随机产生 `tb_verify_thought_<24位hex>`，先查不存在，再以普通 CREATE 新建。没有接收 schema 名的参数；已有 schema 一律不能作为目标。
4. 在该新 schema 用 001／004 建立 5 张最小旧表，写两个明确的临时身份和一条限流哨兵，保存行与结构摘要；不复制任何生产用户行。执行真实 017／021，旧表摘要必须完全一致。
5. 填入预算计数后重复执行 017／021，所有隔离表摘要必须不变；两个业务 worker、8 个并发事务只能合计占用 3 次预算。关闭并重建连接池与 worker 后不能重置额度；北京时间午夜启用新日计数。
6. 验证日额度不足时保留锁定文本与 `judging`，没有裁决、赛果或积分变动；不调用提供商，容器也没有网络。最后再核对全部 5 张旧表摘要。
7. finally 只 DROP 本进程刚创建且符合固定随机前缀的 schema。schema 创建前失败、名字碰撞或验证未证明由本进程创建时，不能清理该名字。创建成功时先输出不含用户数据的 schema 身份事件，异常终止也能保留该次目标证据；结尾输出完整摘要。若清理失败，只报告该新测试 schema 名，不能自动清理其它同前缀 schema。结果只输出摘要／代码，绝不输出 secret 或用户行。

root 审核并准备全新候选目录后，隔离运行形式如下；这些命令尚未执行。`candidate` 必须是新目录，所需内容由脚本默认方案列出的九个文件和脚本自身组成。`name` 也必须全新。

```sh
image="$(docker inspect --format '{{.Image}}' tb-leaderboard-api-1)"
mysql_pid="$(docker inspect --format '{{.State.Pid}}' tb-leaderboard-mysql-1)"
socket="/proc/$mysql_pid/root/var/run/mysqld/mysqld.sock"
test -S "$socket"
docker run --rm --pull=never --name "$name" --network=none --read-only \
  --user=0:0 --memory=192m --cpus=.5 --pids-limit=64 --cap-drop=ALL \
  --security-opt=no-new-privileges --log-driver=none \
  --mount "type=bind,src=$candidate,dst=/candidate,readonly" \
  --mount type=bind,src=/opt/tb-leaderboard/runtime,dst=/app,readonly \
  --mount "type=bind,src=$socket,dst=/mysql.sock,readonly" \
  --mount type=bind,src=/opt/tb-leaderboard/secrets/mysql_root_password,dst=/run/secrets/tb_verify_mysql_root,readonly \
  "$image" node /candidate/scripts/verify-thought-isolated-mysql.mjs \
  --source-root /candidate --execute-isolated
```

该演练验证真实 MySQL 上新增表的幂等性、旧测试表保全与跨连接预算原子性；它不冒充生产迁移已经完成，也不替代实际部署时对生产数据库的备份、恢复演练和原表指纹核对。本轮没有执行上述外部写操作，等待 root 评审。
