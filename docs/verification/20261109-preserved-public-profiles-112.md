# 1.6.11 公共 profile 保留与严格组合校验

基于 `37ae654048a0e255690a846305f199249dcd78f7` 的独立工作树实现，供重新编译的 1.6.12 集成。修改前已完整阅读设计理念（SHA-256 `b6fa71c9f549962dd07b0e6257829c2424dc5472f36ed74df1632ec0c3accff1`）。

清理检查在修改前完成：新工作树没有未跟踪内容、旧构建、`dist`、`__pycache__`、`.pytest_cache` 或 `.backups` 产物。本范围无可清理项，实际清理 0 项、0 bytes。旧八份公开升级基线、已发布完整 1.6.11、五份 rows-v3 payload 及原始验证回执仍是必要输入，全部保留；含私人数据的验证副本不作为公共基线。

新增可选 `preservedPublicProfiles`，共同目标 SHA 与最多九个完整组合一起认证。每个组合只含物理 seed、seed identity、公共描述文件及可选的一份绑定 gzip 的精确 SHA。运行时必须匹配一个完整组合并核对描述与 gzip 绑定；它不是逐文件独立哈希集合。组合里的文件不会出现在替换写集中，其余资源照常管理。无此字段的 schema-1 包保留原路径。

构建器通过显式选项生成该字段，目标共同内容必须与各已有 profile 一致，且来源仅为 1.6.11；原 `preserve_public_seed` 模式保持独立。新 profile 的构建说明记录共同内容目标及组合清单摘要，不把某个物理 seed 写成所有用户共有的文件摘要。

Python 3.13 下相关 71 项检查全部通过：

```text
python -B -m unittest -v test_preserved_public_profiles test_compact_update test_public_library_update test_update_backup_limits test_recovery_backups test_seed_asset_reuse
```

其中九种纯公开 SQLite 夹具布局（八种保留物理 seed 的 row profile 与一种完整 seed）都实际构建并应用同一 ZIP，公共 profile 和未知私人 BLOB 行保持原字节；每种布局的六个程序替换点逐一注入失败，54 次均恢复全部原程序／公共／私人字节。未知 seed、合法文件混搭、越界或额外路径、与写集重叠、重复／超量组合、损坏或缺失 gzip、描述中的 target／payload 名称／SHA／长度不一致均在首次写入前拒绝。与组合无关的 JSON 及 gzip 资源仍正常更新，canonical 构建输入完全不变。

原默认构建、原 `preserve_public_seed` 模式及九项旧 schema-1 安装／回滚测试继续通过。`select` 使用同一个哈希缓存匹配九个候选，只读取匹配物理 seed 一次；`apply` 在创建 cache／lock 前预检，并在事务内恢复旧中断事务后再次校验，因此这两个独立阶段会各读一次 seed。额外读取是明确的校验成本，不宣称零 I/O。

这些是实际 SQLite／ZIP 文件上的协议回归，不是九份真实已发布程序的发行验收。正式公共基线仍须由干净已发布 full111 及八份旧基线加对应已验证 111 profile 构造，再对最终 112 程序做完整文件校验与真实 UI 计时；不使用任何私人状态验证 app，不修改普通安装、旧 111 资产或原失败回执，不放宽一分钟门槛。
