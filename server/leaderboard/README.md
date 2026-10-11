# TB 排行榜服务

TB 的题目、代码、草稿、每日任务和经验值保存在本机。排行榜支持在阿里云服务器上使用 Docker 部署 Node.js API、MySQL 8.4、Redis 8.4 和 Caddy HTTPS。MySQL 保存每个安装用户的昵称、唯一 ID，以及首次本地审核通过的题目摘要；Redis 作为独立服务提供，当前排行榜逻辑尚未使用 Redis 缓存。生产服务使用 MySQL，SQLite 仅用于测试和快照转换。

程序首次运行生成 UUID 和随机凭据；更新版本沿用原身份。安装包不包含任何用户身份、凭据或个人数据库。修改昵称不会改变 ID。复制个人数据库到另一台机器会沿用同一身份；完整卸载并删除个人数据后会创建新身份。

日榜按北京时间当天计算，周榜从北京时间星期一开始，总榜统计全部不同题目。同题重复通过、运行和样例通过均不增加排名。界面展示 `昵称 #完整 ID`。客户端报告本地审核通过记录，服务暂不提供防作弊认证，也不将这类记录称为原站通过。

## 阿里云 Docker 部署

连接目标是实例公网 IP 或 SSH 别名。`https://swasnext.console.aliyun.com/servers/cn-hongkong` 是控制台列表页，不能用作 SSH 主机或排行榜 API 地址。先取得公网 IP、SSH 用户/端口、可用私钥，无需购买域名；公网 IP 可作为 HTTPS 地址；检查实例系统、可用磁盘、现有服务和端口后再安装。

在本机通过 SSH 连接并查看系统：

```sh
ssh -i /path/to/key -p 22 user@SERVER_IP
cat /etc/os-release
df -h
sudo ss -lntp
```

将本目录的部署文件、`src/`、`mysql/`、`redis/`、`scripts/`、`package.json` 和锁文件上传到服务器 `/opt/tb-leaderboard`。不要上传本机依赖或个人 TB 数据库。Ubuntu 22.04/24.04/26.04、Debian 12/13 可使用已准备的官方源安装脚本；已有容器软件或其他系统需要先检查，脚本不会自动卸载现有组件。

```sh
cd /opt/tb-leaderboard
sudo sh scripts/install-docker.sh
sudo sh scripts/init-secrets.sh
sudo docker compose config --quiet
sudo docker compose up -d mysql redis
sudo docker compose build api
```

MySQL 使用 `mysql_data` 命名卷持久化；3306 不映射到宿主机或公网。初始化 SQL 只在空数据卷首次启动时执行。API 监听宿主机 `127.0.0.1:8080` 供运维检查，公开请求通过 Caddy。随机密钥保存在服务器 `secrets/`；重复运行初始化不会更换已有密码。

