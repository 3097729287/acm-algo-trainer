use crate::{
    api::{self, ApiError, ApiRequest, ApiResponse, Method, fields},
    catalogue::Catalogue,
    contest_setup::PreviewBook,
    learning,
    library::{self, Library},
    native_judge::{RunPlan, Toolchains},
    planner::Planner,
    preferences,
    public_assets::{AssetCache, TrustPolicy},
    run_queue::RunQueue,
    storage::PersonalStore,
    templates,
    training::Training,
    usage,
};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    path::PathBuf,
    sync::{Arc, Mutex},
    time::Instant,
};

const CONTRACT: &str = include_str!("../../api/legacy-contract.json");
pub const NATIVE_ROUTES: &[(&str, &str)] = &[
    ("GET", "api/capabilities"),
    ("GET", "account"),
    ("GET", "desktop/fullscreen"),
    ("POST", "desktop/fullscreen"),
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
    ("POST", "code/format"),
    ("POST", "workspace/ready"),
    ("GET", "data"),
    ("GET", "data/export"),
    ("GET", "contests/events"),
    ("GET", "contest"),
    ("POST", "contests/finish"),
    ("POST", "contests/cancel"),
    ("POST", "contests/delete"),
    ("POST", "contests/preview"),
    ("POST", "contests/start"),
    ("GET", "goals"),
    ("POST", "goals/save"),
    ("POST", "goals/archive"),
    ("GET", "workspace"),
    ("GET", "problem"),
    ("GET", "submissions"),
    ("POST", "submissions"),
    ("GET", "solution"),
    ("GET", "lectures"),
    ("GET", "lecture"),
    ("POST", "training/start"),
    ("POST", "training/remove"),
    ("POST", "training/clear"),
    ("GET", "learning-summary"),
    ("GET", "learning-summary/history"),
    ("GET", "learning-summary/quiz"),
    ("POST", "learning-summary/update"),
    ("POST", "learning-summary/refresh"),
    ("POST", "learning-summary/time"),
    ("POST", "preferences"),
    ("GET", "usage"),
    ("POST", "usage"),
    ("GET", "submission"),
    ("GET", "training-lists"),
    ("POST", "training-lists/save"),
    ("POST", "training-lists/add"),
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
    personal: Arc<Mutex<PersonalStore>>,
    builtins: Vec<Value>,
    token: String,
    contract: Value,
    catalogue: Option<Mutex<Catalogue>>,
    curriculum: Value,
    quizzes: Value,
    test_clock: Option<chrono::DateTime<chrono::Utc>>,
    runner: RunQueue,
    desktop_fullscreen: Option<Arc<DesktopFullscreen>>,
    public_assets: Option<AssetCache>,
    previews: Mutex<PreviewBook>,
}
type DesktopFullscreen = dyn Fn(Option<bool>) -> Result<bool, ApiError> + Send + Sync;
impl Service {
    pub fn open(config: ServiceConfig) -> Result<Self, ApiError> {
        let tools = Toolchains::from_resources(&config.resources);
        Self::open_with_runner_tools(config, tools)
    }
    pub fn open_with_runner_tools(
        config: ServiceConfig,
        tools: Toolchains,
    ) -> Result<Self, ApiError> {
        if !config.sandbox {
            return Err(ApiError::new(
                409,
                "RELEASE_GATE",
                "Rust 功能与数据迁移验收尚未完成，不能切换正式工作区",
            ));
        }
        let library = Library::open(&config.library)?;
        let mut personal = PersonalStore::open(&config.personal)?;
        let runner = RunQueue::open(&config.personal, tools, &config.owner, &mut personal)?;
        let builtins = templates::builtin_templates(&config.resources)?;
        let catalog_path = config.library.with_file_name("native-catalog.sqlite3");
        let catalogue = if catalog_path.is_file() {
            Some(Mutex::new(Catalogue::open(&catalog_path, &library.db)?))
        } else {
            None
        };
        let read_resource = |name: &str| -> Result<Value, ApiError> {
            let path = config.resources.join(name);
            if path.is_file() {
                Ok(serde_json::from_slice(&std::fs::read(path)?)?)
            } else {
                Ok(json!({}))
            }
        };
        let curriculum = read_resource("learning-curriculum.json")?;
        let quizzes = read_resource("native-quizzes.json")?;
        let endpoint = read_resource("leaderboard.defaults.json")?;
        let public_assets = endpoint["endpoint"]
            .as_str()
            .filter(|endpoint| !endpoint.is_empty())
            .map(|endpoint| {
                let cache = config
                    .personal
                    .parent()
                    .ok_or_else(|| ApiError::bad("缓存目录无效"))?
                    .join("cache/public-assets.sqlite3");
                Ok::<_, ApiError>(AssetCache::new(
                    cache,
                    TrustPolicy::new(endpoint)?,
                    std::env::var("TB_OFFLINE").ok().as_deref() == Some("1"),
                ))
            })
            .transpose()?;
        Ok(Self {
            config,
            library: Mutex::new(library),
            personal: Arc::new(Mutex::new(personal)),
            builtins,
            token: uuid::Uuid::new_v4().to_string(),
            contract: serde_json::from_str(CONTRACT)?,
            catalogue,
            curriculum,
            quizzes,
            test_clock: None,
            runner,
            desktop_fullscreen: None,
            public_assets,
            previews: Mutex::new(PreviewBook::default()),
        })
    }
    /// Native host/test configuration only. IPC requests cannot change trust or
    /// cache location, and this never grants registered-account authority.
    pub fn with_public_assets(mut self, cache: AssetCache) -> Self {
        self.public_assets = Some(cache);
        self
    }
    fn prefetch_public_assets(&self, r: &ApiRequest) -> Result<(), ApiError> {
        let Some(cache) = self.public_assets.as_ref() else {
            return Ok(());
        };
        if r.method != Method::Get
            || ![
                "problem",
                "library/statement",
                "solution",
                "lecture",
                "library/lecture",
                "library/asset",
            ]
            .contains(&r.path.as_str())
        {
            return Ok(());
        }
        let descriptors = {
            // Match the normal domain lock order; only descriptor discovery is
            // inside this block. No remote transfer owns a service/SQLite lock.
            let catalogue = self
                .catalogue
                .as_ref()
                .map(|catalogue| catalogue.lock().map_err(|_| ApiError::pending()))
                .transpose()?;
            let library = self.library.lock().map_err(|_| ApiError::pending())?;
            let mut personal = self.personal.lock().map_err(|_| ApiError::pending())?;
            let mut references = std::collections::BTreeSet::new();
            let identity = r.param("id");
            let value = match r.path.as_str() {
                "library/asset" => {
                    references.insert(r.param("sha256").unwrap_or("").to_owned());
                    None
                }
                "problem" => {
                    let id = identity.ok_or_else(|| ApiError::bad("题目编号无效"))?;
                    let catalogue = catalogue.as_deref().ok_or_else(ApiError::pending)?;
                    crate::catalogue::row_or_portable(catalogue, &personal, id)?;
                    let training = Training {
                        catalogue,
                        library: &library,
                        personal: &mut personal,
                        now: self.now(),
                    };
                    let contest = r.param("contestId").filter(|id| !id.is_empty());
                    training.history_visible(id, contest)?;
                    if let Some(contest) = contest {
                        if r.param("reviewId").is_some_and(|id| !id.is_empty()) {
                            return Err(ApiError::bad("复习上下文无效"));
                        }
                        crate::contest_history::assert_problem_context(
                            &training, id, contest, false,
                        )?;
                    }
                    let id = catalogue.canonical(id)?.unwrap_or_else(|| id.into());
                    let mut value = library.statement_raw(&id)?;
                    catalogue.problem_projection(&id, &mut value)?;
                    Some(value)
                }
                "library/statement" => Some(
                    library
                        .statement_raw(identity.ok_or_else(|| ApiError::bad("缺少题目编号"))?)?,
                ),
                "solution" => {
                    let id = identity.ok_or_else(|| ApiError::bad("缺少题目编号"))?;
                    let catalogue = catalogue.as_deref().ok_or_else(ApiError::pending)?;
                    let training = Training {
                        catalogue,
                        library: &library,
                        personal: &mut personal,
                        now: self.now(),
                    };
                    training.assert_unlocked(id)?;
                    Some(library.solution(&training.canonical(id)?)?)
                }
                "lecture" | "library/lecture" => {
                    let value =
                        library.lecture(identity.ok_or_else(|| ApiError::bad("缺少讲义编号"))?)?;
                    if r.path == "lecture" {
                        let catalogue = catalogue.as_deref().ok_or_else(ApiError::pending)?;
                        let training = Training {
                            catalogue,
                            library: &library,
                            personal: &mut personal,
                            now: self.now(),
                        };
                        for id in value["sourceProblemIds"]
                            .as_array()
                            .into_iter()
                            .flatten()
                            .filter_map(Value::as_str)
                        {
                            training.assert_unlocked(id)?;
                        }
                    }
                    Some(value)
                }
                _ => None,
            };
            if let Some(value) = value {
                references.extend(library::asset_references(&value));
            }
            let mut result = Vec::new();
            let mut total = 0_u64;
            for sha in references {
                if library.asset_is_local(&sha, catalogue.as_deref().map(|c| &c.db))? {
                    continue;
                }
                let item = cache.descriptor(&library.db, &sha)?.ok_or_else(|| {
                    ApiError::new(
                        503,
                        "ASSET_NOT_CACHED",
                        "原始图片或 PDF 尚未收录，原数据已保留",
                    )
                })?;
                total = total
                    .checked_add(item.bytes)
                    .ok_or_else(|| ApiError::bad("本次资源总量超出范围"))?;
                if result.len() >= 256 || total > 128 * 1024 * 1024 {
                    return Err(ApiError::new(
                        503,
                        "ASSET_REQUEST_LIMIT",
                        "本次资源总量超出缓存限额",
                    ));
                }
                result.push(item);
            }
            result
        };
        for descriptor in descriptors {
            cache.ensure(&descriptor)?;
        }
        Ok(())
    }
    /// Bind the real host window without coupling the domain crate to a GUI.
    /// Calls still pass through protocol, owner and write-token validation.
    pub fn with_desktop_fullscreen<F>(mut self, controller: F) -> Self
    where
        F: Fn(Option<bool>) -> Result<bool, ApiError> + Send + Sync + 'static,
    {
        self.desktop_fullscreen = Some(Arc::new(controller));
        self
    }
    pub fn with_test_clock(mut self, clock: chrono::DateTime<chrono::Utc>) -> Self {
        self.test_clock = Some(clock);
        self
    }
    fn now(&self) -> chrono::DateTime<chrono::Utc> {
        self.test_clock.unwrap_or_else(chrono::Utc::now)
    }
    fn start_local_run(&self, r: &ApiRequest) -> Result<Value, ApiError> {
        let body = r.body.as_ref().unwrap();
        fields(
            body,
            &[
                "id",
                "code",
                "mode",
                "input",
                "sampleRun",
                "language",
                "contestId",
                "reviewId",
            ],
        )?;
        let id = api::required_text(body, "id", 512)?;
        let mode = match body.get("mode") {
            None => "submit",
            Some(Value::String(s)) if s == "run" => "run",
            Some(Value::String(s)) if s == "submit" => "submit",
            _ => return Err(ApiError::bad("运行模式无效")),
        };
        let contest_context = match body.get("contestId") {
            None | Some(Value::Null) => None,
            Some(Value::String(id)) if id.is_empty() => None,
            Some(Value::String(id)) => Some(id.as_str()),
            _ => return Err(ApiError::bad("比赛编号无效")),
        };
        let review_id = match body.get("reviewId") {
            None | Some(Value::Null) => None,
            Some(Value::String(id)) => Some(id.as_str()),
            _ => return Err(ApiError::bad("复习上下文无效")),
        };
        if contest_context.is_some() && review_id.is_some_and(|id| !id.is_empty()) {
            return Err(ApiError::bad("复习上下文无效"));
        }
        let hash = format!("{:x}", Sha256::digest(body.to_string().as_bytes()));
        let key = format!("native-run-request:{}", r.id);
        let previous = {
            let personal = self.personal.lock().map_err(|_| ApiError::pending())?;
            personal.document(&key)?
        };
        let reservation = if previous.is_none() {
            Some(self.runner.reserve()?)
        } else {
            None
        };
        let (plan, answer) = {
            let catalogue = self
                .catalogue
                .as_ref()
                .ok_or_else(|| ApiError::new(503, "CATALOGUE_MISSING", "原生题库索引尚未构建"))?
                .lock()
                .map_err(|_| ApiError::pending())?;
            let library = self.library.lock().map_err(|_| ApiError::pending())?;
            let mut personal = self.personal.lock().map_err(|_| ApiError::pending())?;
            let mut training = Training {
                catalogue: &catalogue,
                library: &library,
                personal: &mut personal,
                now: self.now(),
            };
            self.runner
                .refresh_progress(&training, &self.config.owner)?;
            crate::contest_lifecycle::expire(&training)?;
            training.history_visible(id, contest_context)?;
            if let Some(previous) = training.personal.document(&key)? {
                if previous["schema"] != 1
                    || previous["owner"] != self.config.owner
                    || previous["requestHash"] != hash
                {
                    return Err(ApiError::new(
                        409,
                        "RUN_REQUEST_CONFLICT",
                        "此运行请求编号已用于另一份代码或输入",
                    ));
                }
                return training.submission(
                    previous["submissionId"]
                        .as_str()
                        .ok_or_else(ApiError::pending)?,
                );
            }
            crate::catalogue::row_or_portable(&catalogue, training.personal, id)?;
            if let Some(context) = contest_context {
                crate::contest_history::assert_problem_context(&training, id, context, true)?;
                if mode == "submit" {
                    let record = crate::contest_history::record(&training, context)?;
                    let config: Value =
                        serde_json::from_str(record["config"].as_str().unwrap_or("{}"))?;
                    if matches!(config["strategy"].as_str(), Some("replay" | "team")) {
                        return Err(ApiError::conflict("重现赛请使用原站提交"));
                    }
                }
            } else {
                training.assert_unlocked(id)?;
            }
            let canonical = training.canonical(id)?;
            // Running code only needs text samples and limits, not images/PDF.
            let mut problem = library.statement_raw(&canonical)?;
            catalogue.problem_projection(&canonical, &mut problem)?;
            problem["id"] = canonical.into();
            let plan = RunPlan::prepare(&problem, body)?;
            self.runner.validate_tools(&plan.language)?;
            let unfinished = training
                .personal
                .rows("SELECT id FROM submissions WHERE finished_at IS NULL", [])?;
            for row in unfinished.as_array().unwrap() {
                let marker = training
                    .personal
                    .document(&format!("native-run:{}", row["id"].as_str().unwrap_or("")))?;
                if !marker.is_some_and(|m| RunQueue::accepts_marker(&m, &self.config.owner)) {
                    return Err(ApiError::pending());
                }
            }
            let submission = reservation
                .as_ref()
                .ok_or_else(ApiError::pending)?
                .id
                .clone();
            training.now = self.now();
            crate::contest_lifecycle::expire(&training)?;
            if let Some(context) = contest_context {
                crate::contest_history::assert_problem_context(&training, id, context, true)?;
            }
            let stamp = self
                .now()
                .to_rfc3339_opts(chrono::SecondsFormat::Micros, true);
            let ids = training.ids(id)?;
            let review = crate::reviews::task(&training, id, review_id, true)?;
            let seen: bool = if let Some(task) = &review {
                let seen:Option<String>=training.personal.db.query_row("SELECT MAX(solution_seen_at) FROM training WHERE id IN (SELECT value FROM json_each(?))",[json!(ids).to_string()],|row|row.get(0))?;
                seen.is_some_and(|at| {
                    task["openedAt"].as_str().is_some_and(|opened| {
                        opened <= at.as_str() && at.as_str() <= stamp.as_str()
                    })
                })
            } else {
                training.personal.db.query_row("SELECT COALESCE(MAX(solution_pending),0)!=0 FROM training WHERE id IN (SELECT value FROM json_each(?))",[json!(ids).to_string()],|row|row.get(0))?
            };
            crate::storage::atomic(&training.personal.db, |tx| {
                tx.execute("INSERT INTO submissions(id,problem_id,contest_id,mode,code,submitted_at,verdict,scope,custom_input,solution_seen,sample_run) VALUES(?,?,?,?,?,?,'QUEUED',?,?,?,?)",rusqlite::params![submission,id,contest_context,plan.mode,plan.code,stamp,plan.scope,plan.input,seen as i32,plan.sample_run as i32])?;
                PersonalStore::put(
                    tx,
                    &format!("submission-language:{submission}"),
                    &plan.language,
                    &stamp,
                )?;
                if let Some(review) = &review {
                    PersonalStore::put(
                        tx,
                        &format!("review-receipt:{submission}"),
                        &review["id"].to_string(),
                        &stamp,
                    )?;
                }
                PersonalStore::put(
                tx,
                &format!("native-run:{submission}"),
                &json!({"schema":2,"owner":self.config.owner,"status":"queued","requestId":r.id,"problemId":id,"mode":plan.mode,"scope":plan.scope,"reviewedProfile":plan.profile.map(|p|p.profile_id),"sourceSha256":plan.profile.map(|_|crate::reviewed_judge::SOURCE_SHA256)})
                    .to_string(),
                &stamp,
            )?;
                PersonalStore::put(tx,&key,&json!({"schema":1,"owner":self.config.owner,"requestHash":hash,"submissionId":submission}).to_string(),&stamp)?;
                if plan.mode == "submit" {
                    training.activate_edited(id, contest_context.is_none())?;
                }
                Ok(())
            })?;
            let answer = training.submission(&submission)?;
            (plan, answer)
        };
        self.runner.launch(
            reservation.ok_or_else(ApiError::pending)?,
            plan,
            Arc::clone(&self.personal),
            self.config.owner.clone(),
            self.test_clock,
        )?;
        Ok(answer)
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
        let method = match r.method {
            Method::Get => "GET",
            Method::Head => "HEAD",
            Method::Post => "POST",
        };
        if !NATIVE_ROUTES.contains(&(method, r.path.as_str())) {
            let known = self.contract["endpoints"]
                .as_array()
                .unwrap()
                .iter()
                .any(|v| {
                    v["method"] == method
                        && api::route_matches(v["path"].as_str().unwrap(), &r.path)
                });
            return Err(if known {
                ApiError::pending()
            } else {
                ApiError::missing("没有找到这个接口")
            });
        }
        if r.path == "desktop/fullscreen" {
            let requested = if r.method == Method::Post {
                let body = r.body.as_ref().unwrap();
                fields(body, &["fullscreen"])?;
                Some(
                    body["fullscreen"]
                        .as_bool()
                        .ok_or_else(|| ApiError::bad("全屏参数必须是布尔值"))?,
                )
            } else {
                None
            };
            return match &self.desktop_fullscreen {
                Some(controller) => {
                    Ok(json!({"available":true,"fullscreen":controller(requested)?}))
                }
                None if requested.is_none() => Ok(json!({"available":false,"fullscreen":false})),
                None => Err(ApiError::new(
                    503,
                    "DESKTOP_UNAVAILABLE",
                    "当前浏览器测试没有原生窗口，无法切换全屏",
                )),
            };
        }
        self.prefetch_public_assets(r)?;
        if self.runner.has_pending_write() {
            let mut personal = self.personal.lock().map_err(|_| ApiError::pending())?;
            self.runner.flush_pending(&mut personal)?;
        }
        if r.method == Method::Post && r.path == "submissions" {
            return self.start_local_run(r);
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
        if matches!(
            r.path.as_str(),
            "data"
                | "contests/events"
                | "contest"
                | "contests/finish"
                | "contests/cancel"
                | "contests/delete"
                | "contests/preview"
                | "contests/start"
                | "goals"
                | "goals/save"
                | "goals/archive"
                | "workspace"
                | "problem"
                | "submissions"
                | "submission"
                | "solution"
                | "lectures"
                | "lecture"
                | "training-lists"
                | "training-lists/save"
                | "training-lists/add"
                | "training/start"
                | "training/remove"
                | "training/clear"
        ) || method == "POST"
            && (r.path == "preferences"
                || r.path == "code/format"
                || r.path == "draft" && self.catalogue.is_some()
                || r.path == "learning-summary/refresh"
                || r.path == "learning-summary/update"
                    && !r.body.as_ref().is_some_and(|b| {
                        matches!(
                            b["action"].as_str(),
                            Some("seen" | "view" | "delete-history")
                        )
                    }))
        {
            let catalogue = self
                .catalogue
                .as_ref()
                .ok_or_else(|| ApiError::new(503, "CATALOGUE_MISSING", "原生题库索引尚未构建"))?
                .lock()
                .map_err(|_| ApiError::new(503, "SERVICE_UNAVAILABLE", "题库索引暂时不可用"))?;
            let library = self
                .library
                .lock()
                .map_err(|_| ApiError::new(503, "SERVICE_UNAVAILABLE", "题库暂时不可用"))?;
            let mut personal = self
                .personal
                .lock()
                .map_err(|_| ApiError::new(503, "SERVICE_UNAVAILABLE", "本机数据暂时不可用"))?;
            let mut training = Training {
                catalogue: &catalogue,
                library: &library,
                personal: &mut personal,
                now: self.now(),
            };
            self.runner
                .refresh_progress(&training, &self.config.owner)?;
            return match (method, r.path.as_str()) {
                ("GET", "data") => {
                    let private: bool = personal.db.query_row("SELECT EXISTS(SELECT 1 FROM account_problem_facts WHERE CASE WHEN json_valid(value) THEN json_extract(value,'$.statement.accountReading') ELSE 0 END=1)", [], |row| row.get(0))?;
                    if private {
                        Err(ApiError::pending())
                    } else {
                        catalogue.data(r.param("compact") == Some("1"), &self.token)
                    }
                }
                ("GET", "workspace") => training.workspace(),
                ("POST", "contests/finish") => crate::contest_lifecycle::finish(
                    &training,
                    r.body.as_ref().unwrap()["contestId"].as_str().unwrap_or(""),
                ),
                ("POST", "contests/cancel") => crate::contest_lifecycle::cancel(
                    &training,
                    r.body.as_ref().unwrap()["contestId"].as_str().unwrap_or(""),
                ),
                ("POST", "contests/delete") => {
                    crate::contest_lifecycle::delete(&training, r.body.as_ref().unwrap())
                }
                ("POST", "contests/preview") => self
                    .previews
                    .lock()
                    .map_err(|_| ApiError::pending())?
                    .preview(&training, r.body.as_ref().unwrap()),
                ("POST", "contests/start") => self
                    .previews
                    .lock()
                    .map_err(|_| ApiError::pending())?
                    .start(&training, r.body.as_ref().unwrap()),
                ("GET", "goals") => crate::goals::list(&training, false),
                ("POST", "goals/save") => crate::goals::save(&training, r.body.as_ref().unwrap()),
                ("POST", "goals/archive") => crate::goals::archive(
                    &training,
                    r.body.as_ref().unwrap()["id"].as_str().unwrap_or(""),
                ),
                ("GET", "contests/events") => catalogue.replay_events(training.personal),
                ("GET", "contest") => crate::contest_history::get(
                    &training,
                    r.param("id")
                        .ok_or_else(|| ApiError::bad("缺少模拟赛编号"))?,
                ),
                ("POST", "learning-summary/refresh" | "learning-summary/update") => {
                    let mut planner = Planner {
                        training,
                        curriculum: &self.curriculum,
                        quizzes: &self.quizzes,
                        builtins: &self.builtins,
                    };
                    if r.path.ends_with("/refresh") {
                        planner.refresh()
                    } else {
                        planner.update(r.body.as_ref().unwrap())
                    }
                }
                ("GET", "problem") => {
                    let mut value = training.problem_with_assets(r, self.public_assets.as_ref())?;
                    value["formattingAvailable"] =
                        (r.param("contestId").filter(|id| !id.is_empty()).is_none()
                            && value["locked"] != true
                            && training.running()?.is_none()
                            && crate::code_format::available(
                                &self.config.resources,
                                &crate::code_format::tools_root(&self.config.resources),
                            ))
                        .into();
                    Ok(value)
                }
                ("GET", "submissions") => training.submissions(r, false),
                ("GET", "submission") => {
                    training.submission(r.param("id").ok_or_else(|| ApiError::bad("缺少提交编号"))?)
                }
                ("GET", "solution") => {
                    let id = r.param("id").ok_or_else(|| ApiError::bad("缺少题目编号"))?;
                    training.assert_unlocked(id)?;
                    let canonical = training.canonical(id)?;
                    let mut solution = library.solution(&canonical)?;
                    library.hydrate_with_cache(
                        &mut solution,
                        Some(&catalogue.db),
                        self.public_assets.as_ref(),
                    )?;
                    solution["lectures"] = library.lectures_for_problem(&canonical)?;
                    training.mark_seen(id)?;
                    Ok(solution)
                }
                ("GET", "lectures") => catalogue.lectures(&personal, &self.curriculum, &library.db),
                ("GET", "training-lists") => {
                    catalogue.training_lists(&personal, r.param("custom") == Some("1"))
                }
                ("POST", "training-lists/save") => crate::custom_lists::save(
                    training.personal,
                    r.body.as_ref().unwrap(),
                    self.now(),
                    |store, id| crate::catalogue::row_or_portable(&catalogue, store, id),
                ),
                ("POST", "training-lists/add") => crate::custom_lists::add(
                    training.personal,
                    r.body.as_ref().unwrap(),
                    self.now(),
                    |store, id| crate::catalogue::row_or_portable(&catalogue, store, id),
                ),
                ("GET", "lecture") => {
                    let mut lecture = library
                        .lecture(r.param("id").ok_or_else(|| ApiError::bad("缺少讲义编号"))?)?;
                    for id in lecture["sourceProblemIds"]
                        .as_array()
                        .into_iter()
                        .flatten()
                        .filter_map(Value::as_str)
                    {
                        training.assert_unlocked(id)?;
                    }
                    library.hydrate_with_cache(
                        &mut lecture,
                        Some(&catalogue.db),
                        self.public_assets.as_ref(),
                    )?;
                    Ok(lecture)
                }
                ("POST", "training/start") => training.start(r.body.as_ref().unwrap()),
                ("POST", "training/remove") => training.remove(r.body.as_ref().unwrap()),
                ("POST", "training/clear") => training.clear(r.body.as_ref().unwrap()),
                ("POST", "code/format") => {
                    let body = r.body.as_ref().unwrap();
                    let id = crate::api::required_text(body, "id", 512)?;
                    crate::catalogue::row_or_portable(&catalogue, training.personal, id)?;
                    if training.running()?.is_some()
                        || body
                            .get("contestId")
                            .is_some_and(|v| !v.is_null() && v != "")
                    {
                        return Err(ApiError::new(
                            409,
                            "CONTEST_ACTIVE",
                            "比赛期间不能格式化代码。",
                        ));
                    }
                    training.assert_unlocked(id)?;
                    crate::code_format::format_code(
                        body,
                        &self.config.resources,
                        &crate::code_format::tools_root(&self.config.resources),
                    )
                }
                ("POST", "preferences") => preferences::save(
                    &mut personal,
                    Some(&catalogue),
                    r.body.as_ref().unwrap(),
                    self.now(),
                ),
                ("POST", "draft") => training.save_draft(r.body.as_ref().unwrap()),
                _ => Err(ApiError::missing("没有找到这个接口")),
            };
        }
        if r.method == Method::Get && r.path.starts_with("library/") {
            let catalogue = self
                .catalogue
                .as_ref()
                .map(|catalogue| catalogue.lock().map_err(|_| ApiError::pending()))
                .transpose()?;
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
                    let mut value = library.statement_raw(
                        r.param("id").ok_or_else(|| ApiError::bad("缺少题目编号"))?,
                    )?;
                    library.hydrate_with_cache(
                        &mut value,
                        catalogue.as_deref().map(|c| &c.db),
                        self.public_assets.as_ref(),
                    )?;
                    Ok(value)
                }
                "library/lecture" => {
                    let mut value = library
                        .lecture(r.param("id").ok_or_else(|| ApiError::bad("缺少讲义编号"))?)?;
                    library.hydrate_with_cache(
                        &mut value,
                        catalogue.as_deref().map(|c| &c.db),
                        self.public_assets.as_ref(),
                    )?;
                    Ok(value)
                }
                "library/lectures" => library.lectures(),
                "library/training-lists" => Ok(json!({"lists":library.training_lists()?})),
                "library/asset" => library.asset_with_cache(
                    r.param("sha256").unwrap_or(""),
                    catalogue.as_deref().map(|c| &c.db),
                    self.public_assets.as_ref(),
                ),
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
                "learning-summary" => learning::snapshot(&personal, &self.curriculum, self.now()),
                "learning-summary/history" => {
                    learning::history(&personal, r.param("id").unwrap_or(""))
                }
                "learning-summary/quiz" => {
                    learning::quiz(&self.quizzes, r.param("id").unwrap_or(""))
                }
                "usage" => usage::snapshot(&personal),
                "data/export" => crate::journal_export::export(&personal, self.now()),
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
            "learning-summary/update" => {
                learning::update(&mut personal, body, &self.curriculum, self.now())
            }
            "learning-summary/time" => learning::effective(&mut personal, body, self.now()),
            "usage" => usage::record(&mut personal, body, self.now()),
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
                } else if v["native"] == true {
                    v["status"] = json!(if [
                        "data",
                        "data/export",
                        "contests/events",
                        "contest",
                        "contests/finish",
                        "contests/cancel",
                        "contests/delete",
                        "contests/preview",
                        "contests/start",
                        "goals",
                        "goals/save",
                        "goals/archive",
                        "workspace",
                        "problem",
                        "submission",
                        "training/start",
                        "training/remove",
                        "training/clear",
                        "submissions",
                        "learning-summary",
                        "learning-summary/update",
                        "learning-summary/refresh"
                    ]
                    .contains(&path)
                    {
                        "partial"
                    } else {
                        "implemented"
                    });
                }
                v
            })
            .collect::<Vec<_>>();
        let migrated = endpoints.iter().filter(|v| v["native"] == true).count();
        json!({"protocol":api::PROTOCOL_VERSION,"backend":"rust","transport":"tauri-ipc","releaseReady":false,"sandbox":self.config.sandbox,"owner":self.config.owner,"deployment":"local-test-only","formalArchitecture":"react-python",
            "legacyTotal":endpoints.len(),"legacyImplemented":migrated,"endpoints":endpoints,"nativeRoutes":NATIVE_ROUTES,
            "pendingDomains":["catalogue-projection","training-and-reviews","learning-summary","accounts-and-sync","growth-and-rewards","judge-and-official-browser","online-services","updates-and-installer"]})
    }
}
