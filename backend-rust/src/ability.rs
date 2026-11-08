//! Conservative practice ability used by the existing review scheduler.
//! All inputs come from the account journal; no score or evidence is persisted.
use crate::{
    api::ApiError, catalogue::row_or_portable, identity::canonical_url, training::Training,
};
use chrono::{DateTime, Utc};
use regex::Regex;
use rusqlite::OptionalExtension;
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, HashMap},
    sync::LazyLock,
};

fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v[key].as_str().unwrap_or("")
}
pub(crate) fn time(v: &str) -> Option<DateTime<Utc>> {
    DateTime::parse_from_rfc3339(v)
        .ok()
        .map(|at| at.with_timezone(&Utc))
        .or_else(|| {
            chrono::NaiveDateTime::parse_from_str(v, "%Y-%m-%dT%H:%M:%S%.f")
                .ok()
                .map(|at| at.and_utc())
        })
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
#[derive(Clone, Debug)]
pub struct Rating {
    pub lower: f64,
    pub upper: f64,
    pub weight: f64,
}
static CF_MIRROR: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"^https://www\.luogu\.com\.cn/problem/CF([1-9][0-9]*)([A-Z][0-9]?)$").unwrap()
});

pub fn rating(row: &Value) -> Option<Rating> {
    let value = row["difficulty"]
        .as_f64()
        .filter(|v| v.is_finite() && *v > 0.)?;
    let value = (value / 100.).round_ties_even() * 100.;
    let source = text(row, "difficultySource");
    let reference = CF_MIRROR.captures(text(row,"url")).is_some_and(|c| {
        c[1].parse::<u64>().ok().is_some_and(|contest| row["difficultyOfficialReference"] == json!({"contestId":contest,"index":&c[2],"source":format!("https://codeforces.com/contest/{}/problem/{}",&c[1],&c[2]),"metadataSource":"https://codeforces.com/api/problemset.problems"}))
    });
    if (["Codeforces", "codeforces"].contains(&text(row, "platform")) || reference)
        && !truth(&row["difficultyEstimated"])
        && (source.contains("官方") || source.to_ascii_lowercase().contains("official"))
        && !source.contains("未提供")
        && !source.contains("无官方")
    {
        return Some(Rating {
            lower: value,
            upper: value,
            weight: 1.,
        });
    }
    let atcoder = source.contains("AtCoder Problems");
    let width = if atcoder { 300. } else { 400. };
    let (mut lower, mut upper) = (value - width, value + width);
    if let Some(band) = row["difficultyBand"].as_array().filter(|b| b.len() == 2) {
        if let (Some(l), Some(u)) = (band[0].as_f64(), band[1].as_f64()) {
            if l.is_finite() && u.is_finite() && l > 0. && l <= u {
                lower = lower.min(l);
                upper = upper.max(u);
            }
        }
    }
    Some(Rating {
        lower: (lower / 100.).floor().max(8.) * 100.,
        upper: (upper / 100.).ceil().max(8.) * 100.,
        weight: if atcoder { 0.5 } else { 0.25 },
    })
}

