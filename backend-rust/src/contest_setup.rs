//! Blind local papers selected from the verified public catalogue. A preview
//! is retained in this service instance and never becomes progress evidence.
use crate::{
    api::ApiError, goals, identity::canonical_url, learning::stamp, storage, training::Training,
};
use chrono::{DateTime, Duration, Utc};
use rusqlite::params;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    cmp::Ordering,
    collections::{HashMap, HashSet},
    sync::LazyLock,
};
use uuid::Uuid;

fn text<'a>(value: &'a Value, key: &str) -> &'a str {
    value[key].as_str().unwrap_or("")
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
fn invalid() -> ApiError {
    ApiError::new(
        500,
        "INVALID_STORED_DATA",
        "模拟赛资料格式异常，原记录已保留",
    )
}
fn number(body: &Value, key: &str, default: i64) -> Result<i64, ApiError> {
    body.get(key)
        .map(goals::integer)
        .unwrap_or(Some(default))
        .ok_or_else(|| ApiError::bad("模拟赛参数无效"))
}
fn strings(value: Option<&Value>) -> Result<Vec<String>, ApiError> {
    match value {
        None => Ok(vec![]),
        Some(Value::Array(values)) => values
            .iter()
            .map(|v| v.as_str().map(String::from).ok_or_else(invalid))
            .collect(),
        _ => Err(invalid()),
    }
}
fn key(row: &Value) -> String {
    canonical_url(text(row, "url")).unwrap_or_else(|| text(row, "id").into())
}
fn difficulty(row: &Value) -> f64 {
    row["difficulty"].as_f64().unwrap()
}
fn local_catalogue(t: &Training<'_>) -> Result<(), ApiError> {
    let private: bool = t.personal.db.query_row(
        "SELECT EXISTS(SELECT 1 FROM account_problem_facts)",
        [],
        |row| row.get(0),
    )?;
    if private {
        Err(ApiError::pending())
    } else {
        Ok(())
    }
}
static PROFILES: LazyLock<Result<HashSet<String>, ApiError>> = LazyLock::new(|| {
    let source = include_str!("../../backend/reviewed_cases.py")
        .trim_start_matches('\u{feff}')
        .replace("\r\n", "\n");
    let metadata: Value = serde_json::from_str(include_str!(
        "../../backend/resources/native-reviewed-profiles.json"
    ))?;
    if metadata["version"] != 1
        || metadata["normalization"] != "utf8-lf"
        || metadata["sourceSha256"] != format!("{:x}", Sha256::digest(source.as_bytes()))
    {
        return Err(ApiError::new(
            503,
            "CATALOGUE_STALE",
            "本地评测资料索引已变化，请重新构建",
        ));
    }
    Ok(strings(metadata.get("ids"))?.into_iter().collect())
});
fn profiles() -> Result<&'static HashSet<String>, ApiError> {
    PROFILES.as_ref().map_err(Clone::clone)
}

