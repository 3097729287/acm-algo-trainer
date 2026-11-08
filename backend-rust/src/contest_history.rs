//! Frozen contest history and the narrowly proven legacy automatic joins.
//! Running contests are kept behind the unported finalization boundary.
use crate::{
    api::ApiError, catalogue::row_or_portable, learning::stamp, storage::PersonalStore,
    training::Training,
};
use regex::Regex;
use serde_json::{Value, json};
use std::{
    collections::{BTreeSet, HashMap, HashSet},
    sync::LazyLock,
};

fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v[key].as_str().unwrap_or("")
}
fn truth(v: &Value) -> bool {
    match v {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(v) => v.as_f64() != Some(0.),
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
fn invalid() -> ApiError {
    ApiError::new(
        500,
        "INVALID_STORED_DATA",
        "比赛历史记录格式异常，原数据已保留",
    )
}
fn parsed(raw: &str) -> Result<Value, ApiError> {
    let value: Value = serde_json::from_str(if raw.is_empty() { "{}" } else { raw })?;
    if !value.is_object() {
        return Err(invalid());
    }
    Ok(value)
}
static PUBLIC_NAMES: LazyLock<Value> = LazyLock::new(|| {
    serde_json::from_str(include_str!(
        "../../backend/resources/contest-event-metadata.json"
    ))
    .expect("reviewed public event names")
});
static PATTERNS: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    [
        r"(?i)^(?:AtCoder\s+)?(ABC|ARC|AGC|AHC)\s*#?\s*(\d+)$",
        r"^AtCoder\s*(初学者赛|常规赛|高难度赛|启发式赛)\s*(\d+)$",
        r"(?i)(?:Round|教育赛(?:第)?)\s*#?\s*(\d+)",
        r"(?i)Codeforces Round\s*#?\s*(\d+).*?Div\.\s*([1-4])(?:\s*\+\s*(?:Div\.\s*)?([1-4]))?",
        r"(?i)^Div\.\s*([1-4])(?:\s*\+\s*Div\.\s*([1-4]))?\s+#?\s*(\d+)$",
        r"^Codeforces 第\s*(\d+)\s*轮（第\s*([1-4])(?:、([1-4]))?\s*组）$",
        r"(?i)(小白月赛|挑战赛|练习赛|周赛|入门赛|基础赛|月赛)(?:\s*Round)?\s*#?\s*(\d+)",
        r"(?i)LGR\s*-\s*(\d+)",
    ]
    .into_iter()
    .map(|pattern| Regex::new(pattern).unwrap())
    .collect()
});
fn number(value: &str) -> Result<u64, ApiError> {
    value.parse().map_err(|_| ApiError::pending())
}

