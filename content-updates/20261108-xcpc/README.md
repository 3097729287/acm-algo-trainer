# 2026-11-08 原题补全与 XCPC 新增

本目录记录未发布的公共题库修订；本机稳定程序仍为 1.6.6，本批内容尚未安装。

新增 5 场、63 个原题身份，正文、样例及全部原资源随题库离线保存：

- [The 2026 ICPC Asia Chengdu Regional Contest (The 5th Universal Cup. Stage 5: Grand Prix of Chengdu)](https://codeforces.com/gym/106799)：13 题。
- [2024 China Collegiate Programming Contest (CCPC) Harbin Onsite (The 3rd Universal Cup. Stage 14: Harbin)](https://codeforces.com/gym/105459)：13 题。
- [The 2024 CCPC National Invitational Contest (Changchun) , The 17th Jilin Provincial Collegiate Programming Contest](https://codeforces.com/gym/105170)：12 题。
- [The 2018 ICPC Asia Qingdao Regional Programming Contest (The 1st Universal Cup, Stage 9: Qingdao)](https://codeforces.com/gym/104270)：13 题。
- [2020 CCPC Henan Provincial Collegiate Programming Contest](https://codeforces.com/gym/104095)：12 题。

恢复旧库 33 题：台湾站 12 题、QOJ 重庆站 9 题、QOJ 长春站 11 题及维基已指定的 Once Upon A Time。只解除本次题面审计造成的隐藏，保留其它目录规则、原题 ID、所有旧题面快照和个人历史关联。

河南 L 的原 PDF 中文字符映射损坏；已对照原件第 20–21 页手工转写完整中文、分段收益公式、全部范围与样例，原 PDF 和错误的原始文本提取均保留。另逐行核对并补回 The Messenger 与 Once Upon A Time 的竖排样例。交互题和通信题的点式加粗声明单独正确识别，不能当作普通样例题判定。

实际前端验证：41 份原 PDF 的 86 页全部渲染，原始字节 SHA-256 一致，外部请求 0；98 个原文／翻译渲染条目中，56 个 Markdown 与 42 个 PDF 条目共 0 个渲染错误。新资源共 69 份、10,091,022 字节，追加到 part-0045.bin，旧资源不改写。

新公共种子共 13,480 题、13,439 份题面，原稿缺口由 152 降至 119。新增及恢复原题后，还有 64 份中文待逐页补写；不能把原文可读计作中文已经完成。知识点和难度以真实可见目录分别仍缺 4,320、2,101 题为准，未知评级明确保留 UNKNOWN。

应用脚本：`scripts/apply_verified_originals.py`；运行时与构建不依赖作者缓存，只使用已提交的题面补丁与资源分卷。逐题来源和验证见 `docs/verification/native-originals-20261108.json`。重建后须继续通过公共库、完整后端及个人数据升级验证。
