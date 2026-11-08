//! Daily deadline goals derived from the existing official journal. A frozen
//! selection is never replaced by refreshes, aliases or a same-day removal.
use crate::{
    api::ApiError,
    identity::canonical_url,
    learning::{day, stamp},
    storage,
    training::Training,
};
use chrono::{DateTime, Duration, NaiveDate, Utc};
use regex::Regex;
use rusqlite::{OptionalExtension, params};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{HashMap, HashSet},
    sync::LazyLock,
};

const NOTICE: &str =
    "题量是训练安排，不保证评级或奖项；每周还需比赛、复盘与专项学习。区域赛另需队伍配合。";
const FAMILIES: [(&str, &str); 4] = [
    ("Codeforces Div.3", "Codeforces"),
    ("AtCoder ABC", "AtCoder"),
    ("牛客周赛", "牛客"),
    ("洛谷基础赛 / 月赛", "洛谷"),
];
static CF_TITLE: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"(?i)\bcf\s*(\d{3,4})\b").unwrap());
static INTEGER_TEXT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^[+-]?[0-9](?:_?[0-9])*$").unwrap());
static PATTERNS: LazyLock<Vec<Regex>> = LazyLock::new(|| {
    [
        r"(?i)Div\.\s*3|第\s*3\s*组",
        r"(?i)ABC|AtCoder Beginner|AtCoder 初学者",
        r"周赛",
        r"入门赛|基础赛|月赛",
        r"(?i)\bABC\b|AtCoder Beginner|AtCoder 初学者",
        r"(?i)ICPC|CCPC",
    ]
    .into_iter()
    .map(|v| Regex::new(v).unwrap())
    .collect()
});
fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v.get(key).and_then(Value::as_str).unwrap_or("")
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
    ApiError::new(500, "INVALID_STORED_DATA", "目标记录格式异常，原数据已保留")
}
fn input_error(message: &str) -> ApiError {
    ApiError::new(422, "INVALID_GOAL", message)
}
pub(crate) fn integer(v: &Value) -> Option<i64> {
    match v {
        Value::Bool(v) => Some(i64::from(*v)),
        Value::Number(v) => v.as_i64().or_else(|| {
            v.as_f64()
                .filter(|v| v.is_finite() && *v > i64::MIN as f64 && *v < i64::MAX as f64)
                .map(|v| v as i64)
        }),
        Value::String(v) if INTEGER_TEXT.is_match(v.trim()) => {
            v.trim().replace('_', "").parse().ok()
        }
        _ => None,
    }
}
fn supplied(body: &Value, key: &str, default: i64) -> Result<i64, ApiError> {
    body.get(key)
        .map(integer)
        .unwrap_or(Some(default))
        .ok_or_else(|| input_error("请填写具体截止日期、起点和每日可用分钟数"))
}
fn date(value: &str) -> Option<NaiveDate> {
    NaiveDate::parse_from_str(value, "%Y-%m-%d")
        .ok()
        .or_else(|| NaiveDate::parse_from_str(value, "%Y%m%d").ok())
        .or_else(|| NaiveDate::parse_from_str(value, "%G-W%V-%u").ok())
        .or_else(|| NaiveDate::parse_from_str(value, "%GW%V%u").ok())
}
fn at(value: &str) -> Option<DateTime<Utc>> {
    crate::ability::time(value)
        .or_else(|| crate::ability::time(&value.replacen(' ', "T", 1)))
        .or_else(|| date(value).map(|date| date.and_hms_opt(0, 0, 0).unwrap().and_utc()))
}
fn required_at(value: &str) -> Result<DateTime<Utc>, ApiError> {
    at(value).ok_or_else(invalid)
}
fn local_date(at: DateTime<Utc>) -> NaiveDate {
    NaiveDate::parse_from_str(&day(at), "%Y-%m-%d").unwrap()
}
fn count(v: &Value, key: &str) -> Result<i64, ApiError> {
    v[key].as_i64().ok_or_else(invalid)
}
fn ceil_div(n: i64, d: i64) -> i64 {
    n / d + i64::from(n % d != 0)
}
fn key(row: &Value) -> String {
    canonical_url(text(row, "url")).unwrap_or_else(|| text(row, "id").into())
}
fn fields(row: &Value, names: &[&str]) -> Value {
    Value::Object(
        names
            .iter()
            .map(|name| ((*name).into(), row[*name].clone()))
            .collect(),
    )
}
fn string(value: &Value) -> String {
    match value {
        Value::String(v) => v.clone(),
        Value::Null => "None".into(),
        Value::Bool(v) => if *v { "True" } else { "False" }.into(),
        _ => value.to_string(),
    }
}
fn problem_letter(row: &Value) -> String {
    row.get("problem").map(string).unwrap_or_default()
}
fn eligible_letter(row: &Value, range: &str, uppercase: bool) -> bool {
    let mut letter = problem_letter(row);
    if uppercase {
        letter = letter.to_uppercase();
    }
    if letter.chars().count() != 1 {
        return true;
    }
    let (lower, upper) = if range == "C–F" {
        ("C", "F")
    } else {
        ("A", "D")
    };
    letter.as_str() >= lower && letter.as_str() <= upper
}
fn family_matches(row: &Value, index: usize, task: bool) -> bool {
    text(row, "platform") == FAMILIES[index].1
        && !truth(&row["catalogHidden"])
        && PATTERNS[if task && index == 1 { 4 } else { index }].is_match(&format!(
            "{} {}",
            text(row, "contestFullName"),
            text(row, "contest")
        ))
}