fn reference_present(value: &str) -> bool {
    let Some(raw) = value.strip_prefix("\0TB-CODE-V2:") else {
        return false;
    };
    let Ok(value) = serde_json::from_str::<Value>(raw) else {
        return false;
    };
    let Some(object) = value.as_object() else {
        return false;
    };
    if object.len() != 3 && object.len() != 4
        || object
            .keys()
            .any(|k| !["root", "sha256", "bytes", "offset"].contains(&k.as_str()))
    {
        return false;
    }
    let hash = |key: &str| {
        value[key].as_str().is_some_and(|v| {
            v.len() == 64
                && v.bytes()
                    .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c))
        })
    };
    let Some(bytes) = value["bytes"].as_u64().filter(|v| *v <= 262144) else {
        return false;
    };
    let offset = value.get("offset").map_or(Some(0), Value::as_u64);
    hash("root")
        && hash("sha256")
        && bytes > 0
        && offset.is_some_and(|offset| offset <= 262144 - bytes)
}
fn source_present(t: &Training<'_>, record: &Value, has_refs: bool) -> Result<bool, ApiError> {
    let code = text(record, "code");
    if !code.trim().is_empty() && (!code.starts_with("\0TB-CODE-V2:") || reference_present(code)) {
        return Ok(true);
    }
    if has_refs {
        let reference: Option<String> = t
            .personal
            .db
            .query_row(
                "SELECT reference FROM account_sync_code_refs WHERE submission_id=?",
                [text(record, "id")],
                |r| r.get(0),
            )
            .optional()?;
        if reference.is_some_and(|r| reference_present(&r)) {
            return Ok(true);
        }
    }
    Ok(false)
}
static RECEIPT_ID: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^official-[0-9a-f]{64}$").unwrap());
static RECEIPT_MESSAGE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^原站确认提交 #[1-9][0-9]*(?:\s|$)").unwrap());
fn timed_owner(record: &Value, contests: &[Value], row: &Value) -> bool {
    if !RECEIPT_ID.is_match(text(record, "id"))
        || !RECEIPT_MESSAGE.is_match(text(record, "message"))
    {
        return false;
    }
    let Some(stamp) = time(text(record, "submitted_at")) else {
        return false;
    };
    let mut matches = Vec::new();
    for contest in contests {
        if !["running", "finished"].contains(&text(contest, "status")) {
            continue;
        }
        let (Some(start), Some(mut end)) = (
            time(text(contest, "started_at")),
            time(text(contest, "deadline")),
        ) else {
            continue;
        };
        if let Some(finish) = time(text(contest, "finished_at")) {
            end = end.min(finish);
        }
        if stamp < start || stamp > end {
            continue;
        }
        let slots = serde_json::from_str::<Value>(text(contest, "slots")).unwrap_or(Value::Null);
        if slots
            .as_array()
            .is_some_and(|slots| slots.iter().any(|slot| slot["id"] == record["problem_id"]))
        {
            matches.push(text(contest, "id"));
        }
    }
    let contest = text(record, "contest_id");
    if !contest.is_empty() && matches.contains(&contest) || contest.is_empty() && matches.len() == 1
    {
        return true;
    }
    // Only an original site's explicit public contest interval qualifies.
    row["contestDateSource"] == "原站公开比赛时间"
        && time(text(row, "startedAt"))
            .zip(time(text(row, "endedAt")))
            .is_some_and(|(start, end)| start < end && start <= stamp && stamp < end)
}
#[derive(Clone, Debug)]
pub struct Observation {
    pub id: String,
    pub difficulty: f64,
    pub weight: f64,
    pub solved: bool,
    pub at: DateTime<Utc>,
}

pub fn observations(t: &Training<'_>, records: &[Value]) -> Result<Vec<Observation>, ApiError> {
    let has_refs:bool=t.personal.db.query_row("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='account_sync_code_refs')",[],|r|r.get(0))?;
    let contests = t.personal.rows("SELECT * FROM contests", [])?;
    let mut grouped = HashMap::<String, Vec<(&Value, bool)>>::new();
    let mut metadata = HashMap::new();
    for record in records {
        if record["mode"] != "submit"
            || record["scope"] != "official"
            || !["AC", "WA", "TLE", "MLE", "RE", "OLE"].contains(&text(record, "verdict"))
        {
            continue;
        }
        let (Some(at), Some(finished)) = (
            time(text(record, "submitted_at")),
            time(text(record, "finished_at")),
        ) else {
            continue;
        };
        if at > finished || finished > t.now {
            continue;
        }
        let canonical = t.canonical(text(record, "problem_id"))?;
        if !metadata.contains_key(&canonical) {
            // Review scheduling consumes the same compact training metadata as
            // the legacy path; full-only fields cannot add stronger evidence.
            let row = match t.catalogue.row(&canonical, true)? {
                Some(row) => row,
                None => match row_or_portable(t.catalogue, t.personal, &canonical) {
                    Ok(row) => row,
                    Err(e) if e.status == 404 => continue,
                    Err(e) => return Err(e),
                },
            };
            metadata.insert(canonical.clone(), row);
        }
        let row = &metadata[&canonical];
        let key = canonical_url(text(row, "url")).unwrap_or(canonical);
        let independent = !record["solution_seen"].is_null()
            && !truth(&record["solution_seen"])
            && (source_present(t, record, has_refs)?
                || timed_owner(record, contests.as_array().unwrap(), row));
        grouped.entry(key).or_default().push((record, independent));
    }
    let mut result = Vec::new();
    for (key, mut receipts) in grouped {
        receipts.sort_by(|(a, ai), (b, bi)| {
            time(text(a, "submitted_at"))
                .cmp(&time(text(b, "submitted_at")))
                .then(ai.cmp(bi))
                .then(text(a, "id").cmp(text(b, "id")))
        });
        let first_ac = receipts.iter().find(|(r, _)| r["verdict"] == "AC");
        let failures = receipts
            .iter()
            .filter(|(r, independent)| {
                *independent
                    && r["verdict"] != "AC"
                    && first_ac.is_none_or(|(ac, _)| {
                        time(text(r, "submitted_at")) <= time(text(ac, "submitted_at"))
                    })
            })
            .collect::<Vec<_>>();
        let solved = first_ac.is_some_and(|(_, independent)| *independent);
        if !solved && failures.is_empty() {
            continue;
        }
        let record = if solved {
            first_ac.unwrap().0
        } else {
            failures.last().unwrap().0
        };
        let canonical = t.canonical(text(record, "problem_id"))?;
        let Some(rating) = rating(&metadata[&canonical]) else {
            continue;
        };
        let difficulty = if solved { rating.lower } else { rating.upper };
        if difficulty <= 0. || difficulty > 4000. {
            continue;
        }
        result.push(Observation {
            id: key,
            difficulty,
            weight: rating.weight
                / if solved {
                    (1. + failures.len().min(8) as f64).sqrt()
                } else {
                    1.
                },
            solved,
            at: time(text(record, "submitted_at")).unwrap(),
        });
    }
    Ok(result)
}

