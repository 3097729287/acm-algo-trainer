use crate::{
    api::{self, ApiError, ApiRequest, ApiResponse, Method, fields},
    library::{self, Library},
    storage::PersonalStore,
    templates,
};
use serde_json::{Value, json};
use std::{path::PathBuf, sync::Mutex, time::Instant};

const CONTRACT: &str = include_str!("../../api/legacy-contract.json");
pub const NATIVE_ROUTES: &[(&str, &str)] = &[
    ("GET", "api/capabilities"),
    ("GET", "account"),
    ("GET", "preferences"),
    ("GET", "initial-code"),
    ("POST", "initial-code/save"),
    ("POST", "initial-code/select"),
    ("GET", "templates"),
    ("POST", "templates/save"),
    ("GET", "wiki"),
    ("GET", "library/page"),
    ("GET", "library/statement"),
    ("GET", "library/asset"),
    ("GET", "library/lecture"),
    ("GET", "library/lectures"),
    ("GET", "library/training-lists"),
    ("POST", "draft"),
    ("POST", "workspace/ready"),
];

#[derive(Clone)]
pub struct ServiceConfig {
    pub library: PathBuf,
    pub resources: PathBuf,
    pub personal: PathBuf,
    pub sandbox: bool,
    pub owner: String,
}
impl ServiceConfig {
    pub fn sandbox(source: PathBuf, state: PathBuf) -> Self {
        Self {
            library: source.join("data/library.sqlite3"),
            resources: source.join("backend/resources"),
            personal: state.join("personal.sqlite3"),
            sandbox: true,
            owner: "rust-migration-sandbox".into(),
        }
    }
}
pub struct Service {
    config: ServiceConfig,
    library: Mutex<Library>,
    personal: Mutex<PersonalStore>,
    builtins: Vec<Value>,
    token: String,
    contract: Value,
}
impl Service {
    pub fn open(config: ServiceConfig) -> Result<Self, ApiError> {
        if !config.sandbox {
            return Err(ApiError::new(
                409,
                "RELEASE_GATE",
                "Rust 功能与数据迁移验收尚未完成，不能切换正式工作区",
            ));
        }
        let library = Library::open(&config.library)?;
        let personal = PersonalStore::open(&config.personal)?;
        let builtins = templates::builtin_templates(&config.resources)?;
        Ok(Self {
            config,
            library: Mutex::new(library),
            personal: Mutex::new(personal),
            builtins,
            token: uuid::Uuid::new_v4().to_string(),
            contract: serde_json::from_str(CONTRACT)?,
        })
    }
    pub fn handle(&self, request: ApiRequest) -> ApiResponse {
        let start = Instant::now();
        let result = self.dispatch(&request);
        ApiResponse::complete(request.id, result, start.elapsed())
    }
    fn dispatch(&self, r: &ApiRequest) -> Result<Value, ApiError> {
        r.validate()?;
        if r.method == Method::Get && r.path == "api/capabilities" {
            return Ok(self.capabilities());
        }
        if r.owner.as_deref().is_some_and(|v| v != self.config.owner) {
            return Err(ApiError::new(
                409,
                "ACCOUNT_CHANGED",
                "账号已切换，请重新读取",
            ));
        }
        if r.method == Method::Post && r.token.as_deref() != Some(&self.token) {
            return Err(ApiError::new(403, "SESSION_EXPIRED", "会话已失效，请刷新"));
        }
        if r.method == Method::Get && r.path == "account" {
            // A development workspace is explicit and never represents a
            // registered account, verified growth, online inventory or rewards.
            return Ok(
                json!({"required":true,"authenticated":false,"token":self.token,"admin":false,"sandbox":true,
                "account":null,"restoring":false,"sync":null}),
            );
        }
        let method = if r.method == Method::Get {
            "GET"
        } else {
            "POST"
        };
        if !NATIVE_ROUTES.contains(&(method, r.path.as_str())) {
            let known = self.contract["endpoints"]
                .as_array()
                .unwrap()
                .iter()
                .any(|v| {
                    v["method"] == method
                        && (v["path"] == r.path
                            || v["path"] == "pk/v1/*" && r.path.starts_with("pk/v1/"))
                });
            return Err(if known {
                ApiError::pending()
            } else {
                ApiError::missing("没有找到这个接口")
            });
        }
        // Lock in one fixed order whenever both stores are needed.
        // Independent read-only Wiki queries do not hold the personal lock.
        if r.method == Method::Get && r.path == "wiki" {
            return library::wiki(
                &self.config.resources.join("oi-wiki.sqlite3"),
                r.param("q").unwrap_or(""),
                r.param("id"),
            );
        }
        if r.method == Method::Get && r.path.starts_with("library/") {
            let library = self
                .library
                .lock()
                .map_err(|_| ApiError::new(503, "SERVICE_UNAVAILABLE", "题库暂时不可用"))?;
            return match r.path.as_str() {
                "library/page" => {
                    let mut query = json!({"q":r.param("q").unwrap_or("")});
                    for key in ["offset", "limit"] {
                        if let Some(value) = r.param(key) {
                            query[key] = json!(
                                value
                                    .parse::<u64>()
                                    .map_err(|_| ApiError::bad("分页参数无效"))?
                            );
                        }
                    }
                    library.page(&query)
                }
                "library/statement" => {
                    library.statement(r.param("id").ok_or_else(|| ApiError::bad("缺少题目编号"))?)
                }
                "library/lecture" => {
                    library.lecture(r.param("id").ok_or_else(|| ApiError::bad("缺少讲义编号"))?)
                }
                "library/lectures" => library.lectures(),
                "library/training-lists" => Ok(json!({"lists":library.training_lists()?})),
                "library/asset" => library.asset(r.param("sha256").unwrap_or("")),
                _ => Err(ApiError::missing("没有找到这个接口")),
            };
        }
        let mut personal = self
            .personal
            .lock()
            .map_err(|_| ApiError::new(503, "SERVICE_UNAVAILABLE", "本机数据暂时不可用"))?;
        if r.method == Method::Get {
            return match r.path.as_str() {
                "preferences" => personal.preferences(),
                "initial-code" => templates::initial_catalog(&personal),
                "templates" => templates::catalog(&personal, &self.builtins),
                _ => Err(ApiError::missing("没有找到这个接口")),
            };
        }
        let body = r.body.as_ref().unwrap();
        match r.path.as_str() {
            "workspace/ready" => {
                fields(body, &[])?;
                Ok(json!({"ready":true}))
            }
            "initial-code/save" => templates::initial_save(&mut personal, body),
            "initial-code/select" => templates::initial_choose(&personal, body),
            "templates/save" => templates::save(&personal, body, &self.builtins),
            "draft" => {
                // Drop personal before acquiring library to preserve lock order.
                drop(personal);
                let library = self
                    .library
                    .lock()
                    .map_err(|_| ApiError::new(503, "SERVICE_UNAVAILABLE", "题库暂时不可用"))?;
                let id = library.validate_id(body)?;
                drop(library);
                let mut personal = self
                    .personal
                    .lock()
                    .map_err(|_| ApiError::new(503, "SERVICE_UNAVAILABLE", "本机数据暂时不可用"))?;
                // Alias handling must retain the submitted stable identity, as
                // in the existing journal, after confirming the canonical row.
                personal.assert_unlocked(&id)?;
                personal.save_draft(body)
            }
            _ => Err(ApiError::missing("没有找到这个接口")),
        }
    }
    pub fn capabilities(&self) -> Value {
        let endpoints = self.contract["endpoints"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| {
                let method = v["method"].as_str().unwrap();
                let path = v["path"].as_str().unwrap();
                let mut v = v.clone();
                v["native"] = json!(path != "account" && NATIVE_ROUTES.contains(&(method, path)));
                if path == "account" {
                    v["status"] = json!("sandbox-bootstrap-only");
                }
                v
            })
            .collect::<Vec<_>>();
        let migrated = endpoints.iter().filter(|v| v["native"] == true).count();
        json!({"protocol":api::PROTOCOL_VERSION,"backend":"rust","transport":"tauri-ipc","releaseReady":false,"sandbox":self.config.sandbox,
            "legacyTotal":endpoints.len(),"legacyImplemented":migrated,"endpoints":endpoints,"nativeRoutes":NATIVE_ROUTES,
            "pendingDomains":["catalogue-projection","training-and-reviews","learning-summary","accounts-and-sync","growth-and-rewards","judge-and-official-browser","online-services","updates-and-installer"]})
    }
}
