use base64::{Engine, engine::general_purpose::STANDARD};
use flate2::{Compression, write::ZlibEncoder};
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    io::Write,
    sync::{
        Arc, Mutex,
        atomic::{AtomicUsize, Ordering},
        mpsc,
    },
    time::Duration,
};
use tempfile::TempDir;
use tobe_core::{
    ApiRequest, Service, ServiceConfig,
    api::Method,
    library::{Library, asset_references},
    migration::logical_fingerprint,
    public_assets::{AssetCache, FetchError, Fetcher, PUBLIC_ROOT, TrustPolicy},
    storage::PersonalStore,
};

fn sha(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn compressed(value: Value) -> Vec<u8> {
    let mut z = ZlibEncoder::new(Vec::new(), Compression::default());
    z.write_all(value.to_string().as_bytes()).unwrap();
    z.finish().unwrap()
}
struct Fixture {
    folder: TempDir,
    config: ServiceConfig,
    image: Vec<u8>,
    pdf: Vec<u8>,
}
impl Fixture {
    fn new() -> Self {
        let folder = tempfile::tempdir().unwrap();
        let library = folder.path().join("library.sqlite3");
        let db = Connection::open(&library).unwrap();
        db.execute_batch("CREATE TABLE problems(id TEXT PRIMARY KEY,url TEXT,raw TEXT,encoded TEXT);CREATE TABLE statements(problem_id TEXT PRIMARY KEY,content TEXT);CREATE TABLE statement_assets(sha256 TEXT PRIMARY KEY,mime TEXT,data BLOB);CREATE TABLE remote_statement_assets(sha256 TEXT PRIMARY KEY,mime TEXT,bytes INTEGER,url TEXT);CREATE TABLE solutions(problem_id TEXT PRIMARY KEY,markdown TEXT,images TEXT,source_path TEXT,digest TEXT);CREATE TABLE detailed_solutions(problem_id TEXT PRIMARY KEY,markdown TEXT,images TEXT,source_path TEXT,digest TEXT);CREATE TABLE solution_methods(problem_id TEXT PRIMARY KEY,content TEXT);CREATE TABLE lectures(id TEXT PRIMARY KEY,content TEXT);CREATE TABLE problem_lectures(problem_id TEXT,lecture_id TEXT,kind TEXT,position INTEGER);CREATE TABLE library_meta(key TEXT PRIMARY KEY,value TEXT);INSERT INTO library_meta VALUES('schema','1'),('revision','1');CREATE TABLE catalog_generation(id INTEGER PRIMARY KEY,identity TEXT,generation INTEGER);INSERT INTO catalog_generation VALUES(1,'asset-fixture',1);").unwrap();
        let image=STANDARD.decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK8sAAAAASUVORK5CYII=").unwrap();
        let pdf = b"%PDF-1.4\n% Generated original-resource fixture\n%%EOF".to_vec();
        for (mime, body) in [("image/png", &image), ("application/pdf", &pdf)] {
            let digest = sha(body);
            db.execute(
                "INSERT INTO remote_statement_assets VALUES(?,?,?,?)",
                params![
                    digest,
                    mime,
                    body.len() as i64,
                    format!("{PUBLIC_ROOT}{digest}.bin")
                ],
            )
            .unwrap();
        }
        let row = json!({"id":"fixture::A","title":"原始图片与 PDF","url":"https://example.org/A","difficulty":1000,"tags":[],"platform":"Codeforces","contest":"Div.3 999","problem":"A"});
        db.execute(
            "INSERT INTO problems VALUES('fixture::A','https://example.org/A','{}',?)",
            [row.to_string()],
        )
        .unwrap();
        let images = json!({"figure.png":format!("tb-asset:{}",sha(&image))});
        let statement = json!({"markdown":"![原始图片](figure.png)","images":images,"archivedImages":{"saved.png":format!("/api/library-assets/{}",sha(&image))},"statementPdf":{"data":format!("tb-asset:{}",sha(&pdf))},"attachments":{"paper.pdf":{"data":format!("tb-asset:{}",sha(&pdf))}},"translation":{"markdown":"译文","images":images,"statementPdf":{"data":format!("tb-asset:{}",sha(&pdf))}},"samples":[{"input":"1\n","output":"2\n"}]});
        db.execute(
            "INSERT INTO statements VALUES('fixture::A',?)",
            [statement.to_string()],
        )
        .unwrap();
        for table in ["solutions", "detailed_solutions"] {
            db.execute(&format!("INSERT INTO {table} VALUES('fixture::A','![图](figure.png)',?,'fixture','fixture')"),[images.to_string()]).unwrap();
        }
        db.execute(
            "INSERT INTO solution_methods VALUES('fixture::A',?)",
            [
                json!({"methods":[{"id":"other","markdown":"![图](figure.png)","images":images}]})
                    .to_string(),
            ],
        )
        .unwrap();
        db.execute("INSERT INTO lectures VALUES('lecture::A',?)",[json!({"id":"lecture::A","title":"原始讲义","markdown":"![图](figure.png)","images":images,"sourceProblemIds":["fixture::A"]}).to_string()]).unwrap();
        drop(db);
        let catalogue = Connection::open(folder.path().join("native-catalog.sqlite3")).unwrap();
        catalogue.execute_batch("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);INSERT INTO metadata VALUES('format','4'),('source','{\"schema\":\"1\",\"revision\":\"1\",\"generation\":[\"asset-fixture\",1]}');CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT);INSERT INTO aliases VALUES('fixture::A','fixture::A'),('alias::A','fixture::A');CREATE TABLE catalogue(id TEXT PRIMARY KEY,position INTEGER,full BLOB,compact TEXT);CREATE TABLE problem_projections(id TEXT PRIMARY KEY,patch BLOB,knowledge BLOB,error TEXT);CREATE TABLE derived_assets(sha256 TEXT PRIMARY KEY,mime TEXT,data BLOB);").unwrap();
        catalogue
            .execute(
                "INSERT INTO catalogue VALUES('fixture::A',0,?,?)",
                params![compressed(row.clone()), row.to_string()],
            )
            .unwrap();
        catalogue
            .execute(
                "INSERT INTO problem_projections VALUES('fixture::A',?,?,NULL)",
                params![compressed(json!([])), compressed(json!({}))],
            )
            .unwrap();
        catalogue
            .execute_batch(
                "CREATE TABLE review_knowledge(id TEXT PRIMARY KEY,content BLOB,error TEXT);INSERT INTO metadata VALUES('reviewKnowledgeVersion','1')",
            )
            .unwrap();
        catalogue
            .execute(
                "INSERT INTO review_knowledge VALUES('fixture::A',?,NULL)",
                [compressed(json!({}))],
            )
            .unwrap();
        drop(catalogue);
        let resources = folder.path().join("resources");
        std::fs::create_dir(&resources).unwrap();
        for name in ["code-templates.json", "template-teaching.json"] {
            std::fs::write(resources.join(name), "{\"templates\":[],\"topics\":{}}").unwrap();
        }
        let config = ServiceConfig {
            library,
            resources,
            personal: folder.path().join("state/personal.sqlite3"),
            sandbox: true,
            owner: "asset-owner".into(),
        };
        let personal = PersonalStore::open(&config.personal).unwrap();
        personal
            .db
            .execute(
                "INSERT INTO drafts VALUES('fixture::A','','原普通草稿 😀','2026-11-01T00:00:00Z')",
                [],
            )
            .unwrap();
        Self {
            folder,
            config,
            image,
            pdf,
        }
    }
    fn cache(&self, offline: bool, fetcher: Arc<dyn Fetcher>) -> AssetCache {
        AssetCache::new(
            self.folder.path().join("cache/public-assets.sqlite3"),
            TrustPolicy::new("https://47.82.84.74").unwrap(),
            offline,
        )
        .with_fetcher(fetcher)
    }
    fn fingerprint(&self) -> String {
        logical_fingerprint(&Connection::open(&self.config.personal).unwrap()).unwrap()
    }
    fn transport(&self) -> Arc<Transport> {
        Arc::new(Transport {
            bodies: [
                (sha(&self.image), self.image.clone()),
                (sha(&self.pdf), self.pdf.clone()),
            ]
            .into_iter()
            .collect(),
            calls: AtomicUsize::new(0),
            fail: false,
            entered: Mutex::new(None),
            release: Mutex::new(None),
        })
    }
    fn overdue(&self, config: Value) {
        let personal = Connection::open(&self.config.personal).unwrap();
        personal.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config) VALUES('expired','过期原生考场','running','2026-11-06T03:00:00.000000Z','2026-11-06T04:00:00.000000Z',60,?,?)",params![json!([{"id":"fixture::A","letter":"A","title":"原始图片与 PDF","difficulty":1000,"tags":[],"judgeScope":"official","statementAvailable":true}]).to_string(),config.to_string()]).unwrap();
    }
}
struct Transport {
    bodies: BTreeMap<String, Vec<u8>>,
    calls: AtomicUsize,
    fail: bool,
    entered: Mutex<Option<mpsc::Sender<()>>>,
    release: Mutex<Option<mpsc::Receiver<()>>>,
}
impl Fetcher for Transport {
    fn fetch(
        &self,
        url: &str,
        _mime: &str,
        _bytes: u64,
        _timeout: Duration,
        writer: &mut dyn Write,
    ) -> Result<(), FetchError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        if self.fail {
            return Err(FetchError::Unavailable);
        }
        if let Some(entered) = self.entered.lock().unwrap().take() {
            entered.send(()).unwrap();
        }
        if let Some(release) = self.release.lock().unwrap().take() {
            release.recv_timeout(Duration::from_secs(5)).unwrap();
        }
        let digest = url
            .rsplit('/')
            .next()
            .unwrap()
            .strip_suffix(".bin")
            .unwrap();
        writer
            .write_all(&self.bodies[digest])
            .map_err(|_| FetchError::Unavailable)
    }
}
fn get(service: &Service, path: &str, key: &str, value: &str) -> tobe_core::ApiResponse {
    let mut r = ApiRequest::get(path);
    r.query.insert(key.into(), vec![value.into()]);
    service.handle(r)
}

