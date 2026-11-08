use crate::api::{ApiError, fields, now, required_text};
use rusqlite::{Connection, OpenFlags, OptionalExtension, params};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::path::Path;
use std::time::Duration;

// Keep the existing table names/columns. Unknown tables, columns and journal
// documents remain intact, including data from newer versions.
pub const SCHEMA: &str = include_str!("../schema/personal.sql");

pub struct PersonalStore {
    pub db: Connection,
}
/// Nested journal operations share one connection and roll back as a unit.
/// The guard also restores the savepoint while unwinding a failed operation.
pub(crate) fn atomic<T>(
    db: &Connection,
    operation: impl FnOnce(&Connection) -> Result<T, ApiError>,
) -> Result<T, ApiError> {
    struct Guard<'a> {
        db: &'a Connection,
        name: String,
        committed: bool,
    }
    impl Drop for Guard<'_> {
        fn drop(&mut self) {
            if !self.committed {
                let _ = self
                    .db
                    .execute_batch(&format!("ROLLBACK TO {}; RELEASE {}", self.name, self.name));
            }
        }
    }
    let name = format!("native_{}", uuid::Uuid::new_v4().simple());
    db.execute_batch(&format!("SAVEPOINT {name}"))?;
    let mut guard = Guard {
        db,
        name,
        committed: false,
    };
    let value = operation(db)?;
    db.execute_batch(&format!("RELEASE {}", guard.name))?;
    guard.committed = true;
    Ok(value)
}
impl PersonalStore {
    pub fn open(path: &Path) -> Result<Self, ApiError> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let mut db = Connection::open(path)?;
        db.busy_timeout(Duration::from_secs(5))?;
        db.execute_batch("PRAGMA foreign_keys=ON; PRAGMA synchronous=FULL;")?;
        // Only open already-current schemas or initialize new workspaces. Any
        // legacy schema upgrade goes through the backed-up migration workflow.
        let exists: bool = db.query_row(
            "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='drafts')",
            [],
            |r| r.get(0),
        )?;
        if exists {
            Self::check_schema(&db)?;
        } else {
            let tx = db.transaction()?;
            tx.execute_batch(SCHEMA)?;
            tx.commit()?;
        }
        Ok(Self { db })
    }
    pub fn check_schema(db: &Connection) -> Result<(), ApiError> {
        for (table, required) in [
            ("drafts", &["problem_id", "context", "code", "saved_at"][..]),
            ("training", &["id", "active_at", "active", "removed_at"][..]),
            ("account_preferences", &["key", "value", "updated_at"][..]),
            (
                "submissions",
                &["id", "problem_id", "case_results", "sample_run"][..],
            ),
            (
                "contests",
                &["id", "status", "slots", "config", "deleted_at"][..],
            ),
        ] {
            let mut statement = db.prepare(&format!("PRAGMA table_info({table})"))?;
            let columns = statement
                .query_map([], |r| r.get::<_, String>(1))?
                .collect::<Result<Vec<_>, _>>()?;
            if !required.iter().all(|c| columns.iter().any(|v| v == c)) {
                return Err(ApiError::new(
                    409,
                    "SCHEMA_MIGRATION_REQUIRED",
                    "此数据库需要先完成兼容迁移，原数据已保留",
                ));
            }
        }
        Ok(())
    }
    pub fn pref(&self, key: &str) -> Result<Option<String>, ApiError> {
        Ok(self
            .db
            .query_row(
                "SELECT value FROM account_preferences WHERE key=?",
                [key],
                |r| r.get(0),
            )
            .optional()?)
    }
    pub fn document(&self, key: &str) -> Result<Option<Value>, ApiError> {
        self.pref(key)?
            .map(|v| serde_json::from_str(&v).map_err(Into::into))
            .transpose()
    }
    pub fn documents(&self, prefix: &str) -> Result<Vec<Value>, ApiError> {
        let mut st = self.db.prepare_cached(
            "SELECT value FROM account_preferences WHERE substr(key,1,length(?1))=?1 ORDER BY key",
        )?;
        st.query_map([prefix], |r| r.get::<_, String>(0))?
            .map(|v| Ok(serde_json::from_str(&v?)?))
            .collect()
    }
    pub fn put_document(&self, key: &str, value: &Value) -> Result<(), ApiError> {
        Self::put(&self.db, key, &value.to_string(), &now())
    }
    pub fn put(db: &Connection, key: &str, value: &str, stamp: &str) -> Result<(), ApiError> {
        db.execute("INSERT INTO account_preferences(key,value,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at",params![key,value,stamp])?;
        Ok(())
    }
    pub fn preferences(&self) -> Result<Value, ApiError> {
        let row: Option<(String, String)> = self
            .db
            .query_row(
                "SELECT value,updated_at FROM account_preferences WHERE key='ui'",
                [],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .optional()?;
        match row {
            Some((value, stamp)) => {
                Ok(json!({"preferences":serde_json::from_str::<Value>(&value)?,"updatedAt":stamp}))
            }
            None => Ok(json!({"preferences":null,"updatedAt":null})),
        }
    }
    pub fn draft_key(id: &str, context: &str) -> String {
        format!(
            "draft-language:{:x}",
            Sha256::digest(format!("{id}\0{context}").as_bytes())
        )
    }
    pub fn draft(&self, id: &str, context: &str) -> Result<Value, ApiError> {
        let row: Option<(String, String)> = self
            .db
            .query_row(
                "SELECT code,saved_at FROM drafts WHERE problem_id=? AND context=?",
                params![id, context],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )
            .optional()?;
        let language = self
            .pref(&Self::draft_key(id, context))?
            .filter(|s| ["cpp17", "python3"].contains(&s.as_str()))
            .unwrap_or_else(|| "cpp17".into());
        Ok(match row {
            Some((code, stamp)) => {
                json!({"draft":code,"draftSavedAt":stamp,"draftLanguage":language})
            }
            None => json!({"draft":"","draftSavedAt":null,"draftLanguage":language}),
        })
    }
    pub fn assert_unlocked(&self, id: &str) -> Result<(), ApiError> {
        let slots: Option<String> = self
            .db
            .query_row(
                "SELECT slots FROM contests WHERE status='running'",
                [],
                |r| r.get(0),
            )
            .optional()?;
        if let Some(slots) = slots {
            let slots: Value = serde_json::from_str(&slots)?;
            if slots.as_array().is_some_and(|s| {
                s.iter().any(|v| {
                    v.as_str() == Some(id)
                        || v.get("id").and_then(Value::as_str) == Some(id)
                        || v.get("problemId").and_then(Value::as_str) == Some(id)
                })
            }) {
                return Err(ApiError::new(
                    403,
                    "CONTEST_LOCKED",
                    "比赛期间不能查看题解或历史代码",
                ));
            }
        }
        Ok(())
    }
    pub fn save_draft(&mut self, body: &Value) -> Result<Value, ApiError> {
        self.save_draft_at(body, &now())
    }
    pub fn save_draft_at(&mut self, body: &Value, stamp: &str) -> Result<Value, ApiError> {
        // Callers without a migrated Training context cannot choose a context.
        if body.get("reviewId").is_some_and(|v| !v.is_null())
            || body
                .get("contestId")
                .is_some_and(|v| !v.is_null() && v != "")
        {
            return Err(ApiError::pending());
        }
        self.save_draft_context_at(body, stamp, "")
    }
    pub(crate) fn save_draft_context_at(
        &mut self,
        body: &Value,
        stamp: &str,
        context: &str,
    ) -> Result<Value, ApiError> {
        fields(body, &["id", "code", "contestId", "language", "reviewId"])?;
        let id = required_text(body, "id", 512)?;
        let code = body
            .get("code")
            .and_then(Value::as_str)
            .filter(|s| s.len() <= 65536)
            .ok_or_else(|| ApiError::bad("代码必须是文本，且大小不超过 64 KB"))?;
        let language = body
            .get("language")
            .and_then(Value::as_str)
            .unwrap_or("cpp17");
        if !["cpp17", "python3"].contains(&language) {
            return Err(ApiError::bad("请选择 C++17 或 Python 3"));
        }
        let key = Self::draft_key(id, context);
        let previous = self.draft(id, context)?;
        if previous["draft"] == code
            && previous["draftLanguage"] == language
            && !previous["draftSavedAt"].is_null()
        {
            return Ok(json!({"savedAt":previous["draftSavedAt"]}));
        }
        let tx = self.db.transaction()?;
        if language != "cpp17"
            || tx
                .query_row(
                    "SELECT 1 FROM account_preferences WHERE key=?",
                    [&key],
                    |_| Ok(()),
                )
                .optional()?
                .is_some()
        {
            Self::put(&tx, &key, language, &stamp)?;
        }
        if context.is_empty() && !code.trim().is_empty() {
            tx.execute("INSERT INTO training(id,active_at) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET active=1,removed_at=NULL,active_at=MAX(training.active_at,excluded.active_at)",params![id,stamp])?;
        }
        tx.execute("INSERT INTO drafts(problem_id,context,code,saved_at) VALUES(?,?,?,?) ON CONFLICT(problem_id,context) DO UPDATE SET code=excluded.code,saved_at=excluded.saved_at",params![id,context,code,stamp])?;
        tx.commit()?;
        Ok(json!({"savedAt":stamp}))
    }
    pub fn export(&self) -> Result<Value, ApiError> {
        // Export only explicit personal tables. Credentials/remote sessions are
        // never included by iterating every SQLite table.
        let mut tables = serde_json::Map::new();
        for table in [
            "drafts",
            "training",
            "submissions",
            "contests",
            "goals",
            "daily_missions",
            "account_problem_facts",
        ] {
            tables.insert(
                table.into(),
                self.rows(&format!("SELECT * FROM {table}"), [])?,
            );
        }
        let mut st=self.db.prepare("SELECT key,value,updated_at FROM account_preferences WHERE key='ui' OR key LIKE 'learning-summary%' OR key LIKE 'initial-code:%' OR key LIKE 'custom-template:%'")?;
        let preferences=st.query_map([],|r| Ok(json!({"key":r.get::<_,String>(0)?,"value":r.get::<_,String>(1)?,"updated_at":r.get::<_,String>(2)?})))?.collect::<Result<Vec<_>,_>>()?;
        Ok(json!({"version":1,"exportedAt":now(),"tables":tables,"preferences":preferences}))
    }
    pub fn rows<P: rusqlite::Params>(&self, sql: &str, params: P) -> Result<Value, ApiError> {
        let mut st = self.db.prepare(sql)?;
        let names = st
            .column_names()
            .into_iter()
            .map(String::from)
            .collect::<Vec<_>>();
        let items = st
            .query_map(params, |r| {
                let mut item = serde_json::Map::new();
                for (i, name) in names.iter().enumerate() {
                    let value = match r.get_ref(i)? {
                        rusqlite::types::ValueRef::Null => Value::Null,
                        rusqlite::types::ValueRef::Integer(v) => json!(v),
                        rusqlite::types::ValueRef::Real(v) => json!(v),
                        rusqlite::types::ValueRef::Text(v) => {
                            Value::String(String::from_utf8_lossy(v).into_owned())
                        }
                        rusqlite::types::ValueRef::Blob(_) => Value::Null,
                    };
                    item.insert(name.clone(), value);
                }
                Ok(Value::Object(item))
            })?
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Value::Array(items))
    }
}

pub fn readonly(path: &Path) -> Result<Connection, ApiError> {
    let db = Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )?;
    db.busy_timeout(Duration::from_secs(5))?;
    db.execute_batch("PRAGMA query_only=ON; PRAGMA cache_size=-2048; PRAGMA mmap_size=33554432;")?;
    Ok(db)
}
