# ToBe 把模板写活 · 新窗口提示词

你现在接手 ToBe「把模板写活」及模板与算法实验室的教学衔接，请实际开发、编写、验证并交接，不停在界面调整、盘点或任务清单。用户于 2026-11-02 将本项交给独立窗口，总集成窗口已经停止该项内容开发。前七板块题解另有独立窗口负责；维基、对战、贴纸、启动及最终交付仍由总集成窗口负责。

## 先读取与隔离

1. 读取 `D:\项目\AGENTS.md`、`D:\项目\TB\AGENTS.md`、实际仓库 `AGENTS.md`，以及 `docs/architecture.md`、`docs/next-version-scope.json`、`docs/algorithm-lab-authoring.md`、`docs/algorithm-lab-design.md`、`docs/editorial-teaching-standard.md`、`docs/teaching-handoff-1.5.0.md`、`docs/template-inventory-1.5.0.json` 和当前更新记录。
2. 总集成开发目录只读：`C:\Users\lenovo\AppData\Local\ToBeDev\tb-next-1.5.0`。共享 Git 位于 `D:\项目\TB\开发\tb-daily-training`，远端为 `https://github.com/3097729287/acm-algo-trainer.git`。
3. 从已推送的固定交接分支 `handoff/1.5.0-teaching-20261102` 创建自己的分支和 worktree，建议 `feature/1.5.0-living-templates`、`C:\Users\lenovo\AppData\Local\ToBeDev\tb-150-living-templates`。先核实实际 SHA；已有目录或分支先检查，不覆盖、reset 或复用其他会话目录。不要在总集成工作目录修改、暂存或提交。
4. 读取 `D:\项目\TB\正在使用的构建文件.json`，保护实际候选、升级基线、进程、共享 Git、依赖联接及目标。`tb-next-1.4.37` 由另一会话负责学习规划、推荐和导航解锁等流程，不接管其工作。最终合并、打包、安装及更新清单由总集成窗口统一执行，你不要单独安装、发布或部署。

## 已有成果与真实断点

- `backend/resources/code-templates.json` 原有 **28 份模板**身份、双版代码、示例及关联保持原样，原摘要见盘点文件；不能用一套新内容覆盖旧模板或个人模板。
- 新补充源是 `scripts/template_teaching_basics.py`、`scripts/template_guided_basics.py`，生成入口 `scripts/sync_template_teaching.py`，资源为 `backend/resources/template-teaching.json`、`template-guided.json`。生成器已能从公共文本源工作，不依赖旧作者绝对路径。
- 当前五个基础专题为双指针、滑动窗口、二分、前缀和／差分、单调队列。新增独立模板 `builtin:two-pointers`、`builtin:sliding-window`，未改原 28 份模板的正确实现。五专题有 10 个分别证明的变种、双版代码及 5 道具体原题迁移。
- `scripts/check_template_curriculum.py` 已验证 **25 个程序、2042 组输入**，证据在总集成目录 `.backups/next-150/template-programs-final/report.json`。
- 二分与单调队列新增七章课程及各五道精选跟做题，组件为 `TemplateStudyCourse.jsx`、`TemplateTraceExperiment.jsx`、`TemplateGuidedProblem.jsx`，模型为 `templateTraceModels.js`、`templateGuidedModels.js`。支持实际状态推演、代码行对应、回退、重置、核对、草稿保存、独立实现交接和活动比赛别名锁。
- 跟做原题：二分 P2249、B3691、P1678、P2920、P8873；单调队列 P1886、P2251、P1440、P1714、CF547B。参考程序直接来自既有公共题解或已验证的模板迁移，资源保留原题与程序摘要。
- `scripts/check_template_guided.py` 已验证这 10 道原题的显示程序及两个新增模板的两版主程序，共 **14 个程序、647 组输入**，证据为 `.backups/next-150/guided-references-1/report.json`。
- `frontend/tests/template-teaching-model.mjs` 已通过 28975 个轨迹对照、10 个跟做模型及别名锁；`frontend/tests/template-teaching.mjs` 的第 4 轮通过实际模板、课程、参考代码、状态／代码对应、草稿、辅助标记及窄窗检查。证据分别为 `.backups/next-150/template-teaching-model.log`、`template-teaching-browser-4.log`，截图在 `frontend/tests/screenshots/template-teaching/`。
- 这只是部分成果，不是原 28 份模板全部完成。原有并查集、树状数组、线段树、Trie、倍增、最大流、Li Chao 树、线性基等已有课程与操作实验必须逐项审查；已有演示或五个课堂小例不等同于五道合格原题跟做。

