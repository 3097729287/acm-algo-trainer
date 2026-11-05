use crate::{
    api::{ApiError, required_text},
    storage::PersonalStore,
};
use chrono::{DateTime, TimeZone, Utc};
use rusqlite::OptionalExtension;
use serde_json::{Value, json};

pub const KEY: &str = "learning-summary-v1";
pub const HISTORY: &str = "learning-summary-history:";
pub fn stamp(now: DateTime<Utc>) -> String {
    now.to_rfc3339_opts(chrono::SecondsFormat::Micros, true)
}
pub fn day(now: DateTime<Utc>) -> String {
    now.with_timezone(&chrono::FixedOffset::east_opt(28800).unwrap())
        .format("%Y-%m-%d")
        .to_string()
}
pub fn empty() -> Value {
    json!({"version":1,"revision":"","config":{"goal":{"kind":"xcpc","title":"区域赛铜牌","deadline":""},"weekdayMinutes":null,"weekendMinutes":null,"restDays":[],"team":false,"role":""},
        "plan":null,"proposal":null,"article":[],"topics":[],"seen":{},"view":{},"checks":{},"diagnoses":[]})
}
pub fn snapshot(
    store: &PersonalStore,
    curriculum: &Value,
    now: DateTime<Utc>,
) -> Result<Value, ApiError> {
    let mut state = store.document(KEY)?.unwrap_or_else(empty);
    if !state.is_object() {
        return Err(ApiError::new(
            500,
            "INVALID_STORED_DATA",
            "学习规划记录格式异常，原数据已保留",
        ));
    }
    let histories=store.rows("SELECT value FROM account_preferences WHERE key LIKE 'learning-summary-history:%' ORDER BY updated_at DESC",[])?;
    let mut history = Vec::new();
    for row in histories.as_array().unwrap() {
        let value: Value = serde_json::from_str(row["value"].as_str().unwrap())?;
        if value["deleted"] == true {
            continue;
        }
        history.push(json!({"id":value["id"],"at":value["at"],"reason":value["reason"],"week":value.get("plan").and_then(|p|p.get("week"))}));
    }
    state["history"] = json!(history);
    let allowed = [
        "id",
        "title",
        "level",
        "prerequisites",
        "tags",
        "course",
        "template",
        "lectures",
    ];
    state["availableTopics"] = json!(
        curriculum["topics"]
            .as_array()
            .into_iter()
            .flatten()
            .map(|topic| topic
                .as_object()
                .map(|o| o
                    .iter()
                    .filter(|(k, _)| allowed.contains(&k.as_str()))
                    .map(|(k, v)| (k.clone(), v.clone()))
                    .collect::<serde_json::Map<_, _>>())
                .unwrap_or_default())
            .collect::<Vec<_>>()
    );
    state["now"] = json!(stamp(now));
    if store
        .db
        .query_row("SELECT 1 FROM contests WHERE status='running'", [], |_| {
            Ok(())
        })
        .optional()?
        .is_some()
    {
        return Err(ApiError::pending());
    }
    state["activeContest"] = Value::Null;
    Ok(state)
}
pub fn history(store: &PersonalStore, id: &str) -> Result<Value, ApiError> {
    let value = store
        .document(&format!("{HISTORY}{id}"))?
        .ok_or_else(|| ApiError::missing("这份历史已删除或不存在"))?;
    if value["deleted"] == true {
        return Err(ApiError::missing("这份历史已删除或不存在"));
    }
    Ok(value)
}
pub fn quiz(quizzes: &Value, id: &str) -> Result<Value, ApiError> {
    let row = quizzes
        .get(id)
        .filter(|v| v.is_array())
        .ok_or_else(|| ApiError::missing("没有这项原理检查"))?;
    Ok(json!({"topicId":id,"question":row[0],"options":row[1]}))
}
pub fn update(
    store: &mut PersonalStore,
    body: &Value,
    curriculum: &Value,
    now: DateTime<Utc>,
) -> Result<Value, ApiError> {
    snapshot(store, curriculum, now)?;
    let mut state = store.document(KEY)?.unwrap_or_else(empty);
    if !state.is_object()
        || !state["revision"].is_string()
        || !state["seen"].is_object()
        || !state["article"].is_array()
    {
        return Err(ApiError::new(
            500,
            "INVALID_STORED_DATA",
            "学习规划记录格式异常，原数据已保留",
        ));
    }
    if body.get("revision") != state.get("revision") {
        return Err(ApiError::conflict("规划已更新，请读取后重试"));
    }
    let action = required_text(body, "action", 40)?;
    let mut tombstone = None;
    match action {
        "seen" => {
            let values = body["paragraphs"]
                .as_object()
                .filter(|v| v.len() <= 32)
                .ok_or_else(|| ApiError::bad("段落阅读记录无效"))?;
            for (id, hash) in values {
                if state["article"]
                    .as_array()
                    .is_some_and(|a| a.iter().any(|p| p["id"] == *id && p["hash"] == *hash))
                {
                    state["seen"][id] = hash.clone();
                }
            }
        }
        "view" => {
            let view = body["view"]
                .as_object()
                .filter(|v| serde_json::to_string(v).is_ok_and(|s| s.len() <= 8192))
                .ok_or_else(|| ApiError::bad("阅读状态无效"))?;
            let allowed = [
                "mode",
                "pinned",
                "collapsed",
                "detailed",
                "tone",
                "follow",
                "x",
                "y",
                "width",
                "height",
                "scrollTop",
            ];
            if view.keys().any(|k| !allowed.contains(&k.as_str())) {
                return Err(ApiError::bad("阅读状态无效"));
            }
            for key in ["pinned", "collapsed", "detailed", "follow"] {
                if view.get(key).is_some_and(|v| !v.is_boolean()) {
                    return Err(ApiError::bad("阅读状态无效"));
                }
            }
            if view
                .get("mode")
                .is_some_and(|v| !matches!(v.as_str(), Some("full" | "float")))
                || view
                    .get("tone")
                    .is_some_and(|v| !matches!(v.as_str(), Some("平实" | "鼓励" | "直接")))
            {
                return Err(ApiError::bad("阅读方式无效"));
            }
            for key in ["x", "y", "width", "height", "scrollTop"] {
                if view.get(key).is_some_and(|v| {
                    !v.as_f64()
                        .is_some_and(|n| n.is_finite() && (0.0..=10000000.0).contains(&n))
                }) {
                    return Err(ApiError::bad("阅读位置无效"));
                }
            }
            state["view"] = body["view"].clone();
        }
        "delete-history" => {
            let id = required_text(body, "id", 512)?;
            history(store, id)?;
            tombstone = Some((
                format!("{HISTORY}{id}"),
                json!({"id":id,"deleted":true,"at":stamp(now)}),
            ));
        }
        "configure" | "propose" | "accept" | "dismiss" | "difficulty" | "reflect" | "assist"
        | "complete" | "quiz" | "replace" | "postpone" => return Err(ApiError::pending()),
        _ => return Err(ApiError::bad("不支持这个规划操作")),
    }
    state["revision"] = json!(uuid::Uuid::new_v4().simple().to_string());
    let tx = store.db.transaction()?;
    if let Some((key, value)) = tombstone {
        PersonalStore::put(&tx, &key, &value.to_string(), &stamp(now))?;
    }
    PersonalStore::put(&tx, KEY, &state.to_string(), &stamp(now))?;
    tx.commit()?;
    snapshot(store, curriculum, now)
}
pub fn merge_intervals(intervals: &mut Vec<[f64; 2]>) -> Vec<[f64; 2]> {
    intervals.sort_by(|a, b| a[0].total_cmp(&b[0]).then(a[1].total_cmp(&b[1])));
    let mut result: Vec<[f64; 2]> = Vec::new();
    for &[a, b] in intervals.iter() {
        if let Some(last) = result.last_mut().filter(|last| a <= last[1]) {
            last[1] = last[1].max(b);
        } else {
            result.push([a, b]);
        }
    }
    result
}
pub fn effective(
    store: &mut PersonalStore,
    body: &Value,
    now: DateTime<Utc>,
) -> Result<Value, ApiError> {
    if body.as_object().map_or(0, |v| v.len()) != 1 {
        return Err(ApiError::bad("有效学习时段无效"));
    }
    let spans = body["intervals"]
        .as_array()
        .filter(|v| v.len() <= 128)
        .ok_or_else(|| ApiError::bad("有效学习时段无效"))?;
    let seconds = now.timestamp() as f64 + now.timestamp_subsec_micros() as f64 / 1_000_000.;
    let mut days = std::collections::BTreeMap::<String, Vec<[f64; 2]>>::new();
    for span in spans {
        let values = span
            .as_array()
            .filter(|v| v.len() == 2)
            .ok_or_else(|| ApiError::bad("有效学习时段无效"))?;
        let a = values[0]
            .as_f64()
            .filter(|v| v.is_finite())
            .ok_or_else(|| ApiError::bad("有效学习时段无效"))?;
        let b = values[1]
            .as_f64()
            .filter(|v| v.is_finite())
            .ok_or_else(|| ApiError::bad("有效学习时段无效"))?;
        if !(0. < b - a && b - a < 300.) || a < seconds - 7. * 86400. || b > seconds + 5. {
            return Err(ApiError::bad("有效学习时段超出范围"));
        }
        let mut cursor = a;
        while cursor < b {
            let local = (cursor + 28800.).floor();
            let day_start = (local / 86400.).floor() * 86400. - 28800.;
            let end = b.min(day_start + 86400.);
            let instant = Utc
                .timestamp_opt(cursor.floor() as i64, 0)
                .single()
                .ok_or_else(|| ApiError::bad("有效学习时段无效"))?;
            days.entry(day(instant)).or_default().push([cursor, end]);
            cursor = end;
        }
    }
    let tx = store.db.transaction()?;
    for (day, mut intervals) in days {
        let key = format!("effective-learning-day:{day}");
        let previous: Option<String> = tx
            .query_row(
                "SELECT value FROM account_preferences WHERE key=?",
                [&key],
                |r| r.get(0),
            )
            .optional()?;
        if let Some(previous) = previous {
            let previous: Value = serde_json::from_str(&previous)?;
            let old: Vec<[f64; 2]> = serde_json::from_value(previous["intervals"].clone())?;
            intervals.extend(old);
        }
        let merged = merge_intervals(&mut intervals);
        PersonalStore::put(
            &tx,
            &key,
            &json!({"intervals":merged}).to_string(),
            &stamp(now),
        )?;
    }
    let mut total = 0.;
    {
        let mut st = tx.prepare(
            "SELECT value FROM account_preferences WHERE key LIKE 'effective-learning-day:%'",
        )?;
        for raw in st.query_map([], |r| r.get::<_, String>(0))? {
            let value: Value = serde_json::from_str(&raw?)?;
            let mut intervals: Vec<[f64; 2]> = serde_json::from_value(value["intervals"].clone())?;
            total += merge_intervals(&mut intervals)
                .iter()
                .map(|i| i[1] - i[0])
                .sum::<f64>();
        }
    }
    tx.commit()?;
    Ok(json!({"saved":true,"totalSeconds":total.round_ties_even() as i64}))
}
