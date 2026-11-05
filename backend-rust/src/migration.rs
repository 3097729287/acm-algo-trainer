//! Explicit, copy-only migration. SQLite backup includes committed WAL frames.
use crate::{
    api::{ApiError, now},
    storage::{PersonalStore, readonly},
};
use rusqlite::{Connection, backup::Backup};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{fs::OpenOptions, io::Write, path::Path, time::Duration};

pub fn import_personal(source: &Path, destination: &Path) -> Result<Value, ApiError> {
    if !source.is_file() {
        return Err(ApiError::missing("没有找到待迁移数据库"));
    }
    if destination.exists() {
        return Err(ApiError::conflict("迁移目标已存在，不能覆盖个人数据"));
    }
    if let Some(parent) = destination.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let original = readonly(source)?;
    // Validate before reserving the destination. Never silently upgrade or
    // rewrite the original and never apply a public seed to personal tables.
    PersonalStore::check_schema(&original)?;
    let integrity: String = original.query_row("PRAGMA quick_check", [], |r| r.get(0))?;
    if integrity != "ok" {
        return Err(ApiError::new(
            422,
            "SOURCE_INTEGRITY",
            "原数据库完整性检查未通过，已保留原文件",
        ));
    }
    let staging = destination.with_extension(format!("{}.pending", uuid::Uuid::new_v4().simple()));
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&staging)?;
    let mut copy = Connection::open(&staging)?;
    {
        let backup = Backup::new(&original, &mut copy)?;
        backup.run_to_completion(256, Duration::from_millis(5), None)?;
    }
    let integrity: String = copy.query_row("PRAGMA integrity_check", [], |r| r.get(0))?;
    if integrity != "ok" {
        return Err(ApiError::new(
            422,
            "COPY_INTEGRITY",
            "迁移副本校验失败，已保留原文件及待检查副本",
        ));
    }
    // Fingerprint every logical table, including future/unknown records.
    // Hash the snapshot rather than the source again: the original may be
    // running and commit new rows while an online backup is being made.
    let fingerprint = logical_fingerprint(&copy)?;
    drop(copy);
    // Hard-link promotion is atomic and fails if another migration won the
    // destination race. It never replaces an existing database.
    std::fs::hard_link(&staging, destination)?;
    let receipt = json!({"protocol":1,"createdAt":now(),"method":"sqlite-online-backup","source":source,"destination":destination,
        "snapshotSha256":fingerprint,"integrity":"ok","sourceModified":false,"staging":staging});
    let receipt_path = destination.with_extension("migration.json");
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(receipt_path)?;
    file.write_all(serde_json::to_string_pretty(&receipt)?.as_bytes())?;
    file.sync_all()?;
    Ok(receipt)
}

pub fn logical_fingerprint(db: &Connection) -> Result<String, ApiError> {
    let mut digest = Sha256::new();
    let tables=db.prepare("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")?
        .query_map([],|r|Ok((r.get::<_,String>(0)?,r.get::<_,String>(1)?)))?.collect::<Result<Vec<_>,_>>()?;
    for (name, schema) in tables {
        digest.update(name.as_bytes());
        digest.update([0]);
        digest.update(schema.as_bytes());
        digest.update([0]);
        let escaped = name.replace('"', "\"\"");
        let mut st = db.prepare(&format!("SELECT * FROM \"{escaped}\""))?;
        let count = st.column_count();
        let mut rows = st.query([])?;
        // Sorting per-row digests bounds memory even for large code/BLOB tables.
        let mut hashes = Vec::new();
        while let Some(row) = rows.next()? {
            let mut hash = Sha256::new();
            for i in 0..count {
                match row.get_ref(i)? {
                    rusqlite::types::ValueRef::Null => hash.update([0]),
                    rusqlite::types::ValueRef::Integer(v) => {
                        hash.update([1]);
                        hash.update(v.to_le_bytes());
                    }
                    rusqlite::types::ValueRef::Real(v) => {
                        hash.update([2]);
                        hash.update(v.to_bits().to_le_bytes());
                    }
                    rusqlite::types::ValueRef::Text(v) => {
                        hash.update([3]);
                        hash.update((v.len() as u64).to_le_bytes());
                        hash.update(v);
                    }
                    rusqlite::types::ValueRef::Blob(v) => {
                        hash.update([4]);
                        hash.update((v.len() as u64).to_le_bytes());
                        hash.update(v);
                    }
                }
            }
            hashes.push(hash.finalize());
        }
        hashes.sort_unstable();
        for hash in hashes {
            digest.update(hash);
        }
    }
    Ok(format!("{:x}", digest.finalize()))
}