struct Goal {
    record: Value,
    config: Value,
    start: DateTime<Utc>,
    end: NaiveDate,
}
fn parsed(record: Value) -> Result<Goal, ApiError> {
    let config: Value = serde_json::from_str(text(&record, "config"))?;
    if !config.is_object()
        || !["cf", "xcpc", "lanqiao", "custom"].contains(&text(&config, "kind"))
        || text(&config, "title").is_empty()
    {
        return Err(invalid());
    }
    for (field, min, max) in [
        ("dailyMinutes", 15, 720),
        ("totalProblems", 1, 10000),
        ("currentRating", 0, 4000),
        ("targetRating", 200, 4000),
        ("minutesPerProblem", 1, 1440),
    ] {
        let value = count(&config, field)?;
        if !(min..=max).contains(&value) {
            return Err(invalid());
        }
    }
    let start = required_at(text(&record, "created_at"))?;
    let end = date(text(&config, "deadline")).ok_or_else(invalid)?;
    Ok(Goal {
        record,
        config,
        start,
        end,
    })
}
fn records(t: &Training<'_>) -> Result<Vec<Value>, ApiError> {
    Ok(t.personal
        .rows(
            "SELECT * FROM goals WHERE archived=0 ORDER BY created_at,id",
            [],
        )?
        .as_array()
        .unwrap()
        .clone())
}
fn supported(t: &Training<'_>) -> Result<(), ApiError> {
    let unsupported:bool=t.personal.db.query_row("SELECT EXISTS(SELECT 1 FROM contests WHERE status='running') OR EXISTS(SELECT 1 FROM account_problem_facts)",[],|r|r.get(0))?;
    if unsupported {
        return Err(ApiError::pending());
    }
    Ok(())
}
pub fn validate_existing(t: &Training<'_>) -> Result<(), ApiError> {
    let records = records(t)?;
    if records.is_empty() {
        return Ok(());
    }
    supported(t)?;
    for record in records {
        parsed(record)?;
    }
    Ok(())
}

