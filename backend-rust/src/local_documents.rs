//! The existing transactional document format. Account metadata and protected
//! sessions share this store without rewriting unrelated documents or history.
use crate::ApiError;
use rusqlite::{Connection, OpenFlags, OptionalExtension, TransactionBehavior};
use serde_json::Value;
use std::{
    path::{Path, PathBuf},
    time::Duration,
};

pub const MAX_DOCUMENT_BYTES: usize = 40 * 1024 * 1024;
pub struct Documents {
    root: PathBuf,
}
impl Documents {
    pub fn new(root: &Path) -> Self {
        Self {
            root: root.to_owned(),
        }
    }
    fn name(name: &str) -> Result<(), ApiError> {
        if name.is_empty()
            || name.len() > 128
            || name.contains("..")
            || !name
                .bytes()
                .all(|c| c.is_ascii_alphanumeric() || matches!(c, b'.' | b'-' | b'_'))
        {
            return Err(ApiError::bad("本机文档名称无效"));
        }
        Ok(())
    }
    fn database(&self) -> PathBuf {
        self.root.join("tb-documents.sqlite3")
    }
    fn validate(db: &Connection) -> Result<bool, ApiError> {
        let found: bool = db.query_row(
            "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='documents')",
            [],
            |row| row.get(0),
        )?;
        if found {
            db.prepare("SELECT key,value FROM documents LIMIT 0")?;
        } else {
            let other: bool = db.query_row(
                "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%')",
                [],
                |row| row.get(0),
            )?;
            if other {
                return Err(ApiError::new(
                    409,
                    "DOCUMENT_STORE_COLLISION",
                    "本机文档路径已被其它数据库占用，原文件已保留",
                ));
            }
        }
        Ok(found)
    }
    pub fn load(&self, name: &str, default: Value) -> Result<Value, ApiError> {
        Self::name(name)?;
        let path = self.database();
        if path.is_file() {
            let db = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
            db.busy_timeout(Duration::from_secs(5))?;
            if Self::validate(&db)? {
                let value: Option<String> = db
                    .query_row("SELECT value FROM documents WHERE key=?", [name], |row| {
                        row.get(0)
                    })
                    .optional()?;
                if let Some(value) = value {
                    if value.len() > MAX_DOCUMENT_BYTES {
                        return Err(ApiError::new(
                            503,
                            "DOCUMENT_TOO_LARGE",
                            "本机文档超过读取限制，原记录已保留",
                        ));
                    }
                    return serde_json::from_str(&value).map_err(|_| {
                        ApiError::new(
                            503,
                            "INVALID_LOCAL_DOCUMENT",
                            "本机文档校验失败，原记录已保留",
                        )
                    });
                }
            }
        }
        let legacy = self.root.join(name);
        let value = match std::fs::metadata(&legacy) {
            Ok(info) if info.is_file() && info.len() <= MAX_DOCUMENT_BYTES as u64 => {
                let raw = std::fs::read(&legacy)?;
                let raw = raw.strip_prefix(&[0xef, 0xbb, 0xbf]).unwrap_or(&raw);
                serde_json::from_slice(raw).unwrap_or(default)
            }
            Ok(_) => default,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => default,
            Err(error) => return Err(error.into()),
        };
        // Import one legacy/default key through the same transaction as a new
        // write. The original JSON file remains available for history/recovery.
        self.save(name, &value)?;
        Ok(value)
    }
    pub fn save(&self, name: &str, value: &Value) -> Result<(), ApiError> {
        Self::name(name)?;
        let encoded = serde_json::to_string(value)?;
        if encoded.len() > MAX_DOCUMENT_BYTES {
            return Err(ApiError::new(
                400,
                "DOCUMENT_TOO_LARGE",
                "本机文档超过保存限制，原记录已保留",
            ));
        }
        std::fs::create_dir_all(&self.root)?;
        let mut db = Connection::open(self.database())?;
        db.busy_timeout(Duration::from_secs(5))?;
        db.execute_batch("PRAGMA synchronous=FULL")?;
        Self::validate(&db)?;
        let tx = db.transaction_with_behavior(TransactionBehavior::Immediate)?;
        tx.execute_batch(
            "CREATE TABLE IF NOT EXISTS documents(key TEXT PRIMARY KEY,value TEXT NOT NULL)",
        )?;
        tx.execute("INSERT INTO documents(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",rusqlite::params![name,encoded])?;
        tx.commit()?;
        Ok(())
    }
}
