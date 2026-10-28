# TB 排行榜服务

## 1.2.7 分块同步

配套迁移 `011_account_chunks.sql` 与 v2 私有对象接口为：`GET/PUT /v2/accounts/state`、`POST /v2/accounts/state/missing`、`GET/PUT /v2/accounts/state/objects/:hash`、有界批量 `POST /v2/accounts/state/objects`。只在根 CAS 成功后激活完整版本；旧账号快照不删除。服务只存有界压缩字节，不展开用户整个学习记录。

运行状态以 `/v1/health` 的版本与 `accountChunkProtocol` 为准。`deploy-account-chunks.sh` 先保存在线 SQL 备份，再停写核对原表及二进制对象指纹，只增加 011 与 v2 代理路由的 128 KiB 上限；已有 v2 根时不自动降回旧写入器。

数据指纹采用八个 32 位 XOR 分段，完整保留 SHA-256 的 256 位；避免 MySQL 将无符号 64 位中间值经过 `COALESCE/HEX` 时截断高位。隔离 MySQL 的完整单行 SHA 回归确认了旧问题，修正后 43 项 MySQL 及 41 项 HTTP/SQLite 检查通过。部署前后必须使用同一修正版计算，不能与旧的有损指纹混用。

普通测试与 `npm run test:mysql` 均覆盖分块、旧快照保留、撤销会话、重复与失败续传、图回收、50 个小账号并发。迁移前仍须在线完整 SQL 备份与原表核对，保留环境和数据卷；完成客户端及整个用户任务批次之后才统一部署。不可仅因源码测试通过就把 `accountChunkProtocol: 2` 写成线上能力。

## 1.2.6 题单点赞可取消

公共题单每位用户计一次有效爱心；POST 接受明确的 liked 布尔状态，重试保持幂等，false 仅移除该用户对该题单的记录。旧客户端缺省为 true；人际爱心规则不变。GET 无编号时返回公共题单完整摘要用于预取。使用现有表和索引，无数据迁移；API 切换使用 deploy-training-list-toggle.sh，先在线备份并核对原表指纹。实际部署状态见本机交付记录与健康接口。

## 1.2.5 大记录同步

已认证快照 PUT 的正文接收上限为 120 秒，普通请求仍为 15 秒；头部和空闲连接限制不变。保留认证、4 MiB 信封、64 MiB 展开容量、快照限并发、CAS 与会话复核。未完成上传超时后释放处理槽，心跳不占用该槽。此版本不改变数据库结构；通过 `scripts/deploy-state-upload.sh` 完成在线备份、原表指纹核对后切换 API，实际部署版本以健康接口和私有交付记录为准。

## 1.2.4 公共题单点赞（已部署）

`GET /v1/training-list-likes?id=...` 批量返回不超过 100 份公共题单的共享累计数和当前用户 `likedToday`；`POST` 接受 `{listId}`。编号来自随源码保存的 `src/training-list-ids.json`。按北京时间每人每天一次、不可取消，数据库主键负责并发与重试去重，事务内再次检查账号会话。个人题单保持私有，不写入公共点赞表，也不制造用户爱心通知。迁移缺失时返回不可用，不影响旧版登录、提交、同步与排行。

部署运行包使用现有准备器，新增迁移 `mysql/010_training_list_likes.sql`，执行 `scripts/deploy-training-list-likes.sh`。脚本先在线备份、停止 API 并核对原表指纹，再增量建表并切换；保留原配置、数据库、会话和依赖卷。`trainingListLikesProtocol: 1` 表示表已就绪。2026-10-27 已按用户授权部署 1.2.4，并核对原数据、配置与依赖卷。

## 1.2.3 公开头像与经验进度（已部署）

迁移 `mysql/009_public_avatars.sql` 新增公开头像表；`publicAppearanceProtocol: 1` 表示支持此能力。`PUT /v1/profile` 接受有界的 `avatarData` 和公开经验进度；榜单仅附头像 SHA-256，已登录用户通过 `GET /v1/avatars/:userId` 获取图片。删除头像提交空字符串，旧客户端不带新字段时保留原公开数据。私有账号快照继续隔离。

