#![cfg(windows)]
use flate2::{Compression, write::ZlibEncoder};
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::{
    io::Write,
    path::PathBuf,
    time::{Duration, Instant},
};
use tempfile::TempDir;
use tobe_core::{
    ApiRequest, ApiResponse, Service, ServiceConfig, api::Method, native_judge::Toolchains,
    storage::PersonalStore,
};

fn compressed(value: Value) -> Vec<u8> {
    let mut z = ZlibEncoder::new(Vec::new(), Compression::default());
    z.write_all(value.to_string().as_bytes()).unwrap();
    z.finish().unwrap()
}
fn fixture() -> (TempDir, ServiceConfig) {
    let dir = tempfile::Builder::new()
        .prefix("原生队列 😀 ")
        .tempdir()
        .unwrap();
    let library = dir.path().join("library.sqlite3");
    let db = Connection::open(&library).unwrap();
    db.execute_batch("CREATE TABLE problems(id TEXT PRIMARY KEY,url TEXT,raw TEXT,encoded TEXT);CREATE TABLE statements(problem_id TEXT PRIMARY KEY,content TEXT);CREATE TABLE library_meta(key TEXT PRIMARY KEY,value TEXT);INSERT INTO library_meta VALUES('schema','1'),('revision','1');CREATE TABLE catalog_generation(id INTEGER PRIMARY KEY,identity TEXT,generation INTEGER);INSERT INTO catalog_generation VALUES(1,'fixture',1);").unwrap();
    let row = json!({"id":"fixture::A","title":"加一","url":"https://example.com/A","aliasIds":["alias::A"],"tags":["模拟"],"difficulty":800});
    db.execute(
        "INSERT INTO problems VALUES('fixture::A','https://example.com/A','{}',?)",
        [row.to_string()],
    )
    .unwrap();
    let problem = json!({"id":"fixture::A","title":"加一","markdown":"读入一个整数，输出其加一的值。","statementAvailable":true,"localJudgeSupported":true,"limits":{"timeMs":5000,"memoryMb":128},"samples":[{"input":"1\n","output":"2\n"},{"input":"4\n","output":"5\n"}],"nativeSamplePolicy":{"schema":1,"supported":true,"nonunique":false,"caseInsensitive":false,"checkerUnavailable":false}});
    db.execute(
        "INSERT INTO statements VALUES('fixture::A',?)",
        [problem.to_string()],
    )
    .unwrap();
    drop(db);
    let catalog = Connection::open(dir.path().join("native-catalog.sqlite3")).unwrap();
    catalog.execute_batch("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);INSERT INTO metadata VALUES('format','4'),('source','{\"schema\":\"1\",\"revision\":\"1\",\"generation\":[\"fixture\",1]}');CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT);INSERT INTO aliases VALUES('fixture::A','fixture::A'),('alias::A','fixture::A');CREATE TABLE catalogue(id TEXT PRIMARY KEY,position INTEGER,full BLOB,compact TEXT);CREATE TABLE problem_projections(id TEXT PRIMARY KEY,patch BLOB,knowledge BLOB,error TEXT);").unwrap();
    catalog
        .execute(
            "INSERT INTO catalogue VALUES('fixture::A',0,?,?)",
            params![compressed(row.clone()), row.to_string()],
        )
        .unwrap();
    catalog
        .execute(
            "INSERT INTO problem_projections VALUES('fixture::A',?,?,NULL)",
            params![compressed(json!([])), compressed(json!({}))],
        )
        .unwrap();
    drop(catalog);
    let resources = dir.path().join("resources");
    std::fs::create_dir(&resources).unwrap();
    for name in ["code-templates.json", "template-teaching.json"] {
        std::fs::write(resources.join(name), "{\"templates\":[],\"topics\":{}}").unwrap();
    }
    let config = ServiceConfig {
        library,
        resources,
        personal: dir.path().join("state/personal.sqlite3"),
        sandbox: true,
        owner: "queue-owner".into(),
    };
    {
        let store = PersonalStore::open(&config.personal).unwrap();
        store
            .db
            .execute(
                "INSERT INTO drafts VALUES('fixture::A','','私人草稿 😀','2026-11-01T00:00:00Z')",
                [],
            )
            .unwrap();
        store.db.execute("INSERT INTO training(id,active_at,active) VALUES('fixture::A','2026-11-01T00:00:00Z',1)",[]).unwrap();
        store
            .put_document(
                "identity-sentinel",
                &json!({"owner":"real private identity untouched"}),
            )
            .unwrap();
    }
    (dir, config)
}
fn tools() -> Toolchains {
    Toolchains {
        cpp17: Some(PathBuf::from(
            std::env::var_os("TB_NATIVE_TEST_CPP17").unwrap(),
        )),
        python3: Some(PathBuf::from(
            std::env::var_os("TB_NATIVE_TEST_PYTHON").unwrap(),
        )),
    }
}
fn open(config: &ServiceConfig) -> Service {
    Service::open_with_runner_tools(config.clone(), tools()).unwrap()
}
fn request(service: &Service, body: Value) -> ApiRequest {
    let token = service.handle(ApiRequest::get("account")).data.unwrap()["token"]
        .as_str()
        .unwrap()
        .to_owned();
    let mut r = ApiRequest::get("submissions");
    r.method = Method::Post;
    r.body = Some(body);
    r.owner = Some("queue-owner".into());
    r.token = Some(token);
    r
}
fn body(code: &str) -> Value {
    json!({"id":"alias::A","mode":"run","language":"python3","code":code,"sampleRun":true})
}
fn get(service: &Service, id: &str) -> ApiResponse {
    let mut r = ApiRequest::get("submission");
    r.query.insert("id".into(), vec![id.into()]);
    service.handle(r)
}
fn wait(service: &Service, id: &str) -> Value {
    let deadline = Instant::now() + Duration::from_secs(8);
    loop {
        let answer = get(service, id);
        assert!(answer.ok, "{:?}", answer.error);
        let record = answer.data.unwrap()["submission"].clone();
        if !record["finishedAt"].is_null() {
            return record;
        }
        assert!(Instant::now() < deadline, "Local run did not finish");
        std::thread::sleep(Duration::from_millis(10));
    }
}
fn private_untouched(config: &ServiceConfig) {
    let store = PersonalStore::open(&config.personal).unwrap();
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT code FROM drafts WHERE problem_id='fixture::A'",
                [],
                |r| r.get::<_, String>(0)
            )
            .unwrap(),
        "私人草稿 😀"
    );
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT count(*) FROM training WHERE accepted_at IS NOT NULL",
                [],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
        0
    );
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT count(*) FROM submissions WHERE scope='official' OR verdict='AC'",
                [],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
        0
    );
    assert_eq!(
        store.document("identity-sentinel").unwrap(),
        Some(json!({"owner":"real private identity untouched"}))
    );
}

