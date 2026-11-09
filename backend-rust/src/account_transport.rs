//! Account transport with one absolute response budget and no write replay.
//! Database/account locks belong to the caller and must be released before I/O.
use crate::ApiError;
use reqwest::{
    Method,
    blocking::{Client, Response},
    redirect::Policy,
};
use serde_json::Value;
use std::{
    collections::HashMap,
    error::Error,
    io::Read,
    sync::{Arc, Mutex},
    time::{Duration, Instant},
};
use url::{Host, Url};

pub fn validate_endpoint(value: &str) -> Result<String, ApiError> {
    let invalid = || ApiError::bad("排行榜服务地址无效");
    if value.chars().count() > 2048 {
        return Err(invalid());
    }
    let value = value.trim().trim_end_matches('/');
    if value.is_empty() {
        return Ok(String::new());
    }
    if value.chars().any(char::is_control) {
        return Err(invalid());
    }
    let url = Url::parse(value).map_err(|_| invalid())?;
    let loopback = match url.host() {
        Some(Host::Domain("localhost")) => true,
        Some(Host::Ipv4(ip)) => ip == std::net::Ipv4Addr::LOCALHOST,
        Some(Host::Ipv6(ip)) => ip == std::net::Ipv6Addr::LOCALHOST,
        _ => false,
    };
    if url.host().is_none()
        || !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some_and(|v| !v.is_empty())
        || url.fragment().is_some_and(|v| !v.is_empty())
        || url.scheme() != "https" && !(loopback && url.scheme() == "http")
    {
        return Err(ApiError::bad(
            "排行榜须使用 HTTPS 地址；本机测试可使用回环 HTTP",
        ));
    }
    if url.scheme() == "https" && !loopback && url.port_or_known_default() != Some(443) {
        return Err(ApiError::bad("排行榜 HTTPS 地址须使用标准 443 端口"));
    }
    Ok(value.into())
}