#[test]
fn original_images_pdf_methods_and_lectures_are_downloaded_once_then_read_offline() {
    let f = Fixture::new();
    let transport = f.transport();
    let seed = std::fs::read(&f.config.library).unwrap();
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(false, transport.clone()));
    let problem = get(&service, "problem", "id", "alias::A");
    assert!(problem.ok, "{:?}", problem.error);
    let problem = problem.data.unwrap();
    assert_eq!(problem["draft"], "原普通草稿 😀");
    assert!(
        problem["images"]["figure.png"]
            .as_str()
            .unwrap()
            .starts_with("data:image/png;base64,")
    );
    assert!(
        problem["statementPdf"]["data"]
            .as_str()
            .unwrap()
            .starts_with("data:application/pdf;base64,")
    );
    assert!(
        problem["attachments"]["paper.pdf"]["data"]
            .as_str()
            .unwrap()
            .starts_with("data:application/pdf;base64,")
    );
    assert_eq!(transport.calls.load(Ordering::SeqCst), 2);
    let solution = get(&service, "solution", "id", "fixture::A");
    assert!(solution.ok, "{:?}", solution.error);
    let solution = solution.data.unwrap();
    for value in [
        &solution["images"],
        &solution["detailedSolution"]["images"],
        &solution["methods"][0]["images"],
    ] {
        assert!(
            value["figure.png"]
                .as_str()
                .unwrap()
                .starts_with("data:image/png;base64,")
        );
    }
    assert!(
        get(&service, "lecture", "id", "lecture::A").data.unwrap()["images"]["figure.png"]
            .as_str()
            .unwrap()
            .starts_with("data:image/png;base64,")
    );
    drop(service);
    let offline = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(true, transport.clone()));
    assert!(get(&offline, "problem", "id", "fixture::A").ok);
    assert_eq!(
        get(&offline, "library/asset", "sha256", &sha(&f.pdf))
            .data
            .unwrap()["data"],
        STANDARD.encode(&f.pdf)
    );
    assert_eq!(transport.calls.load(Ordering::SeqCst), 2);
    assert_eq!(std::fs::read(&f.config.library).unwrap(), seed);
}