pub fn save(t: &Training<'_>, body: &Value) -> Result<Value, ApiError> {
    let title = body["title"].as_str().unwrap_or("").trim();
    if title.is_empty() || title.chars().count() > 160 {
        return Err(input_error("请填写 1–160 字的具体目标"));
    }
    let mut kind = match body.get("kind") {
        None => "custom",
        Some(Value::String(v)) => v.as_str(),
        _ => return Err(input_error("目标类型无效")),
    };
    let detected = CF_TITLE
        .captures(title)
        .filter(|_| kind == "custom")
        .map(|c| c[1].parse::<i64>().unwrap());
    if detected.is_some() {
        kind = "cf";
    }
    if !["cf", "xcpc", "lanqiao", "custom"].contains(&kind) {
        return Err(input_error("目标类型无效"));
    }
    let end = date(text(body, "deadline"))
        .ok_or_else(|| input_error("请填写具体截止日期、起点和每日可用分钟数"))?;
    let baseline = supplied(body, "currentRating", 1000)?;
    let minutes = supplied(body, "dailyMinutes", 90)?;
    let target = match detected {
        Some(v) => v,
        None => supplied(
            body,
            "targetRating",
            match kind {
                "cf" => 2200,
                "xcpc" => 2000,
                _ => 1800,
            },
        )?,
    };
    let total = if kind == "custom" {
        supplied(body, "totalProblems", 100)?
    } else {
        ceil_div(target.saturating_sub(baseline).max(0), 100)
            .saturating_mul(30)
            .max(30)
    };
    let today = local_date(t.now);
    if !(today..=today + Duration::days(1826)).contains(&end) {
        return Err(input_error("截止日期须在今天至五年内；过期目标请调整日期"));
    }
    if !(0..=4000).contains(&baseline)
        || !(200..=4000).contains(&target)
        || !(15..=720).contains(&minutes)
        || !(1..=10000).contains(&total)
    {
        return Err(input_error(
            "起点须为 0–4000，目标参考值为 200–4000，每日 15–720 分钟，自定义题量 1–10000",
        ));
    }
    supported(t)?;
    let identity = match body.get("id") {
        None | Some(Value::Null) => format!("goal-{}", uuid::Uuid::new_v4().simple()),
        Some(Value::String(v)) if v.is_empty() => format!("goal-{}", uuid::Uuid::new_v4().simple()),
        Some(Value::String(v)) if v.len() <= 512 => v.clone(),
        _ => return Err(input_error("目标编号无效")),
    };
    let previous: Option<String> = t
        .personal
        .db
        .query_row(
            "SELECT created_at FROM goals WHERE id=?",
            [&identity],
            |r| r.get(0),
        )
        .optional()?;
    if truth(&body["id"]) && previous.is_none() {
        return Err(ApiError::missing("目标不存在"));
    }
    let active = records(t)?;
    for record in active.iter().filter(|record| record["id"] != identity) {
        parsed(record.clone())?;
    }
    if previous.is_none() && active.len() >= 10 {
        return Err(input_error("最多同时规划 10 个目标，请先归档已结束目标"));
    }
    let start = previous.unwrap_or_else(|| stamp(t.now));
    required_at(&start)?;
    let config = json!({"title":title,"kind":kind,"deadline":end.to_string(),"currentRating":baseline,"targetRating":target,"dailyMinutes":minutes,"totalProblems":total,"minutesPerProblem":if ["cf","xcpc"].contains(&kind){60}else{45},"assumption":if kind=="custom"{"按你填写的题量安排。"}else{"参考值每提高 100，安排 30 道新题；最低 30 题。"},"disclaimer":NOTICE});
    storage::atomic(&t.personal.db, |db| {
        db.execute("INSERT INTO goals(id,created_at,config,archived) VALUES(?,?,?,0) ON CONFLICT(id) DO UPDATE SET config=excluded.config",params![identity,start,config.to_string()])?;
        list(t, true)
    })
}
pub fn archive(t: &Training<'_>, identity: &str) -> Result<Value, ApiError> {
    let exists: bool = t.personal.db.query_row(
        "SELECT EXISTS(SELECT 1 FROM goals WHERE id=?)",
        [identity],
        |r| r.get(0),
    )?;
    if !exists {
        return Err(ApiError::missing("目标不存在"));
    }
    supported(t)?;
    for record in records(t)?
        .into_iter()
        .filter(|record| record["id"] != identity)
    {
        parsed(record)?;
    }
    storage::atomic(&t.personal.db, |db| {
        db.execute("UPDATE goals SET archived=1 WHERE id=?", [identity])?;
        list(t, false)
    })
}