#[test]
fn native_post_returns_immediately_and_saves_exact_code_and_real_result() {
    let (_dir, config) = fixture();
    let service = open(&config);
    let code = "import time\ntime.sleep(.65)\nprint(int(input())+1)\n# 中文 😀";
    let started = Instant::now();
    let answer = service.handle(request(&service, body(code)));
    assert!(answer.ok, "{:?}", answer.error);
    assert!(started.elapsed() < Duration::from_millis(500));
    let answer = answer.data.unwrap();
    let id = answer["submission"]["id"].as_str().unwrap();
    assert_eq!(answer["submission"]["verdict"], "QUEUED");
    let before = Instant::now();
    assert!(service.handle(ApiRequest::get("preferences")).ok);
    assert!(
        before.elapsed() < Duration::from_millis(400),
        "Compiling/running must not retain the SQLite/UI lock"
    );
    let record = wait(&service, id);
    assert_eq!(record["verdict"], "SAMPLE_PASS");
    assert_eq!(record["code"], code);
    assert_eq!(record["language"], "python3");
    assert_eq!(record["passed"], 2);
    assert_eq!(record["caseResults"].as_array().unwrap().len(), 2);
    private_untouched(&config);
}
#[test]
fn cpp17_runs_through_the_same_service_and_custom_input_is_not_an_ac() {
    let (_dir, config) = fixture();
    let service = open(&config);
    let code = "#include <iostream>\nint main(){long long n;std::cin>>n;std::cout<<n+1<<'\\n';}\n";
    let answer=service.handle(request(&service,json!({"id":"fixture::A","mode":"run","language":"cpp17","code":code,"sampleRun":false,"input":"99\n"})));
    assert!(answer.ok, "{:?}", answer.error);
    let answer = answer.data.unwrap();
    let record = wait(&service, answer["submission"]["id"].as_str().unwrap());
    assert_eq!(record["verdict"], "RUN_OK");
    assert_eq!(record["output"].as_str().unwrap().trim(), "100");
    assert!(record["caseResults"][0]["expected"].is_null());
    private_untouched(&config);
}
#[test]
fn retries_return_one_immutable_run_and_reusing_the_request_id_for_other_code_fails() {
    let (_dir, config) = fixture();
    let service = open(&config);
    let r = request(&service, body("print(int(input())+1)"));
    let first = service.handle(r.clone());
    assert!(first.ok);
    let id = first.data.unwrap()["submission"]["id"].clone();
    let second = service.handle(r.clone());
    assert!(second.ok);
    assert_eq!(second.data.unwrap()["submission"]["id"], id);
    let mut changed = r.clone();
    changed.body.as_mut().unwrap()["code"] = "print(999)".into();
    assert_eq!(
        service.handle(changed).error.unwrap().code,
        "RUN_REQUEST_CONFLICT"
    );
    wait(&service, id.as_str().unwrap());
    let third = service.handle(r);
    assert_eq!(third.data.unwrap()["submission"]["id"], id);
    let db = Connection::open(&config.personal).unwrap();
    assert_eq!(
        db.query_row("SELECT count(*) FROM submissions", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        1
    );
}
#[test]
fn the_third_concurrent_run_is_rejected_before_a_history_row_is_created() {
    let (_dir, config) = fixture();
    let service = open(&config);
    let code = "import time\ntime.sleep(1)\nprint(int(input())+1)";
    for _ in 0..2 {
        let answer = service.handle(request(&service, body(code)));
        assert!(answer.ok, "{:?}", answer.error);
    }
    assert_eq!(
        service
            .handle(request(&service, body(code)))
            .error
            .unwrap()
            .code,
        "RUNNER_BUSY"
    );
    let db = Connection::open(&config.personal).unwrap();
    assert_eq!(
        db.query_row("SELECT count(*) FROM submissions", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        2
    );
}
#[test]
fn authorization_and_unmigrated_contexts_fail_before_creating_history() {
    let (_dir, config) = fixture();
    let service = open(&config);
    let mut r = request(&service, body("print(2)"));
    r.owner = Some("other-owner".into());
    assert_eq!(service.handle(r).error.unwrap().code, "ACCOUNT_CHANGED");
    let mut r = request(&service, body("print(2)"));
    r.token = Some("stale-token".into());
    assert_eq!(service.handle(r).error.unwrap().code, "SESSION_EXPIRED");
    for extra in [
        json!({"mode":"official"}),
        json!({"contestId":"contest-a"}),
        json!({"reviewId":"review-a"}),
        json!({"language":123}),
        json!({"sampleRun":"true"}),
    ] {
        let mut b = body("print(2)");
        b.as_object_mut()
            .unwrap()
            .extend(extra.as_object().unwrap().clone());
        assert!(!service.handle(request(&service, b)).ok);
    }
    let db = Connection::open(&config.personal).unwrap();
    assert_eq!(
        db.query_row("SELECT count(*) FROM submissions", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
    private_untouched(&config);
}

#[test]
fn sample_submission_activates_only_the_submitted_problem_and_survives_reopen() {
    let (_dir, config) = fixture();
    let store = PersonalStore::open(&config.personal).unwrap();
    store.db.execute("DELETE FROM training", []).unwrap();
    drop(store);
    let service = open(&config);
    let mut input = body("print(int(input())+1)");
    input["mode"] = "submit".into();
    let req = request(&service, input);
    let answer = service.handle(req.clone());
    assert!(answer.ok, "{:?}", answer.error);
    let id = answer.data.unwrap()["submission"]["id"]
        .as_str()
        .unwrap()
        .to_owned();
    let result = wait(&service, &id);
    assert_eq!(result["mode"], "submit");
    assert_eq!(result["scope"], "samples");
    assert_eq!(result["verdict"], "SAMPLE_PASS");
    assert_eq!(result["reviewRewardXp"], 0);
    let db = Connection::open(&config.personal).unwrap();
    let active: Vec<String> = db
        .prepare("SELECT id FROM training WHERE active=1")
        .unwrap()
        .query_map([], |row| row.get(0))
        .unwrap()
        .collect::<Result<_, _>>()
        .unwrap();
    assert_eq!(active, ["alias::A"]);
    drop(service);
    let reopened = open(&config);
    assert_eq!(
        reopened.handle(req.clone()).error.unwrap().code,
        "SESSION_EXPIRED"
    );
    let mut req = req;
    req.token = request(&reopened, req.body.clone().unwrap()).token;
    let retry = reopened.handle(req);
    assert!(retry.ok, "{:?}", retry.error);
    assert_eq!(retry.data.unwrap()["submission"]["id"], id);
    assert_eq!(
        get(&reopened, &id).data.unwrap()["submission"]["code"],
        "print(int(input())+1)"
    );
    assert_eq!(
        db.query_row("SELECT COUNT(*) FROM submissions", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        1
    );
    private_untouched(&config);
}

fn add_reviewed(config: &ServiceConfig) {
    let identity = "入门赛 49::D";
    let row = json!({"id":identity,"title":"不相邻的二级台阶","url":"https://example.com/reviewed","aliasIds":[],"tags":["数学"],"difficulty":800,"judgeScope":"local"});
    let problem = json!({"id":identity,"title":row["title"],"markdown":"允许迈一步或两步，不能连续迈两步。","statementAvailable":true,"localJudgeSupported":true,"limits":{"timeMs":5000,"memoryMb":128},"samples":[{"input":"3\n","output":"3\n"}],"nativeSamplePolicy":{"schema":1,"supported":true,"sourceScope":"local","nonunique":false,"caseInsensitive":false,"checkerUnavailable":false}});
    let library = Connection::open(&config.library).unwrap();
    library
        .execute(
            "INSERT INTO problems VALUES(?,?,'{}',?)",
            params![identity, row["url"].as_str().unwrap(), row.to_string()],
        )
        .unwrap();
    library
        .execute(
            "INSERT INTO statements VALUES(?,?)",
            params![identity, problem.to_string()],
        )
        .unwrap();
    let catalog = Connection::open(
        config
            .library
            .parent()
            .unwrap()
            .join("native-catalog.sqlite3"),
    )
    .unwrap();
    catalog
        .execute("INSERT INTO aliases VALUES(?,?)", [identity, identity])
        .unwrap();
    catalog
        .execute(
            "INSERT INTO catalogue VALUES(?,1,?,?)",
            params![identity, compressed(row.clone()), row.to_string()],
        )
        .unwrap();
    catalog
        .execute(
            "INSERT INTO problem_projections VALUES(?,?,?,NULL)",
            params![identity, compressed(json!([])), compressed(json!({}))],
        )
        .unwrap();
}

#[test]
fn audited_cpp_submission_scores_a_local_exam_without_official_ac_or_rewards() {
    let (_dir, config) = fixture();
    add_reviewed(&config);
    let clock = chrono::DateTime::parse_from_rfc3339("2026-11-06T04:00:00Z")
        .unwrap()
        .to_utc();
    let store = PersonalStore::open(&config.personal).unwrap();
    let slots = json!([{"id":"入门赛 49::D","letter":"A","title":"不相邻的二级台阶","difficulty":800,"tags":["数学"],"judgeScope":"local","statementAvailable":true,"trainingAdded":false},{"id":"fixture::A","letter":"B","title":"加一","difficulty":800,"tags":["模拟"],"judgeScope":"samples","statementAvailable":true,"trainingAdded":false}]);
    store.db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config) VALUES('local-exam','本地审核考场','running','2026-11-06T03:00:00Z','2026-11-06T05:00:00Z',120,?,?)",params![slots.to_string(),json!({"strategy":"comprehensive","editedTrainingOnly":true}).to_string()]).unwrap();
    store.db.execute("INSERT INTO training(id,active_at,active,mock_due,mock_due_at,mock_due_context) VALUES('入门赛 49::D','2026-11-06T03:00:00Z',0,1,'2026-11-06T03:00:00Z','local-exam')",[]).unwrap();
    drop(store);
    let service = open(&config).with_test_clock(clock);
    let code = "#include <iostream>\nint main(){int n;std::cin>>n;unsigned long long d[61]={1,1,2};for(int i=3;i<=n;i++)d[i]=d[i-1]+d[i-3];std::cout<<d[n]<<'\\n';}\n";
    let req = request(
        &service,
        json!({"id":"入门赛 49::D","mode":"submit","language":"cpp17","code":code,"contestId":"local-exam"}),
    );
    let result = service.handle(req.clone());
    assert!(result.ok, "{:?}", result.error);
    let id = result.data.unwrap()["submission"]["id"]
        .as_str()
        .unwrap()
        .to_owned();
    let result = wait(&service, &id);
    assert_eq!(result["verdict"], "SAMPLE_PASS", "{result}");
    assert_eq!(result["scope"], "local");
    assert_eq!(result["passed"], 61);
    assert_eq!(result["total"], 61);
    assert_eq!(result["reviewRewardXp"], 0);
    let mut query = ApiRequest::get("contest");
    query.query.insert("id".into(), vec!["local-exam".into()]);
    let exam = service.handle(query.clone());
    assert!(exam.ok, "{:?}", exam.error);
    assert_eq!(exam.data.unwrap()["contest"]["accepted"], 1);
    let store = PersonalStore::open(&config.personal).unwrap();
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT mock_due FROM training WHERE id='入门赛 49::D'",
                [],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
        0
    );
    assert_eq!(
        store
            .db
            .query_row("SELECT COUNT(*) FROM training WHERE active=1", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        2
    );
    assert!(store.documents("review-reward:").unwrap().is_empty());
    assert_eq!(
        store
            .document(&format!("native-run:{id}"))
            .unwrap()
            .unwrap()["progressPending"],
        false
    );
    private_untouched(&config);
    drop(service);
    let service = open(&config).with_test_clock(clock);
    let mut req = req;
    req.token = request(&service, req.body.clone().unwrap()).token;
    assert_eq!(service.handle(req).data.unwrap()["submission"]["id"], id);
    assert_eq!(
        service.handle(query).data.unwrap()["contest"]["accepted"],
        1
    );
    private_untouched(&config);
}

#[test]
fn replay_submission_is_rejected_before_any_receipt_or_activation() {
    let (_dir, config) = fixture();
    exam(&config, true);
    let clock = chrono::DateTime::parse_from_rfc3339("2026-11-06T04:00:00Z")
        .unwrap()
        .to_utc();
    let service = open(&config).with_test_clock(clock);
    let mut input = body("print(2)");
    input["id"] = "fixture::A".into();
    input["mode"] = "submit".into();
    input["contestId"] = "native-exam".into();
    let error = service.handle(request(&service, input)).error.unwrap();
    assert_eq!(error.status, 409);
    assert!(error.message.contains("原站提交"));
    let store = PersonalStore::open(&config.personal).unwrap();
    assert_eq!(
        store
            .db
            .query_row("SELECT COUNT(*) FROM submissions", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        0
    );
    assert!(store.documents("native-run:").unwrap().is_empty());
    private_untouched(&config);
}

#[test]
fn failed_training_activation_rolls_back_the_whole_submission_reservation() {
    let (_dir, config) = fixture();
    let db = Connection::open(&config.personal).unwrap();
    db.execute_batch("CREATE TRIGGER fail_activation BEFORE INSERT ON training BEGIN SELECT RAISE(ABORT,'activation failed'); END;").unwrap();
    let service = open(&config);
    let mut input = body("print(int(input())+1)");
    input["mode"] = "submit".into();
    let req = request(&service, input);
    assert!(!service.handle(req.clone()).ok);
    assert_eq!(
        db.query_row("SELECT COUNT(*) FROM submissions", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        0
    );
    let store = PersonalStore::open(&config.personal).unwrap();
    assert!(store.documents("native-run:").unwrap().is_empty());
    assert!(store.documents("native-run-request:").unwrap().is_empty());
    db.execute_batch("DROP TRIGGER fail_activation").unwrap();
    let answer = service.handle(req);
    assert!(answer.ok, "{:?}", answer.error);
    wait(
        &service,
        answer.data.unwrap()["submission"]["id"].as_str().unwrap(),
    );
    private_untouched(&config);
}
#[test]
fn review_local_run_keeps_its_binding_without_an_official_pass_or_reward() {
    let (_dir, config) = fixture();
    let review = "1234567890abcdef1234567890abcdef";
    let task = json!({"id":review,"problemId":"fixture::A","problemKey":"example.com/A","due":"2026-11-01","openedAt":null,"completedAt":null,"failures":[],"processed":[]});
    let store = PersonalStore::open(&config.personal).unwrap();
    store
        .put_document(&format!("review-task:{review}"), &task)
        .unwrap();
    drop(store);
    let service = open(&config);
    let mut request_body = body("n=int(input());print(n+1)");
    request_body["reviewId"] = json!(review);
    let answer = service.handle(request(&service, request_body));
    assert!(answer.ok, "{:?}", answer.error);
    let id = answer.data.unwrap()["submission"]["id"]
        .as_str()
        .unwrap()
        .to_owned();
    let result = wait(&service, &id);
    assert_eq!(result["verdict"], "SAMPLE_PASS");
    assert_eq!(result["scope"], "samples");
    assert_eq!(result["reviewRewardXp"], 0);
    let store = PersonalStore::open(&config.personal).unwrap();
    assert_eq!(
        store.document(&format!("review-receipt:{id}")).unwrap(),
        Some(json!(review))
    );
    assert!(
        store
            .document(&format!("review-task:{review}"))
            .unwrap()
            .unwrap()["completedAt"]
            .is_null()
    );
    assert!(store.documents("review-reward:").unwrap().is_empty());
    private_untouched(&config);
}

fn exam(config: &ServiceConfig, available: bool) {
    let store = PersonalStore::open(&config.personal).unwrap();
    store.db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config) VALUES('native-exam','原生考场','running','2026-11-06T03:00:00Z','2026-11-06T05:00:00Z',120,?,?)",params![json!([{"id":"fixture::A","letter":"A","title":"加一","difficulty":800,"tags":["模拟"],"judgeScope":"official","statementAvailable":available,"trainingAdded":false}]).to_string(),json!({"strategy":"replay","editedTrainingOnly":true}).to_string()]).unwrap();
}

#[test]
fn a_real_exam_sample_run_keeps_context_and_private_code_without_becoming_an_official_solve() {
    let (_dir, config) = fixture();
    exam(&config, true);
    let clock = chrono::DateTime::parse_from_rfc3339("2026-11-06T04:00:00Z")
        .unwrap()
        .to_utc();
    let service = open(&config).with_test_clock(clock);
    let mut input = body("n=int(input());print(n+1)");
    input["id"] = json!("fixture::A");
    input["contestId"] = json!("native-exam");
    let answer = service.handle(request(&service, input));
    assert!(answer.ok, "{:?}", answer.error);
    let id = answer.data.unwrap()["submission"]["id"]
        .as_str()
        .unwrap()
        .to_owned();
    let result = wait(&service, &id);
    assert_eq!(result["contestId"], "native-exam");
    assert_eq!(result["verdict"], "SAMPLE_PASS");
    assert_eq!(result["scope"], "samples");
    let mut query = ApiRequest::get("contest");
    query.query.insert("id".into(), vec!["native-exam".into()]);
    let score = service.handle(query);
    assert!(score.ok, "{:?}", score.error);
    assert_eq!(score.data.unwrap()["contest"]["accepted"], 0);
    let mut finish = request(&service, json!({"contestId":"native-exam"}));
    finish.path = "contests/finish".into();
    let ended = service.handle(finish);
    assert!(ended.ok, "{:?}", ended.error);
    assert_eq!(ended.data.unwrap()["contest"]["accepted"], 0);
    private_untouched(&config);
}

#[test]
fn missing_exam_slots_and_late_runs_fail_before_creating_a_history_row() {
    let (_dir, config) = fixture();
    exam(&config, false);
    let clock = chrono::DateTime::parse_from_rfc3339("2026-11-06T04:00:00Z")
        .unwrap()
        .to_utc();
    let service = open(&config).with_test_clock(clock);
    let mut input = body("print(2)");
    input["id"] = json!("fixture::A");
    input["contestId"] = json!("native-exam");
    let refused = service.handle(request(&service, input.clone()));
    assert_eq!(refused.error.unwrap().status, 422);
    drop(service);
    let service = open(&config).with_test_clock(clock + chrono::Duration::hours(2));
    let refused = service.handle(request(&service, input));
    assert_eq!(refused.error.unwrap().status, 409);
    let store = PersonalStore::open(&config.personal).unwrap();
    assert_eq!(
        store
            .db
            .query_row("SELECT COUNT(*) FROM submissions", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        0
    );
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT finished_at FROM contests WHERE id='native-exam'",
                [],
                |row| row.get::<_, String>(0)
            )
            .unwrap(),
        "2026-11-06T05:00:00Z"
    );
    private_untouched(&config);
}
#[test]
fn graceful_shutdown_cancels_and_finishes_owned_jobs_and_releases_the_workspace() {
    let (_dir, config) = fixture();
    let service = open(&config);
    let answer = service.handle(request(
        &service,
        body("import time\ntime.sleep(20)\nprint(2)"),
    ));
    assert!(answer.ok);
    let id = answer.data.unwrap()["submission"]["id"]
        .as_str()
        .unwrap()
        .to_owned();
    assert_eq!(
        Service::open_with_runner_tools(config.clone(), tools())
            .err()
            .unwrap()
            .code,
        "RUNNER_WORKSPACE_BUSY"
    );
    std::thread::sleep(Duration::from_millis(70));
    let started = Instant::now();
    drop(service);
    assert!(started.elapsed() < Duration::from_secs(5));
    let service = open(&config);
    let record = get(&service, &id).data.unwrap()["submission"].clone();
    assert_eq!(record["verdict"], "ERROR");
    assert!(!record["finishedAt"].is_null());
    assert!(record["code"].as_str().unwrap().contains("sleep(20)"));
    private_untouched(&config);
}
#[test]
fn restart_recovers_only_owned_native_jobs_and_preserves_other_pending_records() {
    let (_dir, config) = fixture();
    {
        let store = PersonalStore::open(&config.personal).unwrap();
        for (id, owner) in [("owned", "queue-owner"), ("foreign", "other-owner")] {
            store.db.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,verdict,scope,sample_run) VALUES(?,'fixture::A','run','original source','2026-11-01T00:00:00Z','QUEUED','samples',1)",[id]).unwrap();
            store
                .put_document(
                    &format!("native-run:{id}"),
                    &json!({"schema":1,"owner":owner,"status":"queued"}),
                )
                .unwrap();
        }
    }
    let service = open(&config);
    assert_eq!(
        get(&service, "owned").data.unwrap()["submission"]["verdict"],
        "ERROR"
    );
    assert_eq!(
        get(&service, "foreign").data.unwrap()["submission"]["verdict"],
        "QUEUED"
    );
    assert_eq!(
        service
            .handle(request(&service, body("print(2)")))
            .error
            .unwrap()
            .code,
        "MIGRATION_PENDING"
    );
    let db = Connection::open(&config.personal).unwrap();
    assert_eq!(
        db.query_row("SELECT count(*) FROM submissions", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        2
    );
}

#[test]
fn restart_marks_only_verified_owned_full_submissions_interrupted_without_executing_source() {
    let (_dir, config) = fixture();
    add_reviewed(&config);
    let store = PersonalStore::open(&config.personal).unwrap();
    for (id, owner) in [
        ("reviewed-owned", "queue-owner"),
        ("reviewed-foreign", "other-owner"),
    ] {
        store.db.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,verdict,scope,sample_run) VALUES(?,'入门赛 49::D','submit','MUST NEVER EXECUTE THIS RETAINED SOURCE','2026-11-01T00:00:00Z','QUEUED','local',0)",[id]).unwrap();
        store.put_document(&format!("native-run:{id}"),&json!({"schema":2,"owner":owner,"status":"queued","problemId":"入门赛 49::D","mode":"submit","scope":"local","reviewedProfile":"入门赛 49::D","sourceSha256":tobe_core::reviewed_judge::SOURCE_SHA256})).unwrap();
    }
    drop(store);
    let service = open(&config);
    let owned = get(&service, "reviewed-owned");
    assert!(owned.ok, "{:?}", owned.error);
    let owned = owned.data.unwrap();
    assert_eq!(owned["submission"]["verdict"], "ERROR");
    assert_eq!(owned["submission"]["mode"], "submit");
    assert_eq!(owned["submission"]["scope"], "local");
    assert_eq!(
        owned["submission"]["code"],
        "MUST NEVER EXECUTE THIS RETAINED SOURCE"
    );
    assert_eq!(
        get(&service, "reviewed-foreign").data.unwrap()["submission"]["verdict"],
        "QUEUED"
    );
    private_untouched(&config);
}

#[test]
fn unverified_reviewed_markers_preserve_the_original_pending_row() {
    let (_dir, config) = fixture();
    add_reviewed(&config);
    let store = PersonalStore::open(&config.personal).unwrap();
    store.db.execute("INSERT INTO submissions(id,problem_id,mode,code,submitted_at,verdict,scope,sample_run) VALUES('unverified','入门赛 49::D','submit','original source','2026-11-01T00:00:00Z','QUEUED','local',0)",[]).unwrap();
    let marker = json!({"schema":2,"owner":"queue-owner","status":"queued","problemId":"入门赛 49::D","mode":"submit","scope":"local","reviewedProfile":"入门赛 49::D","sourceSha256":"bad-source"});
    store
        .put_document("native-run:unverified", &marker)
        .unwrap();
    let error = Service::open_with_runner_tools(config.clone(), tools())
        .err()
        .unwrap();
    assert_eq!(error.code, "MIGRATION_PENDING");
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT verdict FROM submissions WHERE id='unverified'",
                [],
                |r| r.get::<_, String>(0)
            )
            .unwrap(),
        "QUEUED"
    );
    assert_eq!(
        store.document("native-run:unverified").unwrap(),
        Some(marker)
    );
    private_untouched(&config);
}

#[test]
fn deferred_progress_write_is_atomic_and_retried_after_restart_without_rerunning_code() {
    let (_dir, config) = fixture();
    add_reviewed(&config);
    let store = PersonalStore::open(&config.personal).unwrap();
    store.db.execute("INSERT INTO training(id,active_at,active,mock_due,mock_due_at,mock_due_context) VALUES('入门赛 49::D','2026-11-01T00:00:00Z',1,1,'2026-11-01T00:00:00Z','local-exam')",[]).unwrap();
    store.db.execute("INSERT INTO submissions(id,problem_id,contest_id,mode,code,submitted_at,finished_at,verdict,scope,sample_run) VALUES('deferred','入门赛 49::D','local-exam','submit','MUST NEVER REEXECUTE','2026-11-02T00:00:00Z','2026-11-02T00:00:01Z','SAMPLE_PASS','local',0)",[]).unwrap();
    store.put_document("native-run:deferred",&json!({"schema":2,"owner":"queue-owner","status":"finished","progressPending":true,"problemId":"入门赛 49::D","mode":"submit","scope":"local","reviewedProfile":"入门赛 49::D","sourceSha256":tobe_core::reviewed_judge::SOURCE_SHA256})).unwrap();
    store.db.execute_batch("CREATE TRIGGER fail_progress BEFORE UPDATE ON training BEGIN SELECT RAISE(ABORT,'temporary progress failure'); END;").unwrap();
    let service = open(&config);
    let result = service.handle(ApiRequest::get("workspace"));
    assert!(!result.ok);
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT mock_due FROM training WHERE id='入门赛 49::D'",
                [],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
        1
    );
    assert_eq!(
        store.document("native-run:deferred").unwrap().unwrap()["progressPending"],
        true
    );
    drop(service);
    store
        .db
        .execute_batch("DROP TRIGGER fail_progress")
        .unwrap();
    let service = open(&config);
    let result = service.handle(ApiRequest::get("workspace"));
    assert!(result.ok, "{:?}", result.error);
    assert_eq!(
        store
            .db
            .query_row(
                "SELECT mock_due FROM training WHERE id='入门赛 49::D'",
                [],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
        0
    );
    assert_eq!(
        store.document("native-run:deferred").unwrap().unwrap()["progressPending"],
        false
    );
    assert_eq!(store.db.query_row("SELECT COUNT(*) FROM submissions WHERE id='deferred' AND code='MUST NEVER REEXECUTE'",[],|r|r.get::<_,i64>(0)).unwrap(),1);
    private_untouched(&config);
}
#[test]
fn completed_output_survives_a_temporary_database_write_failure_and_is_retried() {
    let (_dir, config) = fixture();
    let service = open(&config);
    let db = Connection::open(&config.personal).unwrap();
    db.execute_batch("CREATE TRIGGER fail_run_write BEFORE UPDATE ON submissions BEGIN SELECT RAISE(ABORT,'temporary write failure'); END;").unwrap();
    let answer = service.handle(request(&service, body("print(int(input())+1)")));
    assert!(answer.ok);
    let id = answer.data.unwrap()["submission"]["id"]
        .as_str()
        .unwrap()
        .to_owned();
    let deadline = Instant::now() + Duration::from_secs(5);
    loop {
        if !get(&service, &id).ok {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "Expected a retriable persistence failure"
        );
        std::thread::sleep(Duration::from_millis(10));
    }
    assert!(!service.handle(request(&service, body("print(0)"))).ok);
    db.execute_batch("DROP TRIGGER fail_run_write;").unwrap();
    let record = wait(&service, &id);
    assert_eq!(record["verdict"], "SAMPLE_PASS");
    assert_eq!(record["passed"], 2);
    assert_eq!(record["caseResults"].as_array().unwrap().len(), 2);
    assert_eq!(
        db.query_row("SELECT count(*) FROM submissions", [], |r| r
            .get::<_, i64>(0))
            .unwrap(),
        1
    );
    private_untouched(&config);
}