#[test]
fn offline_or_failed_resources_leave_review_opening_training_and_drafts_unchanged() {
    let f = Fixture::new();
    let transport = Transport {
        bodies: BTreeMap::new(),
        calls: AtomicUsize::new(0),
        fail: true,
        entered: Mutex::new(None),
        release: Mutex::new(None),
    };
    let transport = Arc::new(transport);
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(false, transport.clone()));
    let before = f.fingerprint();
    assert_eq!(
        get(&service, "solution", "id", "fixture::A")
            .error
            .unwrap()
            .code,
        "ASSET_DOWNLOAD"
    );
    assert_eq!(f.fingerprint(), before);
    drop(service);
    let offline = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(true, transport.clone()));
    let mut r = ApiRequest::get("problem");
    r.query.insert("id".into(), vec!["fixture::A".into()]);
    r.query.insert("reviewId".into(), vec!["a".repeat(32)]);
    assert_eq!(offline.handle(r).error.unwrap().code, "ASSET_NOT_CACHED");
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn in_flight_transfer_does_not_hold_library_catalogue_or_personal_locks() {
    let f = Fixture::new();
    let mut transport = f.transport();
    let (entered_tx, entered_rx) = mpsc::channel();
    let (release_tx, release_rx) = mpsc::channel();
    let transport_mut = Arc::get_mut(&mut transport).unwrap();
    *transport_mut.entered.get_mut().unwrap() = Some(entered_tx);
    *transport_mut.release.get_mut().unwrap() = Some(release_rx);
    let service = Arc::new(
        Service::open(f.config.clone())
            .unwrap()
            .with_public_assets(f.cache(false, transport.clone())),
    );
    let cloned = Arc::clone(&service);
    let digest = sha(&f.image);
    let pending = std::thread::spawn(move || get(&cloned, "library/asset", "sha256", &digest));
    entered_rx.recv_timeout(Duration::from_secs(2)).unwrap();
    let cloned = Arc::clone(&service);
    let (read_tx, read_rx) = mpsc::channel();
    let reader = std::thread::spawn(move || {
        read_tx
            .send(cloned.handle(ApiRequest::get("preferences")))
            .unwrap();
    });
    let result = read_rx.recv_timeout(Duration::from_millis(800));
    release_tx.send(()).unwrap();
    assert!(pending.join().unwrap().ok);
    reader.join().unwrap();
    assert!(
        result
            .expect("A resource transfer must not block unrelated personal reads")
            .ok
    );
}