pub(crate) fn public_rows(
    t: &Training<'_>,
) -> Result<(Vec<Value>, HashMap<String, Value>), ApiError> {
    let mut query = t
        .catalogue
        .db
        .prepare_cached("SELECT compact FROM catalogue ORDER BY position")?;
    let rows = query
        .query_map([], |r| r.get::<_, String>(0))?
        .map(|row| Ok(serde_json::from_str::<Value>(&row?)?))
        .collect::<Result<Vec<_>, ApiError>>()?;
    if rows.iter().any(|row| text(row, "id").is_empty()) {
        return Err(invalid());
    }
    let mut metadata = rows
        .iter()
        .map(|row| (text(row, "id").to_owned(), row.clone()))
        .collect::<HashMap<_, _>>();
    let mut aliases = t
        .catalogue
        .db
        .prepare_cached("SELECT id,canonical FROM aliases ORDER BY id")?;
    for alias in aliases.query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))? {
        let (alias, canonical) = alias?;
        if !metadata.contains_key(&alias) {
            if let Some(row) = metadata.get(&canonical) {
                let mut row = row.clone();
                row["id"] = json!(alias);
                metadata.insert(alias, row);
            }
        }
    }
    Ok((rows, metadata))
}
fn activate(t: &Training<'_>, identity: &str) -> Result<(), ApiError> {
    let ids = json!(t.ids(identity)?).to_string();
    let today = local_date(t.now);
    for row in t.personal.rows("SELECT removed_at FROM training WHERE id IN(SELECT value FROM json_each(?)) AND active=0 AND removed_at IS NOT NULL",[ids])?.as_array().unwrap(){if local_date(required_at(text(row,"removed_at"))?)>=today{return Ok(());}}
    t.activate_edited(identity, false)
}
fn selection(raw: &str) -> Result<Vec<String>, ApiError> {
    let ids: Vec<String> = serde_json::from_str(raw)?;
    if ids.len() > 20000 || ids.iter().any(|id| id.is_empty() || id.len() > 512) {
        return Err(invalid());
    }
    Ok(ids)
}
fn empty(t: &Training<'_>) -> Value {
    json!({"goals":[],"date":day(t.now),"contestPlan":{"contests":[],"total":0,"goalCount":0},"goalTasks":[]})
}
pub fn list(t: &Training<'_>, assign: bool) -> Result<Value, ApiError> {
    let records = records(t)?;
    if records.is_empty() {
        return Ok(empty(t));
    }
    supported(t)?;
    let goals = records
        .into_iter()
        .map(parsed)
        .collect::<Result<Vec<_>, _>>()?;
    storage::atomic(&t.personal.db, |_| list_inner(t, assign, &goals))
}
fn list_inner(t: &Training<'_>, assign: bool, goals: &[Goal]) -> Result<Value, ApiError> {
    let review = crate::reviews::plan(t)?;
    let (rows, metadata) = public_rows(t)?;
    let mut accepted = HashMap::<String, DateTime<Utc>>::new();
    for record in t.personal.rows("SELECT problem_id,submitted_at FROM submissions WHERE mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid",[])?.as_array().unwrap(){let identity=text(record,"problem_id");let key=metadata.get(identity).map(key).unwrap_or_else(||identity.into());let at=required_at(text(record,"submitted_at"))?;accepted.entry(key).or_insert(at);}
    let today = local_date(t.now);
    let today_text = today.to_string();
    let assignments = t
        .personal
        .rows(
            "SELECT * FROM goal_daily_assignments WHERE day=?",
            [&today_text],
        )?
        .as_array()
        .unwrap()
        .iter()
        .map(|row| (text(row, "goal_id").to_owned(), row.clone()))
        .collect::<HashMap<_, _>>();
    let mut owners = HashMap::<String, String>::new();
    for goal in goals {
        if let Some(saved) = assignments.get(text(&goal.record, "id")) {
            for identity in selection(text(saved, "ids"))? {
                if let Some(row) = metadata.get(&identity) {
                    owners
                        .entry(key(row))
                        .or_insert_with(|| text(&goal.record, "id").into());
                }
            }
        }
    }
    let review_minutes = count(&review, "minutes")?;
    let available = count(&review, "newMinutes")?;
    let paused = truth(&review["reviewOnly"]);
    let mut new_budget = (review_minutes != 0).then_some(available);
    let mut result = Vec::new();
    let mut daily_selections = HashMap::<String, Vec<Value>>::new();
    for goal in goals {
        let config = &goal.config;
        let id = text(&goal.record, "id");
        let first = local_date(goal.start);
        let days = (goal.end - first).num_days().saturating_add(1).max(1);
        let total = count(config, "totalProblems")?;
        let cost = count(config, "minutesPerProblem")?;
        let evidence = accepted
            .values()
            .filter(|at| goal.start < **at && **at <= t.now && local_date(**at) <= goal.end)
            .copied()
            .collect::<Vec<_>>();
        let done = evidence.len() as i64;
        let elapsed = (today - first).num_days().clamp(0, days);
        let expected = ceil_div(total * elapsed, days);
        let due = ceil_div(total * (elapsed + 1).min(days), days);
        let daily = (due - expected).max(0);
        let all_today_done = evidence
            .iter()
            .filter(|at| local_date(**at) == today)
            .count() as i64;
        let left = ((goal.end - today).num_days() + 1).max(0);
        let remaining = (total - done).max(0);
        let weekly = ceil_div(remaining * left.min(7), left.max(1));
        let capacity =
            ((left * count(config, "dailyMinutes")?) as f64 * 0.7 / cost as f64).floor() as i64;
        let mut warnings = Vec::<String>::new();
        if today > goal.end && remaining != 0 {
            warnings.push("截止日期已过，训练题量尚未完成。请复盘并调整目标。".into());
        }
        if remaining > capacity {
            warnings.push(format!("时间压力：剩余 {remaining} 题超出预计容量 {capacity} 题，建议延后截止日期或调整目标。"));
        }
        if done < expected {
            warnings.push(format!(
                "进度落后 {} 题；本周需安排约 {weekly} 题。",
                expected - done
            ));
        }
        if left <= 14
            && config["kind"] != "custom"
            && count(config, "targetRating")? - count(config, "currentRating")? >= 300
        {
            warnings.push("期限明显偏紧，短期题量不能替代持续参赛与能力积累。".into());
        }
        if config["kind"] == "cf"
            && count(config, "targetRating")? <= count(config, "currentRating")?
        {
            warnings
                .push("填写的起点已达到目标参考值，可改为巩固目标；评级结果需原站核验。".into());
        }
        let weights = if config["kind"] == "xcpc" {
            [2, 2, 4, 2]
        } else {
            [4, 3, 2, 1]
        };
        let mut amounts = [if weekly >= 4 { 1_i64 } else { 0 }; 4];
        for _ in 0..(weekly - amounts.iter().sum::<i64>()).max(0) {
            let best = (0..4)
                .max_by(|a, b| {
                    let order = (weights[*a] as f64 / (amounts[*a] + 1) as f64)
                        .total_cmp(&(weights[*b] as f64 / (amounts[*b] + 1) as f64));
                    order.then_with(|| b.cmp(a))
                })
                .unwrap();
            amounts[best] += 1;
        }
        let lower = count(config, "currentRating")? < 1400;
        let ranges = if lower {
            ["A–D", "A–D", "A–D", "基础题"]
        } else {
            ["C–F", "C–F", "C–F", "提高题"]
        };
        let contest_plan = (0..4)
            .map(|i| json!({"contest":FAMILIES[i].0,"target":amounts[i],"problems":ranges[i]}))
            .collect::<Vec<_>>();
        let before_today = (total - done + all_today_done).max(0);
        let mut target = if left != 0 {
            8.min(before_today)
                .min(daily.max(ceil_div(before_today, left.max(1))))
        } else {
            0
        };
        if review_minutes != 0 {
            target = target.min(available / cost);
        }
        let saved = assignments.get(id);
        let original = match saved {
            Some(saved) => selection(text(saved, "ids"))?,
            None => Vec::new(),
        };
        if saved.is_some_and(|saved| {
            !saved["target"].is_null()
                && saved["target"]
                    .as_i64()
                    .is_none_or(|target| !(0..=20000).contains(&target))
        }) {
            return Err(invalid());
        }
        let mut seen = HashSet::new();
        let mut selected = original
            .iter()
            .filter_map(|identity| metadata.get(identity))
            .filter(|row| {
                let key = key(row);
                if owners.get(&key).map(String::as_str) != Some(id) || seen.contains(&key) {
                    false
                } else {
                    seen.insert(key);
                    true
                }
            })
            .cloned()
            .collect::<Vec<_>>();
        let paused_empty = saved.is_some_and(|saved| saved["target"] == 0)
            && original.is_empty()
            && !paused
            && target > 0;
        if let Some(saved) = saved {
            if !saved["target"].is_null() && !paused_empty {
                target = count(saved, "target")?;
            }
        }
        if paused {
            target = 0;
            selected.clear();
        } else if review_minutes != 0 {
            target = target.min(available / cost);
            selected.truncate(target as usize);
        }
        if let Some(budget) = new_budget {
            target = target.min(budget / cost);
            selected.truncate(target as usize);
        }
        let repairing = paused_empty
            || saved.is_none()
            || saved.is_some_and(|saved| saved["target"].is_null())
            || selected.len() != original.len();
        if repairing && !paused {
            let mut candidates = rows
                .iter()
                .filter(|row| !truth(&row["catalogHidden"]) && !accepted.contains_key(&key(row)))
                .collect::<Vec<_>>();
            let baseline = count(config, "currentRating")? as f64;
            let score = |row: &Value| {
                let preferred = (config["kind"] == "lanqiao"
                    && text(row, "contest").contains("蓝桥"))
                    || (config["kind"] == "cf" && row["platform"] == "Codeforces")
                    || (config["kind"] == "xcpc" && PATTERNS[5].is_match(text(row, "contest")));
                (
                    !preferred,
                    row["difficulty"]
                        .as_f64()
                        .map(|d| (d - baseline - 150.).abs())
                        .unwrap_or(500.),
                )
            };
            candidates.sort_by(|a, b| {
                let a_score = score(a);
                let b_score = score(b);
                a_score
                    .0
                    .cmp(&b_score.0)
                    .then(a_score.1.total_cmp(&b_score.1))
                    .then(text(a, "id").cmp(text(b, "id")))
            });
            for row in candidates {
                if selected.len() >= target as usize {
                    break;
                }
                let key = key(row);
                if seen.contains(&key) || owners.contains_key(&key) {
                    continue;
                }
                owners.insert(key.clone(), id.into());
                seen.insert(key);
                selected.push(row.clone());
            }
            if assign && (paused_empty || !(saved.is_some() && review_minutes != 0)) {
                let ids = selected
                    .iter()
                    .map(|row| text(row, "id"))
                    .collect::<Vec<_>>();
                t.personal.db.execute("INSERT INTO goal_daily_assignments(goal_id,day,ids,target) VALUES(?,?,?,?) ON CONFLICT(goal_id,day) DO UPDATE SET ids=excluded.ids,target=excluded.target",params![id,today_text,json!(ids).to_string(),target])?;
                for row in &selected {
                    if !original.iter().any(|id| row["id"] == *id) {
                        activate(t, text(row, "id"))?;
                    }
                }
            }
        }
        let today_done = selected
            .iter()
            .filter(|row| {
                accepted
                    .get(&key(row))
                    .is_some_and(|at| goal.start < *at && *at <= t.now && local_date(*at) == today)
            })
            .count();
        if let Some(budget) = new_budget.as_mut() {
            *budget = (*budget - selected.len() as i64 * cost).max(0);
        }
        let problems = selected
            .iter()
            .filter(|row| !accepted.contains_key(&key(row)))
            .map(|row| fields(row, &["id", "title", "contest", "difficulty"]))
            .collect::<Vec<_>>();
        daily_selections.insert(id.into(), selected);
        let mut value = config.clone();
        for (key,v) in json!({"id":id,"createdAt":goal.record["created_at"],"progress":done,"remaining":remaining,"remainingDays":left,"weeklyTarget":weekly,"weeklyPlan":[],"contestPlan":contest_plan,"capacity":capacity,"warnings":warnings,"workloadCompleted":done>=total,"dailyTask":{"date":today_text,"target":target,"progress":today_done,"completed":today_done as i64>=target,"problems":problems}}).as_object().unwrap(){value[key]=v.clone();}
        result.push(value);
    }
    let tasks = tasks(
        t,
        &result,
        &rows,
        &metadata,
        &accepted,
        &daily_selections,
        assign,
        &review,
    )?;
    Ok(
        json!({"goals":result,"date":today_text,"notice":NOTICE,"contestPlan":shared_contest_plan(&result,&rows,&accepted),"goalTasks":tasks}),
    )
}

