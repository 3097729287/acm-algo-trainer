//! Explicit local-journal export using the existing portable JSON contract.
//! Service credentials, device documents and browser state are never selected.
use crate::{api::ApiError, storage::PersonalStore};
use chrono::{DateTime, SecondsFormat, Utc};
use regex::Regex;
use rusqlite::{Connection, OptionalExtension, types::ValueRef};
use serde_json::{Value, json};
use std::collections::HashSet;

const TABLES: &[(&str, &str)] = &[
    ("training", "id"),
    ("practice_sets", "id"),
    ("contests", "id"),
    ("drafts", "problem_id,context"),
    ("submissions", "id"),
    ("tb_rank_profile", "id"),
    ("official_first_xp_awards", "problem_key"),
    ("official_xp_state", "id"),
    ("daily_missions", "day,id"),
    ("goals", "id"),
    ("goal_daily_assignments", "goal_id,day"),
    ("ranking_receipts", "endpoint,event_id"),
    ("ranking_reward_totals", "endpoint,user_id"),
    ("achievement_xp_claims", "achievement_id"),
    ("account_preferences", "key"),
    ("account_problem_facts", "problem_id"),
    ("account_sync_conflicts", "id"),
];

fn absolute_windows(value: &str) -> bool {
    let b = value.as_bytes();
    value.starts_with("\\\\")
        || (b.len() >= 3
            && b[0].is_ascii_alphabetic()
            && b[1] == b':'
            && matches!(b[2], b'/' | b'\\'))
}

fn portable(value: Value) -> Value {
    const FORBIDDEN: &[&str] = &[
        "path",
        "source_path",
        "sourcePath",
        "cachePath",
        "localPath",
        "password",
        "auth_token",
        "token",
        "apiKey",
        "api_key",
        "secret",
        "cookies",
        "cookie",
        "headers",
    ];
    match value {
        Value::Object(map) => Value::Object(
            map.into_iter()
                .filter(|(key, _)| !FORBIDDEN.contains(&key.as_str()) && !absolute_windows(key))
                .map(|(key, value)| (key, portable(value)))
                .collect(),
        ),
        Value::Array(values) => Value::Array(values.into_iter().map(portable).collect()),
        Value::String(value) if absolute_windows(&value) => json!(""),
        value => value,
    }
}

fn unsupported() -> ApiError {
    ApiError::new(
        422,
        "EXPORT_FORMAT",
        "个人记录含无法导出的字段，原数据库已保留",
    )
}

fn rows(db: &Connection, table: &str, order: &str) -> Result<Value, ApiError> {
    let mut statement = db.prepare(&format!("SELECT * FROM \"{table}\" ORDER BY {order}"))?;
    let names = statement
        .column_names()
        .into_iter()
        .map(str::to_owned)
        .collect::<Vec<_>>();
    let mut cursor = statement.query([])?;
    let mut result = Vec::new();
    while let Some(row) = cursor.next()? {
        let mut fields = serde_json::Map::new();
        for (index, name) in names.iter().enumerate() {
            let value = match row.get_ref(index)? {
                ValueRef::Null => Value::Null,
                ValueRef::Integer(value) => json!(value),
                ValueRef::Real(value) => {
                    Value::Number(serde_json::Number::from_f64(value).ok_or_else(unsupported)?)
                }
                ValueRef::Text(value) => {
                    Value::String(String::from_utf8(value.to_vec()).map_err(|_| unsupported())?)
                }
                ValueRef::Blob(_) => return Err(unsupported()),
            };
            fields.insert(name.clone(), value);
        }
        result.push(Value::Object(fields));
    }
    Ok(Value::Array(result))
}

