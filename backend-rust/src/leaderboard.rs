//! Account-bound shared-service client. HTTP never borrows a journal connection.
//! The guard must be a quick lease/epoch check, not a callback that takes a DB lock.
//! Tokens are borrowed for one call and are never stored in caches or diagnostics.
use crate::api::{ApiError, fields};
use base64::{Engine, engine::general_purpose::STANDARD};
use chrono::{DateTime, Datelike, Duration as ChronoDuration, FixedOffset, NaiveDate, Utc};
use reqwest::{Method, blocking::Client};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::HashMap,
    io::Read,
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};

pub mod sync;

const SMALL_LIMIT: usize = 256 * 1024;
const SOCIAL_LIMIT: usize = 4 * 1024 * 1024;
const AVATAR_LIMIT: usize = 16_065_568;
const MAX_AVATAR_CACHE: usize = 32 * 1024 * 1024;
const NOTICE: &str = "排行统计 ToBe 保存的原站已确认首次 AC 题数；样例、运行与重复题不计入。记录由客户端同步，暂不提供独立防作弊认证。";
const ACTIVITIES: &[&str] = &[
    "online", "matching", "problem", "replay", "contest", "lecture", "lab", "wiki", "template",
    "ranked", "thought", "library", "lists", "growth", "records", "settings", "rankings", "idle",
];

/// Construct only from the unlocked account manager's owned session snapshot.
/// In particular, this type intentionally has no Debug or Serialize implementation.
pub struct AuthContext<'a> {
    pub owner: &'a str,
    pub endpoint: &'a str,
    pub bearer: &'a str,
    pub admin: bool,
}

#[derive(Clone, PartialEq, Eq, Hash)]
pub(super) struct Scope {
    owner: String,
    endpoint: String,
    epoch: [u8; 32],
}
#[derive(Clone)]
struct Saved {
    at: DateTime<Utc>,
    clock: Instant,
    value: Value,
}
impl Saved {
    fn fresh(&self, now: DateTime<Utc>, seconds: u64) -> bool {
        now >= self.at
            && (now - self.at).num_milliseconds() < (seconds * 1000) as i64
            && self.clock.elapsed() < Duration::from_secs(seconds)
    }
}
#[derive(Default)]
struct Cache {
    profiles: HashMap<Scope, Saved>,
    boards: HashMap<(Scope, String, String), Saved>,
    avatars: HashMap<(Scope, String, String), Saved>,
    sequence: u64,
    board_requests: HashMap<(Scope, String, String), u64>,
    avatar_requests: HashMap<(Scope, String), u64>,
}

#[derive(Clone)]
pub struct LeaderboardClient {
    http: Client,
    loopback_http: Client,
    cache: Arc<Mutex<Cache>>,
}

