# Presence 实例租约与快速重开回归

基于 731f6d04 的独立 fix/presence-lease-20261110，未改 root 工作树、普通安装、VERSION、生产配置或生产数据。先完整重读 391 行设计理念与 AGENTS，核对现有引用、表字段与缓存用途；本范围没有可安全额外删除的旧数据或产物，保留既有回执。只在分支设计镜像追加明确反馈，全局设计由 root 同步。

## 协议与持久化

复用 account_presence 的四列，不新增 DDL。activity 存 base~leaseId：最长现有活动 8 字符、分隔符 1、服务器随机 8 字节的 base64url ID 11 字符，最大 20，符合现有 VARCHAR(20)。token_hash 仍是真实账号 session hash，原 JOIN/过期验证保留。公开 active/idle/closed 视图全部先解码，永不公开 packed 值或租约凭证。

prepare 只读生成 owner/auth/expected-version 绑定的 HMAC ticket，沿用服务器已有 RATE_LIMIT_SALT，不新增 key/config。activate 按原版本 CAS；beat/close 只作用于当前 lease。close 可先写同 lease 的 offline 墓碑，晚到 activate/beat 和重复 close 不复活或延长墓碑。MySQL 沿用 game.session 对账号行的锁，SQLite 沿用原串行事务。无客户端时间字段；未来时间输入拒绝。

客户端在同一账号/实例内保持 ticket，普通活动变化不重建；准备回执晚于关闭/账号切换则不再 activate。ticket 在 activation POST 前保存，关闭时可结束尚在路上的 activation。失去 lease 后，recover 只在当前持有者已关闭或过期时准备新 ticket，不会抢仍活跃实例。新实例重开可准备新 generation，旧回执不能覆盖它。

本机协议携带 presenceOwner，Python 在转发前按当前训练账号检查并剥除此字段；A 的旧 close 在本机已切到 B 时直接 409，不发给 B 的远程身份。服务器 HMAC 也绑定 owner 和 auth，同账号换 token 亦不能重放旧凭证。原站登录、浏览器扩展、快捷键 C loader 均未改；需要重新构建 frontend 和包含 backend.py 的 ToBe.exe。

## 旧客户端

已有 plain activity 行继续正常显示/处理。新 lease 或关闭墓碑的 90 秒保护期内，旧纯 activity 请求不能覆盖或刷新其 last_seen；旧 offline 永不清掉 lease。保护期过后，旧非 offline 心跳可以恢复为 plain 行，默认 25 秒心跳周期下通常不超过 115 秒加网络延迟，不会永久离线。TTL 用独立过期持久行 fixture 验证；乱序正确性使用真实接收顺序，不依赖 TEST_NOW。

## 验证与边界

- server-tests-final.log：11 PASS（8 个新 lease 场景与原 presence/duel 3 场景）。真实生产 HTTP adapter、SQLite 和前置网络屏障，验证同 token 旧 close/beat 后到、close 先于 activate、两 prepare、旧 activation、重复/墓碑、legacy 保护及过期恢复、所有公开视图、20 字符边界、签名篡改/跨 owner/换 token、真实数据库重启。真实请求顺序测试不设置 TEST_NOW。
- backend-relay-final.log：2 PASS。真实 Python Handler/gameplay relay 接入私有 Node fixture 的真实 HTTP API。租约字段保持；本机换账号后旧 close 在发送前拒绝，B 的 presence 行不变；legacy 仍可用，未知字段/客户端时间本地拒绝。Node fixture 账号 token 仅留子进程内存，不输出到日志。
- ui-owner-final.log：真实 React 回归 PASS，保留原五分钟真实 DOM/native-input、红闲置/灰关闭、active-only count、关闭与保存区分、晚回执、窄布局；新增 activity/navigation 固定租约、关闭后晚 prepare 不 activate、activation 在途时 close 使用同 ticket、晚 ACK 不复活、新 generation 重开及换账号晚 prepare。

原始日志在 .backups/presence-lease-20261110/，测试全部局限自有本地 loopback/fixture。server 数据库重启样本与失败日志保留；首次 Python IPC 测试失败为 Windows --loader 绝对路径格式，已改 file URI 并补 setup-failure cleanup。没有触碰历史被拒绝对象、用户账号/token、真实 AI、OJ、生产 heartbeat、SSH 上传、重启或 SQL。

初始 fba 部署稿保持 blocked。不能直接回退到不识别 packed 值的旧 reader；后续部署稿必须 pin 保留 decode/offline 过滤并拒绝 v2 写入的兼容降级 reader，或保留 v2 reader 的同语义修复回退。不得通过清理生产 presence 行绕过协议兼容。实际生产三账号闲置/关闭/重开与当前 Thought 的后验仍待 root 单独执行，本地回归不冒充已上线。
