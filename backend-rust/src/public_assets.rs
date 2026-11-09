//! Public resources only. Call `ensure` outside personal/catalogue/library locks.
//! The public seed remains read-only; bytes enter a separate verified cache.
use crate::api::ApiError;
use rusqlite::{Connection, OpenFlags, OptionalExtension, params};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{
    fs::{self, File, OpenOptions},
    io::{self, Read, Seek, SeekFrom, Write},
    path::{Path, PathBuf},
    sync::{Arc, Condvar, LazyLock, Mutex},
    time::{Duration, Instant},
};

pub const MAX_ASSET_BYTES: u64 = 32 * 1024 * 1024;
pub const PUBLIC_ROOT: &str = "https://raw.githubusercontent.com/3097729287/acm-algo-trainer/a4de0d4b160e1d2270422b8c84995feffc4e3269/";
const RESERVE_BYTES: u64 = 256 * 1024 * 1024;
const MAX_DOWNLOADS: usize = 4;
static HASH_LOCKS: LazyLock<[Mutex<()>; 32]> =
    LazyLock::new(|| std::array::from_fn(|_| Mutex::new(())));
static DOWNLOADS: (Mutex<usize>, Condvar) = (Mutex::new(0), Condvar::new());

fn integrity() -> ApiError {
    ApiError::new(422, "ASSET_INTEGRITY", "公共资源校验失败，原文件已保留")
}
fn busy() -> ApiError {
    ApiError::new(503, "ASSET_BUSY", "公共资源正在缓存，请稍后重试")
}
fn unavailable() -> ApiError {
    ApiError::new(503, "ASSET_DOWNLOAD", "公共资源下载失败，请稍后重试")
}
fn valid_sha(sha: &str) -> bool {
    sha.len() == 64
        && sha
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}