/// Borrow from a verified owned session snapshot; never serialize or log this.
pub struct Credentials<'a> {
    pub owner: &'a str,
    pub bearer: &'a str,
}
pub struct Request<'a> {
    pub method: Method,
    pub path: &'a str,
    pub body: Option<&'a Value>,
    pub credentials: Option<Credentials<'a>>,
    pub state_revision: Option<u64>,
    pub maximum: usize,
    pub timeout: Duration,
}
#[derive(Clone)]
pub struct AccountTransport {
    direct: Client,
    system: Client,
    routes: Arc<Mutex<HashMap<String, bool>>>,
}
fn changed() -> ApiError {
    ApiError::new(409, "OWNER_CHANGED", "账号已切换，本次响应未应用")
}
fn unavailable() -> ApiError {
    ApiError::new(
        503,
        "ACCOUNT_CONNECTION_UNAVAILABLE",
        "账号服务连接失败，请检查网络后重试；本机数据已保留",
    )
}
fn invalid_response() -> ApiError {
    ApiError::new(
        503,
        "ACCOUNT_RESPONSE_INVALID",
        "账号服务响应校验失败，本机数据已保留",
    )
}
fn attempt_error(mut error: ApiError, method: &Method) -> ApiError {
    if *method != Method::GET
        && matches!(
            error.code.as_str(),
            "ACCOUNT_CONNECTION_UNAVAILABLE" | "ACCOUNT_RESPONSE_INVALID"
        )
    {
        error.uncertain = true;
        error.retryable = false;
    }
    error
}
fn current(still_current: &dyn Fn() -> bool) -> Result<(), ApiError> {
    if still_current() {
        Ok(())
    } else {
        Err(changed())
    }
}
fn retryable_connection(error: &reqwest::Error) -> bool {
    if error.is_connect() && error.is_timeout() {
        return true;
    }
    let mut source = error.source();
    while let Some(error) = source {
        if let Some(io) = error.downcast_ref::<std::io::Error>() {
            return matches!(
                io.kind(),
                std::io::ErrorKind::ConnectionRefused
                    | std::io::ErrorKind::ConnectionReset
                    | std::io::ErrorKind::ConnectionAborted
                    | std::io::ErrorKind::TimedOut
                    | std::io::ErrorKind::NotConnected
                    | std::io::ErrorKind::AddrNotAvailable
                    | std::io::ErrorKind::HostUnreachable
                    | std::io::ErrorKind::NetworkUnreachable
            );
        }
        source = error.source();
    }
    false
}
impl AccountTransport {
    pub fn new() -> Result<Self, ApiError> {
        let builder = || {
            Client::builder()
                .redirect(Policy::none())
                .retry(reqwest::retry::never())
                .connect_timeout(Duration::from_secs(3))
                .user_agent("TB/1.0.20")
        };
        Ok(Self {
            direct: builder().no_proxy().build().map_err(|_| unavailable())?,
            system: builder().build().map_err(|_| unavailable())?,
            routes: Arc::new(Mutex::new(HashMap::new())),
        })
    }
    pub fn request(
        &self,
        endpoint: &str,
        request: Request<'_>,
        still_current: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        current(still_current)?;
        let endpoint = validate_endpoint(endpoint)?;
        if endpoint.is_empty() {
            return Err(ApiError::new(
                503,
                "ACCOUNT_UNCONFIGURED",
                "账号服务尚未配置，请连接账号服务后重试",
            ));
        }
        if !request.path.starts_with("/v1/")
            || request.path.chars().any(char::is_control)
            || request.maximum == 0
            || request.maximum > 128 * 1024 * 1024
            || request.timeout.is_zero()
            || request.timeout > Duration::from_secs(120)
        {
            return Err(ApiError::bad("账号请求参数无效"));
        }
        let deadline = Instant::now() + request.timeout;
        let payload = request
            .body
            .map(serde_json::to_vec)
            .transpose()
            .map_err(|_| ApiError::bad("账号请求内容无效"))?;
        let system = *self
            .routes
            .lock()
            .map_err(|_| unavailable())?
            .get(&endpoint)
            .unwrap_or(&false);
        let send = |system: bool| {
            let client = if system { &self.system } else { &self.direct };
            let mut builder = client
                .request(
                    request.method.clone(),
                    format!("{endpoint}{}", request.path),
                )
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .header("X-TB-State-Protocol", "1")
                .header("X-TB-Chunk-Protocol", "2")
                .timeout(deadline.saturating_duration_since(Instant::now()));
            if let Some(auth) = &request.credentials {
                builder = builder
                    .bearer_auth(auth.bearer)
                    .header("X-TB-User", auth.owner);
            }
            if let Some(revision) = request.state_revision.filter(|r| *r > 0) {
                builder = builder.header("X-TB-State-Revision", revision);
            }
            if let Some(value) = &payload {
                builder = builder.body(value.clone());
            }
            builder.send()
        };
        current(still_current)?;
        let response = match send(system) {
            Ok(response) => response,
            Err(error)
                if request.method == Method::GET
                    && retryable_connection(&error)
                    && Instant::now() < deadline =>
            {
                current(still_current)?;
                let response = send(!system).map_err(|_| unavailable())?;
                current(still_current)?;
                self.routes
                    .lock()
                    .map_err(|_| unavailable())?
                    .insert(endpoint.clone(), !system);
                response
            }
            Err(_) => return Err(attempt_error(unavailable(), &request.method)),
        };
        current(still_current)?;
        let status = response.status();
        if status.is_redirection() {
            return Err(ApiError::new(
                503,
                "ACCOUNT_REDIRECT_REJECTED",
                "账号服务发生重定向，请使用最终 HTTPS 地址",
            ));
        }
        let maximum = if status.is_success() {
            request.maximum
        } else {
            4096
        };
        let raw = match read(response, maximum, deadline, still_current) {
            Ok(raw) => raw,
            Err(error) if !status.is_success() && error.code != "OWNER_CHANGED" => vec![],
            Err(error) => return Err(attempt_error(error, &request.method)),
        };
        current(still_current)?;
        if !status.is_success() {
            let document: Option<Value> = serde_json::from_slice(&raw).ok();
            let message = document
                .as_ref()
                .and_then(|v| v["error"].as_str())
                .filter(|v| v.chars().count() <= 180 && !v.chars().any(char::is_control))
                .filter(|message| {
                    !request
                        .credentials
                        .as_ref()
                        .is_some_and(|c| !c.bearer.is_empty() && message.contains(c.bearer))
                })
                .filter(|message| {
                    !request.body.is_some_and(|body| {
                        ["password", "oldPassword", "newPassword"]
                            .iter()
                            .any(|key| {
                                body[*key].as_str().is_some_and(|secret| {
                                    !secret.is_empty() && message.contains(secret)
                                })
                            })
                    })
                })
                .unwrap_or("账号服务暂时无法完成请求");
            let code = if [502, 503, 504].contains(&status.as_u16()) {
                "ACCOUNT_CONNECTION_UNAVAILABLE"
            } else if status.as_u16() == 401 {
                "ACCOUNT_AUTH_REJECTED"
            } else {
                "ACCOUNT_REQUEST_REJECTED"
            };
            return Err(attempt_error(
                ApiError::new(status.as_u16(), code, message),
                &request.method,
            ));
        }
        let result: Value = serde_json::from_slice(&raw)
            .map_err(|_| attempt_error(invalid_response(), &request.method))?;
        if !result.is_object() {
            return Err(attempt_error(invalid_response(), &request.method));
        }
        Ok(result)
    }
}
fn read(
    mut response: Response,
    maximum: usize,
    deadline: Instant,
    still_current: &dyn Fn() -> bool,
) -> Result<Vec<u8>, ApiError> {
    if response
        .content_length()
        .is_some_and(|n| n > maximum as u64)
    {
        return Err(invalid_response());
    }
    let mut raw = Vec::new();
    let mut buffer = [0_u8; 65536];
    loop {
        current(still_current)?;
        if Instant::now() >= deadline {
            return Err(unavailable());
        }
        let take = (maximum + 1 - raw.len()).min(buffer.len());
        let count = response.read(&mut buffer[..take]).map_err(|error| {
            let mut source: Option<&(dyn Error + 'static)> = Some(&error);
            while let Some(error) = source {
                if error
                    .downcast_ref::<reqwest::Error>()
                    .is_some_and(|e| e.is_timeout() || retryable_connection(e))
                {
                    return unavailable();
                }
                source = error.source();
            }
            invalid_response()
        })?;
        if count == 0 {
            break;
        }
        raw.extend_from_slice(&buffer[..count]);
        if raw.len() > maximum {
            return Err(invalid_response());
        }
    }
    current(still_current)?;
    if Instant::now() > deadline {
        return Err(unavailable());
    }
    Ok(raw)
}