/// 10% posterior quantile, capped by the fifth independent success.
pub fn score_from_observations(items: &[Observation]) -> Option<i64> {
    let mut items = items.to_vec();
    items.sort_by(|a, b| {
        a.at.cmp(&b.at)
            .then(a.id.cmp(&b.id))
            .then(a.solved.cmp(&b.solved))
    });
    let mut unique = HashMap::new();
    for item in items {
        unique.entry(item.id.clone()).or_insert(item);
    }
    let mut items = unique
        .into_values()
        .filter(|r| {
            r.difficulty.is_finite() && r.difficulty > 0. && r.difficulty <= 4000. && r.weight > 0.
        })
        .collect::<Vec<_>>();
    items.sort_by(|a, b| a.at.cmp(&b.at).then(a.id.cmp(&b.id)));
    if items.len() > 60 {
        items.drain(..items.len() - 60);
    }
    let mut support = items
        .iter()
        .filter(|r| r.solved)
        .map(|r| r.difficulty)
        .collect::<Vec<_>>();
    if support.len() < 5 {
        return None;
    }
    support.sort_by(|a, b| b.total_cmp(a));
    let mut bands = HashMap::<i64, f64>::new();
    for item in &items {
        *bands
            .entry((item.difficulty / 100.).floor() as i64)
            .or_default() += item.weight.clamp(0., 1.);
    }
    let mut histogram = BTreeMap::<i64, (f64, f64)>::new();
    for item in &items {
        let weight = item.weight.clamp(0., 1.)
            * (8. / bands[&((item.difficulty / 100.).floor() as i64)]).min(1.);
        let entry = histogram.entry(item.difficulty as i64).or_default();
        entry.0 += weight;
        if item.solved {
            entry.1 += weight;
        }
    }
    let scale = 400. / 10f64.ln();
    let densities = (0..=400)
        .map(|index| {
            let ability = index as f64 * 10.;
            let mut density = -0.5 * ((ability - 1200.) / 600.).powi(2);
            for (difficulty, (weight, successes)) in &histogram {
                let delta = (ability - *difficulty as f64) / scale;
                density +=
                    successes * delta - weight * (delta.max(0.) + (-delta.abs()).exp().ln_1p());
            }
            density
        })
        .collect::<Vec<_>>();
    let peak = densities.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    let weights = densities
        .iter()
        .map(|v| (v - peak).exp())
        .collect::<Vec<_>>();
    let total = weights.iter().sum::<f64>();
    let mut cumulative = 0.;
    let mut lower = 4000.;
    for (index, weight) in weights.iter().enumerate() {
        cumulative += weight / total;
        if cumulative >= 0.1 {
            lower = index as f64 * 10.;
            break;
        }
    }
    Some((lower.min(support[4]) / 10.).floor() as i64 * 10)
}
pub fn score(t: &Training<'_>, records: &[Value]) -> Result<Option<i64>, ApiError> {
    Ok(score_from_observations(&observations(t, records)?))
}