pub fn options(body: &Value) -> Result<Value, ApiError> {
    if !body.is_object() {
        return Err(ApiError::bad("模拟赛参数无效"));
    }
    let strategy = body
        .get("strategy")
        .or_else(|| body.get("mode"))
        .and_then(Value::as_str)
        .unwrap_or(
            if body.get("strategy").or_else(|| body.get("mode")).is_some() {
                ""
            } else {
                "comprehensive"
            },
        );
    if !["comprehensive", "topic", "single"].contains(&strategy) {
        return Err(ApiError::bad("训练方式须为综合、专项或单题"));
    }
    let mut raw_tags = body.get("tags").cloned().unwrap_or(json!([]));
    if let Some(topic) = body.get("topic").filter(|v| !v.is_null()) {
        let topic = topic
            .as_str()
            .ok_or_else(|| ApiError::bad("专项知识点无效"))?
            .trim();
        if !topic.is_empty() && !truth(&raw_tags) {
            raw_tags = json!([topic]);
        }
    }
    let mut tags = match &raw_tags {
        Value::Array(v) if v.len() <= 256 => v
            .iter()
            .map(|v| {
                v.as_str()
                    .filter(|v| !v.trim().is_empty() && v.trim().chars().count() <= 80)
                    .map(|v| v.trim().to_owned())
                    .ok_or_else(|| ApiError::bad("请选择有效的专项知识点"))
            })
            .collect::<Result<Vec<_>, _>>()?,
        _ => return Err(ApiError::bad("请选择有效的专项知识点")),
    };
    tags.sort();
    tags.dedup();
    if strategy == "topic" && tags.is_empty() {
        return Err(ApiError::bad("专项训练须选择至少一个知识点"));
    }
    let platform = body
        .get("platform")
        .filter(|v| truth(v))
        .map(|v| {
            v.as_str()
                .filter(|v| v.chars().count() <= 80)
                .ok_or_else(|| ApiError::bad("题目平台无效"))
        })
        .transpose()?
        .unwrap_or("")
        .trim();
    let mut switches = vec![];
    for field in ["excludeSolved", "reviewedOnly"] {
        switches.push(
            body.get(field)
                .map(|v| {
                    v.as_bool()
                        .ok_or_else(|| ApiError::bad("模拟赛筛选选项须为布尔值"))
                })
                .transpose()?
                .unwrap_or(false),
        );
    }
    let rules =
        body.get("rules")
            .and_then(Value::as_str)
            .unwrap_or(if body.get("rules").is_some() {
                ""
            } else {
                "acm"
            });
    if !["acm", "xcpc"].contains(&rules) {
        return Err(ApiError::bad("请选择 ACM 或 XCPC 赛制"));
    }
    let penalty = body
        .get("wrongPenalty")
        .map(goals::integer)
        .unwrap_or(Some(20))
        .ok_or_else(|| ApiError::bad("罚时须为整数分钟"))?;
    let compile = body
        .get("compilePenalty")
        .map(Value::as_bool)
        .unwrap_or(Some(false));
    if !(0..=120).contains(&penalty) || compile.is_none() {
        return Err(ApiError::bad("罚时须为 0–120 分钟，编译错误罚时选项须有效"));
    }
    Ok(
        json!({"strategy":strategy,"tags":tags,"platform":platform,"excludeSolved":switches[0],"reviewedOnly":switches[1],"rules":rules,"wrongPenalty":penalty,"compilePenalty":compile.unwrap()}),
    )
}

