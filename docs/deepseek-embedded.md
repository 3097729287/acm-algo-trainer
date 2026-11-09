# 单题左栏 DeepSeek

入口位于单题题面字号控件左侧。切换只隐藏原题面，原 `<article>`、滚动位置、语言和 CodeMirror 编辑器继续保留。网页使用同一 WinForms 窗口内的独立 WebView2 控件；没有 iframe，也不打开外部浏览器。

## 本机登录资料

原生端从当前已认证的 ToBe 账号上下文确定 owner。持久目录为 `cache/tb-deepseek-webview2/<SHA256(serviceEndpoint,userId)>/`，WebView2 profile 名为 `ToBeDeepSeek`，关闭 InPrivate。账号会话 epoch 参与临时控制能力校验，但不参与持久目录名，因此同一账号重新登录后仍沿用专用网页资料。目录拒绝 reparse/symlink 跳转，并限制为当前 Windows 用户访问。

用户在内置页面自行完成 DeepSeek 登录。程序不导入其它浏览器的 cookie，不自动填写或发送题面、代码、聊天内容。原生网页未暴露 pywebview host objects 或 WebMessage 通路。顶层导航限定 HTTPS DeepSeek 及其页面可见的 Google/Apple 登录站点；不允许任意本地地址、任意端口、`file:` 或带 URL 凭据的导航。下载不会交给外部程序。

`cache` 在现有旧版迁移/清理中属于个人目录，补丁只允许覆盖公共程序路径，Inno 安装和卸载也不登记此用户目录。`backend/test_compact_update.py` 添加了专用 Cookies 与 Local Storage 哨兵，覆盖成功、重复应用和失败恢复路径。这个网页目录属于登录资料，不能当作普通临时缓存删除。

## 窗口与请求边界

前端只发送 viewId、递增 sequence、当前原生 ownerKey、可见性、视口矩形及应用快捷键注册元数据；HTTP API 不接收网址、目录、题面或代码。原生端在 UI 线程再次验证 owner，拒绝旧会话、乱序与跨账号请求；旧隐藏页不能隐藏当前其它 view。快捷键的完整清单、上下文与原生队列边界见 `application-shortcuts.md`。

DOM 弹窗、搜索、学习页隐藏、切回题面、页面退出和 native 最小化都会隐藏原生控件。原生控件发生 resize/DPI 变化时先隐藏，收到新的裁剪矩形后才恢复。坐标按主 WebView 的实际像素与 CSS 视口比例换算，保留分隔线的实际鼠标拖动区域。若几何心跳中断超过三秒，原生端主动隐藏，避免覆盖其它界面。

`GET /api/desktop/deepseek` 与 `POST /api/desktop/deepseek` 沿用本机 Host、Origin/CORS、账号 barrier 和写请求 X-TB-Token 检查。网页账号控制能力由进程随机秘密 HMAC 生成，不是用户凭据。登录状态及网页进程均只在原生端管理。

## 原生活动与在线状态

`desktop/native_activity.py` 使用专门消息线程接收 Windows 低层鼠标/键盘 hook。键盘仅在本窗口或其 owned 登录窗口为前台时计入；鼠标仅在即时 OS 命中窗口属于本窗口树时计入。Windows 标记为 injected 或 lower-integrity injected 的输入均不计入。系统把主触摸/笔输入提升为未注入鼠标事件时沿用同一路径；本机没有触摸硬件，尚无物理触摸设备验收记录。

没有按键值、扫描码、坐标或网页内容进入持久状态或响应。`GET /api/desktop/input-activity` 只读取 `{available,session,revision,observed,ageSeconds}` 内存快照，没有 POST setter、账号同步或活动写操作。网页轮询、加载、focus 与合成 DOM 事件不能推进 revision。presence 分支负责按实际输入 age 合并这个计数；仅合入本分支不会单独改变现有 presence 策略。

## 已完成的隔离验证与边界

- `.backups/deepseek-native-20261109T143518Z-f9299ea6/result-seed.json`、`result-verify.json`：两个独立进程中自有站点 cookie/localStorage 均保留，另一个账号隔离；同窗 native child、resize、125% 缩放、最小化隐藏与代码保留通过。该 case 后续真实站点阶段失败，整体失败回执保留，不能把整体当作通过。
- `.backups/deepseek-native-20261109T144622Z-eea4fcef/result-real.json`：真实公开 DeepSeek 页面实际显示输入框、密码框与登录入口；原生截图 SHA256 为 `c3f4732c24e3ce504b2bf9ce30ca9efb16022ec4b356c551b9a5e31f33587e82`。正常浏览器流程由 HTTP 202 进入 200；实际响应包含 `frame-ancestors 'none'`。没有登录或发送聊天。
- `.backups/deepseek-ui-1794236279085/result.json`：真实 Workbench/CodeMirror 的入口位置、同一编辑器实例、代码、题面 DOM/滚动/语言，以及弹窗、搜索、切页、分隔线、视口调整均通过，0 page error。该测试明确 mock 原生 API，不能代替原生网页实测。
- `.backups/deepseek-native-20261109T155849Z-1b38bfca/result.json`：收紧 URL/目录权限及加入错误恢复后的两个本地原生进程均通过；真实 child HWND 分支、账号隔离、重启持久化、125% 缩放、最小化和代码保留验证通过，seed 阶段故意只崩溃所属测试 renderer 后成功重建。OS 未授予测试窗前台，实际注入检查明确跳过；命令状态机的输入明确为内部 synthetic fixture，未声称真实硬件正向通过。
- `.backups/deepseek-ui-1794239578832/result.json`：扩充后的实际 Workbench 专项通过，0 page error，覆盖字体输入/按钮/CodeMirror/题面/body 焦点、single-flight、保存失败、native DTO 去重和旧注册版本拒绝。原生 API 明确 mock。
- 28 项原生边界、真实本地 HTTP、快捷键队列和 compact 更新保全检查通过，68 个快捷组合模型检查通过；已有 Workbench 长回归通过。生产 build 通过，但此测试 dist 不作为集成候选 producer，集成后须按最终源码重建。
- `frontend/.backups/shortcut-fullapp-1794241844264/result.json`：当前源码的真实 FullApp 窄 probe 通过，0 page/console error；明确使用隔离 mock API，覆盖账号 Ctrl+J 覆盖、原 Ctrl+Right 不被劫持、输入框先保存再下一题、全局命令弹窗在 inert 学习层之上可输入、Escape 只关弹窗、F6 活动面板、Ctrl+B、Ctrl+F 及 Ctrl+2。复用既有匿名 UI profile，没有新建大 profile，没有生产/OJ 请求。
- 旧 `.backups/deepseek-native-20261109T155703Z-c0697bbd` 的 seed 末尾 `codePreserved=false` 未被早期 harness assert，尽管 raw `ok=true`，仍作废其整体通过声明；保留原始回执。之后改用结构化代码状态并硬断言，最新 case 的两个阶段均为 `codePreserved=true`。

所有实际窗口使用 E 盘新建隔离 profile。既有普通 ToBe、普通账号数据库、默认浏览器会话、112 已冻结源码与产物均未操作。保留早先失败回执，未以 title 或 NavigationCompleted 代替实际可用页面判断。自有站点的持久化验证证明了机制；没有声称已经替用户登录 DeepSeek。

相关官方说明：[WebView2 用户数据目录](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/user-data-folder)、[pywebview API](https://pywebview.flowrl.com/api/)、[LowLevelMouseProc](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelmouseproc)、[Windows 笔/触摸的鼠标兼容消息](https://learn.microsoft.com/en-us/windows/win32/tablet/system-events-and-mouse-messages)。