pub fn display_name(t: &Training<'_>, raw: &str) -> Result<String, ApiError> {
    let name = raw.split_whitespace().collect::<Vec<_>>().join(" ");
    if let Some(c) = PATTERNS[0].captures(&name) {
        return Ok(format!("{} {}", c[1].to_ascii_uppercase(), number(&c[2])?));
    }
    if let Some(c) = PATTERNS[1].captures(&name) {
        let series = match &c[1] {
            "初学者赛" => "ABC",
            "常规赛" => "ARC",
            "高难度赛" => "AGC",
            _ => "AHC",
        };
        return Ok(format!("{series} {}", number(&c[2])?));
    }
    if name.to_ascii_lowercase().contains("educational") || name.contains("教育赛") {
        if let Some(c) = PATTERNS[2].captures(&name) {
            return Ok(format!("教育赛 {}", number(&c[1])?));
        }
    } else {
        if let Some(c) = PATTERNS[3].captures(&name) {
            return Ok(format!(
                "Div.{}{} {}",
                &c[2],
                c.get(3)
                    .map_or(String::new(), |m| format!("+Div.{}", m.as_str())),
                number(&c[1])?
            ));
        }
        if let Some(c) = PATTERNS[4].captures(&name) {
            return Ok(format!(
                "Div.{}{} {}",
                &c[1],
                c.get(2)
                    .map_or(String::new(), |m| format!("+Div.{}", m.as_str())),
                number(&c[3])?
            ));
        }
        if let Some(c) = PATTERNS[5].captures(&name) {
            return Ok(format!(
                "Div.{}{} {}",
                &c[2],
                c.get(3)
                    .map_or(String::new(), |m| format!("+Div.{}", m.as_str())),
                number(&c[1])?
            ));
        }
        // Preserve the legacy specificity order (小白月赛 before 月赛).
        if let Some(c) = PATTERNS[6].captures(&name) {
            return Ok(format!("{} {}", &c[1], number(&c[2])?));
        }
        if let Some(c) = PATTERNS[7].captures(&name) {
            return Ok(format!("月赛 {}", number(&c[1])?));
        }
    }
    if let Some(name) = PUBLIC_NAMES["names"][&name]["name"]
        .as_str()
        .filter(|name| !name.is_empty())
    {
        return Ok(name.into());
    }
    let mut names = BTreeSet::new();
    let mut statement=t.catalogue.db.prepare_cached("SELECT DISTINCT json_extract(compact,'$.contest') FROM catalogue WHERE json_extract(compact,'$.contest')=?1 OR json_extract(compact,'$.contestFullName')=?1")?;
    for value in statement.query_map([&name], |row| row.get::<_, String>(0))? {
        names.insert(value?);
    }
    if names.len() == 1 {
        return Ok(names.into_iter().next().unwrap());
    }
    // Unknown retained provenance cannot be silently presented as another event.
    Err(ApiError::pending())
}
pub fn completed_replays(t: &Training<'_>) -> Result<Vec<String>, ApiError> {
    let mut names = BTreeSet::new();
    for record in t
        .personal
        .rows("SELECT config FROM contests WHERE status='finished'", [])?
        .as_array()
        .unwrap()
    {
        let config = parsed(text(record, "config"))?;
        if config["strategy"] == "replay" && !text(&config, "contest").trim().is_empty() {
            names.insert(display_name(t, text(&config, "contest"))?);
        }
    }
    Ok(names.into_iter().collect())
}
pub fn record(t: &Training<'_>, identity: &str) -> Result<Value, ApiError> {
    if identity.is_empty() || identity.len() > 512 {
        return Err(ApiError::bad("缺少模拟赛编号"));
    }
    let records = t
        .personal
        .rows("SELECT * FROM contests WHERE id=?", [identity])?;
    let record = records
        .as_array()
        .unwrap()
        .first()
        .ok_or_else(|| ApiError::missing("没有找到这场模拟赛"))?
        .clone();
    if record["status"] == "running" {
        return Err(ApiError::pending());
    }
    if !["finished", "cancelled"].contains(&text(&record, "status")) {
        return Err(invalid());
    }
    Ok(record)
}
pub fn get(t: &Training<'_>, identity: &str) -> Result<Value, ApiError> {
    let record = record(t, identity)?;
    Ok(json!({"contest":t.contest_projection(&record)?,"now":stamp(t.now)}))
}

pub fn assert_problem_context(
    t: &Training<'_>,
    identity: &str,
    context: &str,
    writing: bool,
) -> Result<(), ApiError> {
    let record = record(t, context)?;
    let slots: Value = serde_json::from_str(text(&record, "slots"))?;
    if !slots
        .as_array()
        .ok_or_else(invalid)?
        .iter()
        .any(|slot| slot["id"] == identity)
    {
        return Err(ApiError::new(403, "CONTEST_SCOPE", "这道题不属于该模拟赛"));
    }
    if writing {
        return Err(ApiError::conflict(
            "模拟赛已经结束，不能继续提交或改写考场草稿",
        ));
    }
    Ok(())
}