发布使用 `scripts/prepare-account-sync-runtime.py` 生成固定提交的运行包，`scripts/deploy-public-profile.sh` 在线备份并比较原表数据后执行迁移及切换。2026-10-26 用户明确确认后已完成部署：在线备份、停写后原表指纹、配置/依赖卷核对及公网 HTTPS 健康检查通过，备份已下载并校验。运行包来源为 `751105f427b5cd59ef2585242aefd0ef07d53f05`；生产数据与具体统计保留在私有运维记录。

1.2.3 于 2026-10-26 备份并核对原有数据后切换；当前源码与后续部署见本页首节。生产切换须完成下述备份、增量迁移与核验；实际运行版本以 `GET /v1/health` 为准。以下旧版本部署记录保留为历史。

## 1.2.2 按排行榜周期统计爱心

日榜只统计北京时间当天收到的爱心；周榜从周日开始；总榜保持累计。点赞回执保留旧字段并添加三种周期计数，旧客户端继续可读。无新增表、字段或同步协议变更。备份与切换沿用下述流程，运行时文件名和目录版本使用 1.2.2；公网健康接口已确认 1.2.2 / 协议 1，原表指纹、账号/快照/成绩、配置和依赖容器保持，备份已下载并校验。

## 1.2.1 今日爱心与兼容升级

1.2.1 增加 `todayLikes`，按北京时间统计当天收到的爱心；累计总数和旧 DTO 保留。沿用 `mysql/008_social.sql`；先备份原 MySQL，再对同一数据库应用幂等建表并更新 API，不能重新建立数据卷或覆盖用户库。新部署会按初始化目录顺序包含此文件。`socialProtocol: 1` 表示两个互动表可用；缺表时旧登录、排行和学习快照继续服务，客户端隐藏互动入口。详情见[工作台开发记录](../../docs/workbench-update-20261020.md)。

已具备 001–007 的生产实例使用 `scripts/deploy-social.sh`，不再使用旧的 `deploy-account-sync.sh`。先固定并公开源码提交，再从干净的对应提交准备运行时：

```sh
python server/leaderboard/scripts/prepare-account-sync-runtime.py --output /path/to/empty-output --source-commit FULL_40_CHARACTER_COMMIT
```

准备器核对 HEAD、服务目录无未提交变化、package 与 lock 版本一致，并将源码提交写入 `BUILD-INFO.json`；产物包含生产依赖、008、审计工具和逐文件 SHA-256 清单。上传 `TB-account-service-1.2.1.tar.gz` 后核对整体 SHA-256，在原 `/opt/tb-leaderboard` 内解包，保持服务器现有 `.env`、所有 compose 覆盖文件、密钥、Caddy 配置及持久卷：

```sh
cd /opt/tb-leaderboard
sh runtime.next-1.2.1/scripts/deploy-social.sh runtime.next-1.2.1 FULL_40_CHARACTER_COMMIT
curl --fail https://47.82.84.74/v1/health
```

脚本在线执行 `mysqldump --single-transaction` 并校验压缩文件，私有保存配置与依赖容器/卷绑定；短暂停止 API、等待在途请求完成后，只执行 008 的幂等建表。`audit-preserved-data.mjs` 在只读一致性事务中核对既有用户、账号、会话、完整学习快照、官方/历史 AC、昵称、登录日、管理及 XP 奖励等 15 张表的记录数、所有字段的 SHA-256 行指纹聚合，并单独记录快照字节、修订号和奖励 XP 总额。只有新加且为空的两张社交表允许出现；已有社交数据必须完全一致。证据只包含聚合指纹，不输出身份、源码、快照正文或凭据。

冻结前后指纹在新 API 接受请求或启动奖励结算之前比较，避免把之后正常用户同步当作迁移改动。通过后才切换运行时并以 `--no-deps` 启动 API，验证 `version: 1.2.1`、`socialProtocol: 1` 与原同步协议；再次确认配置字节、MySQL/Redis/Caddy 容器及卷绑定均未变化。不重建或重启数据库、Redis、代理，不覆盖自定义代理配置。公网 HTTPS 还须独立只读核验。

失败自动恢复旧运行时并启动原 API，保留原数据库、新增表及所有已接受的用户写入；不会把旧 SQL 备份自动覆盖到现有用户库。私有恢复材料与部署证据在 `backups/deploy-social-1.2.1-时间/`，数据库备份位于 `backups/mysql-时间.sql.gz`，部署后须复制到服务器外的受控位置。健康检查不创建测试账号、留言或爱心，也不替代用户正常登录后的跨设备同步验证。

