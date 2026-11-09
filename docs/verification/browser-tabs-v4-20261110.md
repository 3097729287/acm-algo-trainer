# 常用浏览器纯标签页连接 v4

本轮只在独立 `fix/review-latest-ac-20261109` 分支修改；未改普通安装、用户数据库、默认浏览器配置或 VERSION。完整重读全局设计理念（当前 385 行）和 `E:/项目/AGENTS.md`，全局设计文件由主代理维护，本分支仅追加明确的新反馈。

## 清理核查

先核对 launcher、worker、协议、题面读取、VP、打包及 CI 引用。以新 worker 原位替换旧 Cookie 读取/导出与混合传输流程，manifest 移除 cookies 权限，不再打包旧 pair/passive/login-state 脚本。旧 `/api/browser/session` 在解析请求体前返回 410，旧 protocol 2/3 注册被拒绝；生产 launcher 移除独立 Edge 登录预热。当前 CI 和 `test:browser-official` 改验纯标签页 v4，移除旧 Cookie 导出验证的 CI 步骤和两个废弃 hybrid npm 入口；历史源码与回执仍在 Git 历史中，仍有单测引用的旧模块不删除。

没有另行删除磁盘文件、个人登录资料、源码、草稿或历史提交。测试复用已有自有纯测试 profile；只对自有公开 fixture bundle 做逐版保留副本并刷新，不复制浏览器 profile，不修改 Preferences。新交付目录只含 12 个公开静态文件，没有凭据、账号状态、Cookie 或浏览记录。

## 行为

单次任务固定到已连接的一个 browser client。页面由 extension 创建为非活动后台标签页，只静音该标签页；登录或验证码才激活并前置。原生表单的语言、代码、验证与 CSRF 仍由网站处理。派发前与真正点击前的 checkpoint 都重查原账号/比赛授权，捕获的团队授权跨线程保留。已尝试提交后不因旧消息、断线或重连重发。

原站本次 SID 的正式结果持久化且工作台已实际显示对应记录、经过绘制确认后才关闭自建页；手动页面保留。新连接不可读取旧账号的任务能力。题面和 VP 同样走固定的常用浏览器通道，无 JavaScript 文本执行接口；仅内存传递经裁剪的题面 DOM，按块受 4 MB 总量限制。

旧牛客 pending 仅按原 SID、题目、题型、历史 owner、不可变 observer closure 中的源码摘要及语言恢复。旧专用页面已退出登录时，可验证其历史 closure；在新常用浏览器中还必须核对同一 fresh owner，才接受原 SID 终态。旧证据不足保留 pending。没有直接操作用户的三笔历史记录，没有声称用户记录已自动恢复。

## 验证

- `python -m unittest test_connected_browser -v`：最终 26 项全过，包括真实训练服务 team guard、真实 SQLite 重启、旧页面 logged-out 与新 owner 匹配/不匹配、慢表单期间点击前重查、并发消息只派发一次、SID 不串、未配置公开账号时固定首个验证 owner、非 AC 结果、显示 ACK、受限题面分片与 VP owner/命令去重，以及真实生成模拟已组装包后的 frozen 路径及缺件边界。
- 另一次广泛回归命令包含 `test_connected_browser test_team_native_guard test_official_pending_recovery test_nowcoder_receipts test_browser_bridge test_original_virtual_bridge test_private_contest_reading`：当时 76 项全过；随后新增的五个边界在上述最终 26 项中通过。
- 真实 Edge + 真实 extension worker，所有站点响应拦截为本地 fixture：五个平台原生表单、后台 active tab 不变、仅自建 tab 静音、保存后等 ACK 才关、manual 保留、仅 login focus、分片和固定旧 SID GET 恢复、实际 connection 页面全部通过。生产原站网络请求、真实登录和真实提交均为 0。
- 真实 React/CodeMirror 五场景通过：隐藏 CE 不 ACK、同判定旧历史行不 ACK、别题后台完成不 ACK、manual 不 ACK、重启恢复原 SID 保留当前编辑器。新增异步 `displayAcknowledged` 返回后不重复 ACK；pageErrors 为 0。

原始日志保留在本树 `.backups/review-latest-ac-20261109/`：`connected-v4-unit-final-26.log`、`connected-v4-regression-1.log`、`connected-v4-ui-final.log`；worker 成功原始回执为 `connected-browser/1794246174991/result.log`，UI 为 `official-result-ack/1794246349306/result.log`。

早先夹具失败日志也保留：第 2–4 轮因测试 profile 沿用旧 unpacked 路径及 worker 缓存而未连接新 fixture 端口；第 5 轮仅因 fixture 路由误阻止自己的 connection.js，前面平台场景已完成。随后保留旧公开 bundle、副本并显式重载本测试扩展、允许其本地静态资产后，第 6 轮全过。未切换到默认浏览器或对真实站点绕行。

## 交付与集成

已生成可直接手动加载的完整目录：`E:/项目/ToBe/浏览器扩展/ToBe-Session-Bridge-20261110`。固定 ID 为 `blgkmkjbdekeoenepgnajpeafofccbjm`，权限只有 storage/alarms；扩展图标打开 `connection.html` 检查真实本机连接。应用入口收在右上角账号设置的“浏览器连接”。用户需在自己的 Chrome/Edge 扩展页开启开发者模式并加载此完整目录；程序不自动安装、启用、切换浏览器策略或复制登录资料。已有 unpacked 扩展需要手动 Reload 或停用旧项后加载本次目录，不能认为换 CLI 路径自动更新。

`build_release.py` 生成 `browser-extension/` 并由原 release manifest 纳入所有文件；SOURCE manifest 的 desktop 递归扫描也包含新增源码。`compact_update.py` 原 allowlist 已允许该前缀，本轮未改缓存上限、166–112 基线或 public-library 组合策略。主代理仍需在 113 总装时统一扩展版本并执行七基线/32 MiB 上限验收；本分支不声称已做总装验收。

frozen 入口直接使用已组装的 `APP_DIR/browser-extension`，不读取 `browser_extension` raw 源目录、不运行 build、不再次串接 official/identity。测试先真实生成 12 文件的模拟安装包，切换 frozen/executable 到该包，禁止 builder 后实际验证账号连接入口打开已打包目录，资产字节不变；缺目录时普通应用初始化仍可继续，显式打开连接目录报告缺件，既不生成 raw 目录也不启动浏览器。