pub(super) fn checked(still_current: &dyn Fn() -> bool) -> Result<(), ApiError> {
    if still_current() {
        Ok(())
    } else {
        Err(ApiError::new(409, "OWNER_CHANGED", "账号已切换"))
    }
}
pub(super) fn invalid_receipt() -> ApiError {
    ApiError::new(502, "SHARED_RECEIPT", "账号服务回执无效")
}
pub(super) fn sha(value: &[u8]) -> String {
    format!("{:x}", Sha256::digest(value))
}
fn valid_sha(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
pub(super) fn valid_uuid(value: &str) -> bool {
    uuid::Uuid::parse_str(value).ok().is_some_and(|v| {
        v.get_version_num() == 4
            && v.get_variant() == uuid::Variant::RFC4122
            && v.hyphenated().to_string().eq_ignore_ascii_case(value)
    })
}
pub(super) fn day(now: DateTime<Utc>) -> String {
    now.with_timezone(&FixedOffset::east_opt(28800).unwrap())
        .format("%Y-%m-%d")
        .to_string()
}

/// Same configuration boundary as backend/leaderboard.py; empty means disabled.
/// Kept local until account_transport is merged; no caller-supplied route is accepted.
pub fn validate_endpoint(value: &str) -> Result<String, ApiError> {
    let value = value.trim().trim_end_matches('/');
    if value.is_empty() {
        return Ok(String::new());
    }
    let reject = || ApiError::bad("排行榜须使用 HTTPS 地址；本机测试可使用回环 HTTP");
    if value.len() > 2048 || value.chars().any(char::is_control) || value.contains('\\') {
        return Err(reject());
    }
    let parsed = url::Url::parse(value).map_err(|_| reject())?;
    let loopback = matches!(
        parsed.host_str(),
        Some("localhost" | "127.0.0.1" | "[::1]" | "::1")
    );
    if parsed.host_str().is_none()
        || !parsed.username().is_empty()
        || parsed.password().is_some()
        || parsed.query().is_some()
        || parsed.fragment().is_some()
        || !(parsed.scheme() == "https" || loopback && parsed.scheme() == "http")
        || !loopback && parsed.port().is_some_and(|p| p != 443)
    {
        return Err(reject());
    }
    Ok(value.to_owned())
}

/// The caller supplies the last *real* input; heartbeat/polling never alters it.
pub fn activity_after_input<'a>(
    activity: &'a str,
    last_input: DateTime<Utc>,
    now: DateTime<Utc>,
) -> Result<&'a str, ApiError> {
    if !ACTIVITIES.contains(&activity) || last_input > now {
        return Err(ApiError::bad("在线状态无效"));
    }
    Ok(if now - last_input >= ChronoDuration::seconds(300) {
        "idle"
    } else {
        activity
    })
}