`GET /v1/social` 返回本人的爱心总数、最近 100 条私密通知及公开爱心动态。`POST /v1/social/likes` 接收 `targetId`，北京时间每天一次，不提供取消；`POST /v1/social/comments` 接收 `targetId/text/requestId`，留言 1–500 字并按 UUID 幂等；`POST /v1/social/read` 接收 `{ids:[…]}`（最多 100 个本人通知 ID）或 `{all:true}`（当前收件人的全部未读），二者不可混用。所有接口要求现有账号会话，写入事务再次验证会话。公开动态不包含留言正文和通知已读状态。

## 1.1.2 迁移

共享服务 1.1.2 增加昵称唯一性和按版本恢复快照，同步协议仍为 1。注册、改名事务预留 NFKC、空白与小写归一后的昵称；冲突返回 409，整笔资料更新回滚。

既有部署先运行数据库备份，再停 API，应用 `mysql/007_unique_nicknames.sql`，通过同一数据库配置运行 `node scripts/migrate-nicknames.mjs` 后启动新版。预检发现已有重名时中止，不自动修改昵称、账号或登录号。`scripts/deploy-account-sync.sh` 已包含这一步及失败回滚。迁移只增加表，不替换原 MySQL 或卷。

`GET /v1/accounts/state` 可带 `X-TB-State-Revision`。有效会话且版本一致时返回 `{revision,unchanged:true}`，不读取大快照；其他情况保持完整响应。客户端须先确认本机摘要等于已同步基线，才能使用小型确认。旧客户端不发送该头，行为保持兼容。健康检查新增 `nicknameUnique:true`、`stateResumeProtocol:1`。


以下为 **1.1.0 历史部署记录**。2026-10-16 公网 HTTPS 健康检查已确认当时的服务升级。1.1.0 增加排行榜公开成长摘要与稳定公开 ID，数据库、账号同步和排行榜继续共用原服务器。

1.0.20 的账号学习数据以服务端 MySQL 为权威版本，本机 SQLite 作为耐久工作副本与待同步日志。训练、提交源码与官网回执、草稿、模拟赛、目标及固定题单、首通经验、每日领取、成就奖励、排位解锁、排行榜奖励账本和收藏/筛选等账号偏好随账号同步。CF/AtCoder 的公开用户名与已读取的公开证据同样随账号迁移；Cookie、浏览器会话、翻译密钥、机器路径和本机安装设置不会上传。服务使用 Docker 部署 Node.js API、MySQL 8.4、Redis 8.4 和 Caddy HTTPS，Redis 当前尚未用于 API 缓存。生产数据保存在 MySQL；SQLite 仅用于测试和快照转换。

2026-10-16 13:51（北京时间）在已有 `005` 的原排行榜服务器完成 `006_public_progress.sql` 增量迁移，继续使用原 MySQL 数据卷及原 compose 覆盖配置。公网 HTTPS 健康检查确认 `version: 1.1.0`、`accountStateProtocol: 1`、`singleSession: true`、`publicProgressProtocol: 1`。在线备份已下载并核验；此次迁移前后 143 个身份、3 个账号、164107 条官方 AC 记录及其指纹、4 笔共 400 XP 的排行榜奖励和 3 个会话完全一致。账号快照及登录日期各保留 1 条，同账号多会话为 0。新建公开成长表初始为空，等待客户端正常上传；没有制造测试用户或提交。真实账号快照上传和跨电脑恢复仍须以实际登录后的同步状态核验，服务健康不能替代该验证。

个人库还保存本账号已训练、保存草稿、提交、加入模拟赛/练习题单/目标题单的题目事实：轻量题目元数据、原题链接、已缓存题面与样例，必要时包括本机导入题的两版题解与嵌入图片。另一电脑没有原题库 ID 时使用这些账号事实继续显示和练习。不会复制整套公共题库或未被当前账号引用的其他导入内容；原始文件路径不进入快照。仅引用题目集合、题库数据库/WAL 或公开同步批次变化时重新采集，平常心跳不扫描整库。

