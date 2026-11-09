# 应用快捷键统一路由

账号已有的快捷键覆盖设置继续生效。`applicationShortcuts.js` 统一注册当前页面处理器、组合和上下文，在主窗口 capture 阶段优先处理，再由同一处理器执行原动作。CodeMirror、字号输入框、按钮、题面与同源阅读框使用相同路由；原生 DeepSeek 控件使用当前注册表的只读动作回执。

作用域、真实禁用条件和草稿保存约束继续保留。普通文本不作为应用命令：列表的 U/S/F、Enter 和全局 `?` 仍保留原文字输入条件；已注册的修饰键组合、F 键和 Escape 不依赖文本焦点。未注册的浏览器/编辑器键照常处理。外部原站浏览器没有 ToBe 原生主窗口 owner，不会被捕获。

下一题按钮、主文档、CodeMirror 和原生命令共用同一个 `nextProblem`。它等待当前记录保存、再次确认记录和账号未切换，再调用原来的 `onNext`；保存失败不跳题，single-flight 和 key-up 前的 repeat 过滤防止并发跳题。普通题序在完整原始 rows 中跳过明确不可开或已移除的题目，模拟赛沿用原 slots 的可开判断。源码上一题/上一项原本没有注册 Ctrl+Left，本轮没有添加该组合。

原生队列只有 Win32 hook 能加入事件。前端通过带既有本机 token/ownerKey/sequence 的位置请求附带当前注册表；后端只保存经过结构校验的组合、处理器标识和上下文，不接收任意网址、目录或执行脚本。只在 ToBe 前台且焦点位于所属 native child/owned 页面窗口时拦截，主 DOM 的 WebView 分支由前端处理，避免同键执行两次。队列最多 32 项、两秒有效，消费端校验 owner、viewId、注册版本和递增序号；HTTP 没有 enqueue setter。

活动统计仍只读 `/api/desktop/input-activity` 五字段。快捷键路由只把 UI 的工具栏切为键盘模式，不把合成事件或程序聚焦算作活动。消费应用组合使用 `stopPropagation`，允许同 window capture 的可信输入监听；presence 分支合入时将其主文档键盘监听移到 window capture。

全局弹窗在全屏学习层之上沿用原入口显示，避免落在已 inert 的主界面内。F6 按实际活动学习面板中的可见题面、代码和控制台切换焦点。Alt+T 与 Alt+Shift+T 分别沿用做题/阅读工具栏与学习标签栏的现有动作。

## 可配置清单

下表直接从 `frontend/src/lib/shortcuts.js` 生成；空组合保留为未绑定，不新增默认键。

