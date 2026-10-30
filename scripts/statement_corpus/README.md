# 公开题面采集与复核

本目录只处理匿名公开 GET，不读取个人库、登录配置或真实账号，不进行提交。不要把采集目录、原始 HTML、匿名重开 Cookie 或本机路径加入公共包。公开逐题证据只保留 URL、UTC 时间、HTTP 状态、内容校验值和核验结果。

安装 Python 依赖后，设置 `TB_STATEMENT_AUDIT_DIR` 为独立空目录。使用 `snapshot.py --public-seed <明确指定的公共种子> --output <隔离目录>/baseline.sqlite3` 在线备份；该脚本拒绝已有输出及含个人数据表的输入。建立 `evidence` 子目录。后续脚本从这个基线读取，所有网络缓存和验证输出均写入隔离目录。公开库的路径由操作者指定，不自动扫描用户目录。

1. `inventory.py` 全量枚举现有 ID、正文、样例、图片及附件引用；旧统计只作前后比较。
2. `fetch_all.py` 读取实际原站地址。`collect_group_cf.py`、`collect_group_at.py` 从原站整场页面绑定真实题目链接和字母，原始响应使用不可变 SHA 文件名。
3. `collect_resources.py`、`retry_resources.py` 下载真实资源，验证所有 GIF 帧、PDF 页和附件校验值。失败、登录要求、限流均记录，不能据此断言永久丢失。
4. `retry_failed.py`、`retry_pdf.py`、`recover_atcoder.py` 复核恢复路径；`search_qoj_alternatives.py` 只找候选，`verify_qoj_pdf_alternatives.py` 必须同时核对原站比赛题单、明确 PDF 题号、标题、赛事来源和全部已有样例。候选文件不进入已完成数量。
5. `reparse_evidence.py` 用当前读取器复核捕获内容。`prepare_corpus.py` 保留全部原有中文及绑定原文，生成逐题前置 SHA 保护的修复分片、原始资源包、完整性清单和未解决清单。完整原题与普通本地可评测能力分别判断。
6. 在独立 Git 工作区执行 `assemble_public.py`，只把明确的基线与通过核验的内容组装进该工作区。它会更新该工作区的公共文本源，禁止在主会话工作区运行。无法核实的条目暂时退出公共目录，原 ID、别名、历史读取及私人事实保留。
7. 执行 `python scripts/library_seed.py build`、`validate_delivery.py`、`python scripts/check.py` 以及前端构建和相关 Playwright 检查。`validate_delivery.py` 对比整个公共种子，逐题实际还原离线资源，核对全部原站样例及已交付中文，验证所有原始资源和逐题隐藏状态。

`discover_verified_qoj.py` 是当前库收尾后的独立候选批次。直接读取原生全局题号、原站搜索标签、类别关联及原始 PDF；不从连续题号推算比赛字母。原站未公开字母时只记录全局题号，不能声称已核实整场字母映射或启用该场重现赛。入库还需去重、来源复核及新的离线验证。

公共 SQLite 为持久源。`statement_assets.json` 记录原始字节 SHA、MIME、长度、资源包文件和偏移，`statement_asset_parts.json` 记录包校验值。`statement-patches` 校验同题旧内容后才应用；如另一内容会话改动同题，先重新合并，不跳过冲突。此次资源引用要求 schema 7 代码及前端同时交付，禁止向旧程序下发 schema 1 内容热更新。

结果记录在 `docs/statement-integrity-20261030/`。源码分支只交主会话合并，本流程不安装、打包、发布、部署、改快捷方式或清理其他工作区。