从 0.10.4 起整个软件要求登录。注册填写昵称、登录号和密码；注册成功后另行登录。旧安装凭据只能用于一次性关联原身份、成绩、奖励与管理员角色，不能继续作为登录凭据。账号允许验证旧密码后修改密码，不提供找回密码。安装包不包含用户身份、凭据或个人数据库。密码使用 scrypt 随机盐摘要，会话只保存 SHA-256 摘要；本机会话凭据使用 Windows DPAPI 保护，详见[账号说明](../../docs/accounts.md)。

日榜按北京时间当天计算，周榜从周日开始，总榜统计全部不同题目。同题重复通过、运行和样例通过均不增加排名。当天登录或恢复有效登录的注册用户会进入榜单，即使过题数为 0；此前已有该周期成绩的用户照常保留。零题用户不会领取空名次奖励。界面展示昵称。客户端报告已经持久化的原站 AC 回执，按原题只计最早一次；旧本地审核成绩不参与官方排名。未注册的旧身份暂不参与新排行榜，原记录继续保留。服务暂不进行独立原站防作弊复核。

## 1.0.20 同步上线

先部署共享服务，再向客户端分发 1.0.20。新客户端在登录返回前完成账号数据读取、旧本地数据安全合并及版本确认；同步失败停留在登录界面，不先展示空账号。首次合并按各表主键去重，奖励按同一领取键取已领取值，不累加重复经验；草稿等冲突版本保存于账号的 `account_sync_conflicts`，本地应用远端版本前使用 SQLite 在线备份。同步基线保存逐行摘要，远端未改时保留本机尚未上传的编辑或删除，双方均修改时保留冲突版本；后续客户端按版本号 CAS 保存，删除不会因重启重新混入旧副本。网络失败保留本机日志，明确显示待同步，后台重试；退出账号前必须完成上传。

每次登录在账号行锁下撤销旧会话，再签发一个新会话；修改密码也撤销旧令牌。已认证但迟到的旧设备保存仍在事务内重新验证令牌，不能覆盖新设备数据。客户端后台每 3 秒检查会话；同一账号在另一台电脑登录后，旧设备的下一次心跳收到 401 并退出工作台。离线时不能保证实时获知另一设备登录；本机未上传记录保留，下次登录合并。

已存在云端学习版本的账号拒绝不带 `X-TB-State-Protocol: 1` 的旧客户端登录，返回 426 并要求升级，防止旧版本继续仅保存在某一台电脑。迁移前的旧账号仍可升级并带回原身份。新部署须挂载 `mysql/005_account_state.sql`；已有数据卷必须手工执行迁移，不重新创建数据卷。

## 1.1.0 公开成长资料升级

生产使用 `/opt/tb-leaderboard/runtime` 的只读运行时挂载。从已经具备 005 迁移的 1.0.20 升级，仅执行幂等 `mysql/006_public_progress.sql` 新建小型摘要表；账号、云端快照、原会话与历史过题数据不重写。新部署的 Compose 初始化目录包含 001–006 六份迁移。

在开发机准备独立 `runtime.next-1.1.0`：包含 `src/`、`mysql/`、`scripts/`、`Caddyfile`、两份 package 文件、仅生产依赖的 `node_modules/`、逐文件 `runtime-manifest.sha256`：

```powershell
python scripts/prepare-account-sync-runtime.py --output /path/to/empty-output
```

打包器拒绝密钥文件、SQLite/DB 文件、`.env`、私有目录、符号链接与本机二进制扩展。公开运行时须可被容器 node 用户遍历与读取。保留服务器现有 `.env` 及小内存、恢复卷、CPU、runtime 等全部 compose 覆盖文件；实际持久卷 `tb-leaderboard_mysql_data_swap_enabled` 保持原样。上传 `TB-account-service-1.1.0.tar.gz`、核对 SHA-256 并解包后，从 `/opt/tb-leaderboard` 执行：

```sh
sh runtime.next-1.1.0/scripts/deploy-account-sync.sh runtime.next-1.1.0
curl --fail https://47.82.84.74/v1/health
```

脚本先检查旧库已存在账号快照与登录日期表，再用现有备份脚本在线导出 MySQL 并私有备份代理配置。停止 API 后仅执行 006，替换运行时并检查 `version: 1.1.0` 和 `publicProgressProtocol: 1`。启动使用 `--no-deps`，避免重建 MySQL 等依赖容器或改变实际持久卷。