impl LeaderboardClient {
    pub fn new(timeout: Duration) -> Result<Self, ApiError> {
        if timeout.is_zero() || timeout > Duration::from_secs(60) {
            return Err(ApiError::bad("连接超时设置无效"));
        }
        let builder = || {
            Client::builder()
                .timeout(timeout)
                .connect_timeout(timeout.min(Duration::from_secs(3)))
                .redirect(reqwest::redirect::Policy::none())
                .retry(reqwest::retry::never())
                .pool_max_idle_per_host(2)
                .user_agent("TB/2 Native Ranking")
        };
        let http = builder()
            .build()
            .map_err(|_| ApiError::new(503, "SHARED_CONNECTION", "账号服务暂时无法连接"))?;
        // Local fixtures/servers must never put an account bearer through a
        // machine-wide proxy. Custom remote services retain the system route.
        let loopback_http = builder()
            .no_proxy()
            .build()
            .map_err(|_| ApiError::new(503, "SHARED_CONNECTION", "账号服务暂时无法连接"))?;
        Ok(Self {
            http,
            loopback_http,
            cache: Arc::new(Mutex::new(Cache::default())),
        })
    }
    pub(super) fn scope(
        &self,
        auth: &AuthContext<'_>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Scope, ApiError> {
        checked(guard)?;
        if auth.admin {
            return Err(ApiError::new(
                403,
                "ADMIN_WORKSPACE",
                "管理员工作区不连接公共排行",
            ));
        }
        if !valid_uuid(auth.owner)
            || auth.bearer.is_empty()
            || auth.bearer.len() > 4096
            || auth.bearer.bytes().any(|b| !b.is_ascii_graphic())
        {
            return Err(ApiError::new(401, "SESSION_REQUIRED", "请先登录账号"));
        }
        let endpoint = validate_endpoint(auth.endpoint)?;
        if endpoint.is_empty() {
            return Err(ApiError::new(
                503,
                "SHARED_UNCONFIGURED",
                "排行榜服务尚未配置",
            ));
        }
        Ok(Scope {
            owner: auth.owner.to_owned(),
            endpoint,
            epoch: Sha256::digest(auth.bearer.as_bytes()).into(),
        })
    }
    fn lock(&self) -> Result<std::sync::MutexGuard<'_, Cache>, ApiError> {
        self.cache
            .lock()
            .map_err(|_| ApiError::new(503, "SHARED_BUSY", "账号服务缓存正在恢复"))
    }
    /// Called on logout/replacement/invalidated lease; has no network side effects.
    pub fn invalidate_owner(&self, owner: &str) -> Result<(), ApiError> {
        let mut cache = self.lock()?;
        cache.profiles.retain(|s, _| s.owner != owner);
        cache.boards.retain(|(s, _, _), _| s.owner != owner);
        cache.avatars.retain(|(s, _, _), _| s.owner != owner);
        cache.board_requests.retain(|(s, _, _), _| s.owner != owner);
        cache.avatar_requests.retain(|(s, _), _| s.owner != owner);
        Ok(())
    }
    fn invalidate_scope(&self, scope: &Scope) {
        if let Ok(mut c) = self.cache.lock() {
            c.profiles.remove(scope);
            c.boards.retain(|(s, _, _), _| s != scope);
            c.avatars.retain(|(s, _, _), _| s != scope);
            c.board_requests.retain(|(s, _, _), _| s != scope);
            c.avatar_requests.retain(|(s, _), _| s != scope);
        }
    }
    pub(super) fn request(
        &self,
        auth: &AuthContext<'_>,
        method: Method,
        path: &str,
        body: Option<&Value>,
        limit: usize,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        let scope = self.scope(auth, guard)?;
        // All paths are module constants plus percent-encoded validated parameters.
        debug_assert!(path.starts_with("/v1/"));
        let writing = method != Method::GET;
        let loopback = url::Url::parse(&scope.endpoint).ok().is_some_and(|v| {
            matches!(
                v.host_str(),
                Some("localhost" | "127.0.0.1" | "[::1]" | "::1")
            )
        });
        let http = if loopback {
            &self.loopback_http
        } else {
            &self.http
        };
        let mut request = http
            .request(method, format!("{}{path}", scope.endpoint))
            .header("Accept", "application/json")
            .header("Content-Type", "application/json")
            .header("X-TB-User", auth.owner)
            .header("Authorization", format!("Bearer {}", auth.bearer))
            .header("X-TB-State-Protocol", "1");
        if let Some(body) = body {
            request =
                request.body(serde_json::to_vec(body).map_err(|_| ApiError::bad("请求内容无效"))?);
        }
        checked(guard)?;
        let response = request.send();
        checked(guard)?;
        let mut response = response.map_err(|_| {
            let mut e = ApiError::new(503, "SHARED_CONNECTION", "账号服务暂时无法连接");
            e.uncertain = writing;
            e
        })?;
        let status = response.status().as_u16();
        if !(200..300).contains(&status) {
            if status == 401 {
                self.invalidate_scope(&scope);
            }
            let mut e = ApiError::new(
                if (300..400).contains(&status) {
                    502
                } else {
                    status
                },
                if (300..400).contains(&status) {
                    "SHARED_REDIRECT"
                } else if status == 401 {
                    "SESSION_EXPIRED"
                } else {
                    "SHARED_HTTP"
                },
                if status == 401 {
                    "登录已失效，请重新登录"
                } else if status == 429 {
                    "操作较频繁，请稍后重试"
                } else {
                    "账号服务暂时无法完成请求"
                },
            );
            e.uncertain = writing && (status >= 500 || (300..400).contains(&status));
            return Err(e);
        }
        if response.content_length().is_some_and(|n| n > limit as u64) {
            let mut e = invalid_receipt();
            e.uncertain = writing;
            return Err(e);
        }
        let mut bytes = Vec::with_capacity((limit + 1).min(8192));
        let read = response
            .by_ref()
            .take((limit + 1) as u64)
            .read_to_end(&mut bytes);
        checked(guard)?;
        if read.is_err() || bytes.len() > limit {
            let mut e = invalid_receipt();
            e.uncertain = writing;
            return Err(e);
        }
        let value = serde_json::from_slice::<Value>(&bytes)
            .ok()
            .filter(Value::is_object)
            .ok_or_else(|| {
                let mut e = invalid_receipt();
                e.uncertain = writing;
                e
            })?;
        Ok(value)
    }
    pub(super) fn verified_profile(
        &self,
        auth: &AuthContext<'_>,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        let scope = self.scope(auth, guard)?;
        {
            let c = self.lock()?;
            checked(guard)?;
            if let Some(v) = c.profiles.get(&scope).filter(|v| v.fresh(now, 15)) {
                return Ok(v.value.clone());
            }
        }
        let value = self.request(auth, Method::GET, "/v1/profile", None, SMALL_LIMIT, guard)?;
        if value["userId"] != auth.owner {
            return Err(invalid_receipt());
        }
        checked(guard)?;
        let mut c = self.lock()?;
        checked(guard)?;
        if c.profiles.len() >= 32 {
            c.profiles.clear();
        }
        c.profiles.insert(
            scope,
            Saved {
                at: now,
                clock: Instant::now(),
                value: value.clone(),
            },
        );
        Ok(value)
    }
    pub fn rankings(
        &self,
        auth: &AuthContext<'_>,
        period: &str,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        self.fetch_rankings(auth, period, now, guard, false)
    }
    fn fetch_rankings(
        &self,
        auth: &AuthContext<'_>,
        period: &str,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
        force: bool,
    ) -> Result<Value, ApiError> {
        if !["daily", "weekly", "total"].contains(&period) {
            return Err(ApiError::bad("排行周期须为 daily、weekly 或 total"));
        }
        let scope = self.scope(auth, guard)?;
        let key = (scope.clone(), period.to_owned(), day(now));
        let sequence = {
            let mut c = self.lock()?;
            checked(guard)?;
            if let Some(saved) = c.boards.get(&key).filter(|v| !force && v.fresh(now, 8)) {
                return Ok(board_state(saved.value.clone(), &scope, "ready", "", true));
            }
            c.sequence = c.sequence.wrapping_add(1);
            let n = c.sequence;
            if c.board_requests.len() >= 256 {
                c.board_requests
                    .retain(|(s, _, date), _| s == &scope && date == &key.2);
            }
            c.board_requests.insert(key.clone(), n);
            n
        };
        let answer: Result<Value, ApiError> = (|| {
            self.verified_profile(auth, now, guard)?;
            let value = self.request(
                auth,
                Method::GET,
                &format!("/v1/leaderboard?period={period}"),
                None,
                SMALL_LIMIT,
                guard,
            )?;
            validate_board(&value, auth.owner, period, now)?;
            Ok(value)
        })();
        checked(guard)?;
        match answer {
            Ok(value) => {
                let mut c = self.lock()?;
                checked(guard)?;
                if c.board_requests.get(&key) == Some(&sequence) {
                    if c.boards.len() >= 96 {
                        c.boards
                            .retain(|(s, _, date), _| s == &scope && date == &key.2);
                    }
                    c.boards.insert(
                        key,
                        Saved {
                            at: now,
                            clock: Instant::now(),
                            value: value.clone(),
                        },
                    );
                } else if let Some(latest) = c.boards.get(&key) {
                    return Ok(board_state(latest.value.clone(), &scope, "ready", "", true));
                }
                Ok(board_state(value, &scope, "ready", "", true))
            }
            Err(error) if ![401, 403, 409].contains(&error.status) => {
                let c = self.lock()?;
                checked(guard)?;
                let saved = c.boards.get(&key);
                let value = saved.map(|v| v.value.clone()).unwrap_or_else(
                    || json!({"period":period,"date":day(now),"entries":[],"self":null}),
                );
                Ok(board_state(
                    value,
                    &scope,
                    "error",
                    &error.message,
                    saved.is_some(),
                ))
            }
            Err(error) => Err(error),
        }
    }
    pub fn avatar(
        &self,
        auth: &AuthContext<'_>,
        user_id: &str,
        expected_hash: &str,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        if !valid_uuid(user_id) || !valid_sha(expected_hash) {
            return Err(ApiError::bad("头像查询参数无效"));
        }
        let scope = self.scope(auth, guard)?;
        let key = (scope.clone(), user_id.to_owned(), expected_hash.to_owned());
        let sequence = {
            let mut c = self.lock()?;
            checked(guard)?;
            if let Some(v) = c.avatars.get(&key).filter(|v| v.fresh(now, 15)) {
                return Ok(v.value.clone());
            }
            c.sequence = c.sequence.wrapping_add(1);
            let n = c.sequence;
            if c.avatar_requests.len() >= 256 {
                // A single owner's repeated different target IDs must be
                // bounded too. Evicted in-flight reads fail the sequence gate.
                if let Some(oldest) = c
                    .avatar_requests
                    .iter()
                    .min_by_key(|(_, n)| **n)
                    .map(|(key, _)| key.clone())
                {
                    c.avatar_requests.remove(&oldest);
                }
            }
            c.avatar_requests
                .insert((scope.clone(), user_id.to_owned()), n);
            n
        };
        self.verified_profile(auth, now, guard)?;
        let value = self.request(
            auth,
            Method::GET,
            &format!("/v1/avatars/{user_id}"),
            None,
            AVATAR_LIMIT,
            guard,
        )?;
        let avatar = value["avatarData"].as_str().ok_or_else(invalid_receipt)?;
        validate_avatar(avatar).map_err(|_| invalid_receipt())?;
        let digest = if avatar.is_empty() {
            Value::Null
        } else {
            json!(sha(avatar.as_bytes()))
        };
        if value["avatarHash"] != digest {
            return Err(ApiError::new(502, "AVATAR_INTEGRITY", "头像校验失败"));
        }
        let answer = json!({"avatarData":avatar,"avatarHash":digest});
        checked(guard)?;
        let mut c = self.lock()?;
        checked(guard)?;
        if c.avatar_requests.get(&(scope.clone(), user_id.to_owned())) != Some(&sequence) {
            return Err(ApiError::new(
                409,
                "SHARED_STALE_RESPONSE",
                "头像已重新读取，请重试",
            ));
        }
        // Discard earlier hashes, including after removal; never retain a stale portrait.
        c.avatars
            .retain(|(s, id, _), _| s != &scope || id != user_id);
        if let Some(digest) = digest.as_str() {
            c.avatars.insert(
                (scope, user_id.to_owned(), digest.to_owned()),
                Saved {
                    at: now,
                    clock: Instant::now(),
                    value: answer.clone(),
                },
            );
            while c.avatars.len() > 100
                || c.avatars
                    .values()
                    .map(|v| v.value["avatarData"].as_str().map_or(0, str::len))
                    .sum::<usize>()
                    > MAX_AVATAR_CACHE
            {
                let oldest = c
                    .avatars
                    .iter()
                    .min_by_key(|(_, v)| v.clock)
                    .map(|(k, _)| k.clone());
                if let Some(key) = oldest {
                    c.avatars.remove(&key);
                } else {
                    break;
                }
            }
        }
        Ok(answer)
    }
    pub fn social(
        &self,
        auth: &AuthContext<'_>,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        self.verified_profile(auth, now, guard)?;
        let answer = self.request(auth, Method::GET, "/v1/social", None, SOCIAL_LIMIT, guard);
        if let Err(ref e) = answer {
            if [404, 405, 501].contains(&e.status) {
                return Ok(
                    json!({"available":false,"protocol":1,"totalLikes":0,"unreadCount":0,"notifications":[],"activity":[]}),
                );
            }
        }
        let value = answer?;
        validate_social(&value, auth.owner)?;
        checked(guard)?;
        Ok(value)
    }
    pub fn social_write(
        &self,
        auth: &AuthContext<'_>,
        action: &str,
        body: &Value,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        validate_social_write(action, body, auth.owner)?;
        self.verified_profile(auth, now, guard)?;
        let value = self.request(
            auth,
            Method::POST,
            &format!("/v1/social/{action}"),
            Some(body),
            SMALL_LIMIT,
            guard,
        )?;
        let valid = match action {
            "likes" => {
                value["targetId"] == body["targetId"]
                    && value["created"].is_boolean()
                    && valid_likes(&value["likes"])
            }
            "comments" => {
                value["id"] == body["requestId"]
                    && value["created"].is_boolean()
                    && value["createdAt"]
                        .as_str()
                        .is_some_and(|v| DateTime::parse_from_rfc3339(v).is_ok())
                    && value.get("replyTo") == body.get("replyTo")
            }
            "read" => value["ok"] == true,
            _ => false,
        };
        if !valid {
            let mut e = invalid_receipt();
            e.uncertain = true;
            return Err(e);
        }
        checked(guard)?;
        if action == "likes" {
            let scope = self.scope(auth, guard)?;
            let mut c = self.lock()?;
            checked(guard)?;
            c.sequence = c.sequence.wrapping_add(1);
            let revision = c.sequence;
            // Keep the last successful board and apply the actual receipt. A
            // concurrent older GET cannot restore the pre-click liked state.
            for ((s, period, _), saved) in c.boards.iter_mut().filter(|((s, _, _), _)| s == &scope)
            {
                let _ = s;
                let total = value["counts"][period.as_str()]
                    .as_u64()
                    .unwrap_or_else(|| value["likes"]["total"].as_u64().unwrap());
                if let Some(entries) = saved.value["entries"].as_array_mut() {
                    for entry in entries
                        .iter_mut()
                        .filter(|e| e["userId"] == body["targetId"])
                    {
                        entry["likes"] = json!({"total":total,"likedToday":true});
                    }
                }
                if saved.value["self"]["userId"] == body["targetId"] {
                    saved.value["self"]["likes"] = json!({"total":total,"likedToday":true});
                }
                saved.at = now - ChronoDuration::seconds(8);
            }
            for ((s, _, _), n) in &mut c.board_requests {
                if s == &scope {
                    *n = revision;
                }
            }
        }
        Ok(value)
    }
    pub fn list_likes(
        &self,
        auth: &AuthContext<'_>,
        ids: &[String],
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        if ids.len() > 100
            || ids
                .iter()
                .any(|s| s.is_empty() || s.len() > 160 || s.chars().any(char::is_control))
        {
            return Err(ApiError::bad("题单编号无效"));
        }
        self.verified_profile(auth, now, guard)?;
        let query = url::form_urlencoded::Serializer::new(String::new())
            .extend_pairs(ids.iter().map(|id| ("id", id)))
            .finish();
        let answer = self.request(
            auth,
            Method::GET,
            &format!("/v1/training-list-likes?{query}"),
            None,
            SMALL_LIMIT,
            guard,
        );
        if let Err(ref e) = answer {
            if [404, 405, 501].contains(&e.status) {
                return Ok(json!({"available":false,"likes":{}}));
            }
        }
        let value = answer?;
        if !value["available"].is_boolean()
            || !value["likes"].as_object().is_some_and(|o| {
                o.iter()
                    .all(|(id, v)| (ids.is_empty() || ids.contains(id)) && valid_likes(v))
            })
        {
            return Err(invalid_receipt());
        }
        checked(guard)?;
        Ok(value)
    }
    pub fn list_like(
        &self,
        auth: &AuthContext<'_>,
        body: &Value,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        fields(body, &["listId", "liked"])?;
        if !body["listId"]
            .as_str()
            .is_some_and(|s| !s.is_empty() && s.len() <= 160 && !s.chars().any(char::is_control))
            || body.get("liked").is_some_and(|v| !v.is_boolean())
        {
            return Err(ApiError::bad("题单点赞格式无效"));
        }
        self.verified_profile(auth, now, guard)?;
        let value = self.request(
            auth,
            Method::POST,
            "/v1/training-list-likes",
            Some(body),
            SMALL_LIMIT,
            guard,
        )?;
        if value["listId"] != body["listId"]
            || !value["created"].is_boolean()
            || !valid_likes(&value["likes"])
            || value["day"] != day(now)
        {
            let mut e = invalid_receipt();
            e.uncertain = true;
            return Err(e);
        }
        checked(guard)?;
        Ok(value)
    }
    pub fn presence(
        &self,
        auth: &AuthContext<'_>,
        body: &Value,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        fields(body, &["activity"])?;
        if body.as_object().map_or(0, |o| o.len()) != 1
            || !body["activity"]
                .as_str()
                .is_some_and(|a| ACTIVITIES.contains(&a))
        {
            return Err(ApiError::bad("在线状态无效"));
        }
        self.verified_profile(auth, now, guard)?;
        let value = self.request(
            auth,
            Method::POST,
            "/v1/presence",
            Some(body),
            SMALL_LIMIT,
            guard,
        )?;
        if value["owner"] != auth.owner
            || !value["available"].is_boolean()
            || !value["users"].is_array()
            || !(value["count"].is_null() || value["count"].as_u64().is_some())
        {
            let mut e = invalid_receipt();
            e.uncertain = true;
            return Err(e);
        }
        if value["available"] == true {
            let users = value["users"].as_array().unwrap();
            if value["count"].as_u64() != Some(users.len() as u64)
                || users.iter().any(|v| {
                    !v["userId"].as_str().is_some_and(valid_uuid)
                        || !v["activity"]
                            .as_str()
                            .is_some_and(|a| a != "idle" && ACTIVITIES.contains(&a))
                })
            {
                let mut e = invalid_receipt();
                e.uncertain = true;
                return Err(e);
            }
        }
        checked(guard)?;
        Ok(value)
    }
}