fn shared_contest_plan(
    goals: &[Value],
    rows: &[Value],
    accepted: &HashMap<String, DateTime<Utc>>,
) -> Value {
    let mut merged = Vec::<Value>::new();
    let mut positions = HashMap::<String, usize>::new();
    for goal in goals
        .iter()
        .filter(|goal| !truth(&goal["workloadCompleted"]))
    {
        for item in goal["contestPlan"].as_array().unwrap() {
            let target = item["target"].as_i64().unwrap();
            if target <= 0 {
                continue;
            }
            let name = text(item, "contest");
            let index = *positions.entry(name.into()).or_insert_with(|| {
                let mut saved = item.clone();
                saved["goalIds"] = json!([]);
                saved["referenceRating"] = json!(0);
                merged.push(saved);
                merged.len() - 1
            });
            let saved = &mut merged[index];
            saved["target"] = json!(saved["target"].as_i64().unwrap().max(target));
            if goal["currentRating"].as_i64().unwrap_or(0)
                >= saved["referenceRating"].as_i64().unwrap()
            {
                saved["problems"] = item["problems"].clone();
                saved["referenceRating"] = goal["currentRating"].clone();
            }
            saved["goalIds"]
                .as_array_mut()
                .unwrap()
                .push(goal["id"].clone());
        }
    }
    let mut chosen = accepted.keys().cloned().collect::<HashSet<_>>();
    for item in &mut merged {
        let index = FAMILIES
            .iter()
            .position(|family| family.0 == text(item, "contest"))
            .unwrap();
        let mut candidates = rows
            .iter()
            .filter(|row| {
                family_matches(row, index, false)
                    && !chosen.contains(&key(row))
                    && eligible_letter(row, text(item, "problems"), false)
            })
            .collect::<Vec<_>>();
        candidates.sort_by(|a, b| text(a, "id").cmp(text(b, "id")));
        let date_key = |row: &Value| {
            let value = row
                .get("contestDate")
                .filter(|v| truth(v))
                .or_else(|| row.get("startedAt").filter(|v| truth(v)));
            value.map(string).unwrap_or_default()
        };
        candidates.sort_by_key(|row| std::cmp::Reverse(date_key(row)));
        let mut questions = Vec::new();
        for row in candidates {
            let key = key(row);
            if !chosen.insert(key) {
                continue;
            }
            questions.push(fields(
                row,
                &[
                    "id",
                    "title",
                    "contest",
                    "problem",
                    "difficulty",
                    "difficultyEstimated",
                ],
            ));
            if questions.len() as i64 >= item["target"].as_i64().unwrap() {
                break;
            }
        }
        item["questions"] = json!(questions);
    }
    json!({"total":merged.iter().map(|item|item["target"].as_i64().unwrap()).sum::<i64>(),"goalCount":goals.iter().filter(|goal|!truth(&goal["workloadCompleted"])).count(),"contests":merged})
}