现有 Caddy 已支持账号快照 PUT 4194304 字节、其他请求 65536 字节时，不改写或重新加载代理配置。只有与已核对旧模板完全相同（允许 CRLF/LF 差异）的配置才会自动更新，未知自定义配置在改动前拒绝执行；需要更新时保留原 bind mount 文件并 validate/reload。任一后续步骤失败恢复旧运行时和必要的代理配置；新增表与 SQL 备份保留。升级后还须核验公网 HTTPS，服务健康检查不代替真实用户登录同步。

脚本不打印密码、不删除卷、不修改账号或历史 AC。部署成功后将 MySQL 备份复制到服务器外的受控位置。服务状态检查不创建用户；真实登录测试仅在用户正常使用时进行，开发回归必须使用隔离服务。

`account_public_progress` 每个账号只保存一份有界摘要：等级、成长段位、TB 排位段位与分数、自动佩戴的最高 AC/连续训练称号各一枚。客户端通过已认证 `PUT /v1/profile` 更新，仅在摘要改变时上传；旧服务未声明 `publicProgressProtocol: 1` 时保持旧同步流程。请求校验允许字段、字符数、整数范围、称号类别和数量，事务内再次验证当前会话，另一设备登录后的迟到写入会返回 401。摘要来自客户端已有成长计算，不新增防作弊认证。

榜单查询通过 JOIN 读取小摘要，不读取或解压用户源码快照；单次排名聚合同时返回前 100 名和本人（最多 101 行），避免每个周期重复扫描历史。未上传摘要的旧客户端账号显示“成长资料待同步”。公开 ID 为 `TB-` 加内部 UUID 的 32 位大写十六进制形式，昵称修改或设备更换均不改变，不使用登录手机号/登录号。当天登录且零 AC 的账号仍显示，但不授予前三名奖牌或 XP。

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

v0.10.1 沿用 v0.10.0 引入的官方 AC 协议，身份注册、昵称更新和日周总榜接口保持兼容。新版客户端补传本机已保存的原站 AC 回执；空榜也可能表示没有可上传的官方回执，不代表身份丢失。

## 备份与维护

```sh
sudo sh scripts/backup.sh
sudo docker compose ps
sudo docker compose logs --tail=100 api
```

备份脚本用 `mysqldump --single-transaction` 写入 `backups/`，成功后压缩；包含用户身份资料，不能公开提交。部署后将备份复制到服务器外的受控位置，并使用独立数据库做恢复验证。容器设置自动重启、健康检查和日志轮转；日常重建容器保留数据卷。不要使用 `docker compose down -v`，它会删除数据库和证书卷。

## 服务接口

健康检查、注册和登录以外的请求均携带 `X-TB-User: UUID` 和 `Authorization: Bearer 登录会话令牌`。1.0.20 同时携带 `X-TB-State-Protocol: 1`。会话三十天过期；新登录原子撤销该账号全部旧会话，退出撤销当前会话，修改密码撤销全部旧会话并签发当前设备的新会话。请求体只接受规定字段，普通接口最多 64 KiB。账号快照由客户端按白名单导出，使用 gzip 和 base64 封装，SHA-256 校验原始 JSON；压缩请求最多 4 MiB，展开最多 64 MiB。服务端保存压缩快照而不在 64 MiB Node 堆里展开，每次只处理一个大状态读写；其他客户端稍后重试。客户端限量展开、校验摘要和表白名单后才应用。小于 64 KiB 的明文白名单状态仍用于接口兼容和隔离测试。超限保留本机数据并明确报错，不截断记录。