#[test]
fn owner_and_token_are_validated_before_any_public_transfer() {
    let f = Fixture::new();
    let transport = f.transport();
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(false, transport.clone()));
    let before = f.fingerprint();
    let mut r = ApiRequest::get("solution");
    r.owner = Some("another-owner".into());
    r.query.insert("id".into(), vec!["fixture::A".into()]);
    assert_eq!(service.handle(r).error.unwrap().status, 409);
    let mut r = ApiRequest::get("draft");
    r.method = Method::Post;
    r.body = Some(json!({"id":"fixture::A","code":"must not be saved"}));
    assert_eq!(service.handle(r).error.unwrap().status, 403);
    assert_eq!(transport.calls.load(Ordering::SeqCst), 0);
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn corrupt_cached_or_embedded_bytes_never_escape_the_asset_route() {
    let f = Fixture::new();
    let transport = f.transport();
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(false, transport.clone()));
    assert!(get(&service, "library/asset", "sha256", &sha(&f.image)).ok);
    let before = f.fingerprint();
    let cached = Connection::open(f.folder.path().join("cache/public-assets.sqlite3")).unwrap();
    cached
        .execute("UPDATE assets SET data=zeroblob(length(data))", [])
        .unwrap();
    assert_eq!(
        get(&service, "library/asset", "sha256", &sha(&f.image))
            .error
            .unwrap()
            .code,
        "ASSET_INTEGRITY"
    );
    assert_eq!(f.fingerprint(), before);
    let library = Library {
        db: Connection::open_in_memory().unwrap(),
    };
    library
        .db
        .execute_batch("CREATE TABLE statement_assets(sha256 TEXT PRIMARY KEY,mime TEXT,data BLOB)")
        .unwrap();
    library
        .db
        .execute(
            "INSERT INTO statement_assets VALUES(?,'image/png',?)",
            params![sha(&f.image), b"corrupt".as_slice()],
        )
        .unwrap();
    assert_eq!(
        library.asset(&sha(&f.image)).unwrap_err().code,
        "ASSET_INTEGRITY"
    );
}

