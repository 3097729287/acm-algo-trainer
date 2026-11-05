use crate::{
    api::{ApiError, fields},
    learning::{day, merge_intervals, stamp},
    storage::PersonalStore,
};
use chrono::{DateTime, TimeZone, Utc};
use serde_json::{Value, json};

fn state(store: &PersonalStore, key: &str) -> Result<Value, ApiError> {
    let value = store
        .pref(key)?
        .and_then(|raw| serde_json::from_str::<Value>(&raw).ok())
        .filter(|v| v["version"] == 1)
        .unwrap_or(json!({"version":1,"days":{},"sessions":{}}));
    if !value["sessions"].is_object()
        || !value["days"].as_object().is_some_and(|days| {
            days.values().all(|entry| {
                entry.is_object()
                    && entry["seconds"]
                        .as_f64()
                        .is_some_and(|n| n.is_finite() && n >= 0.)
            })
        })
    {
        return Err(ApiError::new(
            500,
            "INVALID_STORED_DATA",
            "使用时长记录格式异常，原数据已保留",
        ));
    }
    Ok(value)
}
pub fn snapshot(store: &PersonalStore) -> Result<Value, ApiError> {
    let state = state(store, "usage-v1")?;
    let mut days = Vec::new();
    let mut best: Option<(String, i64)> = None;
    for (day, entry) in state["days"]
        .as_object()
        .ok_or_else(|| ApiError::new(500, "INVALID_STORED_DATA", "使用时长记录格式异常"))?
    {
        let seconds = entry["seconds"]
            .as_f64()
            .ok_or_else(|| ApiError::new(500, "INVALID_STORED_DATA", "使用时长记录格式异常"))?
            .round_ties_even() as i64;
        if best.as_ref().is_none_or(|(_, n)| seconds > *n) {
            best = Some((day.clone(), seconds));
        }
        days.push(json!({"date":day,"seconds":seconds}));
    }
    Ok(
        json!({"totalSeconds":days.iter().filter_map(|v|v["seconds"].as_i64()).sum::<i64>(),"days":days,"maxDailySeconds":best.as_ref().map(|(_,n)|*n),"maxDailyDate":best.map(|(d,_)|d),"startedAt":state.get("startedAt")}),
    )
}
fn append(value: &mut Value, now: DateTime<Utc>, seconds: f64) -> Result<(), ApiError> {
    let end = now.timestamp() as f64 + now.timestamp_subsec_micros() as f64 / 1_000_000.;
    let start_instant =
        now - chrono::Duration::microseconds((seconds * 1_000_000.).round_ties_even() as i64);
    let start = start_instant.timestamp() as f64
        + start_instant.timestamp_subsec_micros() as f64 / 1_000_000.;
    let mut cursor = start;
    while cursor < end {
        let boundary = ((cursor + 28800.) / 86400.).floor() * 86400. + 86400. - 28800.;
        let stop = end.min(boundary);
        let date = day(Utc
            .timestamp_opt(cursor.floor() as i64, 0)
            .single()
            .unwrap());
        if value["days"].get(&date).is_none() {
            value["days"][&date] = json!({"seconds":0,"intervals":[]});
        }
        let entry = &mut value["days"][&date];
        let mut intervals: Vec<[f64; 2]> =
            serde_json::from_value(entry.get("intervals").cloned().unwrap_or(json!([])))?;
        intervals.push([cursor, stop]);
        let merged = merge_intervals(&mut intervals);
        entry["seconds"] = json!(merged.iter().map(|i| i[1] - i[0]).sum::<f64>());
        entry["intervals"] = json!(merged);
        cursor = stop;
    }
    if value.get("startedAt").is_none() {
        value["startedAt"] = json!(stamp(start_instant));
    }
    let first = day(start_instant);
    for (date, entry) in value["days"].as_object_mut().unwrap() {
        if date < &first {
            entry.as_object_mut().unwrap().remove("intervals");
        }
    }
    Ok(())
}
pub fn record(
    store: &mut PersonalStore,
    body: &Value,
    now: DateTime<Utc>,
) -> Result<Value, ApiError> {
    fields(body, &["sessionId", "sequence", "seconds", "learning"])?;
    let id = body["sessionId"]
        .as_str()
        .filter(|s| {
            s.len() == 36
                && s.bytes()
                    .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b) || b == b'-')
        })
        .ok_or_else(|| ApiError::bad("使用时长格式无效"))?;
    let sequence = body["sequence"]
        .as_i64()
        .filter(|n| (1..=2i64.pow(31)).contains(n))
        .ok_or_else(|| ApiError::bad("使用时长格式无效"))?;
    let seconds = body["seconds"]
        .as_f64()
        .filter(|n| n.is_finite() && 0. < *n && *n <= 60.)
        .ok_or_else(|| ApiError::bad("使用时长格式无效"))?;
    if body.get("learning").is_some_and(|v| !v.is_boolean()) {
        return Err(ApiError::bad("使用时长格式无效"));
    }
    let mut value = state(store, "usage-v1")?;
    if sequence <= value["sessions"][id]["sequence"].as_i64().unwrap_or(0) {
        return Ok(json!({"saved":true}));
    }
    append(&mut value, now, seconds)?;
    value["sessions"][id] = json!({"sequence":sequence,"lastAt":stamp(now)});
    let mut cursors = value["sessions"]
        .as_object()
        .unwrap()
        .iter()
        .map(|(k, v)| (k.clone(), v.clone()))
        .collect::<Vec<_>>();
    cursors.sort_by(|a, b| a.1["lastAt"].as_str().cmp(&b.1["lastAt"].as_str()));
    value["sessions"] = json!(
        cursors
            .into_iter()
            .rev()
            .take(64)
            .collect::<serde_json::Map<_, _>>()
    );
    let study = if body["learning"] == true {
        let mut study = state(store, "learning-usage-v1")?;
        append(&mut study, now, seconds)?;
        Some(study)
    } else {
        None
    };
    let tx = store.db.transaction()?;
    PersonalStore::put(&tx, "usage-v1", &value.to_string(), &stamp(now))?;
    if let Some(study) = study {
        PersonalStore::put(&tx, "learning-usage-v1", &study.to_string(), &stamp(now))?;
    }
    tx.commit()?;
    Ok(json!({"saved":true}))
}
