# 应用闲置、关闭与原生网页输入

独立源码候选，以 `72866bd8fe93a382cf7f0c2e40813fd60ac9aa36` 为基础；没有修改冻结的 112/main、93 producer、既有 dist、VERSION、正式程序或个人状态。未部署共享服务。清理检查先于 worktree 建立：确认可清理项 0，现有 r1/r2 运输、恢复与基线证明继续保留；原始检查记录位于 `整理记录/20261109-在线状态/presence-cleaning-before-worktree-145859394238.json`。

应用仍打开但五分钟没有真实操作时，显示红色“离线”；没有打开、已确认退出或 presence 租约过期时，显示原灰色“离线”。在线人数继续只计算活跃用户。原有 DOM 鼠标、键盘、滚轮、触摸和同源阅读 frame 的可信输入机制保留，程序化聚焦、导航、轮询与心跳不更新真实输入时钟。

服务继续复用 `account_presence`，不改变表结构或学习记录。`users` 与 `count` 保留旧版的 active-only 含义；可选增加 `idleUsers`，只含已有公开 userId 和固定 `idle` 活动。过题榜与排位榜条目增加 `idle` 布尔值。旧客户端忽略新字段即可保持原有统计协议；新客户端只有 `online:false,idle:true` 使用红色，普通 `online:false,idle:false` 使用原灰色。查询失败仍沿用原有 unavailable/未知计数行为。

客户端明确关闭时发送既有 presence POST 的 `activity:'offline'`。它经过原有会话鉴权，只允许相同 token 关闭现有 presence。用原来的单行保存 offline marker，并比较服务请求时刻，避免先前已在途的旧心跳在关闭后重新制造在线状态；正常重新打开后的新心跳仍可恢复。记录不含新增个人内容，不注销账号，也不改登录保留。

原生关闭仍先经 `CloseCoordinator` 的本地草稿/偏好保存屏障。只有保存全部成功后，才发 `tb-desktop-closing`；保存失败与普通 `tb-before-update` 保存不会发关闭状态。小型 offline POST 使用 keepalive，但不加入本地保存等待，不因共享服务不可达阻塞退出。pagehide 提供后备路径；如果退出前网络不可用，远端仍按既有 90 秒租约到期后恢复普通离线。

DeepSeek 子 WebView 与 DOM 分属不同控件，不能让网页 CustomEvent 自称可信输入。与其 native host 分支锁定只读接口：

```json
{"available":true,"session":"process-owned-opaque-id","revision":1,"observed":true,"ageSeconds":0.25}
```

`GET /api/desktop/input-activity` 由 native host 维护，读取仅锁内存，不触发账号恢复、同步或活动写入。native sampler 只有在本 ToBe 主窗或其 owned 登录窗内的真实、未注入输入时推进 revision；键盘需属于前台 root owner，鼠标需命中本窗，导航与聚焦不推进。接口不返回或保存按键、坐标、题面、代码、聊天、cookie 或日常浏览器资料。native 实现与本分支分工，不从网页建立输入自报通道。

前端验证 session、非负安全整型 revision、observed 与有限非负 age。只有新 session 的实际观测或同 session 递增 revision 可以推进输入时间；回退、重复、坏值和旧账号/已清理 observer 的迟到回执均不能推进。使用“采样请求开始的单调时刻 − age”保守回填，与可信 DOM 输入取较新的值，不能把每次轮询返回时刻当作新输入。可用 native 采样每秒只读一次；旧或非 native 后端退回原有 DOM 输入，并以较低频率探测。普通 presence 网络心跳仍是原来的 25 秒，idle 前也会共享一次只读采样，原生真实输入从 idle 恢复时才立即补心跳。

验证已在 root 的 112 真实更新计时与 15 DB 核验结束、明确恢复测试后执行：共享服务全套 162 项中 160 通过、0 失败，2 项原有独立 MySQL 条件测试跳过；presence 浏览器回归通过，包括 active-only 计数、红 idle / 灰 closed、同账号新会话不被旧会话关闭、迟到旧心跳不能复活关闭状态、真实 DOM/阅读 frame、native DTO counter 重复/回退/坏 age、普通保存与最终关闭、keepalive、账号切换和迟到响应。真实 hidden WebView2 关闭检查通过，保存失败没有发最终关闭信号，成功保存后正常关闭。原生物理输入正向没有被自动证明；本分支验证了 DTO consumer，native hook 实装与注入过滤由 DeepSeek native 分支提供，不能把该 fixture 回归当成真实硬件或触摸输入实测。

同批用户反馈已完成：比赛对战/排位中右上重复“匹配中＋时间”移入头像下已有匹配取消框。只移动现有 elapsed 组件，沿用服务 queuedAt 与原计时，不新增常驻框，保留取消、找到对手及 ready 通知；旧顶框 timer 样式不再使用，改由原队列框 timer 使用。按既有 React fixture 与真实 loopback HTTP 服务操作检查，确认切页后同一 queuedAt、只有原取消框内一个计时、取消仍生效、ready 阶段仍隐藏题目；宽窄和找到对手截图已核对。原思维对决 UI 全流程也通过，裁判是隔离 fixture，不能冒充真实 AI 服务或正式比赛提交。没有为该布局增加镜像计时实现。

前端本地生产构建通过（11.35 秒，2483 modules），仅写独立 worktree 的 dist；不作为冻结 93 / 112 的 producer 或正式发布产物。VERSION 未变，无正式包、tag、服务或 stable 更新。验证截图、日志、队列操作结果与构建日志 SHA 记于同目录 JSON 回执；所有测试均为隔离假账号或本机测试窗口，普通 ToBe、真实个人库与日常浏览器 profile 未触碰。