#[test]
fn resource_discovery_ignores_code_text_and_includes_only_rendered_resource_fields() {
    let value = json!({"markdown":format!("tb-asset:{}","a".repeat(64)),"code":format!("tb-asset:{}","a".repeat(64)),"images":{"one":"tb-asset:one"},"methods":[{"images":{"two":"/api/library-assets/two"}}],"translation":{"statementPdf":{"data":"tb-asset:three"}}});
    assert_eq!(
        asset_references(&value).into_iter().collect::<Vec<_>>(),
        vec!["one", "three", "two"]
    );
}

#[test]
fn running_contest_scopes_are_checked_before_any_resource_transfer() {
    let f = Fixture::new();
    let transport = f.transport();
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(false, transport.clone()));
    let personal = Connection::open(&f.config.personal).unwrap();
    personal.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config) VALUES('running','进行中','running','2026-11-01T00:00:00Z','2099-01-01T00:00:00Z',60,'[{\"id\":\"fixture::A\"}]','{}')",[]).unwrap();
    let before = f.fingerprint();
    for (path, id) in [
        ("solution", "fixture::A"),
        ("problem", "alias::A"),
        ("lecture", "lecture::A"),
    ] {
        assert_eq!(get(&service, path, "id", id).error.unwrap().status, 403);
    }
    assert_eq!(transport.calls.load(Ordering::SeqCst), 0);
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn an_ordinary_overdue_alias_read_validates_assets_then_closes_at_the_original_deadline() {
    let f = Fixture::new();
    let transport = f.transport();
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_test_clock("2026-11-06T05:00:00Z".parse().unwrap())
        .with_public_assets(f.cache(false, transport.clone()));
    f.overdue(json!({"strategy":"replay","contest":"Div.3 999"}));
    let response = get(&service, "problem", "id", "alias::A");
    assert!(response.ok, "{:?}", response.error);
    let problem = response.data.unwrap();
    assert_eq!(problem["locked"], false);
    assert_eq!(problem["draft"], "原普通草稿 😀");
    assert_eq!(transport.calls.load(Ordering::SeqCst), 2);
    let personal = Connection::open(&f.config.personal).unwrap();
    let record: (String, String) = personal
        .query_row(
            "SELECT status,finished_at FROM contests WHERE id='expired'",
            [],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .unwrap();
    assert_eq!(
        record,
        ("finished".into(), "2026-11-06T04:00:00.000000Z".into())
    );
    let after = f.fingerprint();
    assert!(get(&service, "problem", "id", "alias::A").ok);
    assert_eq!(f.fingerprint(), after);
    assert_eq!(transport.calls.load(Ordering::SeqCst), 2);
}

#[test]
fn an_overdue_read_with_unavailable_assets_preserves_the_running_journal_and_normal_code() {
    let f = Fixture::new();
    let mut transport = f.transport();
    Arc::get_mut(&mut transport).unwrap().fail = true;
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_test_clock("2026-11-06T05:00:00Z".parse().unwrap())
        .with_public_assets(f.cache(false, transport.clone()));
    f.overdue(json!({"strategy":"replay","contest":"Div.3 999"}));
    let before = f.fingerprint();
    let response = get(&service, "problem", "id", "alias::A");
    assert!(!response.ok);
    assert_eq!(response.error.unwrap().status, 503);
    assert!(transport.calls.load(Ordering::SeqCst) > 0);
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn unsupported_or_malformed_overdue_records_fail_before_any_public_transfer_or_journal_change() {
    for kind in ["reward", "team", "projection", "private"] {
        let f = Fixture::new();
        let transport = f.transport();
        let service = Service::open(f.config.clone())
            .unwrap()
            .with_test_clock("2026-11-06T05:00:00Z".parse().unwrap())
            .with_public_assets(f.cache(false, transport.clone()));
        let config = match kind {
            "reward" => {
                json!({"strategy":"replay","contest":"Div.3 999","backgroundReward":{"owner":"retained-real-owner","version":1}})
            }
            "team" => json!({"strategy":"team"}),
            _ => json!({"strategy":"replay","contest":"Div.3 999"}),
        };
        f.overdue(config);
        let personal = Connection::open(&f.config.personal).unwrap();
        if kind == "projection" {
            personal
                .execute(
                    "UPDATE contests SET slots='[{\"id\":\"fixture::A\"}]' WHERE id='expired'",
                    [],
                )
                .unwrap();
        }
        if kind == "private" {
            personal.execute("INSERT INTO account_problem_facts VALUES('unported-private-alias','{}','2026-11-01T00:00:00Z')",[]).unwrap();
        }
        let before = f.fingerprint();
        let response = get(&service, "problem", "id", "alias::A");
        assert!(!response.ok, "{kind}");
        assert_eq!(
            response.error.unwrap().code,
            if kind == "projection" {
                "INVALID_STORED_DATA"
            } else {
                "MIGRATION_PENDING"
            },
            "{kind}"
        );
        assert_eq!(transport.calls.load(Ordering::SeqCst), 0, "{kind}");
        assert_eq!(f.fingerprint(), before, "{kind}");
    }
}

#[test]
fn a_post_hydration_read_failure_rolls_back_expiry_without_discarding_the_verified_public_cache() {
    let f = Fixture::new();
    let transport = f.transport();
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_test_clock("2026-11-06T05:00:00Z".parse().unwrap())
        .with_public_assets(f.cache(false, transport.clone()));
    f.overdue(json!({"strategy":"replay","contest":"Div.3 999"}));
    Connection::open(&f.config.library)
        .unwrap()
        .execute("DROP TABLE solutions", [])
        .unwrap();
    let before = f.fingerprint();
    let response = get(&service, "problem", "id", "alias::A");
    assert!(!response.ok);
    assert_eq!(transport.calls.load(Ordering::SeqCst), 2);
    assert_eq!(f.fingerprint(), before);
    assert!(
        f.cache(true, f.transport())
            .is_cached(
                &f.cache(true, f.transport())
                    .descriptor(
                        &Connection::open(&f.config.library).unwrap(),
                        &sha(&f.image)
                    )
                    .unwrap()
                    .unwrap()
            )
            .unwrap()
    );
}

#[test]
fn aggregate_resource_limits_fail_before_downloads_or_personal_writes() {
    let f = Fixture::new();
    let transport = f.transport();
    let db = Connection::open(&f.config.library).unwrap();
    let mut images = serde_json::Map::new();
    for index in 0..5 {
        let digest = sha(format!("original-{index}").as_bytes());
        db.execute(
            "INSERT INTO remote_statement_assets VALUES(?,'image/png',33554432,?)",
            params![digest, format!("{PUBLIC_ROOT}{digest}.bin")],
        )
        .unwrap();
        images.insert(index.to_string(), json!(format!("tb-asset:{digest}")));
    }
    db.execute(
        "UPDATE statements SET content=?",
        [json!({"markdown":"原图","images":images}).to_string()],
    )
    .unwrap();
    drop(db);
    let service = Service::open(f.config.clone())
        .unwrap()
        .with_public_assets(f.cache(false, transport.clone()));
    let before = f.fingerprint();
    assert_eq!(
        get(&service, "problem", "id", "fixture::A")
            .error
            .unwrap()
            .code,
        "ASSET_REQUEST_LIMIT"
    );
    assert_eq!(transport.calls.load(Ordering::SeqCst), 0);
    assert_eq!(f.fingerprint(), before);
}