pub fn prune_legacy_joins(t: &Training<'_>) -> Result<(), ApiError> {
    const KEY: &str = "contest-edited-training-v1";
    if t.personal.pref(KEY)?.is_some() {
        return Ok(());
    }
    let mut references = HashMap::<String, Vec<(Value, String)>>::new();
    for record in t
        .personal
        .rows(
            "SELECT slots,config,started_at FROM contests WHERE deleted_at IS NULL",
            [],
        )?
        .as_array()
        .unwrap()
    {
        if truth(&parsed(text(record, "config"))?["editedTrainingOnly"]) {
            continue;
        }
        let slots: Value = serde_json::from_str(text(record, "slots"))?;
        for slot in slots
            .as_array()
            .ok_or_else(invalid)?
            .iter()
            .filter(|slot| slot.get("trainingBefore").is_some())
        {
            references
                .entry(t.canonical(text(slot, "id"))?)
                .or_default()
                .push((slot.clone(), text(record, "started_at").into()));
        }
    }
    if references.is_empty() {
        return Ok(());
    }
    let mut protected = HashSet::new();
    for table in ["drafts", "submissions"] {
        for row in t
            .personal
            .rows(&format!("SELECT DISTINCT problem_id FROM {table}"), [])?
            .as_array()
            .unwrap()
        {
            protected.insert(t.canonical(text(row, "problem_id"))?);
        }
    }
    for row in t
        .personal
        .rows("SELECT ids FROM practice_sets", [])?
        .as_array()
        .unwrap()
    {
        let ids: Vec<String> = serde_json::from_str(text(row, "ids"))?;
        for id in ids {
            protected.insert(t.canonical(&id)?);
        }
    }
    let mut retired = Vec::new();
    for row in t
        .personal
        .rows("SELECT * FROM training WHERE active=1", [])?
        .as_array()
        .unwrap()
    {
        let canonical = t.canonical(text(row, "id"))?;
        let Some(entries) = references.get(&canonical) else {
            continue;
        };
        if protected.contains(&canonical)
            || entries
                .iter()
                .any(|(slot, _)| !truth(&slot["trainingAdded"]))
            || !entries.iter().any(|(slot, _)| {
                !truth(&slot["trainingBefore"]) || !truth(&slot["trainingBefore"]["active"])
            })
            || !entries
                .iter()
                .any(|(_, started)| row["active_at"] == *started)
            || [
                "accepted_at",
                "last_local_at",
                "last_review_at",
                "review_count",
                "solution_pending",
                "solution_seen_at",
            ]
            .iter()
            .any(|key| truth(&row[*key]))
        {
            continue;
        }
        retired.push(row["id"].clone());
    }
    let tx = t.personal.db.unchecked_transaction()?;
    let at = stamp(t.now);
    for id in &retired {
        tx.execute(
            "UPDATE training SET active=0,removed_at=?,mock_due=0 WHERE id=?",
            rusqlite::params![at, id.as_str().ok_or_else(invalid)?],
        )?;
    }
    PersonalStore::put(
        &tx,
        KEY,
        &json!({"retired":retired,"at":at}).to_string(),
        &at,
    )?;
    tx.commit()?;
    Ok(())
}

pub fn live_label(
    t: &Training<'_>,
    record: &Value,
    config: &Value,
    slots: &[Value],
) -> Result<String, ApiError> {
    let name = text(record, "name");
    if !name.starts_with("重现赛 · ") {
        return Ok(name.into());
    }
    let mut live = truth(&config["calendarEvent"]);
    if !live {
        if let Some(slot) = slots.first() {
            if let Ok(original) = row_or_portable(t.catalogue, t.personal, text(slot, "id")) {
                live = crate::ability::time(text(&original, "startedAt"))
                    .zip(crate::ability::time(text(&original, "endedAt")))
                    .zip(crate::ability::time(text(record, "started_at")))
                    .is_some_and(|((began, ended), start)| began <= start && start < ended);
            }
        }
    }
    Ok(if live {
        name.trim_start_matches("重现赛 · ").into()
    } else {
        name.into()
    })
}
