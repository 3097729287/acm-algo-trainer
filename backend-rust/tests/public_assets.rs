use rusqlite::{Connection, params};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    io::{Read, Write},
    net::TcpListener,
    sync::{
        Arc, Barrier, Mutex,
        atomic::{AtomicBool, AtomicUsize, Ordering},
    },
    thread,
    time::Duration,
};
use tobe_core::public_assets::{
    AssetCache, Descriptor, FetchError, Fetcher, MAX_ASSET_BYTES, PUBLIC_ROOT, TrustPolicy,
    descriptor,
};

fn policy() -> TrustPolicy {
    TrustPolicy::new("https://47.82.84.74").unwrap()
}
fn item(data: &[u8], primary: bool) -> Descriptor {
    let sha = format!("{:x}", Sha256::digest(data));
    Descriptor {
        sha256: sha.clone(),
        mime: "application/pdf".into(),
        bytes: data.len() as u64,
        url: if primary {
            format!("{PUBLIC_ROOT}{sha}.bin")
        } else {
            policy().fallback_url(&sha).unwrap()
        },
    }
}
struct Transport {
    bodies: BTreeMap<String, Vec<u8>>,
    fail_primary: bool,
    calls: Mutex<Vec<String>>,
    active: AtomicUsize,
    peak: AtomicUsize,
}
impl Transport {
    fn new(data: &[u8]) -> Self {
        Self::many(vec![data.to_vec()])
    }
    fn many(data: Vec<Vec<u8>>) -> Self {
        Self {
            bodies: data
                .into_iter()
                .map(|bytes| (format!("{:x}", Sha256::digest(&bytes)), bytes))
                .collect(),
            fail_primary: false,
            calls: Mutex::new(vec![]),
            active: AtomicUsize::new(0),
            peak: AtomicUsize::new(0),
        }
    }
}
impl Fetcher for Transport {
    fn fetch(
        &self,
        url: &str,
        _mime: &str,
        _bytes: u64,
        _timeout: Duration,
        out: &mut dyn Write,
    ) -> Result<(), FetchError> {
        self.calls.lock().unwrap().push(url.into());
        if self.fail_primary && url.starts_with(PUBLIC_ROOT) {
            return Err(FetchError::Unavailable);
        }
        let active = self.active.fetch_add(1, Ordering::SeqCst) + 1;
        self.peak.fetch_max(active, Ordering::SeqCst);
        thread::sleep(Duration::from_millis(15));
        let sha = url
            .rsplit('/')
            .next()
            .unwrap()
            .strip_suffix(".bin")
            .unwrap();
        let result = out
            .write_all(&self.bodies[sha])
            .map_err(|_| FetchError::Integrity);
        self.active.fetch_sub(1, Ordering::SeqCst);
        result
    }
}
fn no_temporary_files(dir: &std::path::Path) {
    assert!(!fs::read_dir(dir).unwrap().any(|entry| {
        entry
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with("tobe-public-asset-")
    }));
}

