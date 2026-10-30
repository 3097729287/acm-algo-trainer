# 实际验证结果

全部后端与数据验证在隔离状态下运行，`TB_OFFLINE=1`，未读取真实个人库，真实账号提交数为 0。

| 命令或批次 | 结果 |
| --- | --- |
| `python scripts/check.py` | 最终 899 项，577.998 秒，OK；公共 SQLite 完整性、外键、每份资源 SHA 和离线引用检查同时通过 |
| `python -m unittest test_statement_integrity test_statement_assets test_release_1410 test_bundled_translation` | 34 项，OK；包括后台重试不能解除审计退休或覆盖中文 |
| `npm run build` | 通过 |
| `node tests/statement-translation.mjs` | 通过；英文默认、缓存中文、历史语言标记、图表及响应隔离 |
| `node tests/statement-offline.mjs` | 通过；表格换行、全部样例行、图片、PDF/GIF 原字节下载及无外部请求 |
| `node tests/statement-pdf.mjs` | 通过；三页原 PDF 左栏显示、字节一致、中文切换、右栏草稿保留 |
| `node tests/statement-format.mjs` | 通过 |
| `node tests/platform-registry-model.mjs` | 通过；原有 65 个 QOJ 身份和新增 11 个唯一问题，平台与 XCPC 分类独立 |
| `node tests/training-list-platforms-model.mjs` | 通过 |
| `node tests/statement-corpus.mjs <corpus> <result>` | 全量 11,822 份 HTML 题面实际解析；136 题公式问题经原站修复后复核，残余 59 题已暂缓 |
| 同上，中文批次 | 3,241 份实际解析；8 题异常已暂缓，与原文异常合计 64 个 ID |
| `node tests/statement-native-corpus.mjs <corpus> <result>` | 166 份原生 PDF 在实际左栏逐份核对显示文件 SHA，外部请求 0 |
| `node tests/statement-language-corpus.mjs <corpus> <result>` | 检查 3,276 份带中文的存档，恢复 241 题历史语言标记造成的切换入口遗漏；中文正文改动 0 |
| `validate_delivery.py` | 12,282 ID、12,183 存档逐题实际还原；11,924 完整、358 暂缓；19,194 对原站样例输入输出核对；原有 2,898 份中文经既有清理后完全一致 |
| 资源全量验证 | 5,947 个 SHA；1,021 份 PDF 的 1,694 页；10 份 GIF 的全部 437 帧；原件与派生显示文件分别记录 |
| 旧公共种子升级及在线备份 | 8 类合成私人事实、私有导入、改动题面及中文与升级前 WAL 在线备份一致；358 题不进入公共选题与公共题单；原持久题单与历史内容保留 |
| QOJ 去重批次 | 对整个原库存档比较全部样例签名和原始 PDF SHA；仅找到两份候选，逐段核对规格与约束后复用原 ID；另 11 题完整入库 |
| 公开内容保护 | 默认/详细题解、讲义、关联、方法、题单逐行等同安装版基线；提交前再次在线备份核对最新版 |
| 隐私与 Git 检查 | 公共文件无本机绝对路径、真实凭据或个人记录；`git diff --check` 通过；原始资源按二进制入 Git |

最终重建时曾因本会话临时盘空间不足，在完成 SQLite 构建后的自动备份步骤中断。没有替换运行中的安装库；使用已完整构建的隔离候选，逐题比较全部源题面、检查外键、完整性和每份资产 SHA 后，在隔离工作区保留旧文件并核验移动，随后运行上述最终 899 项完整检查。透明压缩只应用于本会话捕获缓存，文件内容及校验值保持。

早期阶段的失败日志及修复后结果均保留在隔离验证目录，未把旧阶段通过记录冒充最终结果。原始日志含测试工作区绝对路径，不放入公开数据；完整命令和日志位置列入本地交接文件。
