//! Shared pure policy for journal merges and the growth business service.
//! This validates old receipts; it does not create an earned grant or an AC.
use chrono::{DateTime, Datelike, NaiveDate, NaiveDateTime, Utc};
use serde_json::{Map, Value, json};
use std::collections::BTreeSet;

pub const EXPERIENCE_KEY: &str = "experience-challenge-v1";
pub const SIX_KEY: &str = "experience-challenge-six-v1";
pub const STARTER_KEY: &str = "starter-level-curve-v1";
pub const EXPERIENCE_PROBLEMS: [&str; 2] = [
    "template-drill:binary-search:1",
    "template-drill:prefix-difference:1",
];
pub const RANK_UNLOCK_XP: i64 = 500;
pub const LEVEL_SIX_XP: i64 = 1500;

fn fields(object: &Map<String, Value>, names: &[&str]) -> bool {
    object.len() == names.len() && names.iter().all(|key| object.contains_key(*key))
}
pub(crate) fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(value) => *value,
        Value::String(value) => !value.is_empty(),
        Value::Number(value) => value.as_f64() != Some(0.),
        Value::Array(value) => !value.is_empty(),
        Value::Object(value) => !value.is_empty(),
    }
}
fn integer(value: &Value) -> Option<i64> {
    if value.is_f64() { None } else { value.as_i64() }
}
fn python_equal_one(value: &Value) -> bool {
    // These two legacy fields used `== 1`, unlike the explicit type checks on
    // seenVersion/amounts. Retain readable old receipts, without minting any XP.
    value.as_f64() == Some(1.) || value == &Value::Bool(true)
}
pub fn empty_experience(owner: &str) -> Value {
    json!({"policyVersion":1,"owner":owner,"seenVersion":0,"choice":null,
        "problemId":null,"challengeId":null,"startedAt":null,"attempts":[],
        "passedAt":null,"submissionId":null,"awardedXp":null})
}
fn valid_submission(value: &Value) -> bool {
    value
        .as_str()
        .and_then(|v| v.strip_prefix("submission-"))
        .is_some_and(|v| {
            v.len() == 32
                && v.bytes()
                    .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
        })
}

pub fn validate_experience(value: &Value, owner: Option<&str>) -> Option<Value> {
    let object = value.as_object()?;
    if !fields(
        object,
        &[
            "policyVersion",
            "owner",
            "seenVersion",
            "choice",
            "problemId",
            "challengeId",
            "startedAt",
            "attempts",
            "passedAt",
            "submissionId",
            "awardedXp",
        ],
    ) || !python_equal_one(&object["policyVersion"])
    {
        return None;
    }
    let actual = object["owner"].as_str()?;
    if owner.is_some_and(|owner| owner != actual) {
        return None;
    }
    if !matches!(integer(&object["seenVersion"]), Some(0 | 1)) {
        return None;
    }
    let experienced = object["choice"].as_str() == Some("experienced");
    if !(object["choice"].is_null() || experienced || object["choice"].as_str() == Some("beginner"))
    {
        return None;
    }
    let attempts = object["attempts"].as_array()?;
    if attempts.len() > 128 || attempts.iter().any(|v| !valid_submission(v)) {
        return None;
    }
    if experienced {
        if !EXPERIENCE_PROBLEMS.contains(&object["problemId"].as_str()?)
            || !object["startedAt"].is_string()
            || uuid::Uuid::parse_str(object["challengeId"].as_str()?).is_err()
        {
            return None;
        }
    } else if !attempts.is_empty()
        || [
            "problemId",
            "challengeId",
            "startedAt",
            "passedAt",
            "submissionId",
            "awardedXp",
        ]
        .iter()
        .any(|key| !object[*key].is_null())
    {
        return None;
    }
    if truth(&object["passedAt"])
        && (!experienced
            || !object["passedAt"].is_string()
            || !attempts.contains(&object["submissionId"]))
    {
        return None;
    }
    if !object["awardedXp"].is_null()
        && (!truth(&object["passedAt"])
            || !integer(&object["awardedXp"]).is_some_and(|v| (0..=RANK_UNLOCK_XP).contains(&v)))
    {
        return None;
    }
    Some(value.clone())
}
pub fn merge_experience(left: &Value, right: &Value) -> Option<Value> {
    let (a, b) = (
        validate_experience(left, None),
        validate_experience(right, None),
    );
    let (a, b) = match (a, b) {
        (Some(a), Some(b)) => (a, b),
        (Some(a), None) => return Some(a),
        (None, Some(b)) => return Some(b),
        (None, None) => return None,
    };
    if a["owner"] != b["owner"] {
        return None;
    }
    let score = |v: &Value| {
        (
            truth(&v["passedAt"]),
            v["choice"].as_str() == Some("experienced"),
            v["startedAt"].as_str().unwrap_or("").to_owned(),
            v["challengeId"].as_str().unwrap_or("").to_owned(),
        )
    };
    // Python max keeps the first operand on an exact score tie.
    let mut result = if score(&b) > score(&a) {
        b.clone()
    } else {
        a.clone()
    };
    result["seenVersion"] = json!(a["seenVersion"].as_i64()?.max(b["seenVersion"].as_i64()?));
    let mut attempts = BTreeSet::new();
    for value in [&a, &b] {
        if value["challengeId"] == result["challengeId"] {
            for attempt in value["attempts"].as_array()? {
                attempts.insert(attempt.as_str()?.to_owned());
            }
        }
    }
    let mut attempts: Vec<_> = attempts.into_iter().collect();
    if attempts.len() > 128 {
        attempts.drain(..attempts.len() - 128);
    }
    if truth(&result["passedAt"]) {
        let passed = result["submissionId"].as_str()?.to_owned();
        if !attempts.contains(&passed) {
            attempts.push(passed);
        }
        if attempts.len() > 128 {
            attempts.drain(..attempts.len() - 128);
        }
        let grant = [&a, &b]
            .into_iter()
            .filter(|v| truth(&v["passedAt"]))
            .filter_map(|v| integer(&v["awardedXp"]))
            .max();
        result["awardedXp"] = json!(grant);
    }
    result["attempts"] = json!(attempts);
    Some(result)
}