#[test]
fn descriptors_require_exact_pinned_identity_mime_size_and_trusted_location() {
    let valid = item(b"public", true);
    valid.validate(&policy()).unwrap();
    let domestic = Descriptor {
        url: policy()
            .fallback_url(&valid.sha256)
            .unwrap()
            .replace("47.82.84.74/", "47.82.84.74:443/"),
        ..valid.clone()
    };
    domestic
        .validate(&TrustPolicy::new(" HTTPS://47.82.84.74/ ").unwrap())
        .unwrap();
    let mut cases = vec![];
    for url in [
        format!("{}?token=secret", valid.url),
        format!("{}#fragment", valid.url),
        valid.url.replace(
            "a4de0d4b160e1d2270422b8c84995feffc4e3269",
            "0000000000000000000000000000000000000000",
        ),
        valid
            .url
            .replace("raw.githubusercontent.com", "attacker.invalid"),
        format!(
            "https://47.82.84.74/updates/library-assets/{}.bin/../{}.bin",
            valid.sha256, valid.sha256
        ),
        format!(
            "https://user:password@47.82.84.74/updates/library-assets/{}.bin",
            valid.sha256
        ),
        format!(
            "http://47.82.84.74/updates/library-assets/{}.bin",
            valid.sha256
        ),
    ] {
        cases.push(Descriptor {
            url,
            ..valid.clone()
        });
    }
    cases.push(Descriptor {
        bytes: 0,
        ..valid.clone()
    });
    cases.push(Descriptor {
        bytes: MAX_ASSET_BYTES + 1,
        ..valid.clone()
    });
    cases.push(Descriptor {
        mime: "text/html".into(),
        ..valid.clone()
    });
    cases.push(Descriptor {
        sha256: valid.sha256.to_uppercase(),
        ..valid.clone()
    });
    for value in cases {
        assert!(value.validate(&policy()).is_err(), "{value:?}");
    }
    for endpoint in [
        "http://example.com",
        "https://example.com:444",
        "https://example.com/path",
        "https://u:p@example.com",
        "https://example.com?key=x",
    ] {
        assert!(TrustPolicy::new(endpoint).is_err());
    }
    assert!(serde_json::from_value::<Descriptor>(serde_json::json!({"sha256":valid.sha256,"mime":valid.mime,"bytes":true,"url":valid.url})).is_err());
    let db = Connection::open_in_memory().unwrap();
    assert!(descriptor(&db, &valid.sha256, &policy()).unwrap().is_none());
    db.execute_batch("CREATE TABLE remote_statement_assets(sha256 TEXT PRIMARY KEY,mime TEXT,bytes INTEGER,url TEXT)").unwrap();
    db.execute(
        "INSERT INTO remote_statement_assets VALUES(?,?,?,?)",
        params![valid.sha256, valid.mime, valid.bytes as i64, valid.url],
    )
    .unwrap();
    assert_eq!(
        descriptor(&db, &valid.sha256, &policy()).unwrap(),
        Some(valid)
    );
}

#[test]
fn verified_download_is_shared_with_legacy_cache_and_offline_restart() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("public-assets.sqlite3");
    let bytes = b"%PDF-1.7\npublic original\n";
    let transport = Arc::new(Transport::new(bytes));
    let value = item(bytes, false);
    let cache = AssetCache::new(path.clone(), policy(), false).with_fetcher(transport.clone());
    cache.ensure(&value).unwrap();
    cache.ensure(&value).unwrap();
    assert_eq!(transport.calls.lock().unwrap().len(), 1);
    let offline = AssetCache::new(path.clone(), policy(), true);
    offline.ensure(&value).unwrap();
    let found = offline.read_cached(&value).unwrap().unwrap();
    assert_eq!(found.data, bytes);
    assert_eq!(found.mime, value.mime);
    let db = Connection::open(&path).unwrap();
    assert_eq!(
        db.query_row("SELECT count(*) FROM assets", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        1
    );
    assert_eq!(
        db.query_row("SELECT mime,data FROM assets", [], |r| Ok((
            r.get::<_, String>(0)?,
            r.get::<_, Vec<u8>>(1)?
        )))
        .unwrap(),
        (value.mime, bytes.to_vec())
    );
    no_temporary_files(dir.path());
}

#[test]
fn absent_offline_resource_does_not_create_a_cache_or_touch_a_seed() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("missing/cache.sqlite3");
    let cache = AssetCache::new(path.clone(), policy(), true);
    let error = cache.ensure(&item(b"not downloaded", false)).unwrap_err();
    assert_eq!(error.code, "ASSET_NOT_CACHED");
    assert!(!path.parent().unwrap().exists());
}