## 完成标准

逐项盘点并报告已完成、部分完成、未开始和明确暂停。范围包含数据结构与基本解题思路，保留现有模板身份、讲解、代码、原题关联、实验和学习记录。

每个模板讲清解决什么问题、从哪些题目条件识别、标准写法、每个变量和不变量、初始化、处理顺序、状态变化、结束条件及复杂度；解释适用条件和失效原因、可修改的部分及修改后须重证的内容、教学上有价值的变种、边界与反例。

具体说明题目如何改变目标、状态、维护和答案统计。二分边界语义、指针移动依据、窗口可维护性、等号与重复值处理必须分别证明和验证，不机械替换比较符号。用真实原题展示“基本模板 → 题目差异 → 修改实现 → 验证结果”，提供相互对应的讲解版与竞赛版程序，保留已有正确实现。

实验室沿用现有教学流程，按专题设计有效交互、状态推演、边界实验与练习。数据、代码位置、图形和解释同步；操作能看见真实结果，可回退、重置、核对。不是所有算法套用同一种动画或只揭示提示。按现有规范衔接五道精选跟做、题目特有变化及独立实现，保留进度和草稿。保留学习算法的目录位置与顶部导航，不恢复“打开对应模板”入口。操作按钮优先图标，保留无障碍名称和必要提示，做好对齐和缩放适配。

## 与题解窗口的边界

你负责模板、课程及专用资源／验证脚本。前七板块窗口负责 `data/core7-editorials/`、公共题解表与逐题复核台账。两者有同题时不同时重写公共题解 JSON；把题目特有精修放入独立补丁清单，注明题目身份、方法、原文摘要、修改理由和验证程序，交题解窗口或总集成审查合并。基础教学内容与题目特有推理按规范分开，不丢失原图、引用或学习记录。

当前整体验证有一项已知的基础讲义抽取摘要登记失败，详见 `.backups/next-150/backend-check-2.log`；该项已经交给题解窗口，不放宽其断言或并发修同一登记文件。你产生的新失败仍须自行定位修复，交接时明确区分。

## 验证、数据与交接

只用隔离数据；代码运行官方样例、必要边界和独立小数据对照，不向原站提交。测试用 `TB_OFFLINE=1`，本机 Python 为 `C:\Users\lenovo\AppData\Local\Programs\Python\Python313\python.exe`；后端按实际需要设置 `PYTHONPATH=backend;backend/common;desktop`。后端更改运行 `scripts/check.py`，前端更改运行构建与相关浏览器检查；教学正文还需阅读复核，不能以数值正确代替讲解清楚。

编辑已有文件先备份。SQLite 迁移前使用在线备份保留已提交 WAL；账号、训练、代码、草稿、设置、课程记录和本机新增教学内容不能被旧公共种子覆盖。当前两盘空间很低，先查实际空间，避免复制完整安装、大候选或整套数据库；只读共享已核验的不可变公共种子和依赖，个人数据库禁止硬链接，不能原地重建共享种子。

清理只用 Windows 系统回收站；失败、不支持或容量不足时保留，不永久删除、不清空、不改容量或挤掉已有项，回收不冒充实际释放空间。

更新你负责的文档、逐模板完成矩阵和验证证据，提交并推送自己的分支。交接完整 SHA、修改路径、每个模板的讲解／变种／双版程序／实验／原题迁移对应关系、运行证据、保留数据证明和剩余问题。总集成窗口随后统一合并和交付；不得把界面改动、任务清单、未验证程序或源码提交算成全套模板已完成，不声称已安装或上线。