fn include_task(
    tasks: &mut Vec<Value>,
    positions: &mut HashMap<String, usize>,
    row: &Value,
    goal: &Value,
    source: &str,
    accepted: &HashMap<String, DateTime<Utc>>,
    maximum: Option<usize>,
) {
    let identity = key(row);
    if !positions.contains_key(&identity) && maximum.is_some_and(|maximum| tasks.len() >= maximum) {
        return;
    }
    let index = *positions.entry(identity.clone()).or_insert_with(|| {
        let mut task = fields(
            row,
            &[
                "id",
                "title",
                "contest",
                "problem",
                "platform",
                "difficulty",
                "difficultyEstimated",
            ],
        );
        task["accepted"] = json!(accepted.contains_key(&identity));
        task["goalTitles"] = json!([]);
        task["sources"] = json!([]);
        tasks.push(task);
        tasks.len() - 1
    });
    let task = &mut tasks[index];
    if !task["goalTitles"]
        .as_array()
        .unwrap()
        .contains(&goal["title"])
    {
        task["goalTitles"]
            .as_array_mut()
            .unwrap()
            .push(goal["title"].clone());
    }
    if !task["sources"].as_array().unwrap().contains(&json!(source)) {
        task["sources"].as_array_mut().unwrap().push(json!(source));
    }
}
fn tasks(
    t: &Training<'_>,
    goals: &[Value],
    rows: &[Value],
    metadata: &HashMap<String, Value>,
    accepted: &HashMap<String, DateTime<Utc>>,
    daily: &HashMap<String, Vec<Value>>,
    assign: bool,
    review: &Value,
) -> Result<Vec<Value>, ApiError> {
    let minutes = count(review, "minutes")?;
    let available = count(review, "newMinutes")?;
    let cost = goals
        .iter()
        .map(|goal| goal["minutesPerProblem"].as_i64().unwrap_or(45))
        .min()
        .unwrap_or(45);
    if truth(&review["reviewOnly"]) || minutes != 0 && available < cost {
        return Ok(Vec::new());
    }
    let maximum = (minutes != 0).then_some((available / cost) as usize);
    let mut events = Vec::<(String, String, Vec<&Value>)>::new();
    let mut event_positions = HashMap::<(String, String), usize>::new();
    for row in rows.iter().filter(|row| !truth(&row["catalogHidden"])) {
        let url = canonical_url(text(row, "url")).unwrap_or_default();
        let event = if row["platform"] == "洛谷" {
            format!(
                "luogu/{}",
                row.get("contestId")
                    .filter(|value| truth(value))
                    .or_else(|| row.get("contest"))
                    .map(string)
                    .unwrap_or_default()
            )
        } else {
            url.rsplit_once('/')
                .map(|value| value.0.to_owned())
                .unwrap_or(url)
        };
        if event.is_empty() {
            continue;
        }
        let site = text(row, "platform").to_owned();
        let index = *event_positions
            .entry((site.clone(), event.clone()))
            .or_insert_with(|| {
                events.push((site, event, Vec::new()));
                events.len() - 1
            });
        events[index].2.push(row);
    }
    let persisted = t
        .personal
        .rows(
            "SELECT * FROM practice_sets WHERE id LIKE 'goal-contest:%'",
            [],
        )?
        .as_array()
        .unwrap()
        .clone();
    let mut tasks = Vec::new();
    let mut positions = HashMap::new();
    for goal in goals
        .iter()
        .filter(|goal| !truth(&goal["workloadCompleted"]))
    {
        let id = text(goal, "id");
        if let Some(selected) = daily.get(id) {
            for row in selected {
                include_task(
                    &mut tasks,
                    &mut positions,
                    row,
                    goal,
                    "每日目标",
                    accepted,
                    maximum,
                );
            }
        }
        let prefix = format!("goal-contest:{id}:");
        for group in persisted
            .iter()
            .filter(|group| text(group, "id").starts_with(&prefix))
        {
            for identity in selection(text(group, "ids"))? {
                if let Some(row) = metadata.get(&identity) {
                    include_task(
                        &mut tasks,
                        &mut positions,
                        row,
                        goal,
                        "比赛目标",
                        accepted,
                        maximum,
                    );
                }
            }
        }
        for requirement in goal["contestPlan"].as_array().unwrap() {
            if minutes != 0 || count(requirement, "target")? <= 0 {
                continue;
            }
            let family = FAMILIES
                .iter()
                .position(|family| family.0 == text(requirement, "contest"))
                .ok_or_else(invalid)?;
            let mut matching = Vec::new();
            for (_, event, roster) in events.iter().filter(|(site, _, roster)| {
                site == FAMILIES[family].1 && family_matches(roster[0], family, true)
            }) {
                let end = roster
                    .iter()
                    .filter_map(|row| {
                        row.get("endedAt")
                            .filter(|value| truth(value))
                            .or_else(|| row.get("contestDate").filter(|value| truth(value)))
                            .or_else(|| row.get("startedAt"))
                            .and_then(Value::as_str)
                            .and_then(at)
                    })
                    .max();
                let added = roster
                    .iter()
                    .filter_map(|row| row["addedAt"].as_str().and_then(at))
                    .max()
                    .or(end);
                if end.is_some_and(|end| end > t.now) {
                    continue;
                }
                let since = (t.now - Duration::days(7)).max(required_at(text(goal, "createdAt"))?);
                if let Some(added) = added {
                    if since <= added && added <= t.now {
                        matching.push((added, event, roster));
                    }
                }
            }
            matching.sort_by(|a, b| b.0.cmp(&a.0));
            for (_, event, roster) in matching.into_iter().take(4) {
                let mut roster = roster.clone();
                roster.sort_by(|a, b| {
                    problem_letter(a)
                        .cmp(&problem_letter(b))
                        .then(text(a, "id").cmp(text(b, "id")))
                });
                let mut seen = HashSet::new();
                let selected = roster
                    .into_iter()
                    .filter(|row| {
                        eligible_letter(row, text(requirement, "problems"), true)
                            && seen.insert(key(row))
                    })
                    .take(8.min(count(requirement, "target")? as usize))
                    .collect::<Vec<_>>();
                if selected.is_empty() {
                    continue;
                }
                let digest = format!("{:x}", Sha256::digest(event.as_bytes()));
                let group_id = format!("{prefix}{}", &digest[..20]);
                let saved = persisted.iter().find(|record| record["id"] == group_id);
                let old_ids = match saved {
                    Some(saved) => selection(text(saved, "ids"))?,
                    None => Vec::new(),
                };
                let mut seen = HashSet::new();
                let ids = old_ids
                    .iter()
                    .cloned()
                    .chain(selected.iter().map(|row| text(row, "id").to_owned()))
                    .filter(|id| seen.insert(id.clone()))
                    .collect::<Vec<_>>();
                if assign && ids != old_ids {
                    let name = format!(
                        "目标题目 · {} · {} · {}",
                        text(goal, "title"),
                        text(selected[0], "contest"),
                        &group_id[group_id.len() - 8..]
                    );
                    t.personal.db.execute("INSERT INTO practice_sets(id,name,ids,created_at) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET ids=excluded.ids",params![group_id,name,json!(ids).to_string(),stamp(t.now)])?;
                    for row in &selected {
                        if !old_ids.iter().any(|id| row["id"] == *id) {
                            activate(t, text(row, "id"))?;
                        }
                    }
                }
                for row in selected {
                    include_task(
                        &mut tasks,
                        &mut positions,
                        row,
                        goal,
                        "比赛目标",
                        accepted,
                        maximum,
                    );
                }
            }
        }
    }
    tasks.sort_by(|a, b| {
        truth(&a["accepted"])
            .cmp(&truth(&b["accepted"]))
            .then(text(a, "contest").cmp(text(b, "contest")))
            .then_with(|| {
                let value = |row: &Value| {
                    row.get("problem")
                        .filter(|v| truth(v))
                        .map(string)
                        .unwrap_or_default()
                };
                value(a).cmp(&value(b))
            })
    });
    Ok(tasks)
}
