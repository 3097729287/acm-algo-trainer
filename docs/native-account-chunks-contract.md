# Rust 账户分块模块的独立交付边界

2026-11-09。现有 `account_vault.rs` / `local_documents.rs` / `account_transport.rs` 已实现加密存储和传输；完整会话激活及云状态尚未接通。检查后没有可删除的既有分块实现：Rust 中还没有该模块。保留所有历史数据和当前独立验证回执，不重建公共题库或整包。

本组仅新增 `backend-rust/src/account_chunks.rs`、独立测试和小型公开协议夹具，可加一行 `lib.rs` 注册。不改 `service.rs`、账号协调器、个人库应用事务或正常安装，不接触真实账号、会话或凭据。以 `backend/account_chunks.py` 和 `backend/account_sync.py` 的实际协议为准。

## 纯 Rust 接口

统一返回 `Result<T, crate::ApiError>`，JSON 使用现有 `serde_json::Value`。所有对象先校验，再交回协调器；没有从 UI 反序列化的“已验证状态”能力。

```rust
pub enum ObjectKind { Data, Concat }
pub struct ChunkObject {
    pub hash: String,
    pub kind: ObjectKind,
    pub payload: Vec<u8>, // 实际 gzip 字节
    pub children: Vec<String>,
}
pub struct Canonicalized {
    pub state: Value,
    pub code_references: Vec<(String, String)>,
}
pub struct Unpacked {
    pub state: Value,
    pub duplicate_learning_summary: bool,
}

pub fn encode(value: &Value) -> Result<Vec<u8>, ApiError>;
pub fn from_wire(expected_hash: &str, value: &Value) -> Result<ChunkObject, ApiError>;
pub fn to_wire(value: &ChunkObject) -> Result<Value, ApiError>;
pub fn code_reference(value: &str) -> Result<Option<CodeReference>, ApiError>;
pub fn write_blob(raw: &[u8], links: &[String],
    store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>) -> Result<String, ApiError>;
pub fn read_blob(root: &str, maximum: usize,
    load: &mut dyn FnMut(&str) -> Result<ChunkObject, ApiError>) -> Result<Vec<u8>, ApiError>;
pub fn pack_state(state: &Value,
    store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>) -> Result<String, ApiError>;
pub fn unpack_state(root: &str,
    load: &mut dyn FnMut(&str) -> Result<ChunkObject, ApiError>) -> Result<Unpacked, ApiError>;
pub fn canonicalize_state(state: &Value, known_refs: &BTreeMap<String, String>,
    now: DateTime<Utc>, store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>)
    -> Result<Canonicalized, ApiError>;
pub fn read_code(reference: &CodeReference,
    load: &mut dyn FnMut(&str) -> Result<ChunkObject, ApiError>) -> Result<String, ApiError>;
```

`CodeReference` 使用旧 `root/sha256/bytes/offset` 字段；`offset` 缺省为零。结构体可由模块校验后提供，不允许跳过 `code_reference` 来采信远端声明。签名若确有合理调整，先通知接线负责人。

对象加载和保存由回调注入。生产回调每次只短锁读取或写入对象缓存；网络请求在外锁执行，前后校验当前 owner/endpoint/会话 epoch。模块不拥有长期 SQLite 句柄、账号 token、HTTP 客户端或 UI。已确认的现有传输器是 `account_transport::AccountTransport::request(endpoint, Request, &dyn Fn() -> bool)`，写请求不能自动重放。

## 必须保留的协议和数据语义

- 对象 ID 为 `SHA256(kind + "\n" + children.join("") + "\n" + gzip_payload)`；children 为排序去重后的精确小写 SHA。原缓存和远端对象每次均验证摘要。64 KiB 解压节点、66 KiB 压缩节点、256 子依赖、128 个 concat parts、深度 24、128 MiB 单项、4 MiB manifest、4096 个每表分桶及 512 MiB 展开总量均保持。
- manifest 为 `tb-private-chunk-state-v2`，还原 `tb-account-state-v1`。固定 17 张表和主键、分桶宽度、提交月份前缀、行排序与 `publicAccounts` 均按旧实现。缺失/重复主键拒绝。旧 `learning-summary-v1` 的特殊重复仅原样保留并设置 `duplicate_learning_summary`，由主同步层执行已经对照的恢复逻辑，不能丢弃其中一份。
- `encode` 对照 Python 的 `ensure_ascii=False/separators/sort_keys`，特别覆盖 Unicode、控制字符、整数和有限浮点格式。若 Rust gzip 产生另一份有效压缩字节，明确记录；验证 Python 能读 Rust 对象、Rust 能读现有 Python 对象。不得拿未验证的压缩差异替换旧对象 hash 或已有引用。
- 历史代码 30 天分界、月/哈希桶打包、64 KiB 归档、262144 字节代码范围与 offset/摘要/UTF-8 都保持。canonicalize 仅返回用于同步的引用及待保存 refs，不能删除、改空或覆盖当前机器已经保存的实际源码。已有匹配 refs 复用，未取回的冷代码不为同步而强制下载。
- 损坏 gzip、循环图、越界 concat、错误回执、缓存错摘要、非法代码引用均明确失败，保留旧状态。不能将这些错误归为可使用离线租约的纯网络中断。

根协调器另行负责 `/v2/accounts/state` 协商、真正 missing/upload 确认、revision CAS、旧 v1 迁移、冲突保存、journal capture/apply 和身份激活。该纯模块交付不计为登录或同步 API 已完成。

## 验收

使用临时图缓存和实际旧 Python 对照：空状态、17 表完整状态、中文/emoji、多级依赖、共享节点、旧 gzip/新 gzip 双向、精确代码切片、30 天边界、已缓存冷代码保留，以及上述损坏/限额反例。生产 Rust 不调用 Python。夹具只含构造账户和公开协议，不放真人源码、凭据或数据；提交写明实际测试数量和限制，不把纯模块测试称为账户端到端验收。