/// Timestamp forms generated by current clients and readable legacy ISO dates.
/// Naive dates/times use UTC, as the Python policy does.
pub(crate) fn parse_time(value: &Value) -> Option<DateTime<Utc>> {
    let raw = value.as_str()?;
    if raw.ends_with('z') {
        return None;
    }
    let normalized;
    let raw = if raw.chars().nth(4) == Some('-')
        && raw.chars().nth(7) == Some('-')
        && raw.chars().count() > 10
    {
        // datetime.fromisoformat permits any single character as the separator.
        let split = raw.char_indices().nth(11).map(|v| v.0).unwrap_or(raw.len());
        normalized = format!("{}T{}", &raw[..10], &raw[split..]);
        normalized.as_str()
    } else {
        raw
    };
    let valid = |time: DateTime<Utc>| {
        ((1..=9999).contains(&time.year()) && time.timestamp_subsec_nanos() < 1_000_000_000)
            .then_some(time)
    };
    if let Ok(value) = DateTime::parse_from_rfc3339(raw) {
        return valid(value.with_timezone(&Utc));
    }
    for format in [
        "%Y-%m-%dT%H:%M:%S%.f%#z",
        "%Y-%m-%d %H:%M:%S%.f%#z",
        "%Y%m%dT%H%M%S%.f%#z",
    ] {
        if let Ok(value) = DateTime::parse_from_str(raw, format) {
            return valid(value.with_timezone(&Utc));
        }
    }
    for format in [
        "%Y-%m-%dT%H:%M:%S%.f",
        "%Y-%m-%d %H:%M:%S%.f",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H",
        "%Y%m%dT%H%M%S%.f",
    ] {
        if let Ok(value) = NaiveDateTime::parse_from_str(raw, format) {
            return valid(value.and_utc());
        }
    }
    for format in ["%Y-%m-%d", "%Y%m%d", "%G-W%V-%u", "%GW%V%u"] {
        if let Ok(value) = NaiveDate::parse_from_str(raw, format) {
            return value.and_hms_opt(0, 0, 0).and_then(|v| valid(v.and_utc()));
        }
    }
    None
}
pub fn validate_starter(value: &Value, owner: Option<&str>) -> Option<Value> {
    let object = value.as_object()?;
    if !fields(object, &["version", "owner", "selectedAt"])
        || integer(&object["version"]) != Some(1)
    {
        return None;
    }
    let actual = object["owner"].as_str()?;
    if actual.is_empty()
        || owner.is_some_and(|owner| owner != actual)
        || parse_time(&object["selectedAt"]).is_none()
    {
        return None;
    }
    Some(value.clone())
}
pub fn merge_starter(left: &Value, right: &Value) -> Option<Value> {
    let (a, b) = (validate_starter(left, None), validate_starter(right, None));
    match (a, b) {
        (Some(a), Some(b)) if a["owner"] == b["owner"] => {
            Some(if b["selectedAt"].as_str()? < a["selectedAt"].as_str()? {
                b
            } else {
                a
            })
        }
        (Some(_), Some(_)) => None,
        (Some(a), None) => Some(a),
        (None, Some(b)) => Some(b),
        _ => None,
    }
}
pub fn six_receipt(value: &Value, owner: &str) -> Option<Value> {
    let parsed;
    let value = if let Some(text) = value.as_str() {
        parsed = serde_json::from_str::<Value>(text).ok()?;
        &parsed
    } else {
        value
    };
    let object = value.as_object()?;
    if !python_equal_one(object.get("version")?)
        || object.get("owner")?.as_str() != Some(owner)
        || !integer(object.get("xp")?).is_some_and(|v| (0..=LEVEL_SIX_XP).contains(&v))
        || !object.get("awardedAt")?.is_string()
    {
        return None;
    }
    // Old receipts accepted additional metadata; preserve it instead of erasing.
    Some(value.clone())
}