| 接口 | 请求 | 返回 |
|---|---|---|
| `POST /v1/accounts/register` | `{loginId,nickname,password}` | `{account}`；不自动登录；旧凭据可在头部用于一次性关联 |
| `POST /v1/accounts/login` | `{loginId,password}` | `{account,token,expiresAt}`；令牌只交给本机后台 |
| `GET /v1/accounts/me` | 无 | 当前注册账号 |
| `GET /v1/accounts/state` | 无 | `{revision,state}`，仅当前账号可读 |
| `PUT /v1/accounts/state` | `{revision,state}` | 保存整个账号白名单状态；返回 `{revision,savedAt}`；旧版本 409、撤销会话 401 |
| `POST /v1/accounts/logout` | `{}` | 撤销当前会话 |
| `POST /v1/accounts/password` | `{oldPassword,newPassword}` | 验证旧密码并撤销全部旧会话，返回新会话 |
| `GET /v1/profile` | 无 | 当前身份、昵称、公开 ID、`publicProgress` 与能力标志 |
| `PUT /v1/profile` | `{nickname?,publicProgress?}`，至少一个 | 更新自己的昵称或成长摘要；只传旧 nickname 字段仍兼容 |
| `POST /v1/events` | `{events:[{eventId,problemKey,acceptedAt,difficulty,scope:"official"}]}` | `{processed,scope,notice}` |
| `GET /v1/leaderboard?period=daily` | 周期 `daily`、`weekly` 或 `total` | `{period,date,timezone,entries,self,notice}` |
| `GET /v1/rewards` | 无 | 当前身份的累计排行榜经验与最近 50 条奖励 |
| `POST /v1/admin/leaderboard/delete` | `{userId,period,confirmation:"delete"}` | 管理员删除所选成绩；`userId:null` 清空所选周期 |

每批最多 100 条通过记录。`problemKey` 是原题规范化链接的 SHA-256 摘要；`eventId` 是身份和原题摘要的 SHA-256 摘要。排行榜事件接口不发送题目代码、草稿、测试数据、翻译 API Key、原站 Cookie 或密码。账号状态同步接口单独保存用户要求同步的源码、草稿与学习记录，排行榜响应不会泄露这些私有数据。记录按用户和原题唯一，重传不会增加题数；异步评测导致更早的通过记录稍后到达时，服务修正到更早日期。

本机接口为 `GET/POST /api/profile`、`GET /api/leaderboard?period=daily`、`POST /api/leaderboard/sync`、`GET /api/daily-tasks` 和 `POST /api/daily-tasks/claim`。每日任务领取和奖励先在本机 SQLite 事务中保存，再写入账号云端状态；重传不重复领取。

## 奖牌与排行榜经验

日榜、周榜、累计榜各有三种专属奖牌，档次依次为累计第一、累计第二、累计第三、周榜第一、周榜第二、周榜第三、日榜第一、日榜第二、日榜第三。前三名为三个独立席位，同题数先完成者排在前面，完成时间也相同时按固定用户 ID 排序。

按北京时间每天 0 点结算前一天，前三名分别获得 100、60、30 XP。每周日 0 点结算上一周，前三名分别获得 500、300、150 XP。周榜周期为周日 0 点到下周日 0 点。累计榜仅授予当前奖牌，不额外发放经验。用户没有成绩时不分配空名次。

服务使用数据库事务保存结算游标、周期快照与奖励，重试、并发查询和服务器重启都不会重复发放；停机期间未结算的完整周期在恢复时补结算。启用功能时从当前日和当前周开始，不追溯以前已结束的周期。晚同步的成绩可以更新排名，但不改写已经结算的奖励。客户端定期同步服务器奖励总额，在本机按服务器地址和身份保存，刷新和重新打开不会重复累加。客户端关闭时服务器照常结算。

升级现有服务须先备份 MySQL，再按顺序应用未执行的迁移，包括 `mysql/004_accounts.sql`、`mysql/005_account_state.sql` 与 `mysql/006_public_progress.sql`，随后更新 `src/` 并重启 API。新部署由 MySQL 初始化目录执行六份迁移。旧 `/v1/profile/register` 返回 410，提示升级并注册账号。

## 管理员删除

管理员由运维直接在 `ranking_admins` 表中授予已注册的用户 ID。客户端不能通过请求字段、昵称或界面设置提升权限；删除请求仍须验证该身份原有的安装凭据。本机转发接口为 `POST /api/leaderboard/admin/delete`，继续要求本机会话令牌和同源校验。

管理员可删除某个用户当前周期的成绩，或清空当前周期。累计榜的操作涵盖所有时间。删除以原题为单位保留标记，三个榜单同步扣除相应题目，重传旧成绩不会恢复；未来首次通过的新题仍能计分。操作写入审计表，已发放经验保留。身份、官方回执证据及用户本机的训练、代码和草稿均保留。

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