#[test]
fn primary_transport_failure_uses_only_the_pinned_domestic_fallback() {
    let dir = tempfile::tempdir().unwrap();
    let bytes = b"original figure";
    let mut transport = Transport::new(bytes);
    transport.fail_primary = true;
    let transport = Arc::new(transport);
    let value = item(bytes, true);
    let cache = AssetCache::new(dir.path().join("cache.sqlite3"), policy(), false)
        .with_fetcher(transport.clone());
    cache.ensure(&value).unwrap();
    assert_eq!(
        *transport.calls.lock().unwrap(),
        vec![
            value.url.clone(),
            policy().fallback_url(&value.sha256).unwrap()
        ]
    );
    assert_eq!(cache.read_cached(&value).unwrap().unwrap().data, bytes);
    no_temporary_files(dir.path());
}

struct BadBody {
    body: Vec<u8>,
    calls: AtomicUsize,
}
impl Fetcher for BadBody {
    fn fetch(
        &self,
        _: &str,
        _: &str,
        _: u64,
        _: Duration,
        out: &mut dyn Write,
    ) -> Result<(), FetchError> {
        self.calls.fetch_add(1, Ordering::SeqCst);
        out.write_all(&self.body).map_err(|_| FetchError::Integrity)
    }
}
#[test]
fn wrong_truncated_and_oversized_bytes_never_enter_cache_or_trigger_a_fallback() {
    let value = item(b"correct", true);
    for body in [
        b"corrupt".to_vec(),
        b"short".to_vec(),
        b"correct plus extra".to_vec(),
    ] {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("cache.sqlite3");
        let transport = Arc::new(BadBody {
            body,
            calls: AtomicUsize::new(0),
        });
        let cache = AssetCache::new(path.clone(), policy(), false).with_fetcher(transport.clone());
        assert_eq!(cache.ensure(&value).unwrap_err().code, "ASSET_INTEGRITY");
        assert_eq!(transport.calls.load(Ordering::SeqCst), 1);
        assert!(!path.exists());
        no_temporary_files(dir.path());
    }
}

#[test]
fn corrupted_cache_and_foreign_personal_database_remain_unchanged() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("cache.sqlite3");
    let bytes = b"original";
    let value = item(bytes, false);
    let cache = AssetCache::new(path.clone(), policy(), false)
        .with_fetcher(Arc::new(Transport::new(bytes)));
    cache.ensure(&value).unwrap();
    {
        let db = Connection::open(&path).unwrap();
        db.execute("UPDATE assets SET data=?", [b"tampered".as_slice()])
            .unwrap();
    }
    let before = fs::read(&path).unwrap();
    assert_eq!(cache.ensure(&value).unwrap_err().code, "ASSET_INTEGRITY");
    assert_eq!(fs::read(&path).unwrap(), before);
    let personal = dir.path().join("personal.sqlite3");
    {
        let db = Connection::open(&personal).unwrap();
        db.execute_batch("CREATE TABLE drafts(code TEXT);INSERT INTO drafts VALUES('keep original code');CREATE TABLE sqliteXnot_an_internal_table(value TEXT)").unwrap();
    }
    let before = fs::read(&personal).unwrap();
    let protected = AssetCache::new(personal.clone(), policy(), false);
    assert_eq!(
        protected.ensure(&value).unwrap_err().code,
        "ASSET_CACHE_SCOPE"
    );
    assert_eq!(fs::read(personal).unwrap(), before);
    no_temporary_files(dir.path());
}

#[test]
fn duplicate_requests_download_once_and_distinct_requests_use_at_most_four_transports() {
    let dir = tempfile::tempdir().unwrap();
    let bytes = b"single public asset";
    let value = item(bytes, false);
    let transport = Arc::new(Transport::new(bytes));
    let cache = AssetCache::new(dir.path().join("single.sqlite3"), policy(), false)
        .with_fetcher(transport.clone());
    let barrier = Arc::new(Barrier::new(12));
    let threads: Vec<_> = (0..12)
        .map(|_| {
            let cache = cache.clone();
            let value = value.clone();
            let barrier = barrier.clone();
            thread::spawn(move || {
                barrier.wait();
                cache.ensure(&value).unwrap()
            })
        })
        .collect();
    for thread in threads {
        thread.join().unwrap();
    }
    assert_eq!(transport.calls.lock().unwrap().len(), 1);
    let bodies: Vec<Vec<u8>> = (0..12)
        .map(|i| format!("different-public-body-{i}").into_bytes())
        .collect();
    let transport = Arc::new(Transport::many(bodies.clone()));
    let cache = AssetCache::new(dir.path().join("many.sqlite3"), policy(), false)
        .with_fetcher(transport.clone());
    let barrier = Arc::new(Barrier::new(12));
    let threads: Vec<_> = bodies
        .into_iter()
        .map(|bytes| {
            let cache = cache.clone();
            let barrier = barrier.clone();
            thread::spawn(move || {
                barrier.wait();
                cache.ensure(&item(&bytes, false)).unwrap()
            })
        })
        .collect();
    for thread in threads {
        thread.join().unwrap();
    }
    assert_eq!(transport.calls.lock().unwrap().len(), 12);
    assert!(transport.peak.load(Ordering::SeqCst) <= 4);
    no_temporary_files(dir.path());
}