Redis 使用 `redis:8.4-alpine`，容器内地址 `redis:6379`，默认用户为 `default`，密码保存在 `secrets/redis_password`。6379 不映射到宿主机或公网，开启 ACL 密码认证、AOF 每秒刷盘、RDB 快照与 `redis_data` 持久卷，初始内存上限 256 MiB、达到上限后拒绝新增而不自动淘汰数据。健康检查使用认证后的 PING。依据：[Redis 官方镜像](https://hub.docker.com/_/redis)、[持久化说明](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)。

有旧排行榜快照时，先完成下一节导入，再启动 API。新数据库无需导入时可以直接启动：

```sh
sudo docker compose up -d api
curl --fail http://127.0.0.1:8080/v1/health
```

在阿里云实例防火墙允许 TCP 80、443；SSH 端口按管理需要放行。在 `.env` 中将 `SITE_ADDRESS` 设为实例公网 IP（不带协议前缀），然后启动 HTTPS。使用域名时才需要配置 DNS：

```sh
sudo cp .env.example .env
# 将 .env 的 SITE_ADDRESS 改成服务器公网 IP。
sudo docker compose --profile https up -d
sudo docker compose ps
curl --fail https://SERVER_IP/v1/health
```

Caddy 2.11.6 显式使用 Let's Encrypt 的 `shortlived` ACME profile，为公网 IP 签发受信任证书并自动续期（有效期 160 小时）；无需网站界面或域名。依据：[IP 证书说明](https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability)、[Caddy ACME 配置](https://caddyserver.com/docs/caddyfile/directives/tls)。`caddy_data` 持久保存证书。配置 `default_sni` 为 `SITE_ADDRESS`，让直接访问 IP、未发送 SNI 的客户端也能选到对应证书，见 [Caddy 全局选项](https://caddyserver.com/docs/caddyfile/options#default-sni)。API 仅在这一受控反向代理部署中设置 `TRUST_PROXY=1`，不能将 API 8080 直接公开。健康检查实际查询数据库，MySQL 故障时返回 503。

安装依据：[Docker Ubuntu](https://docs.docker.com/engine/install/ubuntu/)、[Docker Debian](https://docs.docker.com/engine/install/debian/)、[MySQL 官方镜像](https://hub.docker.com/_/mysql)、[Caddy HTTPS](https://caddyserver.com/docs/automatic-https)。

小内存部署至少使用 1 GiB 实例，并配置 2 GiB 交换空间。在 `.env` 启用 `COMPOSE_FILE=compose.yaml:compose.small.yaml`；本次 0.5 GiB 实例在同时运行四个服务时出现严重内存和磁盘等待，不能将初始化成功视为整套服务可稳定运行。用户升级为 1 GiB 后，系统检测到 894 MiB 内存，SSH 和公网健康检查恢复；仍需按实际负载验证容量。`compose.small.yaml` 将 MySQL 限制为 1 核、224 MiB 内存（含交换空间总上限 768 MiB），缓冲池 32 MiB，关闭 performance_schema；Redis 数据上限 32 MiB，Redis、API、Caddy 分别限制为 0.25、0.5、0.25 核。三个服务的健康检查在启动后每 60 秒执行，API 使用内置 HTTP 客户端检查，减少反复启动检查进程的开销。

检查 `swapon --show` 与 `sysctl vm.swappiness`。本次实例原设置为 0，改为 60 后 MySQL 初始化通过，但原来的单文件覆盖未能在重启后保持：TuneD 启用了 `reapply_sysctl=1`，处理 `sysctl.d` 后又读取 `/etc/sysctl.conf`，其中的 0 覆盖了新值。修复时先备份配置，将 `/etc/sysctl.conf` 和 `/etc/sysctl.d/99-zz-tb-resource.conf` 中的该项统一为 `vm.swappiness = 60`（`99-sysctl.conf` 是前者的符号链接），执行 `sudo sysctl -w vm.swappiness=60`，再重启 TuneD 和服务器分别验证。保留其他 sysctl 项与现有调优配置。本机还在 `/etc/tuned/tb-leaderboard/tuned.conf` 创建了继承 `virtual-guest` 的配置：`[main]` 中设置 `include=virtual-guest`，`[sysctl]` 中设置 `vm.swappiness=60`，使用 `tuned-adm profile tb-leaderboard` 激活。这样保留原有调优，并让 `tuned-adm verify` 的目标与覆盖值一致；TuneD 重启和整机重启均已验证。参数含义见 [Linux 内核文档](https://docs.kernel.org/admin-guide/sysctl/vm.html#swappiness)。交换空间只能缓冲内存峰值，不能替代物理内存。

小内存服务器不宜直接构建 API 镜像。可以在开发机的独立目录准备 `runtime/`：复制 `package.json`、`package-lock.json`、`src/`、`mysql/`、`scripts/`，在该目录执行 `npm ci --omit=dev --ignore-scripts --no-audit --no-fund`，然后仅上传此目录到 `/opt/tb-leaderboard/runtime`。当前生产依赖为纯 JavaScript；跨系统准备时必须检查不存在 `.node` 本地扩展，并验证导入 `src/server.mjs`。不要上传开发依赖、个人数据库或密钥。

在 `.env` 配置 `COMPOSE_FILE=compose.yaml:compose.small.yaml:compose.runtime.yaml`，使用 `docker compose --profile https up --no-build -d` 启动。`compose.runtime.yaml` 清除构建配置，改用官方 Node.js 24 镜像，并以非 root 用户运行只读挂载的程序。常规服务器仍可使用原 Dockerfile。

## 导入旧排行榜快照

旧服务器已退役，最终 SQL 与 JSON 备份为受保护的私有迁移资料。JSON 使用 `tb-ranking-v1` 格式，包含 `users` 和 `events`；不得提交到公开仓库。SQLite SQL 可通过 `node scripts/export-sqlite.mjs sqlite-export.sql migration-data.json` 转换，转换时验证完整性与外键。

先启动 MySQL，保持 API 停止或 `READ_ONLY=1`，将 JSON 上传到服务器受保护目录后导入：

```sh
sudo docker compose stop api
sudo docker compose run --rm --no-deps -v /opt/tb-leaderboard/migration-data.json:/migration.json:ro api node scripts/import-snapshot.mjs /migration.json
sudo docker compose up -d api
```

导入保留用户 ID、昵称、凭据 SHA-256 摘要、首次通过时间和去重键。目标存在用户或记录时拒绝导入；任意一行失败会回滚整批。非 root 容器需要读取权限，父目录只允许管理员访问，导入后恢复私有归档权限。临时限流桶无需迁移。

核对源与目标数量、原身份认证、日周总榜、受信任 HTTPS 和备份恢复后，将 `READ_ONLY` 设为 `0`。在 TB“设置 → 账号与身份”使用 `https://47.82.84.74`；默认资源已更新，已安装客户端的显式设置需要单独更新。2026-10-11 已在升级后的 1 GiB 实例完成部署，启用 `READ_ONLY=0`，并验证重启恢复、原身份、公网 HTTPS 和客户端同步。

v0.10.0 使用官方 AC 协议，身份注册、昵称更新和日周总榜接口保持兼容。新版客户端补传本机已保存的原站 AC 回执；空榜也可能表示没有可上传的官方回执，不代表身份丢失。

## 备份与维护

```sh
sudo sh scripts/backup.sh
sudo docker compose ps
sudo docker compose logs --tail=100 api
```

备份脚本用 `mysqldump --single-transaction` 写入 `backups/`，成功后压缩；包含用户身份资料，不能公开提交。部署后将备份复制到服务器外的受控位置，并使用独立数据库做恢复验证。容器设置自动重启、健康检查和日志轮转；日常重建容器保留数据卷。不要使用 `docker compose down -v`，它会删除数据库和证书卷。

## 服务接口

除了 `GET /v1/health`，请求均携带 `X-TB-User: UUID` 和 `Authorization: Bearer 安装凭据`。凭据由客户端首次运行生成，服务器只保存其 SHA-256 摘要。请求体仅接受规定字段，最多 64 KiB。

| 接口 | 请求 | 返回 |
|---|---|---|
| `POST /v1/profile/register` | `{userId,nickname}` | `{userId,nickname,createdAt}`；重复注册验证原凭据 |
| `GET /v1/profile` | 无 | 当前身份与昵称 |
| `PUT /v1/profile` | `{nickname}` | 更新自己的昵称 |
| `POST /v1/events` | `{events:[{eventId,problemKey,acceptedAt,difficulty,scope:"official"}]}` | `{processed,scope,notice}` |
| `GET /v1/leaderboard?period=daily` | 周期 `daily`、`weekly` 或 `total` | `{period,date,timezone,entries,self,notice}` |

每批最多 100 条通过记录。`problemKey` 是原题规范化链接的 SHA-256 摘要；`eventId` 是身份和原题摘要的 SHA-256 摘要。不发送题目代码、草稿、测试数据、翻译 API Key、原站 Cookie 或密码。记录按用户和原题唯一，重传不会增加题数；异步评测导致更早的通过记录稍后到达时，服务修正到更早日期。

本机接口为 `GET/POST /api/profile`、`GET /api/leaderboard?period=daily`、`POST /api/leaderboard/sync`、`GET /api/daily-tasks` 和 `POST /api/daily-tasks/claim`。每日任务领取与奖励保存在本机 SQLite 事务中，不依赖服务器。

## 本地验证

需要 Node.js 24 或更新版本。接口测试执行同一生产处理器和真实 SQLite 查询，MySQL 测试通过生产 HTTP 适配器连接独立测试库：

```powershell
npm.cmd ci --ignore-scripts
npm.cmd test
$env:TB_MYSQL_TEST_PORT = "测试实例的本机端口"
$env:TB_MYSQL_TEST_PASSWORD = "测试实例的 root 密码"
npm.cmd run test:mysql
```

MySQL 测试只连接 `127.0.0.1` 的显式测试端口，创建并清理随机 `tb_test_` 数据库。CI 使用 MySQL 8.4 容器。覆盖事务回滚、并发限流、Unicode、身份保护、快照导入及禁止覆盖已有数据。

在仓库根目录验证桌面客户端：

```powershell
$env:TB_OFFLINE = "1"
$env:PYTHONPATH = "$PWD/backend;$PWD/backend/common;$PWD/desktop"
python -m unittest test_v5_services.IdentityAndClientTests
```

接口回归测试使用 `tests/local-server.mjs` 的 SQLite 适配器。开发时仅回环地址允许 HTTP；公开服务必须用 HTTPS。测试数据和结果不能作为阿里云已部署或旧库已完成迁移的证据。

## 0.10.0 官方 AC 协议

`POST /v1/events` 仅接受 `scope: "official"`，响应包含 `processed` 和相同 scope。昵称和身份协议保持不变。`mysql/002_official_ac.sql` 新增 `official_ac_events`；旧 `ac_events` 及原身份保留，旧本地成绩不转换成官方成绩。日榜、周榜与总榜从新表计数。

客户端仅导出持久化的原站 AC 提交回执，原题 URL 规范化后计算哈希，同一身份/原题只计最早一次。无日期的公开账号汇总不计为当日成绩。请求不含提交代码、Cookie 或翻译密钥；服务校验身份、范围、日期及去重，尚不进行原站独立防作弊复核。

现有 MySQL 升级：先运行 `sh scripts/backup.sh`，使用数据库管理员执行 `mysql/002_official_ac.sql`，再部署新 API。初始化新卷时 Compose 同时挂载 001 和 002。不要重建生产卷，也不要把旧快照重复导入已有数据库。运行时挂载部署可直接更新 `/opt/tb-leaderboard/runtime/src/` 后重启 API，无须在 1 GiB 实例构建镜像。
