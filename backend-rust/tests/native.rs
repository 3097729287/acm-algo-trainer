use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::path::Path;
use tempfile::TempDir;
use tobe_core::{
    ApiRequest, Service, ServiceConfig,
    api::{Method, PROTOCOL_VERSION},
    migration,
    storage::PersonalStore,
    templates,
};

fn store(temp: &TempDir) -> PersonalStore {
    PersonalStore::open(&temp.path().join("personal.sqlite3")).unwrap()
}
fn write(path: &Path, content: Value) {
    std::fs::write(path, content.to_string()).unwrap();
}
fn fixture() -> (TempDir, ServiceConfig) {
    let temp = TempDir::new().unwrap();
    let library = temp.path().join("library.sqlite3");
    let resources = temp.path().join("resources");
    std::fs::create_dir(&resources).unwrap();
    let db = Connection::open(&library).unwrap();
    db.execute_batch("CREATE TABLE problems(id TEXT PRIMARY KEY,url TEXT,raw TEXT,encoded TEXT); CREATE TABLE statements(problem_id TEXT PRIMARY KEY,content TEXT); CREATE TABLE training_lists(id TEXT PRIMARY KEY,content TEXT); CREATE TABLE lectures(id TEXT PRIMARY KEY,content TEXT); CREATE TABLE statement_assets(sha256 TEXT PRIMARY KEY,mime TEXT,data BLOB);").unwrap();
    for (id, title) in [("sample::A", "真实题面"), ("sample::B", "Second problem")] {
        let row =
            json!({"id":id,"title":title,"url":"https://example.com/task","aliasIds":["alias::A"]});
        db.execute(
            "INSERT INTO problems VALUES(?1,'https://example.com/task','{}',?2)",
            params![id, row.to_string()],
        )
        .unwrap();
        db.execute(
            "INSERT INTO statements VALUES(?1,?2)",
            params![
                id,
                json!({"markdown":"原始正文","samples":[{"input":"1\n","output":"2\n"}]})
                    .to_string()
            ],
        )
        .unwrap();
    }
    write(
        &resources.join("code-templates.json"),
        json!({"templates":[{"id":"builtin:test","title":"Builtin","code":"int main() {}","language":"cpp17","practiceIds":["sample::A"]}]}),
    );
    write(
        &resources.join("template-teaching.json"),
        json!({"templates":[],"topics":{}}),
    );
    let config = ServiceConfig {
        library,
        resources,
        personal: temp.path().join("state/personal.sqlite3"),
        sandbox: true,
        owner: "test-owner".into(),
    };
    (temp, config)
}
fn post(service: &Service, path: &str, body: Value) -> tobe_core::ApiResponse {
    let bootstrap = service.handle(ApiRequest::get("account"));
    let token = bootstrap.data.unwrap()["token"]
        .as_str()
        .unwrap()
        .to_owned();
    let mut request = ApiRequest::get(path);
    request.method = Method::Post;
    request.body = Some(body);
    request.token = Some(token);
    request.owner = Some("test-owner".into());
    service.handle(request)
}

