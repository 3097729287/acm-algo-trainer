//! Exact public replay rosters. Missing statements retain their original place;
//! origin VP and account-bound reward authority are never inferred locally.
use crate::{api::ApiError, contest_setup, identity::canonical_url, training::Training};
use regex::Regex;
use serde_json::{Value, json};
use std::{cmp::Ordering, collections::HashMap, sync::LazyLock};
use url::Url;
use uuid::Uuid;

fn text<'a>(value: &'a Value, name: &str) -> &'a str {
    value[name].as_str().unwrap_or("")
}
fn truth(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::Number(v) => v.as_f64() != Some(0.),
        Value::String(v) => !v.is_empty(),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
static MIRRORS: LazyLock<HashMap<String, String>> = LazyLock::new(|| {
    let values: HashMap<String, String> =
        serde_json::from_str(include_str!("../../backend/resources/replay-mirrors.json"))
            .expect("reviewed public replay mirrors");
    values
        .into_iter()
        .filter_map(|(a, b)| Some((canonical_url(&a)?, canonical_url(&b)?)))
        .collect()
});
static TOKENS: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"[0-9]+|[^0-9]+").unwrap());
static LETTER: LazyLock<Regex> = LazyLock::new(|| Regex::new(r"^[A-Z][0-9]{0,2}$").unwrap());
static URL_PATTERNS: LazyLock<Vec<(&str, Regex)>> = LazyLock::new(|| {
    [
        (
            "codeforces.com",
            r"/(?:contest|gym)/\d+/problem/[A-Za-z]\d?|/problemset/problem/\d+/[A-Za-z]\d?",
        ),
        (
            "www.codeforces.com",
            r"/(?:contest|gym)/\d+/problem/[A-Za-z]\d?|/problemset/problem/\d+/[A-Za-z]\d?",
        ),
        ("atcoder.jp", r"/contests/[\w-]+/tasks/[\w-]+"),
        (
            "ac.nowcoder.com",
            r"/acm/(?:contest/\d+/[A-Za-z]\d?|problem/[1-9]\d{0,19})",
        ),
        ("www.luogu.com.cn", r"/problem/[A-Za-z0-9_]+"),
        ("luogu.com.cn", r"/problem/[A-Za-z0-9_]+"),
        ("qoj.ac", r"/problem/[1-9]\d*"),
    ]
    .into_iter()
    .map(|(host, pattern)| (host, Regex::new(&format!("^(?:{pattern})$")).unwrap()))
    .collect()
});