fn board_state(mut value: Value, scope: &Scope, status: &str, error: &str, saved: bool) -> Value {
    let o = value.as_object_mut().unwrap();
    o.insert("configured".into(), json!(true));
    o.insert("status".into(), json!(status));
    o.insert("endpoint".into(), json!(scope.endpoint));
    o.insert("error".into(), json!(error));
    o.insert("notice".into(), json!(NOTICE));
    o.insert("hasSnapshot".into(), json!(saved));
    o.insert("isAdmin".into(), json!(false));
    value
}
fn validate_board(
    value: &Value,
    owner: &str,
    period: &str,
    now: DateTime<Utc>,
) -> Result<(), ApiError> {
    if value["period"] != period
        || value["date"] != day(now)
        || value["timezone"] != "Asia/Shanghai"
        || !value["entries"].is_array()
        || !(value["self"].is_null() || value["self"]["userId"] == owner)
    {
        return Err(invalid_receipt());
    }
    let entries = value["entries"].as_array().unwrap();
    if entries.len() > 100
        || entries
            .iter()
            .chain(value.get("self").filter(|v| !v.is_null()).into_iter())
            .any(|v| !v["userId"].as_str().is_some_and(valid_uuid) || v["count"].as_u64().is_none())
    {
        return Err(invalid_receipt());
    }
    if period == "total" {
        if !value["startDate"].is_null() || !value["endDate"].is_null() {
            return Err(invalid_receipt());
        }
    } else {
        let date = NaiveDate::parse_from_str(&day(now), "%Y-%m-%d").unwrap();
        let start = if period == "weekly" {
            date - ChronoDuration::days(date.weekday().num_days_from_monday() as i64)
        } else {
            date
        };
        if value["startDate"] != start.to_string()
            || value["endDate"]
                != (start + ChronoDuration::days(if period == "weekly" { 7 } else { 1 }))
                    .to_string()
        {
            return Err(invalid_receipt());
        }
    }
    Ok(())
}
fn valid_likes(value: &Value) -> bool {
    value["total"].as_u64().is_some() && value["likedToday"].is_boolean()
}
fn validate_social(value: &Value, owner: &str) -> Result<(), ApiError> {
    if !value["available"].is_boolean()
        || value["protocol"] != 1
        || value["totalLikes"].as_u64().is_none()
        || value["unreadCount"].as_u64().is_none()
        || !value["activity"].is_array()
        || !value["notifications"].is_array()
    {
        return Err(invalid_receipt());
    }
    let notifications = value["notifications"].as_array().unwrap();
    if notifications.len() > 100
        || notifications.iter().any(|n| {
            n["recipient"]["userId"] != owner
                || !n["id"].as_str().is_some_and(valid_uuid)
                || !n["actor"]["userId"].as_str().is_some_and(valid_uuid)
        })
    {
        return Err(invalid_receipt());
    }
    Ok(())
}
fn validate_social_write(action: &str, body: &Value, owner: &str) -> Result<(), ApiError> {
    let reject = || ApiError::bad("互动请求格式无效");
    let Some(o) = body.as_object() else {
        return Err(reject());
    };
    match action {
        "read" => {
            if o.len() != 1
                || !(body["all"] == true
                    || body["ids"].as_array().is_some_and(|v| {
                        v.len() <= 100 && v.iter().all(|id| id.as_str().is_some_and(valid_uuid))
                    }))
            {
                return Err(reject());
            }
            fields(body, &["ids", "all"])?;
        }
        "likes" | "comments" => {
            if !body["targetId"]
                .as_str()
                .is_some_and(|s| s != owner && valid_uuid(s))
            {
                return Err(ApiError::bad("请选择其他训练者"));
            }
            if action == "likes" {
                fields(body, &["targetId"])?;
            } else {
                fields(body, &["targetId", "text", "requestId", "replyTo", "gift"])?;
                if !body["text"].as_str().is_some_and(|s|!s.trim().is_empty()&&s.trim().chars().count()<=500&&!s.chars().any(|c|matches!(c,'\0'..='\u{8}'|'\u{b}'..='\u{c}'|'\u{e}'..='\u{1f}'|'\u{7f}'))) || !body["requestId"].as_str().is_some_and(valid_uuid) || body.get("replyTo").is_some_and(|v|!v.as_str().is_some_and(valid_uuid)) {return Err(ApiError::bad("留言须为 1–500 字"));}
                if let Some(g) = body.get("gift") {
                    fields(g, &["unitId", "revision", "presetRevision"])?;
                    if !g["unitId"].as_str().is_some_and(valid_uuid)
                        || g["revision"]
                            .as_u64()
                            .is_none_or(|v| v > 9_007_199_254_740_991)
                        || g.get("presetRevision")
                            .is_some_and(|v| v.as_u64().is_none_or(|n| n > 9_007_199_254_740_991))
                    {
                        return Err(ApiError::bad("赠送贴纸无效"));
                    }
                }
            }
        }
        _ => return Err(reject()),
    }
    Ok(())
}
pub(super) fn validate_avatar(value: &str) -> Result<(), ApiError> {
    if value.is_empty() {
        return Ok(());
    }
    let reject = || ApiError::bad("头像图片格式无效");
    if value.len() > 16_000_023 {
        return Err(reject());
    }
    let (kind, payload) = value
        .strip_prefix("data:image/")
        .and_then(|v| v.split_once(";base64,"))
        .ok_or_else(reject)?;
    let data = STANDARD.decode(payload).map_err(|_| reject())?;
    if data.len() > 12_000_000 {
        return Err(reject());
    }
    let valid = match kind {
        "png" => {
            data.len() >= 24 && data.starts_with(b"\x89PNG\r\n\x1a\n") && &data[12..16] == b"IHDR"
        }
        "jpeg" => {
            data.len() >= 4 && data.starts_with(b"\xff\xd8\xff") && data.ends_with(b"\xff\xd9")
        }
        "webp" => {
            data.len() >= 16
                && data.starts_with(b"RIFF")
                && &data[8..12] == b"WEBP"
                && u32::from_le_bytes(data[4..8].try_into().unwrap()) as usize == data.len() - 8
        }
        _ => false,
    };
    if valid { Ok(()) } else { Err(reject()) }
}
