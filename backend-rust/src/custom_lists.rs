//! Durable account-owned lists. Transactions include the real creation action.
use crate::{
    api::{ApiError, fields},
    identity::canonical_url,
    learning::stamp,
    preferences,
    storage::PersonalStore,
};
use chrono::{DateTime, Utc};
use rusqlite::OptionalExtension;
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};

const PREFIX: &str = "custom-training-list:";
pub const MAX_PROBLEMS: usize = 20000;
fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
        Value::Number(v) => v.as_f64() != Some(0.),
    }
}
fn identity(value: &str) -> Result<(), ApiError> {
    let valid = value
        .strip_prefix("custom:")
        .and_then(|v| {
            uuid::Uuid::parse_str(v)
                .ok()
                .map(|uuid| uuid.hyphenated().to_string() == v)
        })
        .unwrap_or(false);
    if valid {
        Ok(())
    } else {
        Err(ApiError::bad("题单编号无效"))
    }
}
fn ids(value: Option<&Value>) -> Result<Vec<String>, ApiError> {
    let empty = json!([]);
    let values = value
        .unwrap_or(&empty)
        .as_array()
        .ok_or_else(|| ApiError::bad("题单题目格式无效"))?;
    if values.len() > MAX_PROBLEMS {
        return Err(ApiError::bad("每份题单最多添加 20000 道题"));
    }
    let mut seen = HashSet::new();
    let mut result = Vec::new();
    for value in values {
        let id = value
            .as_str()
            .filter(|v| !v.is_empty() && v.chars().count() <= 512)
            .ok_or_else(|| ApiError::bad("题单题目格式无效"))?;
        if seen.insert(id) {
            result.push(id.to_owned());
        }
    }
    Ok(result)
}
pub fn read(store: &PersonalStore) -> Result<Vec<Value>, ApiError> {
    let mut statement = store.db.prepare_cached("SELECT value FROM account_preferences WHERE key LIKE 'custom-training-list:%' ORDER BY updated_at DESC,key")?;
    let mut values = Vec::new();
    for raw in statement.query_map([], |r| r.get::<_, String>(0))? {
        if let Ok(value) = serde_json::from_str::<Value>(&raw?) {
            if value.is_object() && !truth(&value["deleted"]) && value["problems"].is_array() {
                values.push(value);
            }
        }
    }
    Ok(values)
}
fn existing(store: &PersonalStore, id: &str) -> Result<Value, ApiError> {
    identity(id)?;
    let value = store
        .document(&format!("{PREFIX}{id}"))?
        .filter(|v| v.is_object() && !truth(&v["deleted"]) && truth(&v["custom"]))
        .ok_or_else(|| ApiError::missing("没有找到这份题单"))?;
    if !value["problems"].is_array() || value["id"] != id {
        return Err(ApiError::new(
            500,
            "INVALID_STORED_DATA",
            "题单记录格式异常，原数据已保留",
        ));
    }
    Ok(value)
}
fn problems<F>(
    store: &PersonalStore,
    ids: &[String],
    now: DateTime<Utc>,
    resolve: &mut F,
) -> Result<Vec<Value>, ApiError>
where
    F: FnMut(&PersonalStore, &str) -> Result<Value, ApiError>,
{
    let mut values = Vec::new();
    let mut seen = HashSet::new();
    for id in ids {
        let row = resolve(store, id)?;
        let id = row["id"]
            .as_str()
            .ok_or_else(|| ApiError::missing("没有找到这道题"))?;
        let key = row["url"]
            .as_str()
            .and_then(canonical_url)
            .unwrap_or_else(|| id.to_owned());
        if seen.insert(key) {
            let pid = row["problem"]
                .as_str()
                .filter(|v| !v.is_empty())
                .unwrap_or(id);
            values.push(json!({"problemId":id,"pid":pid,"url":row.get("url").unwrap_or(&Value::Null),"sections":[],"addedAt":stamp(now)}));
        }
    }
    Ok(values)
}
fn write(store: &mut PersonalStore, values: &[Value], now: DateTime<Utc>) -> Result<(), ApiError> {
    if values.is_empty() {
        return Ok(());
    }
    let tx = store.db.transaction()?;
    for value in values {
        let id = value["id"].as_str().unwrap();
        let key = format!("{PREFIX}{id}");
        let present = tx
            .query_row(
                "SELECT 1 FROM account_preferences WHERE key=?",
                [&key],
                |_| Ok(()),
            )
            .optional()?
            .is_some();
        if !truth(&value["deleted"]) && !present {
            preferences::action(&tx, "create-list", id, now)?;
        }
        PersonalStore::put(&tx, &key, &value.to_string(), &stamp(now))?;
    }
    tx.commit()?;
    Ok(())
}
pub fn save<F>(
    store: &mut PersonalStore,
    body: &Value,
    now: DateTime<Utc>,
    mut resolve: F,
) -> Result<Value, ApiError>
where
    F: FnMut(&PersonalStore, &str) -> Result<Value, ApiError>,
{
    fields(body, &["id", "title", "problemIds", "deleted"])?;
    let requested = match body.get("id") {
        None | Some(Value::Null) => None,
        Some(Value::String(v)) if v.is_empty() => None,
        Some(Value::String(v)) => Some(v.as_str()),
        _ => return Err(ApiError::bad("题单编号无效")),
    };
    let id = requested
        .map(str::to_owned)
        .unwrap_or_else(|| format!("custom:{}", uuid::Uuid::new_v4()));
    identity(&id)?;
    if body
        .get("deleted")
        .is_some_and(|v| !v.is_null() && !v.is_boolean())
    {
        return Err(ApiError::bad("题单格式无效"));
    }
    let deleted = body["deleted"] == true;
    let title = body
        .get("title")
        .map_or(Some(""), Value::as_str)
        .ok_or_else(|| ApiError::bad("题单名称须为 1～80 个字符"))?;
    if !deleted
        && (title.trim().is_empty()
            || title.trim().chars().count() > 80
            || title.chars().any(|c| c <= '\u{1f}' || c == '\u{7f}'))
    {
        return Err(ApiError::bad("题单名称须为 1～80 个字符"));
    }
    let ids = ids(body.get("problemIds"))?;
    let previous = requested.map(|_| existing(store, &id)).transpose()?;
    if deleted && previous.is_none() {
        return Err(ApiError::missing("没有找到这份题单"));
    }
    if previous.is_none() && read(store)?.len() >= 100 {
        return Err(ApiError::bad("最多创建 100 份题单"));
    }
    let mut items = problems(store, &ids, now, &mut resolve)?;
    if let Some(previous) = &previous {
        let old = previous["problems"]
            .as_array()
            .unwrap()
            .iter()
            .filter_map(|v| v["problemId"].as_str().map(|id| (id, v)))
            .collect::<HashMap<_, _>>();
        for value in &mut items {
            if let Some(old) = old.get(value["problemId"].as_str().unwrap()) {
                if truth(&old["addedAt"]) {
                    value["addedAt"] = old["addedAt"].clone();
                } else {
                    value.as_object_mut().unwrap().remove("addedAt");
                }
            }
        }
    }
    let value = if deleted {
        let mut value = previous.unwrap();
        value["deleted"] = json!(true);
        value
    } else {
        json!({"id":id,"title":title.trim(),"custom":true,"available":true,"aggregateChildren":false,"children":[],"problems":items,"categories":[{"id":"personal","name":"我的题单","order":-1,"position":0}],"topicPath":["我的题单"],"deleted":false})
    };
    write(store, std::slice::from_ref(&value), now)?;
    Ok(json!({"list":value,"customLists":read(store)?}))
}
pub fn add<F>(
    store: &mut PersonalStore,
    body: &Value,
    now: DateTime<Utc>,
    mut resolve: F,
) -> Result<Value, ApiError>
where
    F: FnMut(&PersonalStore, &str) -> Result<Value, ApiError>,
{
    fields(body, &["listIds", "problemIds"])?;
    let destinations = body["listIds"]
        .as_array()
        .filter(|v| !v.is_empty() && v.len() <= 100)
        .ok_or_else(|| ApiError::bad("请选择自建题单"))?;
    if body.get("problemIds").is_none() {
        return Err(ApiError::bad("题单格式无效"));
    }
    let ids = ids(body.get("problemIds"))?;
    if ids.is_empty() {
        return Err(ApiError::bad("没有匹配的题目"));
    }
    let mut seen = HashSet::new();
    let mut values = Vec::new();
    for id in destinations {
        let id = id.as_str().ok_or_else(|| ApiError::bad("请选择自建题单"))?;
        if seen.insert(id) {
            values.push(existing(store, id)?);
        }
    }
    let additions = problems(store, &ids, now, &mut resolve)?;
    let mut counts = serde_json::Map::new();
    let mut changed = Vec::new();
    for mut value in values {
        let current = value["problems"].as_array().unwrap();
        let ids = current
            .iter()
            .filter_map(|v| v["problemId"].as_str())
            .collect::<HashSet<_>>();
        let urls = current
            .iter()
            .filter_map(|v| v["url"].as_str().and_then(canonical_url))
            .collect::<HashSet<_>>();
        let new = additions
            .iter()
            .filter(|v| {
                !ids.contains(v["problemId"].as_str().unwrap())
                    && v["url"]
                        .as_str()
                        .and_then(canonical_url)
                        .is_none_or(|url| !urls.contains(&url))
            })
            .cloned()
            .collect::<Vec<_>>();
        if current.len() + new.len() > MAX_PROBLEMS {
            return Err(ApiError::bad("每份题单最多添加 20000 道题"));
        }
        counts.insert(value["id"].as_str().unwrap().to_owned(), json!(new.len()));
        if !new.is_empty() {
            value["problems"].as_array_mut().unwrap().extend(new);
            changed.push(value);
        }
    }
    write(store, &changed, now)?;
    Ok(json!({"customLists":read(store)?,"added":counts}))
}