| ID | Action | Default | Scope |
|---|---|---|---|
| `bookmark-previous` | 上一个书签 | `Alt+ArrowLeft` | 主界面书签 |
| `bookmark-next` | 下一个书签 | `Alt+ArrowRight` | 主界面书签 |
| `commands` | 命令面板 | `Ctrl+K` | 全局 |
| `sidebar` | 展开或收起菜单 | `Ctrl+B` | 全局 |
| `settings` | 打开设置 | `Ctrl+,` | 全局 |
| `search` | 搜索 | `Ctrl+F` | 全局 |
| `refresh` | 刷新 | `F5` | 全局 |
| `regions` | 切换焦点区域 | `F6` | 全局 |
| `help` | 快捷键设置 | `?` | 全局 |
| `page-mine` | 我的训练 | `Ctrl+1` | 导航 |
| `page-library` | 题库 | `Ctrl+2` | 导航 |
| `page-training-lists` | 题单 | — | 导航 |
| `page-templates` | 模板 | — | 导航 |
| `page-paths` | 实验室 | `Ctrl+3` | 导航 |
| `page-competitions` | 比赛 | `Ctrl+4` | 导航 |
| `page-mock` | 模拟赛 | `Ctrl+5` | 导航 |
| `page-records` | 提交记录 | `Ctrl+6` | 导航 |
| `page-growth` | 成长 | `Ctrl+7` | 导航 |
| `page-activity` | 活动记录 | `Ctrl+8` | 导航 |
| `page-lectures` | 从零讲 | `Ctrl+9` | 导航 |
| `practice` | 打开选中题目 | `Enter` | 题目列表 |
| `solution` | 查看题解 | `U` | 题目列表 |
| `favorite` | 收藏题目 | `S` | 题目列表 |
| `listSearch` | 搜索题目 | `F` | 题目列表 |
| `run` | 自测运行 | `Ctrl+R` | 编辑器 |
| `submit` | 提交 | `Ctrl+Enter` | 编辑器 |
| `official` | 原站提交 | `Ctrl+Shift+Enter` | 编辑器 |
| `save` | 格式化代码 | `Ctrl+S` | 编辑器 |
| `pane-0` | 题面与代码 | `Alt+0` | 编辑器 |
| `pane-1` | 只看题面 | `Alt+1` | 编辑器 |
| `pane-2` | 只看代码 | `Alt+2` | 编辑器 |
| `study-toolbar-lock` | 锁定或解锁学习书签栏 | `Alt+Shift+T` | 编辑器 |
| `learning-summary` | 任务概览 | `Ctrl+Shift+P` | 全局 |
| `statement-font` | 调整题面字号 | `Alt+F` | 编辑器 |
| `statement-original` | 在浏览器打开原题 | `Alt+O` | 编辑器 |
| `code-language` | 选择编程语言 | `Alt+G` | 编辑器 |
| `workbench-undo` | 撤销载入代码 | `Alt+Z` | 编辑器 |
| `theme` | 切换日夜间模式 | `Ctrl+Shift+L` | 全局 |
| `calendar` | 比赛日历 | `Ctrl+Shift+C` | 全局 |
| `daily-tasks` | 每日任务 | `Ctrl+Shift+D` | 全局 |
| `achievements` | 成就 | `Ctrl+Shift+A` | 全局 |
| `list-filter` | 筛选题目 | `Alt+F` | 题目列表 |
| `list-random` | 随机选题 | `Alt+R` | 题目列表 |
| `list-difficulty` | 按难度排序 | `Alt+D` | 题目列表 |
| `list-recent` | 按最近练习排序 | `Alt+T` | 题目列表 |
| `workbench-back` | 返回列表 | `Alt+ArrowLeft` | 编辑器 |
| `workbench-next` | 下一题 | `Ctrl+ArrowRight` | 编辑器 |
| `statement-language` | 切换题面语言 | `Alt+L` | 编辑器 |
| `statement-copy` | 复制题面 | `Alt+C` | 编辑器 |
| `toolbar-lock` | 锁定或解锁工具栏 | `Alt+T` | 编辑器 |
| `initial-code` | 选择初始代码模板 | `Alt+I` | 编辑器 |
| `code-templates` | 打开模板 | `Alt+M` | 编辑器 |
| `workbench-solution` | 题解 | `Alt+U` | 编辑器 |
| `console-toggle` | 展开或收起运行结果 | `Alt+R` | 编辑器 |
| `catalog-up` | 返回上层 | `Alt+ArrowUp` | 题单 |
| `catalog-home` | 返回题单首页 | `Alt+Home` | 题单 |
| `catalog-filter` | 筛选题单 | `Alt+F` | 题单 |
| `catalog-new` | 新建题单 | `Alt+N` | 题单 |
| `contest-filter` | 筛选比赛 | `Alt+F` | 比赛 |
| `contest-folders` | 比赛文件夹浏览 | `Alt+V` | 比赛 |
| `contest-up` | 返回上层 | `Alt+ArrowUp` | 比赛 |
| `mock-filter` | 模拟赛筛选 | `Alt+F` | 模拟赛 |
| `mock-regenerate` | 重新选题 | `Alt+R` | 模拟赛 |
| `lecture-learned` | 标记或取消已学会 | `Alt+K` | 从零讲 |
| `lecture-fullscreen` | 切换全屏阅读 | `Alt+Enter` | 从零讲 |
| `lecture-back` | 返回上篇 | `Alt+ArrowUp` | 从零讲 |
| `template-copy` | 复制模板代码 | `Alt+C` | 模板 |
| `template-back` | 返回模板目录 | `Alt+ArrowUp` | 模板 |
| `records-platform` | 提交平台筛选 | `Alt+P` | 提交记录 |
| `records-result` | 提交结果筛选 | `Alt+V` | 提交记录 |
| `ranking-daily` | 每日排行榜 | `Alt+1` | 排行榜 |
| `ranking-weekly` | 本周排行榜 | `Alt+2` | 排行榜 |
| `ranking-all` | 累计排行榜 | `Alt+3` | 排行榜 |
| `initial-new` | 新建初始代码模板 | `Alt+N` | 初始代码模板 |
| `initial-copy` | 复制为初始代码模板 | `Alt+C` | 初始代码模板 |

## 源码已有的固定组合

| 上下文 | 组合 | 原动作 |
|---|---|---|
| 桌面窗口 | F11 | 切换原生全屏 |
| 学习标签页 | Ctrl+T / Ctrl+W | 新建搜索标签 / 关闭当前标签 |
| 学习标签页 | Ctrl+Tab / Ctrl+Shift+Tab | 下一个 / 上一个标签 |
| 学习标签页 | Ctrl+\\ | 原分栏动作 |
| 学习标签页 | Ctrl+Alt+Left / Ctrl+Alt+Right | 移入原左右分组 |
| 学习标签页 | Escape | 关闭搜索或返回主界面 |
| 独立编辑器 | Ctrl+Tab | 原 onLeave 聚焦动作；学习标签页优先使用标签切换 |

## 验证边界

68 个有修饰键/功能键的可配置组合逐项通过主文档及相同 native 路由模型检查；自定义覆盖、repeat、过期/旧上下文回执与普通输入均覆盖。实际 Workbench 回归验证焦点、保存失败、代码与题面实例保持、native DTO 消费去重；API 明确隔离 mock，不把它称作真实原站提交或硬件输入。

真实 Windows 控件检查证明了 native child 与主 DOM 的 HWND 分支区别、cookie/localStorage 跨进程保留、账号隔离、崩溃重建、DPI/缩放及最小化隐藏。测试进程未取得前台权限，因此实际注入拒绝检查被明确跳过，硬件输入正向没有自动实测声明；输入来源过滤和命令队列由离线模型验证。真实 DeepSeek 公开登录页另有原生截图，未替用户登录或发送聊天。

原有 LearningBrowser 的“关闭空搜索后排序实验步骤保持”在本分支和六文件精确 728 Git 对象覆盖基线均于同一行失败。失败回执保留，本轮没有修改算法实验。

当前源码 FullApp 窄回归在 `frontend/.backups/shortcut-fullapp-1794241844264/result.json` 通过，0 page/console error。该测试使用假账号、明确 mock API 和既有匿名 UI profile，覆盖自定义键、输入焦点、保存后 next、全局弹窗、F6、侧栏、学习搜索和页面导航；不声称真实后台或 OJ 验收。低空间重跑可设置 `TB_SHORTCUT_PROFILE` 为本工作树已存在的 `deepseek-ui-数字/profile`，并以 `TB_SHORTCUT_SOURCE=1` 验证源码；脚本拒绝其它浏览器 profile。