fn shelf(row: &Value, requested: &str) -> bool {
    let lower = requested.to_lowercase();
    let platform = match lower.as_str() {
        "codeforces" => "codeforces",
        "atcoder" => "atcoder",
        "nowcoder" => "牛客",
        "luogu" => "洛谷",
        v => v,
    };
    if platform.is_empty() || platform == "all" {
        return true;
    }
    if ["xcpc", "acm"].contains(&platform) {
        static ACM: LazyLock<regex::Regex> = LazyLock::new(|| {
            regex::Regex::new(r"(?i)ICPC|CCPC|XCPC|ACM|区域赛|邀请赛|省赛|网络(?:预选)?赛|分区赛|大学生.*程序设计").unwrap()
        });
        return row["series"] == "XCPC" || ACM.is_match(text(row, "contest"));
    }
    if platform == "lanqiao" {
        return row
            .get("series")
            .filter(|v| truth(v))
            .map_or(text(row, "contest"), |v| v.as_str().unwrap_or(""))
            .starts_with("蓝桥杯");
    }
    platform == text(row, "platform").to_lowercase()
}
fn eligible(
    row: &Value,
    config: &Value,
    lower: i64,
    upper: i64,
    solved: &HashSet<String>,
) -> Result<bool, ApiError> {
    if !row["difficulty"]
        .as_f64()
        .is_some_and(|d| d.is_finite() && d >= lower as f64 && d <= upper as f64)
    {
        return Ok(false);
    }
    if truth(&row["catalogHidden"])
        || !shelf(row, text(config, "platform"))
        || config["excludeSolved"] == true && solved.contains(&key(row))
    {
        return Ok(false);
    }
    let selected = strings(config.get("tags"))?;
    if !selected.is_empty() {
        let mut scope = strings(row.get("tags"))?
            .into_iter()
            .collect::<HashSet<_>>();
        for path in strings(row.get("knowledgeCategories"))? {
            scope.extend(
                path.split(" / ")
                    .map(str::trim)
                    .filter(|s| !s.is_empty())
                    .map(String::from),
            );
        }
        if !selected.iter().any(|tag| scope.contains(tag)) {
            return Ok(false);
        }
    }
    Ok(config["reviewedOnly"] != true || profiles()?.contains(text(row, "id")))
}
fn ready(row: &Value) -> Result<bool, ApiError> {
    row["catalogContentReady"]
        .as_bool()
        .ok_or_else(ApiError::pending)
}
fn solved(
    t: &Training<'_>,
    metadata: &HashMap<String, Value>,
) -> Result<HashSet<String>, ApiError> {
    Ok(t.personal.rows("SELECT problem_id FROM submissions WHERE mode='submit' AND scope='official' AND verdict='AC' AND finished_at IS NOT NULL",[])?.as_array().unwrap().iter().map(|receipt|metadata.get(text(receipt,"problem_id")).map(key).unwrap_or_else(||text(receipt,"problem_id").into())).collect())
}
fn families(row: &Value) -> Result<HashSet<&'static str>, ApiError> {
    let mut result = HashSet::new();
    for tag in strings(row.get("tags"))? {
        if tag.contains("DP") || tag.contains("动态规划") {
            result.insert("dp");
        }
        if [
            "图论",
            "BFS",
            "拓扑排序",
            "差分约束",
            "最短路",
            "并查集",
            "树",
            "树形 DP",
        ]
        .contains(&tag.as_str())
        {
            result.insert("graph");
        }
        if [
            "模拟",
            "枚举",
            "贪心",
            "排序",
            "前缀和",
            "差分",
            "二分查找",
            "双指针",
        ]
        .contains(&tag.as_str())
        {
            result.insert("basic");
        }
    }
    Ok(result)
}
#[derive(Clone, Default, PartialEq, Eq, PartialOrd, Ord)]
struct Exposure(bool, usize, String);
#[derive(Clone)]
struct Preview {
    at: DateTime<Utc>,
    plan: Value,
    slots: Vec<Value>,
}
#[derive(Default)]
pub struct PreviewBook {
    previews: Vec<Preview>,
    previous: HashMap<String, Vec<String>>,
}
impl PreviewBook {
    pub fn preview(&mut self, t: &Training<'_>, body: &Value) -> Result<Value, ApiError> {
        self.preview_with(t, body, &mut || {
            let bytes = *Uuid::new_v4().as_bytes();
            let bits = bytes[..6]
                .iter()
                .fold(0_u64, |v, b| v * 256 + u64::from(*b));
            bits as f64 / (1_u64 << 48) as f64
        })
    }
    fn preview_with(
        &mut self,
        t: &Training<'_>,
        body: &Value,
        draw: &mut impl FnMut() -> f64,
    ) -> Result<Value, ApiError> {
        local_catalogue(t)?;
        if body["mode"] == "replay" {
            return Err(ApiError::pending());
        }
        let local_profiles = profiles()?;
        let config = options(body)?;
        let count = if config["strategy"] == "single" {
            1
        } else {
            number(body, "count", 6)?
        };
        let lower = number(body, "min", 0)?;
        let upper = number(body, "max", 10000)?;
        if !(1..=20).contains(&count)
            || !(0..=10000).contains(&lower)
            || lower > upper
            || upper > 10000
        {
            return Err(ApiError::bad(
                "题数须为 1–20，时长须为 1–1440 分钟，难度上下限须有效",
            ));
        }
        let band = if upper <= 1400 {
            0
        } else if upper <= 1700 {
            1
        } else if upper <= 2000 {
            2
        } else {
            3
        };
        let base = if config["strategy"] == "topic" {
            [90, 120, 150, 180]
        } else {
            [120, 150, 180, 210]
        }[band];
        let duration = number(
            body,
            "duration",
            if body.get("mode").is_none() {
                if config["rules"] == "xcpc" { 300 } else { 120 }
            } else if config["strategy"] == "single" {
                [30, 45, 60, 75][band]
            } else {
                ((base * count + 59) / 60 * 15).clamp(30, 480)
            },
        )?;
        if !(1..=1440).contains(&duration) {
            return Err(ApiError::bad(
                "题数须为 1–20，时长须为 1–1440 分钟，难度上下限须有效",
            ));
        }
        let (rows, metadata) = goals::public_rows(t)?;
        let solved = if config["excludeSolved"] == true {
            solved(t, &metadata)?
        } else {
            HashSet::new()
        };
        let mut seen = HashSet::new();
        let mut candidates = vec![];
        for row in rows {
            if eligible(&row, &config, lower, upper, &solved)?
                && ready(&row)?
                && seen.insert(key(&row))
            {
                candidates.push(row);
            }
        }
        let available = candidates.len();
        if available < count as usize {
            return Err(ApiError::new(
                422,
                "INSUFFICIENT_PROBLEMS",
                &format!(
                    "当前范围只有 {available} 道具备原题面和样例的题目，无法组成 {count} 题模拟赛。请扩大难度范围或减少题数。"
                ),
            ));
        }
        let mut levels = candidates.iter().map(difficulty).collect::<Vec<_>>();
        levels.sort_by(f64::total_cmp);
        levels.dedup();
        if config["strategy"] == "comprehensive" && levels.len() < count as usize {
            return Err(ApiError::new(
                422,
                "INSUFFICIENT_DIFFICULTIES",
                &format!(
                    "当前可用题目只有 {} 档不同难度，无法组成 {count} 题递进模拟赛。请扩大难度范围或减少题数。",
                    levels.len()
                ),
            ));
        }
        let active = t
            .personal
            .rows("SELECT id,accepted_at FROM training WHERE active=1", [])?
            .as_array()
            .unwrap()
            .iter()
            .map(|r| (text(r, "id").to_owned(), truth(&r["accepted_at"])))
            .collect::<HashMap<_, _>>();
        let mut exposures = HashMap::<String, Exposure>::new();
        for paper in t
            .personal
            .rows(
                "SELECT slots,started_at FROM contests ORDER BY started_at",
                [],
            )?
            .as_array()
            .unwrap()
        {
            for slot in serde_json::from_str::<Vec<Value>>(text(paper, "slots"))? {
                let id = text(&slot, "id");
                if id.is_empty() {
                    return Err(invalid());
                }
                let k = metadata.get(id).map(key).unwrap_or_else(|| id.into());
                let e = exposures.entry(k).or_default();
                e.0 = true;
                e.1 += 1;
                e.2 = text(paper, "started_at").into();
            }
        }
        for paper in &self.previews {
            for slot in &paper.slots {
                let id = text(slot, "id");
                let k = metadata.get(id).map(key).unwrap_or_else(|| id.into());
                let e = exposures.entry(k).or_default();
                e.0 = true;
                e.1 += 1;
            }
        }
        let exposure = |r: &Value| exposures.get(&key(r)).cloned().unwrap_or_default();
        let mut ranks = HashMap::new();
        for row in &candidates {
            let value = draw();
            if !value.is_finite() || !(0.0..1.0).contains(&value) {
                return Err(invalid());
            }
            ranks.insert(text(row, "id").to_owned(), value);
        }
        let width = 100_f64.max((upper - lower) as f64 / count as f64 * 0.65);
        let pool = candidates.clone();
        let mut chosen = Vec::<Value>::new();
        let mut covered = HashSet::<String>::new();
        let mut main_tags = HashSet::<String>::new();
        let mut platforms = HashSet::<String>::new();
        for index in 0..count {
            let center =
                lower as f64 + (upper - lower) as f64 * ((index as f64 + 0.5) / count as f64);
            let scores = candidates
                .iter()
                .map(|row| {
                    let tags = strings(row.get("tags"))?;
                    let main = tags.first().map(String::as_str).unwrap_or("");
                    let novel = tags
                        .iter()
                        .filter(|tag| !covered.contains(*tag))
                        .collect::<HashSet<_>>()
                        .len();
                    Ok((
                        chosen.iter().any(|old| difficulty(old) == difficulty(row)),
                        ((difficulty(row) - center).abs() / width) as i64 / 2,
                        exposure(row),
                        !main.is_empty() && main_tags.contains(main),
                        active.get(text(row, "id")).copied().unwrap_or(false),
                        active.contains_key(text(row, "id")),
                        platforms.contains(text(row, "platform")),
                        ranks[text(row, "id")] - 0.06 * novel.min(3) as f64,
                        (difficulty(row) - center).abs(),
                        text(row, "id").to_owned(),
                    ))
                })
                .collect::<Result<Vec<_>, ApiError>>()?;
            let selected = (0..candidates.len())
                .min_by(|&a, &b| {
                    let a = &scores[a];
                    let b = &scores[b];
                    (&a.0, &a.1, &a.2, &a.3, &a.4, &a.5, &a.6)
                        .cmp(&(&b.0, &b.1, &b.2, &b.3, &b.4, &b.5, &b.6))
                        .then_with(|| a.7.total_cmp(&b.7))
                        .then_with(|| a.8.total_cmp(&b.8))
                        .then_with(|| a.9.cmp(&b.9))
                })
                .unwrap();
            let row = candidates.remove(selected);
            let tags = strings(row.get("tags"))?;
            covered.extend(tags.clone());
            if let Some(main) = tags.first() {
                main_tags.insert(main.clone());
            }
            platforms.insert(text(&row, "platform").into());
            chosen.push(row);
        }
        let required = if config["strategy"] == "comprehensive" && count >= 3 {
            pool.iter().try_fold(HashSet::new(), |mut all, row| {
                all.extend(families(row)?);
                Ok::<_, ApiError>(all)
            })?
        } else {
            HashSet::new()
        };
        for family in ["dp", "graph", "basic"] {
            let current = chosen.iter().try_fold(HashSet::new(), |mut all, row| {
                all.extend(families(row)?);
                Ok::<_, ApiError>(all)
            })?;
            if !required.contains(family) || current.contains(family) {
                continue;
            }
            let mut best: Option<(Exposure, i64, f64, usize, Value)> = None;
            for replacement in &pool {
                if chosen.iter().any(|r| r["id"] == replacement["id"])
                    || !families(replacement)?.contains(family)
                {
                    continue;
                }
                for (index, row) in chosen.iter().enumerate() {
                    if exposure(replacement) > exposure(row) {
                        continue;
                    }
                    let mut alternate = chosen.clone();
                    alternate[index] = replacement.clone();
                    if !preserves(&chosen, &alternate, &required)? {
                        continue;
                    }
                    let score = (
                        exposure(replacement),
                        ((difficulty(replacement) - difficulty(row)).abs() / width) as i64,
                        ranks[text(replacement, "id")],
                        index,
                        replacement.clone(),
                    );
                    if best
                        .as_ref()
                        .is_none_or(|old| compare_replacement(&score, old) == Ordering::Less)
                    {
                        best = Some(score);
                    }
                }
            }
            if let Some((_, _, _, index, row)) = best {
                chosen[index] = row;
            }
        }
        chosen.sort_by(|a, b| {
            difficulty(a)
                .total_cmp(&difficulty(b))
                .then_with(|| text(a, "id").cmp(text(b, "id")))
        });
        let preview_key = json!([count, duration, lower, upper, config]).to_string();
        if self.previous.get(&preview_key).is_some_and(|previous| {
            *previous
                == chosen
                    .iter()
                    .map(|r| text(r, "id").to_owned())
                    .collect::<Vec<_>>()
        }) {
            let mut best: Option<(f64, usize, Value)> = None;
            for replacement in &pool {
                if chosen.iter().any(|r| r["id"] == replacement["id"]) {
                    continue;
                }
                for (index, row) in chosen.iter().enumerate() {
                    if exposure(replacement) > exposure(row)
                        || (difficulty(replacement) - difficulty(row)).abs() > width * 1.5
                    {
                        continue;
                    }
                    let mut alternate = chosen.clone();
                    alternate[index] = replacement.clone();
                    if !preserves(&chosen, &alternate, &required)? {
                        continue;
                    }
                    let score = (ranks[text(replacement, "id")], index, replacement.clone());
                    if best.as_ref().is_none_or(|old| {
                        score.0.total_cmp(&old.0).then(score.1.cmp(&old.1)) == Ordering::Less
                    }) {
                        best = Some(score);
                    }
                }
            }
            if let Some((_, index, row)) = best {
                chosen[index] = row;
                chosen.sort_by(|a, b| {
                    difficulty(a)
                        .total_cmp(&difficulty(b))
                        .then_with(|| text(a, "id").cmp(text(b, "id")))
                });
            }
        }
        let ids = chosen
            .iter()
            .map(|r| text(r, "id").to_owned())
            .collect::<Vec<_>>();
        let slots=chosen.iter().enumerate().map(|(i,r)|json!({"letter":char::from(b'A'+i as u8).to_string(),"id":r["id"],"title":r["title"],"difficulty":r["difficulty"],"tags":r.get("tags").cloned().unwrap_or(json!([])),"judgeScope":if local_profiles.contains(text(r,"id")){"local"}else{"samples"}})).collect::<Vec<_>>();
        let repeated = chosen.iter().filter(|row| exposure(row).0).count();
        let plan = json!({"previewId":Uuid::new_v4().simple().to_string(),"name":format!("模拟赛 · {} 题 / {duration} 分钟",slots.len()),"slots":slots.iter().map(|slot|json!({"letter":slot["letter"],"id":slot["id"],"title":slot["title"],"judgeScope":slot["judgeScope"]})).collect::<Vec<_>>(),"duration":duration,"min":lower,"max":upper,"strategy":config["strategy"],"constraints":config,"selectionNotice":if repeated>0{format!("当前范围的新题不足，本卷含 {repeated} 道曾抽取或练习的题目。")}else{String::new()}});
        self.previous.insert(preview_key, ids.clone());
        let preview = Preview {
            at: t.now,
            plan: plan.clone(),
            slots,
        };
        if let Some(old) = self.previews.iter_mut().find(|p| {
            p.slots
                .iter()
                .map(|r| text(r, "id"))
                .eq(ids.iter().map(String::as_str))
        }) {
            *old = preview;
        } else {
            self.previews.push(preview);
        }
        while self.previews.len() > 20 {
            self.previews.remove(0);
        }
        Ok(json!({"plan":plan,"available":available}))
    }
    pub fn start(&mut self, t: &Training<'_>, body: &Value) -> Result<Value, ApiError> {
        local_catalogue(t)?;
        let ids = body["ids"]
            .as_array()
            .filter(|values| !values.is_empty() && values.len() <= 100)
            .ok_or_else(|| ApiError::bad("请选择 1–100 道不重复的模拟赛题目"))?
            .iter()
            .map(|v| {
                v.as_str()
                    .filter(|v| !v.is_empty() && v.len() <= 512)
                    .map(String::from)
                    .ok_or_else(|| ApiError::bad("请选择 1–100 道不重复的模拟赛题目"))
            })
            .collect::<Result<Vec<_>, _>>()?;
        if ids.iter().collect::<HashSet<_>>().len() != ids.len() {
            return Err(ApiError::bad("请选择 1–100 道不重复的模拟赛题目"));
        }
        let duration = number(body, "duration", 120)?;
        let index = self
            .previews
            .iter()
            .position(|p| {
                p.slots
                    .iter()
                    .map(|r| text(r, "id"))
                    .eq(ids.iter().map(String::as_str))
            })
            .ok_or_else(|| ApiError::conflict("选题预览已变化或过期，请重新生成并确认"))?;
        let preview = self.previews[index].clone();
        if preview.plan["duration"] != duration || t.now - preview.at > Duration::minutes(30) {
            return Err(ApiError::conflict("选题预览已变化或过期，请重新生成并确认"));
        }
        if body
            .get("previewId")
            .is_some_and(|value| *value != preview.plan["previewId"])
        {
            return Err(ApiError::conflict("选题预览已更新，请使用当前预览"));
        }
        let mut config = preview.plan["constraints"].clone();
        if config["strategy"] == "replay"
            || config.get("calendarEvent").is_some()
            || config.get("backgroundReward").is_some()
        {
            return Err(ApiError::pending());
        }
        if [
            "strategy",
            "mode",
            "tags",
            "topic",
            "platform",
            "excludeSolved",
            "reviewedOnly",
            "rules",
            "wrongPenalty",
            "compilePenalty",
        ]
        .iter()
        .any(|field| body.get(*field).is_some())
        {
            let mut requested = config.clone();
            for (name, value) in body
                .as_object()
                .ok_or_else(|| ApiError::bad("模拟赛参数无效"))?
            {
                requested[name] = value.clone();
            }
            if body.get("mode").is_some() && body.get("strategy").is_none() {
                requested["strategy"] = body["mode"].clone();
            }
            if body.get("topic").is_some() && body.get("tags").is_none() {
                requested["tags"] = json!([]);
            }
            if options(&requested)? != config {
                return Err(ApiError::conflict("筛选条件已变化，请重新生成题目"));
            }
        }
        if body
            .get("count")
            .is_some_and(|v| !numeric_equal(v, ids.len() as i64))
        {
            return Err(ApiError::conflict("题数已变化，请重新生成题目"));
        }
        for field in ["min", "max"] {
            if body
                .get(field)
                .is_some_and(|v| !numeric_equal(v, preview.plan[field].as_i64().unwrap()))
            {
                return Err(ApiError::conflict("难度条件已变化，请重新生成题目"));
            }
        }
        let (_, metadata) = goals::public_rows(t)?;
        let solved = if config["excludeSolved"] == true {
            solved(t, &metadata)?
        } else {
            HashSet::new()
        };
        let local_profiles = profiles()?;
        for identity in &ids {
            let row = metadata
                .get(identity)
                .ok_or_else(|| ApiError::conflict("原题面或评测资料已变化，请重新生成题目"))?;
            if !ready(row)?
                || !eligible(
                    row,
                    &config,
                    preview.plan["min"].as_i64().unwrap(),
                    preview.plan["max"].as_i64().unwrap(),
                    &solved,
                )?
            {
                return Err(ApiError::conflict(
                    "题目资料或通过状态已变化，请重新生成题目",
                ));
            }
        }
        let name = body
            .get("name")
            .filter(|v| truth(v))
            .unwrap_or(&preview.plan["name"])
            .as_str()
            .filter(|v| v.chars().count() <= 100)
            .ok_or_else(|| ApiError::bad("模拟赛名称过长"))?;
        let result = storage::atomic(&t.personal.db, |db| {
            crate::contest_lifecycle::expire(t)?;
            let running: bool = db.query_row(
                "SELECT EXISTS(SELECT 1 FROM contests WHERE status='running')",
                [],
                |row| row.get(0),
            )?;
            if running {
                return Err(ApiError::conflict(
                    "已有一场模拟赛正在进行，请先回到考场或交卷",
                ));
            }
            let mut owned = HashSet::new();
            for prior in t
                .personal
                .rows(
                    "SELECT slots,config FROM contests WHERE deleted_at IS NULL",
                    [],
                )?
                .as_array()
                .unwrap()
            {
                let options: Value = serde_json::from_str(text(prior, "config"))?;
                if options["strategy"] == "replay" {
                    for slot in serde_json::from_str::<Vec<Value>>(text(prior, "slots"))? {
                        if truth(&slot["trainingAdded"]) {
                            owned.insert(text(&slot, "id").to_owned());
                        }
                    }
                }
            }
            let mut slots = preview.slots.clone();
            for slot in &mut slots {
                let id = text(slot, "id").to_owned();
                let equivalent = t.ids(&id)?;
                let active:bool=db.query_row("SELECT EXISTS(SELECT 1 FROM training WHERE id IN(SELECT value FROM json_each(?)) AND active=1)",[json!(equivalent).to_string()],|row|row.get(0))?;
                slot["trainingAdded"] =
                    json!(equivalent.iter().any(|id| owned.contains(id)) || !active);
                slot["trainingBefore"] = t
                    .personal
                    .rows(
                        "SELECT active,active_at,removed_at FROM training WHERE id=?",
                        [&id],
                    )?
                    .as_array()
                    .unwrap()
                    .first()
                    .cloned()
                    .unwrap_or(Value::Null);
                slot["judgeScope"] = json!(if local_profiles.contains(&id) {
                    "local"
                } else {
                    "samples"
                });
            }
            config["editedTrainingOnly"] = true.into();
            let started = stamp(t.now);
            let deadline = stamp(t.now + Duration::minutes(duration));
            let id = format!("contest-{}", Uuid::new_v4().simple());
            db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config) VALUES(?,?,'running',?,?,?,?,?)",params![id,name,started,deadline,duration,json!(slots).to_string(),config.to_string()])?;
            let raw = t
                .personal
                .rows("SELECT * FROM contests WHERE id=?", [&id])?;
            Ok(json!({"contest":t.contest_projection(&raw[0])?,"workspace":t.workspace()?}))
        })?;
        self.previews.remove(index);
        Ok(result)
    }
}
fn numeric_equal(value: &Value, expected: i64) -> bool {
    match value {
        Value::Bool(v) => i64::from(*v) == expected,
        Value::Number(v) => v.as_f64() == Some(expected as f64),
        _ => false,
    }
}
fn compare_replacement(
    a: &(Exposure, i64, f64, usize, Value),
    b: &(Exposure, i64, f64, usize, Value),
) -> Ordering {
    a.0.cmp(&b.0)
        .then(a.1.cmp(&b.1))
        .then_with(|| a.2.total_cmp(&b.2))
        .then(a.3.cmp(&b.3))
}
fn preserves(
    chosen: &[Value],
    alternate: &[Value],
    required: &HashSet<&'static str>,
) -> Result<bool, ApiError> {
    let levels = |rows: &[Value]| {
        let mut values = rows.iter().map(difficulty).collect::<Vec<_>>();
        values.sort_by(f64::total_cmp);
        values.dedup();
        values.len()
    };
    if levels(chosen) != levels(alternate) {
        return Ok(false);
    }
    let covered = |rows: &[Value]| {
        rows.iter().try_fold(HashSet::new(), |mut all, row| {
            all.extend(families(row)?);
            Ok::<_, ApiError>(all)
        })
    };
    let before = covered(chosen)?;
    let after = covered(alternate)?;
    Ok(before
        .intersection(required)
        .all(|family| after.contains(family)))
}

#[cfg(test)]
mod tests;