#[test]
fn desktop_fullscreen_uses_host_state_after_validating_authority() {
    use std::sync::{
        Arc,
        atomic::{AtomicBool, AtomicUsize, Ordering},
    };
    let (_temp, config) = fixture();
    let personal_path = config.personal.clone();
    let fullscreen = Arc::new(AtomicBool::new(false));
    let calls = Arc::new(AtomicUsize::new(0));
    let host_state = Arc::clone(&fullscreen);
    let host_calls = Arc::clone(&calls);
    let service = Service::open(config)
        .unwrap()
        .with_desktop_fullscreen(move |requested| {
            host_calls.fetch_add(1, Ordering::SeqCst);
            if let Some(requested) = requested {
                host_state.store(requested, Ordering::SeqCst);
            }
            Ok(host_state.load(Ordering::SeqCst))
        });
    assert_eq!(
        service
            .handle(ApiRequest::get("desktop/fullscreen"))
            .data
            .unwrap(),
        json!({"available":true,"fullscreen":false})
    );
    assert_eq!(
        post(&service, "desktop/fullscreen", json!({"fullscreen":true}))
            .data
            .unwrap()["fullscreen"],
        true
    );
    // A host-side change must be observed, rather than an optimistic UI cache.
    fullscreen.store(false, Ordering::SeqCst);
    assert_eq!(
        service
            .handle(ApiRequest::get("desktop/fullscreen"))
            .data
            .unwrap()["fullscreen"],
        false
    );
    let called = calls.load(Ordering::SeqCst);
    for body in [
        json!({}),
        json!({"fullscreen":1}),
        json!({"fullscreen":"true"}),
        json!({"fullscreen":null}),
        json!({"fullscreen":true,"extra":true}),
    ] {
        assert_eq!(
            post(&service, "desktop/fullscreen", body)
                .error
                .unwrap()
                .status,
            400
        );
    }
    let mut invalid = ApiRequest::get("desktop/fullscreen");
    invalid.method = Method::Post;
    invalid.body = Some(json!({"fullscreen":true}));
    invalid.token = Some("forged".into());
    assert_eq!(
        service.handle(invalid).error.unwrap().code,
        "SESSION_EXPIRED"
    );
    let mut switched = ApiRequest::get("desktop/fullscreen");
    switched.owner = Some("another-owner".into());
    assert_eq!(
        service.handle(switched).error.unwrap().code,
        "ACCOUNT_CHANGED"
    );
    assert_eq!(calls.load(Ordering::SeqCst), called);
    assert!(!fullscreen.load(Ordering::SeqCst));
    let db = Connection::open(personal_path).unwrap();
    for table in [
        "training",
        "submissions",
        "drafts",
        "achievement_xp_claims",
        "official_first_xp_awards",
    ] {
        assert_eq!(
            db.query_row(&format!("SELECT count(*) FROM {table}"), [], |row| row
                .get::<_, i64>(0))
                .unwrap(),
            0,
            "{table}"
        );
    }
}

#[test]
fn headless_fullscreen_exposes_unavailability_without_claiming_a_window() {
    let (_temp, config) = fixture();
    let service = Service::open(config).unwrap();
    assert_eq!(
        service
            .handle(ApiRequest::get("desktop/fullscreen"))
            .data
            .unwrap(),
        json!({"available":false,"fullscreen":false})
    );
    assert_eq!(
        post(&service, "desktop/fullscreen", json!({"fullscreen":true}))
            .error
            .unwrap()
            .code,
        "DESKTOP_UNAVAILABLE"
    );
    let (_temp, config) = fixture();
    let service = Service::open(config).unwrap().with_desktop_fullscreen(|_| {
        Err(tobe_core::ApiError::new(
            503,
            "DESKTOP_UNAVAILABLE",
            "窗口已关闭",
        ))
    });
    assert_eq!(
        service
            .handle(ApiRequest::get("desktop/fullscreen"))
            .error
            .unwrap()
            .code,
        "DESKTOP_UNAVAILABLE"
    );
}