#[test]
fn actual_http_transport_never_follows_redirects_or_sends_account_headers() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let root = format!("http://{}", listener.local_addr().unwrap());
    listener.set_nonblocking(true).unwrap();
    let stop = Arc::new(AtomicBool::new(false));
    let requests = Arc::new(Mutex::new(Vec::new()));
    let (shutdown, seen, target) = (stop.clone(), requests.clone(), root.clone());
    let server = thread::spawn(move || {
        while !shutdown.load(Ordering::SeqCst) {
            match listener.accept() {
                Ok((mut socket, _)) => {
                    socket
                        .set_read_timeout(Some(Duration::from_secs(2)))
                        .unwrap();
                    let mut buffer = [0u8; 8192];
                    let n = socket.read(&mut buffer).unwrap();
                    seen.lock()
                        .unwrap()
                        .push(String::from_utf8_lossy(&buffer[..n]).into_owned());
                    let response = format!(
                        "HTTP/1.1 302 Found\r\nLocation: {target}/do-not-follow\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                    );
                    socket.write_all(response.as_bytes()).unwrap();
                }
                Err(error) if error.kind() == std::io::ErrorKind::WouldBlock => {
                    thread::sleep(Duration::from_millis(10))
                }
                Err(error) => panic!("{error}"),
            }
        }
    });
    let policy = TrustPolicy::new(&root).unwrap();
    let mut value = item(b"expected", false);
    value.url = policy.fallback_url(&value.sha256).unwrap();
    let dir = tempfile::tempdir().unwrap();
    let cache = AssetCache::new(dir.path().join("cache.sqlite3"), policy, false);
    let result = cache.ensure(&value);
    stop.store(true, Ordering::SeqCst);
    server.join().unwrap();
    assert_eq!(result.unwrap_err().code, "ASSET_DOWNLOAD");
    let requests = requests.lock().unwrap();
    assert_eq!(requests.len(), 1);
    let headers = requests[0].to_ascii_lowercase();
    assert!(headers.contains("accept-encoding: identity"));
    assert!(!headers.contains("authorization:"));
    assert!(!headers.contains("cookie:"));
    assert!(!headers.contains("do-not-follow"));
    no_temporary_files(dir.path());
}

#[test]
#[ignore = "Explicit live public HTTPS smoke; no accounts or credentials"]
fn actual_public_https_download_then_offline_cache_read() {
    let metadata = fs::read(
        std::env::var_os("TB_PUBLIC_ASSET_SMOKE_DESCRIPTOR").expect("public descriptor path"),
    )
    .unwrap();
    let value: Descriptor = serde_json::from_slice(&metadata).unwrap();
    value.validate(&policy()).unwrap();
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("cache.sqlite3");
    AssetCache::new(path.clone(), policy(), false)
        .ensure(&value)
        .unwrap();
    let result = AssetCache::new(path, policy(), true)
        .read_cached(&value)
        .unwrap()
        .unwrap();
    assert_eq!(result.data.len() as u64, value.bytes);
    assert_eq!(format!("{:x}", Sha256::digest(&result.data)), value.sha256);
    no_temporary_files(dir.path());
}
