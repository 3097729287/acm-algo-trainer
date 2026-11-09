//! Pure, bounded v2 account objects. Cache and transport ownership stay with the caller.
//!
//! Hashes bind the actual gzip bytes, not a recompressed representation. This module
//! neither opens a database nor performs network I/O. Canonicalization only builds
//! an outgoing projection; it never changes a machine's stored source code.
use crate::ApiError;
use base64::{Engine, engine::general_purpose::STANDARD};
use chrono::{DateTime, Duration, NaiveDate, NaiveDateTime, Utc};
use flate2::{Compression, GzBuilder, bufread::GzDecoder};
use serde_json::{Map, Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::io::{Cursor, Read, Write};

pub const CHUNK: usize = 64 * 1024;
pub const RAW_LIMIT: usize = 128 * 1024 * 1024;
pub const PAYLOAD_LIMIT: usize = 66 * 1024;
pub const MANIFEST_LIMIT: usize = 4 * 1024 * 1024;
pub const STATE_LIMIT: usize = 512 * 1024 * 1024;
pub const CODE_LIMIT: usize = 262_144;
pub const CODE_PREFIX: &str = "\0TB-CODE-V2:";

/// Insertion order is part of the old packer's dependency grouping.
pub const TABLES: &[(&str, &[&str])] = &[
    ("training", &["id"]),
    ("practice_sets", &["id"]),
    ("contests", &["id"]),
    ("drafts", &["problem_id", "context"]),
    ("submissions", &["id"]),
    ("tb_rank_profile", &["id"]),
    ("official_first_xp_awards", &["problem_key"]),
    ("official_xp_state", &["id"]),
    ("daily_missions", &["day", "id"]),
    ("goals", &["id"]),
    ("goal_daily_assignments", &["goal_id", "day"]),
    ("ranking_receipts", &["endpoint", "event_id"]),
    ("ranking_reward_totals", &["endpoint", "user_id"]),
    ("achievement_xp_claims", &["achievement_id"]),
    ("account_preferences", &["key"]),
    ("account_problem_facts", &["problem_id"]),
    ("account_sync_conflicts", &["id"]),
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ObjectKind {
    Data,
    Concat,
}
impl ObjectKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Data => "data",
            Self::Concat => "concat",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ChunkObject {
    pub hash: String,
    pub kind: ObjectKind,
    pub payload: Vec<u8>,
    pub children: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct Canonicalized {
    pub state: Value,
    pub code_references: Vec<(String, String)>,
}

#[derive(Clone, Debug)]
pub struct Unpacked {
    pub state: Value,
    pub duplicate_learning_summary: bool,
}

/// Validated only through `code_reference`; not an unchecked deserialization type.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CodeReference {
    root: String,
    sha256: String,
    bytes: usize,
    offset: usize,
}
impl CodeReference {
    pub fn root(&self) -> &str {
        &self.root
    }
    pub fn sha256(&self) -> &str {
        &self.sha256
    }
    pub fn bytes(&self) -> usize {
        self.bytes
    }
    pub fn offset(&self) -> usize {
        self.offset
    }
}

fn invalid(detail: &str) -> ApiError {
    let mut error = ApiError::new(
        503,
        "ACCOUNT_CHUNK_INVALID",
        &format!("账号分块校验失败：{detail}；本机记录已保留"),
    );
    // Corrupt authenticated data is not a network interruption/offline-lease signal.
    error.retryable = false;
    error
}
fn limit(detail: &str) -> ApiError {
    ApiError::new(
        413,
        "ACCOUNT_CHUNK_LIMIT",
        &format!("账号分块超过容量：{detail}；本机记录已保留"),
    )
}
fn hash(raw: &[u8]) -> String {
    format!("{:x}", Sha256::digest(raw))
}
fn valid_hash(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
}
fn exact_fields(object: &Map<String, Value>, fields: &[&str]) -> bool {
    object.len() == fields.len() && fields.iter().all(|key| object.contains_key(*key))
}

/// Python json.dumps(... ensure_ascii=False, separators=(',', ':'), sort_keys=True).
/// serde_json's shortest float digits use a different exponent presentation; adapt
/// that presentation without changing the represented finite f64.
pub fn encode(value: &Value) -> Result<Vec<u8>, ApiError> {
    fn visit(value: &Value, output: &mut Vec<u8>, depth: usize) -> Result<(), ApiError> {
        if depth > 128 {
            return Err(invalid("JSON nesting"));
        }
        match value {
            Value::Null => output.extend_from_slice(b"null"),
            Value::Bool(value) => output.extend_from_slice(if *value { b"true" } else { b"false" }),
            Value::String(value) => output.extend_from_slice(
                serde_json::to_string(value)
                    .map_err(|_| invalid("JSON string"))?
                    .as_bytes(),
            ),
            Value::Number(value) => {
                let spelling = if value.is_f64() {
                    python_float(&value.to_string())?
                } else {
                    value.to_string()
                };
                output.extend_from_slice(spelling.as_bytes());
            }
            Value::Array(values) => {
                output.push(b'[');
                for (index, value) in values.iter().enumerate() {
                    if index != 0 {
                        output.push(b',');
                    }
                    visit(value, output, depth + 1)?;
                }
                output.push(b']');
            }
            Value::Object(values) => {
                output.push(b'{');
                let mut keys: Vec<_> = values.keys().collect();
                keys.sort();
                for (index, key) in keys.iter().enumerate() {
                    if index != 0 {
                        output.push(b',');
                    }
                    output.extend_from_slice(
                        serde_json::to_string(key)
                            .map_err(|_| invalid("JSON key"))?
                            .as_bytes(),
                    );
                    output.push(b':');
                    visit(&values[*key], output, depth + 1)?;
                }
                output.push(b'}');
            }
        }
        if output.len() > RAW_LIMIT {
            return Err(limit("JSON value"));
        }
        Ok(())
    }
    let mut output = Vec::new();
    visit(value, &mut output, 0)?;
    Ok(output)
}

fn python_float(spelling: &str) -> Result<String, ApiError> {
    let (sign, value) = spelling
        .strip_prefix('-')
        .map_or(("", spelling), |v| ("-", v));
    let (mantissa, power) = if let Some((left, right)) = value.split_once(['e', 'E']) {
        (
            left,
            right.parse::<i32>().map_err(|_| invalid("finite number"))?,
        )
    } else {
        (value, 0)
    };
    let decimal = mantissa.find('.').unwrap_or(mantissa.len()) as i32;
    let digits: String = mantissa.chars().filter(|c| *c != '.').collect();
    if digits.is_empty() || !digits.bytes().all(|c| c.is_ascii_digit()) {
        return Err(invalid("finite number"));
    }
    let first = digits.bytes().position(|c| c != b'0');
    let Some(first) = first else {
        return Ok(format!("{sign}0.0"));
    };
    let exponent = decimal + power - first as i32 - 1;
    let significant = digits[first..].trim_end_matches('0');
    if !(-4..16).contains(&exponent) {
        let mut result = format!("{sign}{}", &significant[..1]);
        if significant.len() > 1 {
            result.push('.');
            result.push_str(&significant[1..]);
        }
        result.push('e');
        result.push(if exponent < 0 { '-' } else { '+' });
        result.push_str(&format!("{:02}", exponent.unsigned_abs()));
        Ok(result)
    } else {
        let point = exponent + 1;
        if point <= 0 {
            Ok(format!(
                "{sign}0.{}{significant}",
                "0".repeat((-point) as usize)
            ))
        } else if point as usize >= significant.len() {
            Ok(format!(
                "{sign}{significant}{}.0",
                "0".repeat(point as usize - significant.len())
            ))
        } else {
            let point = point as usize;
            Ok(format!(
                "{sign}{}.{}",
                &significant[..point],
                &significant[point..]
            ))
        }
    }
}

fn object_hash(kind: ObjectKind, payload: &[u8], children: &[String]) -> String {
    let mut digest = Sha256::new();
    digest.update(kind.as_str().as_bytes());
    digest.update(b"\n");
    for child in children {
        digest.update(child.as_bytes());
    }
    digest.update(b"\n");
    digest.update(payload);
    format!("{:x}", digest.finalize())
}
fn validate_object(value: &ChunkObject, expected: &str) -> Result<(), ApiError> {
    if !valid_hash(expected)
        || value.hash != expected
        || value.payload.len() > PAYLOAD_LIMIT
        || value.children.len() > 256
        || value.children.iter().any(|v| !valid_hash(v))
        || value.children.windows(2).any(|pair| pair[0] >= pair[1])
        || object_hash(value.kind, &value.payload, &value.children) != expected
    {
        return Err(invalid("object identity, payload or links"));
    }
    Ok(())
}

pub fn from_wire(expected_hash: &str, value: &Value) -> Result<ChunkObject, ApiError> {
    let object = value.as_object().ok_or_else(|| invalid("object schema"))?;
    if !(exact_fields(object, &["kind", "data", "children"])
        || (exact_fields(object, &["hash", "kind", "data", "children"])
            && object["hash"].as_str() == Some(expected_hash)))
    {
        return Err(invalid("object fields"));
    }
    let kind = match object["kind"].as_str() {
        Some("data") => ObjectKind::Data,
        Some("concat") => ObjectKind::Concat,
        _ => return Err(invalid("object kind")),
    };
    let data = object["data"]
        .as_str()
        .ok_or_else(|| invalid("object data"))?;
    if data.len() > PAYLOAD_LIMIT.div_ceil(3) * 4 {
        return Err(limit("encoded payload"));
    }
    let payload = STANDARD
        .decode(data)
        .map_err(|_| invalid("object base64"))?;
    let items = object["children"]
        .as_array()
        .ok_or_else(|| invalid("object children"))?;
    if items.len() > 256 {
        return Err(limit("child count"));
    }
    let children = items
        .iter()
        .map(|value| {
            value
                .as_str()
                .map(str::to_owned)
                .ok_or_else(|| invalid("child ID"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    let result = ChunkObject {
        hash: expected_hash.to_owned(),
        kind,
        payload,
        children,
    };
    validate_object(&result, expected_hash)?;
    Ok(result)
}
pub fn to_wire(value: &ChunkObject) -> Result<Value, ApiError> {
    validate_object(value, &value.hash)?;
    Ok(
        json!({"hash":value.hash,"kind":value.kind.as_str(),"data":STANDARD.encode(&value.payload),"children":value.children}),
    )
}

fn node(
    kind: ObjectKind,
    raw: &[u8],
    children: &[String],
    store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>,
) -> Result<String, ApiError> {
    if raw.len() > CHUNK {
        return Err(limit("node expansion"));
    }
    let children: Vec<_> = children
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect();
    if children.len() > 256 {
        return Err(limit("child count"));
    }
    if children.iter().any(|v| !valid_hash(v)) {
        return Err(invalid("child ID"));
    }
    let mut encoder = GzBuilder::new()
        .mtime(0)
        .operating_system(255)
        .write(Vec::new(), Compression::new(6));
    encoder.write_all(raw).map_err(|_| invalid("gzip encode"))?;
    let payload = encoder.finish().map_err(|_| invalid("gzip finish"))?;
    let identity = object_hash(kind, &payload, &children);
    let object = ChunkObject {
        hash: identity.clone(),
        kind,
        payload,
        children,
    };
    validate_object(&object, &identity)?;
    store(&object)?;
    Ok(identity)
}
fn links(
    identities: &[String],
    store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>,
) -> Result<Vec<String>, ApiError> {
    let mut seen = BTreeSet::new();
    let mut identities: Vec<_> = identities
        .iter()
        .filter(|v| seen.insert((*v).clone()))
        .cloned()
        .collect();
    if identities.iter().any(|v| !valid_hash(v)) {
        return Err(invalid("linked object ID"));
    }
    while identities.len() > 128 {
        identities = identities
            .chunks(128)
            .map(|group| node(ObjectKind::Concat, b"{\"parts\":[]}", group, store))
            .collect::<Result<_, _>>()?;
    }
    Ok(identities)
}
pub fn write_blob(
    raw: &[u8],
    dependencies: &[String],
    store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>,
) -> Result<String, ApiError> {
    if raw.len() > RAW_LIMIT {
        return Err(limit("blob"));
    }
    if dependencies.iter().any(|v| !valid_hash(v)) {
        return Err(invalid("linked object ID"));
    }
    let mut parts = raw
        .chunks(CHUNK)
        .map(|part| node(ObjectKind::Data, part, &[], store))
        .collect::<Result<Vec<_>, _>>()?;
    if parts.is_empty() {
        parts.push(node(ObjectKind::Data, &[], &[], store)?);
    }
    while parts.len() > 128 {
        parts = parts
            .chunks(128)
            .map(|group| {
                node(
                    ObjectKind::Concat,
                    &encode(&json!({"parts":group}))?,
                    group,
                    store,
                )
            })
            .collect::<Result<_, _>>()?;
    }
    let mut children = parts.clone();
    children.extend(links(dependencies, store)?);
    node(
        ObjectKind::Concat,
        &encode(&json!({"parts":parts}))?,
        &children,
        store,
    )
}

fn expand(payload: &[u8]) -> Result<Vec<u8>, ApiError> {
    // Multi-member gzip and zero padding are accepted by Python's GzipFile.
    // A cursor-backed bufread decoder leaves the exact tail for the next member.
    let mut cursor = Cursor::new(payload);
    let mut output = Vec::new();
    let mut members = 0;
    while (cursor.position() as usize) < payload.len() {
        if members > 0 {
            while (cursor.position() as usize) < payload.len()
                && payload[cursor.position() as usize] == 0
            {
                cursor.set_position(cursor.position() + 1);
            }
            if cursor.position() as usize == payload.len() {
                break;
            }
        }
        let previous = cursor.position();
        let mut decoder = GzDecoder::new(&mut cursor);
        decoder
            .by_ref()
            .take((CHUNK + 1 - output.len()) as u64)
            .read_to_end(&mut output)
            .map_err(|_| invalid("gzip data or CRC"))?;
        drop(decoder);
        if output.len() > CHUNK {
            return Err(limit("node expansion"));
        }
        if cursor.position() <= previous {
            return Err(invalid("gzip progress"));
        }
        members += 1;
    }
    if members == 0 {
        return Err(invalid("empty gzip"));
    }
    Ok(output)
}
pub fn read_blob(
    root: &str,
    maximum: usize,
    load: &mut dyn FnMut(&str) -> Result<ChunkObject, ApiError>,
) -> Result<Vec<u8>, ApiError> {
    fn visit(
        key: &str,
        depth: usize,
        maximum: usize,
        ancestors: &mut BTreeSet<String>,
        output: &mut Vec<u8>,
        load: &mut dyn FnMut(&str) -> Result<ChunkObject, ApiError>,
    ) -> Result<(), ApiError> {
        if depth > 24 || !valid_hash(key) || !ancestors.insert(key.to_owned()) {
            return Err(invalid("graph depth or cycle"));
        }
        let result = (|| {
            let object = load(key)?;
            validate_object(&object, key)?;
            let raw = expand(&object.payload)?;
            match object.kind {
                ObjectKind::Data => {
                    if raw.len() > maximum.saturating_sub(output.len()) {
                        return Err(limit("blob expansion"));
                    }
                    output.extend_from_slice(&raw);
                }
                ObjectKind::Concat => {
                    let value: Value =
                        serde_json::from_slice(&raw).map_err(|_| invalid("concat JSON"))?;
                    let index = value.as_object().ok_or_else(|| invalid("concat schema"))?;
                    if !exact_fields(index, &["parts"]) {
                        return Err(invalid("concat fields"));
                    }
                    let parts = index["parts"]
                        .as_array()
                        .ok_or_else(|| invalid("concat parts"))?;
                    if parts.len() > 128 {
                        return Err(limit("concat parts"));
                    }
                    for part in parts {
                        let part = part.as_str().ok_or_else(|| invalid("concat part ID"))?;
                        if object
                            .children
                            .binary_search_by(|v| v.as_str().cmp(part))
                            .is_err()
                        {
                            return Err(invalid("unlinked concat part"));
                        }
                        visit(part, depth + 1, maximum, ancestors, output, load)?;
                    }
                }
            }
            Ok(())
        })();
        ancestors.remove(key);
        result
    }
    if maximum > RAW_LIMIT {
        return Err(limit("read maximum"));
    }
    let mut output = Vec::new();
    visit(root, 0, maximum, &mut BTreeSet::new(), &mut output, load)?;
    Ok(output)
}

pub fn code_reference(value: &str) -> Result<Option<CodeReference>, ApiError> {
    let Some(raw) = value.strip_prefix(CODE_PREFIX) else {
        return Ok(None);
    };
    // A bounded reference is tiny even with JSON whitespace; reject before parsing.
    if raw.len() > CHUNK {
        return Err(invalid("code reference size"));
    }
    let value: Value = serde_json::from_str(raw).map_err(|_| invalid("code reference JSON"))?;
    let object = value
        .as_object()
        .ok_or_else(|| invalid("code reference schema"))?;
    if !(exact_fields(object, &["root", "sha256", "bytes"])
        || exact_fields(object, &["root", "sha256", "bytes", "offset"]))
    {
        return Err(invalid("code reference fields"));
    }
    let root = object["root"]
        .as_str()
        .filter(|v| valid_hash(v))
        .ok_or_else(|| invalid("code root"))?;
    let sha256 = object["sha256"]
        .as_str()
        .filter(|v| valid_hash(v))
        .ok_or_else(|| invalid("code digest"))?;
    let bytes = object["bytes"]
        .as_u64()
        .filter(|_| !object["bytes"].is_f64())
        .ok_or_else(|| invalid("code bytes"))?;
    let offset = match object.get("offset") {
        Some(value) => value
            .as_u64()
            .filter(|_| !value.is_f64())
            .ok_or_else(|| invalid("code offset"))?,
        None => 0,
    };
    if bytes > CODE_LIMIT as u64 || offset > CODE_LIMIT as u64 - bytes {
        return Err(invalid("code range"));
    }
    Ok(Some(CodeReference {
        root: root.to_owned(),
        sha256: sha256.to_owned(),
        bytes: bytes as usize,
        offset: offset as usize,
    }))
}
pub fn read_code(
    reference: &CodeReference,
    load: &mut dyn FnMut(&str) -> Result<ChunkObject, ApiError>,
) -> Result<String, ApiError> {
    let archive = read_blob(reference.root(), CODE_LIMIT, load)?;
    let raw = archive
        .get(reference.offset..reference.offset + reference.bytes)
        .ok_or_else(|| invalid("code archive range"))?;
    if hash(raw) != reference.sha256 {
        return Err(invalid("code archive digest"));
    }
    String::from_utf8(raw.to_vec()).map_err(|_| invalid("code UTF-8"))
}

fn tables(state: &Value) -> Result<&Map<String, Value>, ApiError> {
    if state.get("format").and_then(Value::as_str) != Some("tb-account-state-v1") {
        return Err(invalid("state format"));
    }
    let tables = state
        .get("tables")
        .and_then(Value::as_object)
        .ok_or_else(|| invalid("state tables"))?;
    if tables
        .keys()
        .any(|name| !TABLES.iter().any(|(table, _)| *table == name))
    {
        return Err(invalid("unknown state table"));
    }
    if state.get("publicAccounts").is_none() {
        return Err(invalid("public account profiles"));
    }
    Ok(tables)
}
fn primary(table: &str, keys: &[&str], row: &Value) -> Result<Vec<Value>, ApiError> {
    let row = row.as_object().ok_or_else(|| invalid("table row"))?;
    keys.iter()
        .map(|key| {
            let value = row
                .get(*key)
                .ok_or_else(|| invalid("missing primary key"))?;
            if table == "tb_rank_profile" || table == "official_xp_state" {
                if !(value.is_i64() || value.is_u64()) || value.is_f64() {
                    return Err(invalid("integer primary key"));
                }
            } else if !value.is_string() {
                return Err(invalid("text primary key"));
            }
            Ok(value.clone())
        })
        .collect()
}
fn text_or_empty(value: Option<&Value>) -> Result<String, ApiError> {
    match value {
        None | Some(Value::Null) | Some(Value::Bool(false)) => Ok(String::new()),
        Some(Value::String(value)) => Ok(value.clone()),
        Some(Value::Number(value)) if value.as_i64() == Some(0) || value.as_u64() == Some(0) => {
            Ok(String::new())
        }
        Some(Value::Number(value)) => {
            if value.is_f64() {
                python_float(&value.to_string())
            } else {
                Ok(value.to_string())
            }
        }
        Some(Value::Bool(true)) => Ok("True".to_owned()),
        _ => Err(invalid("timestamp type")),
    }
}
fn month(row: &Value) -> Result<String, ApiError> {
    Ok(text_or_empty(row.get("submitted_at"))?
        .chars()
        .take(7)
        .collect())
}
fn code_links(table: &str, rows: &[Value]) -> Result<Vec<String>, ApiError> {
    let mut result = Vec::new();
    for row in rows {
        let conflict = if table == "account_sync_conflicts" {
            row.get("data")
                .and_then(Value::as_str)
                .and_then(|v| serde_json::from_str::<Value>(v).ok())
        } else {
            None
        };
        let source = if table == "submissions" {
            Some(row)
        } else {
            conflict
                .as_ref()
                .filter(|v| v.get("table").and_then(Value::as_str) == Some("submissions"))
                .and_then(|v| v.get("row"))
                .filter(|v| v.is_object())
        };
        if let Some(value) = source.and_then(|v| v.get("code")).and_then(Value::as_str) {
            if let Some(reference) = code_reference(value)? {
                result.push(reference.root);
            }
        }
    }
    Ok(result)
}
pub fn pack_state(
    state: &Value,
    store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>,
) -> Result<String, ApiError> {
    let input = tables(state)?;
    let mut output = Map::new();
    let mut roots = Vec::new();
    let mut total = 0usize;
    for &(table, keys) in TABLES {
        let mut buckets: BTreeMap<String, Vec<Value>> = BTreeMap::new();
        let mut seen = BTreeSet::new();
        if let Some(rows) = input.get(table) {
            for row in rows.as_array().ok_or_else(|| invalid("table rows"))? {
                let identity = encode(&Value::Array(primary(table, keys, row)?))?;
                if !seen.insert(identity.clone()) {
                    return Err(invalid("duplicate primary key"));
                }
                let digest = hash(&identity);
                let width = if table == "account_problem_facts" || table == "account_sync_conflicts"
                {
                    2
                } else {
                    1
                };
                let bucket = if table == "submissions" {
                    format!("{}:{}", month(row)?, &digest[..width])
                } else {
                    digest[..width].to_owned()
                };
                buckets.entry(bucket).or_default().push(row.clone());
            }
        }
        if buckets.len() > 4096 {
            return Err(limit("table buckets"));
        }
        let mut entries = Vec::new();
        for (bucket, rows) in buckets {
            let dependencies = code_links(table, &rows)?;
            let raw = encode(&Value::Array(rows))?;
            total = total
                .checked_add(raw.len())
                .ok_or_else(|| limit("state expansion"))?;
            if total > STATE_LIMIT {
                return Err(limit("state expansion"));
            }
            let root = write_blob(&raw, &dependencies, store)?;
            roots.push(root.clone());
            entries.push(json!({"bucket":bucket,"root":root}));
        }
        output.insert(table.to_owned(), Value::Array(entries));
    }
    let profile = write_blob(&encode(&state["publicAccounts"])?, &[], store)?;
    roots.push(profile.clone());
    let raw = encode(
        &json!({"format":"tb-private-chunk-state-v2","tables":output,"publicAccounts":profile}),
    )?;
    if raw.len() > MANIFEST_LIMIT {
        return Err(limit("manifest"));
    }
    write_blob(&raw, &roots, store)
}

pub fn unpack_state(
    root: &str,
    load: &mut dyn FnMut(&str) -> Result<ChunkObject, ApiError>,
) -> Result<Unpacked, ApiError> {
    let manifest: Value = serde_json::from_slice(&read_blob(root, MANIFEST_LIMIT, load)?)
        .map_err(|_| invalid("manifest JSON"))?;
    let object = manifest
        .as_object()
        .ok_or_else(|| invalid("manifest schema"))?;
    if !exact_fields(object, &["format", "tables", "publicAccounts"])
        || object["format"].as_str() != Some("tb-private-chunk-state-v2")
    {
        return Err(invalid("manifest fields"));
    }
    let input = object["tables"]
        .as_object()
        .ok_or_else(|| invalid("manifest tables"))?;
    if input.len() != TABLES.len() || TABLES.iter().any(|(name, _)| !input.contains_key(*name)) {
        return Err(invalid("manifest table set"));
    }
    let profile_root = object["publicAccounts"]
        .as_str()
        .ok_or_else(|| invalid("profile root"))?;
    let profiles: Value = serde_json::from_slice(&read_blob(profile_root, RAW_LIMIT, load)?)
        .map_err(|_| invalid("profiles JSON"))?;
    let mut total = 0usize;
    let mut duplicate_learning_summary = false;
    let mut output = Map::new();
    for &(table, keys) in TABLES {
        let entries = input[table]
            .as_array()
            .ok_or_else(|| invalid("table index"))?;
        if entries.len() > 4096 {
            return Err(limit("table buckets"));
        }
        let mut seen = BTreeSet::new();
        let mut buckets = BTreeSet::new();
        let mut rows = Vec::new();
        for entry in entries {
            let entry = entry.as_object().ok_or_else(|| invalid("bucket schema"))?;
            if !exact_fields(entry, &["bucket", "root"]) {
                return Err(invalid("bucket fields"));
            }
            let bucket = entry["bucket"]
                .as_str()
                .ok_or_else(|| invalid("bucket name"))?;
            if !buckets.insert(bucket.to_owned()) {
                return Err(invalid("duplicate bucket"));
            }
            let root = entry["root"]
                .as_str()
                .ok_or_else(|| invalid("bucket root"))?;
            let raw = read_blob(root, RAW_LIMIT, load)?;
            total = total
                .checked_add(raw.len())
                .ok_or_else(|| limit("state expansion"))?;
            if total > STATE_LIMIT {
                return Err(limit("state expansion"));
            }
            let group: Value = serde_json::from_slice(&raw).map_err(|_| invalid("bucket JSON"))?;
            let Value::Array(group) = group else {
                return Err(invalid("bucket rows"));
            };
            for row in group {
                let identity = primary(table, keys, &row)?;
                if !seen.insert(encode(&Value::Array(identity.clone()))?) {
                    if table == "account_preferences"
                        && identity == vec![json!("learning-summary-v1")]
                    {
                        duplicate_learning_summary = true;
                    } else {
                        return Err(invalid("duplicate primary key"));
                    }
                }
                let sorting = identity
                    .iter()
                    .map(|v| text_or_empty(Some(v)))
                    .collect::<Result<Vec<_>, _>>()?;
                rows.push((sorting, row));
            }
        }
        rows.sort_by(|a, b| a.0.cmp(&b.0)); // stable: duplicate legacy summaries preserve their order.
        output.insert(
            table.to_owned(),
            Value::Array(rows.into_iter().map(|(_, row)| row).collect()),
        );
    }
    Ok(Unpacked {
        state: json!({"format":"tb-account-state-v1","tables":output,"publicAccounts":profiles}),
        duplicate_learning_summary,
    })
}

fn timestamp(raw: &Value) -> Option<DateTime<Utc>> {
    let value = raw.as_str()?;
    if let Ok(time) = DateTime::parse_from_rfc3339(value) {
        return Some(time.with_timezone(&Utc));
    }
    for format in [
        "%Y-%m-%dT%H:%M:%S%.f",
        "%Y-%m-%d %H:%M:%S%.f",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ] {
        if let Ok(time) = NaiveDateTime::parse_from_str(value, format) {
            return Some(time.and_utc());
        }
    }
    NaiveDate::parse_from_str(value, "%Y-%m-%d")
        .ok()?
        .and_hms_opt(0, 0, 0)
        .map(|time| time.and_utc())
}
pub fn canonicalize_state(
    state: &Value,
    known_refs: &BTreeMap<String, String>,
    now: DateTime<Utc>,
    store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>,
) -> Result<Canonicalized, ApiError> {
    let input = tables(state)?;
    let mut projection = state.clone();
    let mut rows = input
        .get("submissions")
        .map(|v| {
            v.as_array()
                .cloned()
                .ok_or_else(|| invalid("submission rows"))
        })
        .transpose()?
        .unwrap_or_default();
    let cutoff = now
        .checked_sub_signed(Duration::days(30))
        .ok_or_else(|| invalid("archive cutoff"))?;
    let mut pending: BTreeMap<String, Vec<(String, usize, Vec<u8>)>> = BTreeMap::new();
    let mut seen = BTreeSet::new();
    for (index, row) in rows.iter_mut().enumerate() {
        let identity = primary("submissions", &["id"], row)?[0]
            .as_str()
            .unwrap()
            .to_owned();
        if !seen.insert(identity.clone()) {
            return Err(invalid("duplicate submission ID"));
        }
        let code = match row.get("code") {
            Some(value) => value
                .as_str()
                .ok_or_else(|| invalid("submission code type"))?,
            None => "",
        };
        if code_reference(code)?.is_some() {
            continue;
        }
        let raw = code.as_bytes();
        if let Some(serialized) = known_refs.get(&identity) {
            let reference =
                code_reference(serialized)?.ok_or_else(|| invalid("known code reference"))?;
            if code.is_empty() || hash(raw) == reference.sha256 {
                if !code.is_empty() && raw.len() != reference.bytes {
                    return Err(invalid("known code length"));
                }
                row["code"] = json!(serialized);
                continue;
            }
        }
        if !code.is_empty()
            && row
                .get("finished_at")
                .and_then(timestamp)
                .is_some_and(|time| time < cutoff)
        {
            if raw.len() > CODE_LIMIT {
                return Err(limit("historical source"));
            }
            let bucket = format!("{}:{}", month(row)?, &hash(identity.as_bytes())[..1]);
            pending
                .entry(bucket)
                .or_default()
                .push((identity, index, raw.to_vec()));
        }
    }
    let mut saved = Vec::new();
    fn archive(
        items: &[(String, usize, Vec<u8>)],
        rows: &mut [Value],
        saved: &mut Vec<(String, String)>,
        store: &mut dyn FnMut(&ChunkObject) -> Result<(), ApiError>,
    ) -> Result<(), ApiError> {
        if items.is_empty() {
            return Ok(());
        }
        let raw: Vec<_> = items
            .iter()
            .flat_map(|(_, _, code)| code.iter().copied())
            .collect();
        let root = write_blob(&raw, &[], store)?;
        let mut offset = 0;
        for (identity, index, code) in items {
            let reference = format!(
                "{CODE_PREFIX}{}",
                String::from_utf8(encode(
                    &json!({"root":root,"sha256":hash(code),"bytes":code.len(),"offset":offset})
                )?)
                .map_err(|_| invalid("reference encoding"))?
            );
            rows[*index]["code"] = json!(reference);
            saved.push((identity.clone(), reference));
            offset += code.len();
        }
        Ok(())
    }
    for (_, mut items) in pending {
        items.sort_by(|a, b| a.0.cmp(&b.0));
        let mut group = Vec::new();
        let mut size = 0;
        for item in items {
            if !group.is_empty() && size + item.2.len() > CHUNK {
                archive(&group, &mut rows, &mut saved, store)?;
                group.clear();
                size = 0;
            }
            size += item.2.len();
            group.push(item);
        }
        archive(&group, &mut rows, &mut saved, store)?;
    }
    projection["tables"]["submissions"] = Value::Array(rows);
    Ok(Canonicalized {
        state: projection,
        code_references: saved,
    })
}