#[test]
fn rejects_wrong_protocol_and_invalid_paths() {
    let mut request = ApiRequest::get("preferences");
    request.version = PROTOCOL_VERSION + 1;
    assert_eq!(request.validate().unwrap_err().status, 426);
    for path in [
        "../draft",
        "/api/draft",
        "draft//save",
        "https://evil",
        "draft?x=y",
        "draft\\save",
        "draft\0",
        "draft/",
    ] {
        assert!(ApiRequest::get(path).validate().is_err(), "{path}");
    }
}
#[test]
fn separates_read_and_write_envelopes() {
    let mut request = ApiRequest::get("preferences");
    request.body = Some(json!({}));
    assert!(request.validate().is_err());
    request.method = Method::Post;
    assert!(request.validate().is_ok());
    request.body = Some(json!([]));
    assert!(request.validate().is_err());
}
#[test]
fn supplemental_public_assets_preserve_bytes_and_verify_integrity() {
    use base64::{Engine, engine::general_purpose::STANDARD};
    use sha2::{Digest, Sha256};
    let (_temp, config) = fixture();
    let library = tobe_core::library::Library::open(&config.library).unwrap();
    let derived = Connection::open_in_memory().unwrap();
    derived
        .execute_batch("CREATE TABLE derived_assets(sha256 TEXT PRIMARY KEY,mime TEXT,data BLOB)")
        .unwrap();
    let raw = b"original public resource bytes";
    let sha = format!("{:x}", Sha256::digest(raw));
    derived
        .execute(
            "INSERT INTO derived_assets VALUES(?,'image/png',?)",
            params![sha, raw.as_slice()],
        )
        .unwrap();
    let mut value = json!({"images":{"original":format!("tb-asset:{sha}")},"translation":{"statementPdf":{"data":format!("tb-asset:{sha}")}}});
    library.hydrate_with(&mut value, Some(&derived)).unwrap();
    let expected = format!("data:image/png;base64,{}", STANDARD.encode(raw));
    assert_eq!(value["images"]["original"], expected);
    assert_eq!(value["translation"]["statementPdf"]["data"], expected);
    derived
        .execute(
            "UPDATE derived_assets SET data=?",
            [b"corrupted".as_slice()],
        )
        .unwrap();
    let mut value = json!({"images":{"original":format!("tb-asset:{sha}")}});
    assert_eq!(
        library
            .hydrate_with(&mut value, Some(&derived))
            .unwrap_err()
            .code,
        "ASSET_INTEGRITY"
    );
    assert_eq!(
        library
            .db
            .query_row("SELECT count(*) FROM statement_assets", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        0
    );
}

#[test]
fn rejects_extra_envelope_fields() {
    let value =
        json!({"version":1,"id":"x","method":"GET","path":"preferences","shell":"anything"});
    assert!(serde_json::from_value::<ApiRequest>(value).is_err());
}
#[test]
fn request_size_limits_count_utf8_bytes() {
    let mut request = ApiRequest::get("draft");
    request.method = Method::Post;
    request.body = Some(json!({"code":"中".repeat(100_000)}));
    assert!(request.validate().is_err());
}
#[test]
fn sqlite_persists_unicode_empty_draft_and_language() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    store
        .save_draft(&json!({"id":"练习::A","code":"print('中文')","language":"python3"}))
        .unwrap();
    let value = store.draft("练习::A", "").unwrap();
    assert_eq!(value["draftLanguage"], "python3");
    assert_eq!(value["draft"], "print('中文')");
    let saved = value["draftSavedAt"].clone();
    assert_eq!(
        store
            .save_draft(&json!({"id":"练习::A","code":"print('中文')","language":"python3"}))
            .unwrap()["savedAt"],
        saved
    );
    store
        .save_draft(&json!({"id":"练习::A","code":"","language":"python3"}))
        .unwrap();
    drop(store);
    let store = PersonalStore::open(&temp.path().join("personal.sqlite3")).unwrap();
    assert_eq!(store.draft("练习::A", "").unwrap()["draft"], "");
}
#[test]
fn byte_limit_and_invalid_language_do_not_overwrite_draft() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    store
        .save_draft(&json!({"id":"A","code":"original"}))
        .unwrap();
    for body in [
        json!({"id":"A","code":"x".repeat(65537)}),
        json!({"id":"A","code":"中".repeat(22000)}),
        json!({"id":"A","code":"changed","language":"shell"}),
    ] {
        assert!(store.save_draft(&body).is_err());
    }
    assert_eq!(store.draft("A", "").unwrap()["draft"], "original");
}
#[test]
fn draft_contexts_cannot_fall_through_to_main_code() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    store
        .save_draft(&json!({"id":"A","code":"original"}))
        .unwrap();
    for field in ["reviewId", "contestId"] {
        let mut body = json!({"id":"A","code":"changed"});
        body[field] = json!("context");
        assert_eq!(
            store.save_draft(&body).unwrap_err().code,
            "MIGRATION_PENDING"
        );
    }
    assert_eq!(store.draft("A", "").unwrap()["draft"], "original");
}
#[test]
fn initial_template_revision_conflicts_keep_prior_code() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let first = templates::initial_save(
        &mut store,
        &json!({"title":"我的起始程序","language":"python3","code":"print(1)"}),
    )
    .unwrap()["template"]
        .clone();
    let id = first["id"].as_str().unwrap();
    let error=templates::initial_save(&mut store,&json!({"id":id,"title":"Changed","language":"python3","code":"overwritten","revision":"stale"})).unwrap_err();
    assert_eq!(error.status, 409);
    assert_eq!(store.document(id).unwrap().unwrap()["code"], "print(1)");
}
#[test]
fn deleting_selected_template_resets_selection_and_retains_tombstone() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let first = templates::initial_save(
        &mut store,
        &json!({"title":"Mine","language":"cpp17","code":"int main(){}"}),
    )
    .unwrap()["template"]
        .clone();
    templates::initial_choose(
        &store,
        &json!({"id":first["id"],"language":"cpp17","revision":""}),
    )
    .unwrap();
    let result = templates::initial_save(
        &mut store,
        &json!({"id":first["id"],"revision":first["revision"],"delete":true}),
    )
    .unwrap();
    assert_eq!(result["selection"]["cpp17"], "default");
    assert_eq!(
        store
            .document(first["id"].as_str().unwrap())
            .unwrap()
            .unwrap()["deleted"],
        true
    );
}
#[test]
fn cannot_select_template_for_wrong_language() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let first = templates::initial_save(
        &mut store,
        &json!({"title":"Mine","language":"python3","code":"print(1)"}),
    )
    .unwrap()["template"]
        .clone();
    assert!(
        templates::initial_choose(
            &store,
            &json!({"id":first["id"],"language":"cpp17","revision":""})
        )
        .is_err()
    );
}
#[test]
fn custom_template_tombstones_and_revisions_match_journal() {
    let temp = TempDir::new().unwrap();
    let store = store(&temp);
    let first = templates::save(
        &store,
        &json!({"title":"测试","code":"int x;","language":"cpp17"}),
        &[],
    )
    .unwrap()["template"]
        .clone();
    assert_eq!(first["category"], "我的模板");
    assert!(
        templates::save(
            &store,
            &json!({"id":first["id"],"revision":"wrong","delete":true}),
            &[]
        )
        .is_err()
    );
    let result = templates::save(
        &store,
        &json!({"id":first["id"],"revision":first["revision"],"delete":true}),
        &[],
    )
    .unwrap();
    assert_eq!(result["templates"], json!([]));
    assert_eq!(result["template"]["deleted"], true);
}
#[test]
fn migration_copies_committed_wal_and_unknown_future_tables() {
    let temp = TempDir::new().unwrap();
    let source = temp.path().join("source.sqlite3");
    let store = PersonalStore::open(&source).unwrap();
    store.db.execute_batch("PRAGMA journal_mode=WAL; PRAGMA wal_autocheckpoint=0; CREATE TABLE future_records(id INTEGER PRIMARY KEY,data BLOB); INSERT INTO future_records VALUES(1,x'0001ff');").unwrap();
    store
        .db
        .execute(
            "INSERT INTO drafts VALUES('A','','committed in WAL','2026-01-01T00:00:00Z')",
            [],
        )
        .unwrap();
    let before = migration::logical_fingerprint(&store.db).unwrap();
    let destination = temp.path().join("copy.sqlite3");
    let receipt = migration::import_personal(&source, &destination).unwrap();
    let copy = Connection::open(destination).unwrap();
    assert_eq!(migration::logical_fingerprint(&copy).unwrap(), before);
    assert_eq!(receipt["snapshotSha256"], before);
    assert_eq!(migration::logical_fingerprint(&store.db).unwrap(), before);
}
#[test]
fn migration_does_not_copy_uncommitted_changes() {
    let temp = TempDir::new().unwrap();
    let source = temp.path().join("source.sqlite3");
    let store = PersonalStore::open(&source).unwrap();
    store.db.execute_batch("PRAGMA journal_mode=WAL; BEGIN IMMEDIATE; INSERT INTO drafts VALUES('uncommitted','','private','now');").unwrap();
    let destination = temp.path().join("copy.sqlite3");
    migration::import_personal(&source, &destination).unwrap();
    let copy = Connection::open(destination).unwrap();
    assert_eq!(
        copy.query_row("SELECT count(*) FROM drafts", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        0
    );
    store.db.execute_batch("ROLLBACK").unwrap();
}
#[test]
fn migration_refuses_overwrite_and_legacy_incompatible_schema() {
    let temp = TempDir::new().unwrap();
    let source = temp.path().join("source.sqlite3");
    let _store = PersonalStore::open(&source).unwrap();
    let destination = temp.path().join("existing.sqlite3");
    std::fs::write(&destination, b"preserved").unwrap();
    assert_eq!(
        migration::import_personal(&source, &destination)
            .unwrap_err()
            .status,
        409
    );
    assert_eq!(std::fs::read(&destination).unwrap(), b"preserved");
    let old = temp.path().join("old.sqlite3");
    Connection::open(&old)
        .unwrap()
        .execute_batch("CREATE TABLE drafts(code TEXT)")
        .unwrap();
    assert_eq!(
        migration::import_personal(&old, &temp.path().join("blocked.sqlite3"))
            .unwrap_err()
            .code,
        "SCHEMA_MIGRATION_REQUIRED"
    );
    assert!(!temp.path().join("blocked.sqlite3").exists());
}
#[test]
fn simultaneous_migrations_cannot_replace_each_other() {
    let temp = TempDir::new().unwrap();
    let source = temp.path().join("source.sqlite3");
    let _store = PersonalStore::open(&source).unwrap();
    let destination = temp.path().join("target.sqlite3");
    let jobs = (0..2)
        .map(|_| {
            let source = source.clone();
            let destination = destination.clone();
            std::thread::spawn(move || migration::import_personal(&source, &destination))
        })
        .collect::<Vec<_>>();
    let results = jobs
        .into_iter()
        .map(|j| j.join().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(results.iter().filter(|r| r.is_ok()).count(), 1);
}
#[test]
fn native_route_guards_tokens_and_cross_owner_reads() {
    let (_temp, config) = fixture();
    let service = Service::open(config).unwrap();
    let mut request = ApiRequest::get("initial-code/save");
    request.method = Method::Post;
    request.body = Some(json!({}));
    assert_eq!(service.handle(request).error.unwrap().status, 403);
    let mut request = ApiRequest::get("preferences");
    request.owner = Some("another-owner".into());
    assert_eq!(
        service.handle(request).error.unwrap().code,
        "ACCOUNT_CHANGED"
    );
}
#[test]
fn unfinished_routes_are_explicit_and_release_gate_cannot_be_bypassed() {
    let (_temp, mut config) = fixture();
    let service = Service::open(config.clone()).unwrap();
    let bootstrap = service.handle(ApiRequest::get("account")).data.unwrap();
    assert_eq!(bootstrap["authenticated"], false);
    assert_eq!(
        service
            .handle(ApiRequest::get("insights"))
            .error
            .unwrap()
            .code,
        "MIGRATION_PENDING"
    );
    assert_eq!(
        service
            .handle(ApiRequest::get("unregistered/anything"))
            .error
            .unwrap()
            .status,
        404
    );
    assert_eq!(service.capabilities()["releaseReady"], false);
    config.sandbox = false;
    assert!(Service::open(config).is_err());
}

#[test]
fn malformed_stored_templates_return_structured_errors_without_overwrite() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let id = "initial-code:11111111111111111111111111111111";
    store
        .put_document(id, &json!("malformed old value"))
        .unwrap();
    let error = templates::initial_save(&mut store, &json!({"id":id,"delete":true})).unwrap_err();
    assert_eq!(error.code, "INVALID_STORED_DATA");
    assert_eq!(
        store.document(id).unwrap().unwrap(),
        json!("malformed old value")
    );
}
#[test]
fn library_paging_validates_and_returns_real_unicode_content() {
    let (_temp, config) = fixture();
    let service = Service::open(config).unwrap();
    let mut request = ApiRequest::get("library/page");
    request.query.insert("q".into(), vec!["真实".into()]);
    let value = service.handle(request).data.unwrap();
    assert_eq!(value["total"], 1);
    assert_eq!(value["rows"][0]["title"], "真实题面");
    let mut request = ApiRequest::get("library/page");
    request.query.insert("limit".into(), vec!["-1".into()]);
    assert_eq!(service.handle(request).error.unwrap().status, 400);
}
#[test]
fn native_saves_only_known_problems_and_no_phantom_training() {
    let (_temp, config) = fixture();
    let service = Service::open(config).unwrap();
    assert_eq!(
        post(&service, "draft", json!({"id":"unknown","code":"x"}))
            .error
            .unwrap()
            .status,
        404
    );
    assert!(
        post(
            &service,
            "draft",
            json!({"id":"sample::A","code":"int main(){}"})
        )
        .ok
    );
}
#[test]
fn capabilities_inventory_has_every_legacy_operation() {
    let (_temp, config) = fixture();
    let service = Service::open(config).unwrap();
    let value = service.capabilities();
    assert_eq!(value["legacyTotal"], 139);
    assert!(value["legacyImplemented"].as_u64().unwrap() < 139);
    for path in ["account/register", "account/login", "account/password"] {
        assert!(
            value["endpoints"]
                .as_array()
                .unwrap()
                .iter()
                .any(|e| e["method"] == "POST" && e["path"] == path)
        );
    }
    assert_eq!(
        value["endpoints"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|e| e["path"] == "pk/v1/*")
            .count(),
        2
    );
    assert_eq!(
        value["endpoints"]
            .as_array()
            .unwrap()
            .iter()
            .filter(|e| e["path"] == "team-training/*" && e["native"] == false)
            .count(),
        2
    );
    for request in [
        ApiRequest::get("team-training/history/9ff50828-f862-4544-9535-d5ba858db3e5"),
        ApiRequest::get("team-training/workbench/problem"),
    ] {
        assert_eq!(
            service.handle(request).error.unwrap().code,
            "MIGRATION_PENDING"
        );
    }
    assert_eq!(
        post(&service, "team-training/create", json!({"name":"三人训练"}))
            .error
            .unwrap()
            .code,
        "MIGRATION_PENDING"
    );
}
#[test]
fn production_schema_and_legacy_language_key_are_compatible() {
    let temp = TempDir::new().unwrap();
    let store = store(&temp);
    let key = PersonalStore::draft_key("A", "");
    assert_eq!(key.len(), 79);
    let tables = store
        .db
        .prepare("SELECT name FROM sqlite_master WHERE type='table'")
        .unwrap()
        .query_map([], |r| r.get::<_, String>(0))
        .unwrap()
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    assert!(tables.contains(&"official_first_xp_awards".into()));
    assert!(tables.contains(&"ranking_profile".into()));
}
#[test]
fn logical_fingerprint_covers_blobs_and_is_independent_of_row_order() {
    let a = Connection::open_in_memory().unwrap();
    let b = Connection::open_in_memory().unwrap();
    for db in [&a, &b] {
        db.execute_batch("CREATE TABLE x(a INTEGER,b BLOB)")
            .unwrap();
    }
    a.execute_batch("INSERT INTO x VALUES(1,x'00ff'),(2,x'0102')")
        .unwrap();
    b.execute_batch("INSERT INTO x VALUES(2,x'0102'),(1,x'00ff')")
        .unwrap();
    assert_eq!(
        migration::logical_fingerprint(&a).unwrap(),
        migration::logical_fingerprint(&b).unwrap()
    );
    b.execute_batch("UPDATE x SET b=x'03' WHERE a=1").unwrap();
    assert_ne!(
        migration::logical_fingerprint(&a).unwrap(),
        migration::logical_fingerprint(&b).unwrap()
    );
}
#[test]
fn export_does_not_include_authentication_tables_or_keys() {
    let temp = TempDir::new().unwrap();
    let store = store(&temp);
    store
        .put_document("secret-token", &json!("never-export"))
        .unwrap();
    store.db.execute("INSERT INTO ranking_profile VALUES(1,'user','nickname','never-export','https://example.com','now',NULL)",[]).unwrap();
    assert!(!store.export().unwrap().to_string().contains("never-export"));
}