#[derive(Clone, Debug)]
pub struct TrustPolicy {
    service_root: String,
}
impl TrustPolicy {
    /// `endpoint` comes from protected application configuration, never a request.
    pub fn new(endpoint: &str) -> Result<Self, ApiError> {
        let root = endpoint.trim().trim_end_matches('/');
        let parsed = url::Url::parse(root).map_err(|_| ApiError::bad("公共资源服务地址无效"))?;
        let loopback = matches!(
            parsed.host_str(),
            Some("127.0.0.1" | "localhost" | "[::1]" | "::1")
        );
        if root.len() > 2048
            || parsed.host_str().is_none()
            || !parsed.username().is_empty()
            || parsed.password().is_some()
            || parsed.query().is_some()
            || parsed.fragment().is_some()
            || !matches!(parsed.path(), "" | "/")
            || !(parsed.scheme() == "https" || loopback && parsed.scheme() == "http")
            || !loopback && parsed.port().is_some_and(|port| port != 443)
        {
            return Err(ApiError::bad("公共资源服务地址无效"));
        }
        Ok(Self {
            service_root: parsed.origin().ascii_serialization(),
        })
    }
    pub fn fallback_url(&self, sha: &str) -> Result<String, ApiError> {
        if !valid_sha(sha) {
            return Err(ApiError::bad("公共资源摘要无效"));
        }
        Ok(format!(
            "{}/updates/library-assets/{sha}.bin",
            self.service_root
        ))
    }
    fn accepts(&self, target: &str, sha: &str) -> bool {
        if target == format!("{PUBLIC_ROOT}{sha}.bin") {
            return true;
        }
        let Ok(parsed) = url::Url::parse(target) else {
            return false;
        };
        // Compare the raw suffix too: URL normalization must not turn a dot
        // segment or encoded alternate path into an approved resource.
        let raw_path = target
            .split_once("://")
            .and_then(|(_, rest)| rest.find('/').map(|at| &rest[at..]));
        parsed.username().is_empty()
            && parsed.password().is_none()
            && parsed.query().is_none()
            && parsed.fragment().is_none()
            && parsed.origin().ascii_serialization() == self.service_root
            && raw_path == Some(format!("/updates/library-assets/{sha}.bin").as_str())
    }
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
pub struct Descriptor {
    pub sha256: String,
    pub mime: String,
    pub bytes: u64,
    pub url: String,
}
impl Descriptor {
    pub fn validate(&self, policy: &TrustPolicy) -> Result<(), ApiError> {
        if !valid_sha(&self.sha256)
            || self.bytes == 0
            || self.bytes > MAX_ASSET_BYTES
            || !matches!(
                self.mime.as_str(),
                "application/pdf"
                    | "image/png"
                    | "image/jpeg"
                    | "image/webp"
                    | "image/gif"
                    | "image/bmp"
                    | "application/zip"
            )
            || !policy.accepts(&self.url, &self.sha256)
        {
            return Err(ApiError::new(422, "ASSET_DESCRIPTOR", "公共资源描述无效"));
        }
        Ok(())
    }
}

pub fn descriptor(
    db: &Connection,
    sha: &str,
    policy: &TrustPolicy,
) -> Result<Option<Descriptor>, ApiError> {
    if !valid_sha(sha) {
        return Err(ApiError::bad("公共资源摘要无效"));
    }
    let exists: bool = db.query_row("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='remote_statement_assets')", [], |r| r.get(0))?;
    if !exists {
        return Ok(None);
    }
    let row: Option<(String, i64, String)> = db
        .query_row(
            "SELECT mime,bytes,url FROM remote_statement_assets WHERE sha256=?",
            [sha],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )
        .optional()?;
    let item = row
        .map(|(mime, bytes, url)| {
            Ok::<_, ApiError>(Descriptor {
                sha256: sha.into(),
                mime,
                bytes: bytes.try_into().map_err(|_| integrity())?,
                url,
            })
        })
        .transpose()?;
    if let Some(item) = &item {
        item.validate(policy)?;
    }
    Ok(item)
}

#[derive(Debug)]
pub struct AssetBytes {
    pub mime: String,
    pub data: Vec<u8>,
}
#[derive(Debug)]
pub enum FetchError {
    Unavailable,
    Integrity,
}
/// A transport never receives account tokens, cookies or personal database paths.
pub trait Fetcher: Send + Sync {
    fn fetch(
        &self,
        url: &str,
        mime: &str,
        bytes: u64,
        timeout: Duration,
        writer: &mut dyn Write,
    ) -> Result<(), FetchError>;
}
pub struct HttpFetcher;
impl Fetcher for HttpFetcher {
    fn fetch(
        &self,
        url: &str,
        mime: &str,
        bytes: u64,
        timeout: Duration,
        writer: &mut dyn Write,
    ) -> Result<(), FetchError> {
        let parsed = url::Url::parse(url).map_err(|_| FetchError::Integrity)?;
        let loopback = matches!(
            parsed.host_str(),
            Some("127.0.0.1" | "localhost" | "[::1]" | "::1")
        );
        let bundled = parsed.host_str() == Some("47.82.84.74");
        let deadline = Instant::now() + timeout;
        let request = |direct: bool, budget: Duration| {
            let mut builder = reqwest::blocking::Client::builder()
                .redirect(reqwest::redirect::Policy::none())
                .connect_timeout(Duration::from_secs(8).min(budget))
                .timeout(budget)
                .user_agent("ToBe-Public-Assets/1");
            if direct {
                builder = builder.no_proxy();
            }
            builder
                .build()
                .map_err(|_| FetchError::Unavailable)?
                .get(url)
                .header("Accept", mime)
                .header("Accept-Encoding", "identity")
                .send()
                .map_err(|_| FetchError::Unavailable)
        };
        let response = match request(loopback || bundled, timeout) {
            Ok(response) => response,
            Err(_) if bundled && Instant::now() < deadline => {
                // Only a connection/header failure retries the user's system
                // route. No response bytes have entered the writer yet.
                request(false, deadline.saturating_duration_since(Instant::now()))?
            }
            Err(error) => return Err(error),
        };
        if response.status() != reqwest::StatusCode::OK {
            return Err(FetchError::Unavailable);
        }
        if response
            .content_length()
            .is_some_and(|length| length != bytes)
        {
            return Err(FetchError::Integrity);
        }
        io::copy(&mut response.take(bytes + 1), writer).map_err(|e| {
            if e.kind() == io::ErrorKind::InvalidData {
                FetchError::Integrity
            } else {
                FetchError::Unavailable
            }
        })?;
        Ok(())
    }
}

#[derive(Clone)]
pub struct AssetCache {
    path: PathBuf,
    policy: TrustPolicy,
    offline: bool,
    fetcher: Arc<dyn Fetcher>,
}
impl AssetCache {
    pub fn new(path: PathBuf, policy: TrustPolicy, offline: bool) -> Self {
        Self {
            path,
            policy,
            offline,
            fetcher: Arc::new(HttpFetcher),
        }
    }
    pub fn with_fetcher(mut self, fetcher: Arc<dyn Fetcher>) -> Self {
        self.fetcher = fetcher;
        self
    }
    pub fn descriptor(&self, db: &Connection, sha: &str) -> Result<Option<Descriptor>, ApiError> {
        descriptor(db, sha, &self.policy)
    }
    pub fn is_cached(&self, item: &Descriptor) -> Result<bool, ApiError> {
        item.validate(&self.policy)?;
        if !self.path.exists() {
            return Ok(false);
        }
        let db = self.open(false)?;
        verify(&db, item)
    }
    pub fn read_cached(&self, item: &Descriptor) -> Result<Option<AssetBytes>, ApiError> {
        item.validate(&self.policy)?;
        if !self.path.exists() {
            return Ok(None);
        }
        let db = self.open(false)?;
        db.execute_batch("BEGIN")?;
        if !verify(&db, item)? {
            return Ok(None);
        }
        let data: Vec<u8> = db.query_row(
            "SELECT data FROM assets WHERE sha256=?",
            [&item.sha256],
            |r| r.get(0),
        )?;
        // The read transaction keeps validation and returned bytes in one snapshot.
        Ok(Some(AssetBytes {
            mime: item.mime.clone(),
            data,
        }))
    }
    pub fn ensure(&self, item: &Descriptor) -> Result<(), ApiError> {
        item.validate(&self.policy)?;
        if self.is_cached(item)? {
            return Ok(());
        }
        if self.offline {
            return Err(ApiError::new(
                503,
                "ASSET_NOT_CACHED",
                "此资源尚未下载，离线时暂不可读",
            ));
        }
        let bucket =
            u8::from_str_radix(&item.sha256[..2], 16).map_err(|_| integrity())? as usize % 32;
        let _single = HASH_LOCKS[bucket].lock().map_err(|_| busy())?;
        if self.is_cached(item)? {
            return Ok(());
        }
        let parent = self
            .path
            .parent()
            .ok_or_else(|| ApiError::bad("公共资源缓存路径无效"))?;
        plain_path(&self.path)?;
        fs::create_dir_all(parent)?;
        plain_path(&self.path)?;
        let lock_path = parent.join(format!("public-assets-{bucket:02}.lock"));
        plain_path(&lock_path)?;
        let lock = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(lock_path)?;
        let _cross_process = FileLock::acquire(lock)?;
        if self.is_cached(item)? {
            return Ok(());
        }
        let _slot = DownloadSlot::acquire()?;
        if fs2::available_space(parent)? < item.bytes * 3 + RESERVE_BYTES {
            return Err(ApiError::new(
                507,
                "ASSET_SPACE",
                "磁盘空间不足，公共资源未继续下载",
            ));
        }
        // No partial bytes are ever inserted into SQLite. This owned file is
        // removed on all exits, including transport, checksum and SQLite errors.
        let mut temporary = tempfile::Builder::new()
            .prefix("tobe-public-asset-")
            .tempfile_in(parent)?;
        let first = self.download(
            item,
            &item.url,
            Duration::from_secs(20),
            temporary.as_file_mut(),
        );
        match first {
            Ok(()) => (),
            Err(FetchError::Unavailable) if item.url.starts_with(PUBLIC_ROOT) => {
                temporary.as_file_mut().set_len(0)?;
                temporary.as_file_mut().seek(SeekFrom::Start(0))?;
                self.download(
                    item,
                    &self.policy.fallback_url(&item.sha256)?,
                    Duration::from_secs(45),
                    temporary.as_file_mut(),
                )
                .map_err(fetch_error)?;
            }
            Err(error) => return Err(fetch_error(error)),
        }
        temporary.as_file_mut().sync_all()?;
        temporary.as_file_mut().seek(SeekFrom::Start(0))?;
        let mut db = self.open(true)?;
        let tx = db.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
        if !verify(&tx, item)? {
            tx.execute(
                "INSERT INTO assets(sha256,mime,data) VALUES(?,?,zeroblob(?))",
                params![item.sha256, item.mime, item.bytes as i64],
            )?;
            let rowid = tx.last_insert_rowid();
            {
                let mut blob = tx.blob_open("main", "assets", "data", rowid, false)?;
                if io::copy(temporary.as_file_mut(), &mut blob)? != item.bytes {
                    return Err(integrity());
                }
            }
            if !verify(&tx, item)? {
                return Err(integrity());
            }
        }
        tx.commit()?;
        Ok(())
    }
    fn download(
        &self,
        item: &Descriptor,
        url: &str,
        timeout: Duration,
        file: &mut File,
    ) -> Result<(), FetchError> {
        let mut writer = CheckedWriter {
            writer: file,
            expected: item.bytes,
            written: 0,
            hash: Sha256::new(),
        };
        self.fetcher
            .fetch(url, &item.mime, item.bytes, timeout, &mut writer)?;
        if writer.written != item.bytes || format!("{:x}", writer.hash.finalize()) != item.sha256 {
            return Err(FetchError::Integrity);
        }
        Ok(())
    }
    fn open(&self, writable: bool) -> Result<Connection, ApiError> {
        plain_path(&self.path)?;
        for suffix in ["-wal", "-shm", "-journal"] {
            let mut side = self.path.as_os_str().to_os_string();
            side.push(suffix);
            plain_path(&PathBuf::from(side))?;
        }
        let flags = if writable {
            OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE
        } else {
            OpenFlags::SQLITE_OPEN_READ_ONLY
        };
        let db = Connection::open_with_flags(&self.path, flags)?;
        db.busy_timeout(Duration::from_secs(30))?;
        let objects: Vec<(String, String)> = db
            .prepare("SELECT name,type FROM sqlite_master WHERE name NOT GLOB 'sqlite_*'")?
            .query_map([], |r| Ok((r.get(0)?, r.get(1)?)))?
            .collect::<Result<_, _>>()?;
        if objects
            .iter()
            .any(|(name, kind)| name != "assets" || kind != "table")
        {
            return Err(ApiError::new(
                409,
                "ASSET_CACHE_SCOPE",
                "该数据库不属于公共资源缓存，原文件保留",
            ));
        }
        if objects.is_empty() {
            if writable {
                db.execute_batch("CREATE TABLE IF NOT EXISTS assets(sha256 TEXT PRIMARY KEY,mime TEXT NOT NULL,data BLOB NOT NULL)")?;
            }
        } else {
            let columns: Vec<String> = db
                .prepare("PRAGMA table_info(assets)")?
                .query_map([], |r| r.get(1))?
                .collect::<Result<_, _>>()?;
            if columns != ["sha256", "mime", "data"] {
                return Err(integrity());
            }
        }
        Ok(db)
    }
}

fn fetch_error(error: FetchError) -> ApiError {
    match error {
        FetchError::Unavailable => unavailable(),
        FetchError::Integrity => integrity(),
    }
}
fn plain_path(path: &Path) -> Result<(), ApiError> {
    for item in path.ancestors() {
        match path_metadata(item) {
            Ok(metadata) => {
                #[cfg(windows)]
                let redirected = {
                    use std::os::windows::fs::MetadataExt;
                    metadata.file_attributes() & 0x400 != 0
                };
                #[cfg(not(windows))]
                let redirected = false;
                if metadata.file_type().is_symlink() || redirected {
                    return Err(ApiError::new(
                        409,
                        "ASSET_CACHE_PATH",
                        "公共资源缓存路径包含重定向",
                    ));
                }
            }
            Err(error) if error.kind() == io::ErrorKind::NotFound => (),
            Err(error) => return Err(error.into()),
        }
    }
    Ok(())
}
fn path_metadata(path: &Path) -> io::Result<fs::Metadata> {
    #[cfg(windows)]
    let began = Instant::now();
    loop {
        match fs::symlink_metadata(path) {
            // Concurrent SQLite journal creation/removal can briefly make a
            // Windows metadata open return AccessDenied/SharingViolation.
            // Retry the proof itself; never treat denied access as absence or
            // skip the reparse-point check. Persistent denial still fails.
            #[cfg(windows)]
            Err(error)
                if matches!(error.raw_os_error(), Some(5 | 32 | 33))
                    && began.elapsed() < Duration::from_millis(50) =>
            {
                std::thread::sleep(Duration::from_millis(2));
            }
            result => return result,
        }
    }
}
fn verify(db: &Connection, item: &Descriptor) -> Result<bool, ApiError> {
    let table: bool = db.query_row(
        "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='assets')",
        [],
        |r| r.get(0),
    )?;
    if !table {
        return Ok(false);
    }
    let row: Option<(i64, String, i64)> = db
        .query_row(
            "SELECT rowid,mime,length(data) FROM assets WHERE sha256=?",
            [&item.sha256],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )
        .optional()?;
    let Some((rowid, mime, bytes)) = row else {
        return Ok(false);
    };
    if mime != item.mime || bytes < 0 || bytes as u64 != item.bytes {
        return Err(integrity());
    }
    let mut blob = db.blob_open("main", "assets", "data", rowid, true)?;
    let mut hash = Sha256::new();
    let mut buffer = [0u8; 65536];
    let mut count = 0u64;
    loop {
        let size = blob.read(&mut buffer)?;
        if size == 0 {
            break;
        }
        count += size as u64;
        hash.update(&buffer[..size]);
    }
    if count != item.bytes || format!("{:x}", hash.finalize()) != item.sha256 {
        return Err(integrity());
    }
    Ok(true)
}
struct CheckedWriter<'a> {
    writer: &'a mut File,
    expected: u64,
    written: u64,
    hash: Sha256,
}
impl Write for CheckedWriter<'_> {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        if bytes.len() as u64 > self.expected.saturating_sub(self.written) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "public asset exceeded pinned size",
            ));
        }
        let size = self.writer.write(bytes)?;
        self.hash.update(&bytes[..size]);
        self.written += size as u64;
        Ok(size)
    }
    fn flush(&mut self) -> io::Result<()> {
        self.writer.flush()
    }
}
struct FileLock(File);
impl FileLock {
    fn acquire(file: File) -> Result<Self, ApiError> {
        let deadline = Instant::now() + Duration::from_secs(70);
        loop {
            match fs2::FileExt::try_lock_exclusive(&file) {
                Ok(()) => return Ok(Self(file)),
                Err(error)
                    if (error.kind() == io::ErrorKind::WouldBlock
                        || error.raw_os_error() == fs2::lock_contended_error().raw_os_error())
                        && Instant::now() < deadline =>
                {
                    std::thread::sleep(Duration::from_millis(20))
                }
                Err(_) => return Err(busy()),
            }
        }
    }
}
impl Drop for FileLock {
    fn drop(&mut self) {
        let _ = fs2::FileExt::unlock(&self.0);
    }
}
struct DownloadSlot;
impl DownloadSlot {
    fn acquire() -> Result<Self, ApiError> {
        let count = DOWNLOADS.0.lock().map_err(|_| busy())?;
        let (mut count, waited) = DOWNLOADS
            .1
            .wait_timeout_while(count, Duration::from_secs(70), |count| {
                *count >= MAX_DOWNLOADS
            })
            .map_err(|_| busy())?;
        if waited.timed_out() && *count >= MAX_DOWNLOADS {
            return Err(busy());
        }
        *count += 1;
        Ok(Self)
    }
}
impl Drop for DownloadSlot {
    fn drop(&mut self) {
        if let Ok(mut count) = DOWNLOADS.0.lock() {
            *count -= 1;
            DOWNLOADS.1.notify_one();
        }
    }
}
