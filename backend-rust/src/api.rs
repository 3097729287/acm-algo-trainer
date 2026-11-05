use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;

pub const PROTOCOL_VERSION: u32 = 1;

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "UPPERCASE")]
pub enum Method {
    Get,
    Post,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ApiRequest {
    pub version: u32,
    pub id: String,
    pub method: Method,
    pub path: String,
    #[serde(default)]
    pub query: BTreeMap<String, Vec<String>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub body: Option<Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub token: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub owner: Option<String>,
}

impl ApiRequest {
    pub fn get(path: &str) -> Self {
        Self {
            version: PROTOCOL_VERSION,
            id: uuid::Uuid::new_v4().simple().to_string(),
            method: Method::Get,
            path: path.into(),
            query: BTreeMap::new(),
            body: None,
            token: None,
            owner: None,
        }
    }
    pub fn param(&self, key: &str) -> Option<&str> {
        self.query
            .get(key)
            .and_then(|v| v.first())
            .map(String::as_str)
    }
    pub fn validate(&self) -> Result<(), ApiError> {
        if self.version != PROTOCOL_VERSION {
            return Err(ApiError::new(426, "PROTOCOL_VERSION", "接口版本不兼容"));
        }
        if self.id.is_empty() || self.id.len() > 128 || self.id.chars().any(char::is_control) {
            return Err(ApiError::bad("请求编号无效"));
        }
        if self.path.is_empty()
            || self.path.len() > 256
            || self.path.starts_with('/')
            || self.path.ends_with('/')
            || self
                .path
                .split('/')
                .any(|s| s.is_empty() || s == "." || s == "..")
            || self
                .path
                .bytes()
                .any(|b| !(b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'/' || b == b'-'))
        {
            return Err(ApiError::bad("接口路径无效"));
        }
        if self.query.len() > 64
            || self
                .query
                .iter()
                .any(|(k, v)| k.len() > 128 || v.len() > 128 || v.iter().any(|s| s.len() > 4096))
        {
            return Err(ApiError::bad("查询参数过大"));
        }
        match self.method {
            Method::Get if self.body.is_some() => {
                return Err(ApiError::bad("读取请求不能携带正文"));
            }
            Method::Post if !self.body.as_ref().is_some_and(Value::is_object) => {
                return Err(ApiError::bad("请求必须是 JSON 对象"));
            }
            _ => {}
        }
        let maximum = match self.path.as_str() {
            "preferences" => 48 * 1024 * 1024,
            "training-lists/add" | "training-lists/save" => 32 * 1024 * 1024,
            _ => 262144,
        };
        if self
            .body
            .as_ref()
            .is_some_and(|v| v.to_string().len() > maximum)
        {
            return Err(ApiError::bad("请求数据大小无效"));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct ApiError {
    pub code: String,
    pub status: u16,
    pub message: String,
    pub retryable: bool,
    #[serde(default)]
    pub uncertain: bool,
}
impl ApiError {
    pub fn new(status: u16, code: &str, message: &str) -> Self {
        Self {
            code: code.into(),
            status,
            message: message.into(),
            retryable: matches!(status, 429 | 502 | 503 | 504),
            uncertain: false,
        }
    }
    pub fn bad(message: &str) -> Self {
        Self::new(400, "VALIDATION", message)
    }
    pub fn missing(message: &str) -> Self {
        Self::new(404, "NOT_FOUND", message)
    }
    pub fn conflict(message: &str) -> Self {
        Self::new(409, "CONFLICT", message)
    }
    pub fn pending() -> Self {
        Self::new(
            501,
            "MIGRATION_PENDING",
            "此功能尚未完成 Rust 兼容性验收，请使用当前正式版",
        )
    }
}
impl std::fmt::Display for ApiError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.message)
    }
}
impl std::error::Error for ApiError {}
impl From<rusqlite::Error> for ApiError {
    fn from(error: rusqlite::Error) -> Self {
        match error {
            rusqlite::Error::QueryReturnedNoRows => Self::missing("没有找到这条记录"),
            rusqlite::Error::SqliteFailure(ref code, _)
                if matches!(
                    code.code,
                    rusqlite::ErrorCode::DatabaseBusy | rusqlite::ErrorCode::DatabaseLocked
                ) =>
            {
                Self::new(503, "STORAGE_BUSY", "本机数据正在保存，请稍后重试")
            }
            _ => Self::new(500, "STORAGE_ERROR", "本机数据读取或保存失败，原数据已保留"),
        }
    }
}
impl From<std::io::Error> for ApiError {
    fn from(_: std::io::Error) -> Self {
        Self::new(500, "IO_ERROR", "本机文件读取或保存失败，原数据已保留")
    }
}
impl From<serde_json::Error> for ApiError {
    fn from(_: serde_json::Error) -> Self {
        Self::new(500, "INVALID_STORED_DATA", "本机记录格式异常，原数据已保留")
    }
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ApiResponse {
    pub version: u32,
    pub id: String,
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<ApiError>,
    pub meta: ResponseMeta,
}
#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ResponseMeta {
    pub elapsed_micros: u64,
    pub backend: String,
}
impl ApiResponse {
    pub fn complete(
        id: String,
        result: Result<Value, ApiError>,
        elapsed: std::time::Duration,
    ) -> Self {
        let (data, error) = match result {
            Ok(v) => (Some(v), None),
            Err(e) => (None, Some(e)),
        };
        Self {
            version: PROTOCOL_VERSION,
            id,
            ok: error.is_none(),
            data,
            error,
            meta: ResponseMeta {
                elapsed_micros: elapsed.as_micros().min(u64::MAX as u128) as u64,
                backend: "rust".into(),
            },
        }
    }
}

pub fn required_text<'a>(body: &'a Value, key: &str, maximum: usize) -> Result<&'a str, ApiError> {
    body.get(key)
        .and_then(Value::as_str)
        .filter(|s| !s.is_empty() && s.len() <= maximum && !s.contains('\0'))
        .ok_or_else(|| ApiError::bad("请求字段格式无效"))
}
pub fn fields(body: &Value, allowed: &[&str]) -> Result<(), ApiError> {
    if !body
        .as_object()
        .is_some_and(|o| o.keys().all(|k| allowed.contains(&k.as_str())))
    {
        return Err(ApiError::bad("请求字段无效"));
    }
    Ok(())
}
pub fn now() -> String {
    chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Micros, true)
}
pub fn today() -> String {
    chrono::Utc::now()
        .with_timezone(&chrono::FixedOffset::east_opt(28800).unwrap())
        .format("%Y-%m-%d")
        .to_string()
}