pub fn export(store: &PersonalStore, now: DateTime<Utc>) -> Result<Value, ApiError> {
    // The SQLite read transaction also pins external/WAL writers to one
    // snapshot. The mutex alone only serializes writers in this process.
    let snapshot = store.db.unchecked_transaction()?;
    let existing = snapshot
        .prepare("SELECT name FROM sqlite_master WHERE type='table'")?
        .query_map([], |row| row.get::<_, String>(0))?
        .collect::<Result<HashSet<_>, _>>()?;
    let mut tables = serde_json::Map::new();
    for (table, order) in TABLES {
        tables.insert(
            (*table).to_owned(),
            if existing.contains(*table) {
                rows(&snapshot, table, order)?
            } else {
                json!([])
            },
        );
    }
    let language =
        Regex::new(r"^(?:draft-language:[a-f0-9]{64}|submission-language:[a-z0-9-]{1,100})$")
            .unwrap();
    let mut preferences = Vec::new();
    for mut row in tables["account_preferences"].as_array().unwrap().clone() {
        let key = row["key"].as_str().ok_or_else(unsupported)?;
        if key == "ui" || key == "receipt-bindings" {
            let value = serde_json::from_str(row["value"].as_str().ok_or_else(unsupported)?)?;
            row["value"] = json!(serde_json::to_string(&portable(value))?);
            preferences.push(row);
        } else if language.is_match(key)
            && matches!(row["value"].as_str(), Some("cpp17" | "python3"))
        {
            preferences.push(row);
        }
    }
    tables.insert("account_preferences".into(), json!(preferences));
    let nickname = if existing.contains("ranking_profile") {
        snapshot
            .query_row(
                "SELECT nickname FROM ranking_profile WHERE singleton=1",
                [],
                |row| row.get::<_, String>(0),
            )
            .optional()?
            .unwrap_or_default()
    } else {
        String::new()
    };
    snapshot.commit()?;
    // Online profile adapters have not yet migrated. The explicit local test
    // workspace has no connected public accounts; the route is marked partial.
    Ok(
        json!({"format":"tb-learning-export","formatVersion":1,"appVersion":env!("CARGO_PKG_VERSION"),
        "exportedAt":now.to_rfc3339_opts(SecondsFormat::Micros,true),"nickname":nickname,"tables":tables,"publicAccounts":[]}),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::migration::logical_fingerprint;
    use rusqlite::params;

    fn store(folder: &tempfile::TempDir) -> PersonalStore {
        PersonalStore::open(&folder.path().join("personal.sqlite3")).unwrap()
    }
    fn clock() -> DateTime<Utc> {
        "2026-11-09T09:00:00Z".parse().unwrap()
    }

    #[test]
    fn exports_every_allowed_table_in_key_order_without_credentials_or_writes() {
        let folder = tempfile::tempdir().unwrap();
        let store = store(&folder);
        store
            .db
            .execute("INSERT INTO drafts VALUES('z','',?,'now')", ["中文\n\0"])
            .unwrap();
        store
            .db
            .execute(
                "INSERT INTO drafts VALUES('a','review:1','print(42)','now')",
                [],
            )
            .unwrap();
        store.db.execute("INSERT INTO ranking_profile(singleton,user_id,nickname,auth_token,created_at) VALUES(1,'test','测试昵称','credential-must-stay-local','now')",[]).unwrap();
        store.db.execute_batch("CREATE TABLE future_private_cookie(value); INSERT INTO future_private_cookie VALUES('private-cookie');").unwrap();
        let before = logical_fingerprint(&store.db).unwrap();
        let value = export(&store, clock()).unwrap();
        assert_eq!(value["tables"].as_object().unwrap().len(), 17);
        assert_eq!(value["tables"]["drafts"][0]["problem_id"], "a");
        assert_eq!(value["tables"]["drafts"][1]["code"], "中文\n\0");
        assert_eq!(value["tables"]["account_sync_conflicts"], json!([]));
        assert_eq!(value["nickname"], "测试昵称");
        assert!(!value.to_string().contains("credential-must-stay-local"));
        assert!(!value.to_string().contains("private-cookie"));
        assert_eq!(before, logical_fingerprint(&store.db).unwrap());
    }

    #[test]
    fn portable_preferences_keep_languages_and_recursively_remove_device_secrets() {
        let folder = tempfile::tempdir().unwrap();
        let store = store(&folder);
        let value = json!({"nested":{"token":"private-token","good":"保留","location":"C:\\Local\\file"},"items":["\\\\server\\private","https://example.org/a"],"E:/private":9,"apiKey":"private-api","relative":"draft/a"});
        for key in ["ui", "receipt-bindings"] {
            store
                .db
                .execute(
                    "INSERT INTO account_preferences VALUES(?,?,?)",
                    params![key, value.to_string(), "now"],
                )
                .unwrap();
        }
        for (key, value) in [
            (format!("draft-language:{}", "a".repeat(64)), "python3"),
            ("submission-language:abc-123".into(), "cpp17"),
            ("submission-language:invalid_key".into(), "cpp17"),
            ("submission-language:invalid".into(), "private-language"),
            ("translation-settings".into(), "private-setting"),
        ] {
            store
                .db
                .execute(
                    "INSERT INTO account_preferences VALUES(?,?,?)",
                    params![key, value, "now"],
                )
                .unwrap();
        }
        let result = export(&store, clock()).unwrap();
        let prefs = result["tables"]["account_preferences"].as_array().unwrap();
        assert_eq!(prefs.len(), 4);
        let ui: Value = serde_json::from_str(
            prefs.iter().find(|r| r["key"] == "ui").unwrap()["value"]
                .as_str()
                .unwrap(),
        )
        .unwrap();
        assert_eq!(
            ui,
            json!({"nested":{"good":"保留","location":""},"items":["","https://example.org/a"],"relative":"draft/a"})
        );
        assert!(!result.to_string().contains("private-"));
        assert_eq!(store.document("ui").unwrap().unwrap(), value);
    }

    #[test]
    fn invalid_stored_json_or_binary_fields_fail_without_returning_lossy_backup() {
        let folder = tempfile::tempdir().unwrap();
        let store = store(&folder);
        store
            .db
            .execute(
                "INSERT INTO account_preferences VALUES('ui','{broken','now')",
                [],
            )
            .unwrap();
        let before = logical_fingerprint(&store.db).unwrap();
        assert!(export(&store, clock()).is_err());
        assert_eq!(before, logical_fingerprint(&store.db).unwrap());
        store
            .db
            .execute("DELETE FROM account_preferences", [])
            .unwrap();
        store
            .db
            .execute("INSERT INTO drafts VALUES('a','',x'FF00','now')", [])
            .unwrap();
        let before = logical_fingerprint(&store.db).unwrap();
        assert_eq!(export(&store, clock()).unwrap_err().code, "EXPORT_FORMAT");
        assert_eq!(before, logical_fingerprint(&store.db).unwrap());
    }
}