pub struct ReplayPaper {
    pub plan: Value,
    pub slots: Vec<Value>,
}
fn source_supported(raw: &str) -> bool {
    let Ok(url) = Url::parse(raw) else {
        return false;
    };
    url.scheme() == "https"
        && url.username().is_empty()
        && url.password().is_none()
        && url.port_or_known_default() == Some(443)
        && url.query().is_none_or(str::is_empty)
        && URL_PATTERNS
            .iter()
            .any(|(host, pattern)| url.host_str() == Some(*host) && pattern.is_match(url.path()))
}
pub(crate) fn ready(row: &Value) -> Result<bool, ApiError> {
    if truth(&row["catalogHidden"])
        || matches!(
            text(row, "problemType"),
            "communication" | "output-only" | "attachment"
        )
        || !source_supported(text(row, "url"))
    {
        return Ok(false);
    }
    let Some(ready) = row["catalogReplayReady"].as_bool() else {
        return Err(ApiError::pending());
    };
    // A stale school import needs a fresh compiled integrity proof, rather
    // than promoting an ordinary sample flag to native submission readiness.
    if !ready && truth(&row["schoolTraining"]) && row["catalogContentReady"] == true {
        return Err(ApiError::pending());
    }
    Ok(ready)
}
fn visible(row: &Value) -> bool {
    !truth(&row["catalogHidden"])
        || truth(&row["schoolTraining"])
        || row["statementRetirementPolicy"] == "public-statement-audit-v1"
            && !truth(&row["statementPriorVisibility"]["catalogHidden"])
}
fn preferred(row: &Value) -> (bool, bool, bool) {
    (
        !truth(&row["catalogContentReady"]),
        !matches!(text(row, "platform"), "Codeforces" | "codeforces"),
        row["source"] == "remote",
    )
}
pub(crate) fn roster(t: &Training<'_>, name: &str) -> Result<Vec<Value>, ApiError> {
    let mut groups: Vec<Vec<Value>> = vec![];
    let mut positions = HashMap::<String, usize>::new();
    for row in t.catalogue.contest_rows(name)? {
        if !visible(&row)
            || matches!(
                text(&row, "source"),
                "luogu-training" | "algorithm-lab" | "algorithm-lab-curation"
            )
            || truth(&row["labTopic"])
        {
            continue;
        }
        let key = canonical_url(text(&row, "url")).unwrap_or_else(|| text(&row, "id").into());
        let key = MIRRORS.get(&key).cloned().unwrap_or(key);
        let next = groups.len();
        let index = *positions.entry(key).or_insert(next);
        if index == groups.len() {
            groups.push(vec![]);
        }
        groups[index].push(row);
    }
    let mut rows = vec![];
    for group in groups {
        let mut selected = group
            .iter()
            .min_by_key(|row| preferred(row))
            .unwrap()
            .clone();
        let mut tags = vec![];
        for row in &group {
            let empty = vec![];
            for tag in row
                .get("tags")
                .map(|v| v.as_array().ok_or_else(ApiError::pending))
                .transpose()?
                .unwrap_or(&empty)
            {
                if !tag.is_string() {
                    return Err(ApiError::pending());
                }
                if !tags.contains(tag) {
                    tags.push(tag.clone());
                }
            }
        }
        selected["tags"] = json!(tags);
        rows.push(selected);
    }
    rows.sort_by(|a, b| natural(text(a, "problem"), text(b, "problem")));
    Ok(rows)
}
fn natural(a: &str, b: &str) -> Ordering {
    let tokens = |value: &str| {
        TOKENS
            .find_iter(value)
            .map(|m| m.as_str().to_owned())
            .collect::<Vec<_>>()
    };
    let left = tokens(a);
    let right = tokens(b);
    for (a, b) in left.iter().zip(&right) {
        let a_number = a.bytes().all(|v| v.is_ascii_digit());
        let b_number = b.bytes().all(|v| v.is_ascii_digit());
        let order = match (a_number, b_number) {
            (true, true) => {
                let a = a.trim_start_matches('0');
                let b = b.trim_start_matches('0');
                a.len().cmp(&b.len()).then_with(|| a.cmp(b))
            }
            (true, false) => Ordering::Less,
            (false, true) => Ordering::Greater,
            (false, false) => a.to_uppercase().cmp(&b.to_uppercase()),
        };
        if order != Ordering::Equal {
            return order;
        }
    }
    left.len().cmp(&right.len())
}
pub(crate) fn requires_origin_vp(rows: &[Value]) -> bool {
    static ORIGINAL: LazyLock<Regex> =
        LazyLock::new(|| Regex::new(r"^/(contest|gym)/(\d+)/problem/[A-Za-z]\d?$").unwrap());
    let mut event = None;
    for row in rows {
        let Ok(url) = Url::parse(text(row, "url")) else {
            return false;
        };
        if url.scheme() != "https"
            || !matches!(
                url.host_str(),
                Some("codeforces.com" | "www.codeforces.com")
            )
        {
            return false;
        }
        let Some(capture) = ORIGINAL.captures(url.path()) else {
            return false;
        };
        let identity = format!("{}:{}", &capture[1], &capture[2]);
        if event.as_ref().is_some_and(|value| *value != identity) {
            return false;
        }
        event = Some(identity);
    }
    event.is_some()
}
pub fn preview(t: &Training<'_>, body: &Value) -> Result<ReplayPaper, ApiError> {
    let name = body["contest"]
        .as_str()
        .filter(|name| !name.is_empty() && name.chars().count() <= 512)
        .ok_or_else(|| ApiError::bad("请选择已收录比赛"))?;
    let mut rows = roster(t, name)?;
    if rows.is_empty() {
        return Err(ApiError::missing("这场比赛尚未收录"));
    }
    let events = t.catalogue.replay_events(t.personal)?;
    let known = events["events"]
        .as_array()
        .unwrap()
        .iter()
        .find(|event| event["name"] == name)
        .ok_or_else(ApiError::pending)?;
    if known["count"].as_u64() != Some(rows.len() as u64) {
        return Err(ApiError::pending());
    }
    let mut info = json!({});
    for field in [
        "name",
        "count",
        "expectedCount",
        "complete",
        "duration",
        "durationSource",
        "rules",
    ] {
        info[field] = known[field].clone();
    }
    let mut available = 0;
    let mut missing = vec![];
    let mut slots = vec![];
    for (position, row) in rows.iter_mut().enumerate() {
        let available_here = ready(row)?;
        if available_here {
            available += 1;
        } else {
            missing.push(row["problem"].clone());
        }
        let label = row["contestLetter"]
            .as_str()
            .filter(|s| !s.is_empty())
            .map(str::to_owned)
            .unwrap_or_else(|| {
                if LETTER.is_match(text(row, "problem")) {
                    text(row, "problem").into()
                } else {
                    char::from_u32(65 + position as u32)
                        .unwrap_or('?')
                        .to_string()
                }
            });
        slots.push(json!({"letter":label,"id":row["id"],"title":row["title"],"difficulty":row["difficulty"],"tags":row["tags"],"judgeScope":if available_here{"official"}else{"unsupported"},"statementAvailable":available_here}));
    }
    if available == 0 {
        return Err(ApiError::new(
            422,
            "NO_REPLAY_STATEMENTS",
            "这场比赛暂无可打开的题目，请先补全题面",
        ));
    }
    info["availableCount"] = json!(available);
    info["missingProblems"] = json!(missing);
    if !missing.is_empty() {
        info["complete"] = false.into();
    }
    let duration = body
        .get("duration")
        .map(crate::goals::integer)
        .unwrap_or_else(|| known["duration"].as_i64())
        .ok_or_else(|| ApiError::bad("重现赛时长无效"))?;
    if !(1..=1440).contains(&duration) {
        return Err(ApiError::bad("时长须为 1–1440 分钟"));
    }
    let mut rules_body = body.clone();
    rules_body["strategy"] = "comprehensive".into();
    rules_body["tags"] = json!([]);
    if body.get("rules").is_none() {
        rules_body["rules"] = info["rules"].clone();
    }
    // Replay ignores ordinary training filters, exactly as the legacy route.
    for field in ["platform", "excludeSolved", "reviewedOnly", "topic"] {
        rules_body.as_object_mut().unwrap().remove(field);
    }
    let rules = contest_setup::options(&rules_body)?;
    // Complete original-duration papers have an owner-bound reward envelope.
    // Until account/reward migration, retain this authority boundary rather
    // than silently dropping the policy or manufacturing a local owner.
    let originals = rows
        .iter()
        .map(|row| text(row, "url").trim_end_matches('/').to_owned())
        .collect::<std::collections::HashSet<_>>();
    if info["complete"] != false
        && rows.len() >= 2
        && info["duration"] == duration
        && originals.len() == rows.len()
    {
        return Err(ApiError::pending());
    }
    let mut config = json!({"strategy":"replay","contest":name,"tags":[],"platform":"","excludeSolved":false,"reviewedOnly":false});
    for field in ["rules", "wrongPenalty", "compilePenalty"] {
        config[field] = rules[field].clone();
    }
    let ratings = rows
        .iter()
        .map(|row| &row["difficulty"])
        .filter(|v| v.is_number())
        .collect::<Vec<_>>();
    let order = |a: &&Value, b: &&Value| a.as_f64().unwrap().total_cmp(&b.as_f64().unwrap());
    let min = ratings
        .iter()
        .copied()
        .min_by(order)
        .cloned()
        .unwrap_or(Value::Null);
    let max = ratings
        .iter()
        .copied()
        .max_by(order)
        .cloned()
        .unwrap_or(Value::Null);
    let plan = json!({"previewId":Uuid::new_v4().simple().to_string(),"name":format!("重现赛 · {name}"),"slots":slots.iter().map(|row|json!({"letter":row["letter"],"id":row["id"],"title":row["title"],"judgeScope":row["judgeScope"],"statementAvailable":row["statementAvailable"]})).collect::<Vec<_>>(),"duration":duration,"min":0,"max":10000,"strategy":"replay","constraints":config,"event":info,"difficultyRange":{"min":min,"max":max}});
    Ok(ReplayPaper { plan, slots })
}
