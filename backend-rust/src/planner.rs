//! Weekly planning on the existing account journal. Unported official evidence
//! and review scheduling are rejected before writes; no mastery is guessed.
use crate::{
    api::{ApiError, required_text},
    learning::{self, HISTORY, KEY, day, stamp},
    storage::PersonalStore,
    training::Training,
};
use chrono::{DateTime, Datelike, Duration, NaiveDate, Utc};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::HashSet;

const STAGES: [&str; 5] = [
    "基础编码",
    "常用算法与实现",
    "专题应用",
    "混合限时运用",
    "区域赛模拟与查缺",
];
const LEVELS: [&str; 7] = [
    "尚未验证",
    "接触过",
    "理解原理",
    "能跟着实现",
    "能独立实现",
    "能独立用来解题",
    "隔一段时间仍能完成",
];
const DIAGNOSES: [(&str, &str, &str); 10] = [
    (
        "meaning",
        "题意没理解",
        "先重述输入、输出与一个样例，再核对题面条件。",
    ),
    (
        "idea",
        "没有思路",
        "先判断是缺少适用条件还是识别方法，可用短原理检查定位。",
    ),
    (
        "implementation",
        "知道方法但写不出",
        "先做脱离示例的模板操作，核对不变量与边界。",
    ),
    (
        "bug",
        "代码出错",
        "先核对反例、边界与实际判定，结果本身不能说明具体错因。",
    ),
    (
        "forgot",
        "旧知识忘了",
        "先做少量重写检查；再次确认困难后，再采纳补充方案。",
    ),
    (
        "schedule",
        "任务安排不合适",
        "可以调整可用时间、日期与休息日，重排受影响任务。",
    ),
    (
        "easy",
        "任务太简单",
        "可以直接用未做过的原题验证，独立通过后再调整起点。",
    ),
    (
        "hard",
        "任务太难",
        "先确认困难位置，再选择补先修或减少任务量。",
    ),
    (
        "verify",
        "不知道怎样检验",
        "短原理检查、模板操作和独立原题各验证不同能力。",
    ),
    (
        "transfer",
        "学习后仍不会做题",
        "先用不提示算法的限时任务检验识别，交卷后再查看方法。",
    ),
];
fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v.get(key).and_then(Value::as_str).unwrap_or("")
}
fn array(v: &Value) -> &[Value] {
    v.as_array().map(Vec::as_slice).unwrap_or(&[])
}
fn truth(v: &Value) -> bool {
    match v {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::String(v) => !v.is_empty(),
        Value::Number(v) => v.as_f64() != Some(0.),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
fn invalid() -> ApiError {
    ApiError::new(
        500,
        "INVALID_STORED_DATA",
        "学习规划记录格式异常，原数据已保留",
    )
}
fn digest(v: &Value) -> String {
    format!("{:x}", Sha256::digest(v.to_string().as_bytes()))
}
fn uuid() -> String {
    uuid::Uuid::new_v4().simple().to_string()
}
fn date(s: &str) -> Result<NaiveDate, ApiError> {
    NaiveDate::parse_from_str(s, "%Y-%m-%d")
        .or_else(|_| NaiveDate::parse_from_str(s, "%Y%m%d"))
        .or_else(|_| NaiveDate::parse_from_str(s, "%G-W%V-%u"))
        .or_else(|_| NaiveDate::parse_from_str(&format!("{s}-1"), "%G-W%V-%u"))
        .map_err(|_| ApiError::bad("计划日期无效"))
}
fn monday(now: DateTime<Utc>) -> NaiveDate {
    let local = now
        .with_timezone(&chrono::FixedOffset::east_opt(28800).unwrap())
        .date_naive();
    local - Duration::days(local.weekday().num_days_from_monday() as i64)
}
fn parsed(v: &Value) -> Option<DateTime<Utc>> {
    v.as_str()
        .and_then(|s| DateTime::parse_from_rfc3339(s).ok())
        .map(|d| d.with_timezone(&Utc))
}

// Public roster originals use these exact judge identities. Unknown hosts
// retain their exact path; query-based judges retain their problem parameter.
pub fn original(value: &Value) -> Option<String> {
    let s = value.as_str()?.trim();
    let (scheme, rest) = s.split_once("://")?;
    if scheme != "http" && scheme != "https" {
        return None;
    }
    let cut = rest.find(['/', '?', '#']).unwrap_or(rest.len());
    let host = rest[..cut].to_lowercase();
    let host = host.strip_prefix("www.").unwrap_or(&host);
    if host.is_empty() {
        return None;
    }
    let rest = &rest[cut..];
    let path = rest
        .split(['?', '#'])
        .next()
        .unwrap_or("")
        .trim_end_matches('/');
    let p: Vec<_> = path.split('/').collect();
    let digits = |s: &str| !s.is_empty() && s.bytes().all(|b| b.is_ascii_digit());
    let word = |s: &str| !s.is_empty() && s.bytes().all(|b| b.is_ascii_alphanumeric());
    if ["codeforces.com", "m1.codeforces.com", "m2.codeforces.com"].contains(&host) {
        if p.len() == 5 && p[1] == "contest" && digits(p[2]) && p[3] == "problem" && word(p[4]) {
            return Some(format!(
                "codeforces.com/contest/{}/problem/{}",
                p[2],
                p[4].to_uppercase()
            ));
        }
        if p.len() == 5 && p[1] == "problemset" && p[2] == "problem" && digits(p[3]) && word(p[4]) {
            return Some(format!(
                "codeforces.com/contest/{}/problem/{}",
                p[3],
                p[4].to_uppercase()
            ));
        }
        if p.len() == 5 && p[1] == "gym" && digits(p[2]) && p[3] == "problem" && word(p[4]) {
            return Some(format!(
                "codeforces.com/gym/{}/problem/{}",
                p[2],
                p[4].to_uppercase()
            ));
        }
    }
    if host == "atcoder.jp" && p.len() == 5 && p[1] == "contests" && p[3] == "tasks" {
        return Some(format!("atcoder.jp{}", path.to_lowercase()));
    }
    if host == "luogu.com.cn" && p.len() == 3 && p[1] == "problem" {
        return Some(format!("luogu.com.cn/problem/{}", p[2].to_uppercase()));
    }
    if host == "ac.nowcoder.com"
        && p.len() == 5
        && p[1] == "acm"
        && p[2] == "contest"
        && digits(p[3])
        && word(p[4])
    {
        return Some(format!(
            "ac.nowcoder.com/acm/contest/{}/{}",
            p[3],
            p[4].to_uppercase()
        ));
    }
    if host == "qoj.ac" {
        let start = if p.get(1) == Some(&"contest") { 3 } else { 1 };
        if p.get(start) == Some(&"problem") && p.get(start + 1).is_some_and(|s| digits(s)) {
            return Some(format!("qoj.ac/problem/{}", p[start + 1]));
        }
    }
    let query = rest
        .split_once('?')
        .map(|(_, s)| s.split('#').next().unwrap_or(""))
        .unwrap_or("");
    for (hosts, route, key, canonical) in [
        (
            &["onlinejudge.org", "uva.onlinejudge.org"][..],
            "/index.php",
            "problem",
            "onlinejudge.org",
        ),
        (
            &["acm.hdu.edu.cn"][..],
            "/showproblem.php",
            "pid",
            "acm.hdu.edu.cn",
        ),
        (&["poj.org"][..], "/problem", "id", "poj.org"),
    ] {
        if hosts.contains(&host) && path == route {
            if let Some(id) = query
                .split('&')
                .filter_map(|s| s.split_once('='))
                .find_map(|(k, v)| (k == key && digits(v)).then_some(v))
            {
                return Some(format!("{canonical}/problem/{id}"));
            }
        }
    }
    if host == "spoj.com" && p.len() == 3 && p[1] == "problems" {
        return Some(format!("spoj.com/problems/{}", p[2].to_uppercase()));
    }
    Some(format!("{host}{path}"))
}
fn matches(row: &Value, topic: &Value) -> bool {
    original(&row["url"])
        .is_some_and(|id| array(&topic["practiceOriginals"]).iter().any(|v| v == &id))
        || !truth(&row["knowledgeReviewRequired"])
            && array(&topic["tags"])
                .iter()
                .any(|tag| array(&row["tags"]).contains(tag))
}
fn stage(topics: &[Value]) -> usize {
    if topics
        .iter()
        .take(7)
        .filter(|t| t["level"].as_u64().unwrap_or(0) >= 5)
        .count()
        < 3
    {
        0
    } else if topics
        .iter()
        .skip(7)
        .filter(|t| t["level"].as_u64().unwrap_or(0) >= 5)
        .count()
        < 3
    {
        1
    } else if topics
        .iter()
        .skip(7)
        .filter(|t| t["level"].as_u64().unwrap_or(0) >= 6)
        .count()
        < 3
    {
        2
    } else {
        3
    }
}
fn task(
    kind: &str,
    id: Value,
    title: String,
    minutes: i64,
    topic: Value,
    condition: &str,
) -> Value {
    json!({"key":format!("{kind}:{}",id.as_str().unwrap_or("")),"kind":kind,"id":id,"title":title,"minutes":minutes,"topicId":topic,"condition":condition})
}

pub struct Planner<'a, 'b> {
    pub training: Training<'a>,
    pub curriculum: &'b Value,
    pub quizzes: &'b Value,
    pub builtins: &'b [Value],
}
impl Planner<'_, '_> {
    fn definitions(&self) -> Result<&[Value], ApiError> {
        self.curriculum["topics"]
            .as_array()
            .map(Vec::as_slice)
            .filter(|v| !v.is_empty())
            .ok_or_else(|| ApiError::new(503, "CURRICULUM_MISSING", "学习课程目录尚未构建"))
    }
    fn load(&self) -> Result<Value, ApiError> {
        let v = self
            .training
            .personal
            .document(KEY)?
            .unwrap_or_else(learning::empty);
        if !v.is_object()
            || !v["revision"].is_string()
            || !["config", "checks", "seen", "view"]
                .iter()
                .all(|k| v[*k].is_object())
            || !["article", "topics", "diagnoses"]
                .iter()
                .all(|k| v[*k].is_array())
        {
            return Err(invalid());
        }
        if v.get("completed").is_some_and(|v| !v.is_object()) {
            return Err(invalid());
        }
        if v["checks"]
            .as_object()
            .unwrap()
            .values()
            .any(|entry| !entry.is_object())
        {
            return Err(invalid());
        }
        for key in ["plan", "proposal"] {
            if truth(&v[key]) {
                let plan = &v[key];
                if !plan.is_object()
                    || !plan["tasks"].is_array()
                    || !plan["tracks"].is_array()
                    || !plan["days"].is_array()
                    || !plan["week"].is_string()
                    || date(text(plan, "week")).is_err()
                    || self.tracks(&plan["tracks"]).is_err()
                    || !plan["id"].is_string()
                    || plan
                        .get("stage")
                        .is_some_and(|v| !v.as_u64().is_some_and(|n| n < 5))
                    || array(&plan["days"]).iter().any(|d| {
                        date(text(d, "date")).is_err()
                            || !d["minutes"]
                                .as_i64()
                                .is_some_and(|n| (0..=720).contains(&n))
                            || !d["used"].is_i64()
                    })
                    || plan.get("waiting").is_some_and(|w| !w.is_array())
                    || array(&plan["tasks"])
                        .iter()
                        .chain(array(&plan["waiting"]))
                        .any(|t| {
                            !t.is_object()
                                || !t["key"].is_string()
                                || !t["kind"].is_string()
                                || !t["minutes"].is_i64()
                        })
                {
                    return Err(invalid());
                }
            }
        }
        Ok(v)
    }
    fn scope(&self) -> Result<(), ApiError> {
        let special:bool=self.training.personal.db.query_row("SELECT EXISTS(SELECT 1 FROM submissions WHERE mode='submit' AND scope='official' AND finished_at IS NOT NULL) OR EXISTS(SELECT 1 FROM account_preferences WHERE key LIKE 'review-state:%' OR key LIKE 'review-task:%') OR EXISTS(SELECT 1 FROM contests) OR EXISTS(SELECT 1 FROM goals WHERE archived=0) OR EXISTS(SELECT 1 FROM account_problem_facts)",[],|r|r.get(0))?;
        if special {
            return Err(ApiError::pending());
        }
        Ok(())
    }
    fn atomic(&mut self, body: Option<&Value>) -> Result<Value, ApiError> {
        self.training
            .personal
            .db
            .execute_batch("SAVEPOINT native_learning")?;
        let result = match body {
            Some(body) => self.update_inner(body),
            None => self.refresh_inner(None),
        };
        match result {
            Ok(v) => {
                if let Err(error) = self
                    .training
                    .personal
                    .db
                    .execute_batch("RELEASE native_learning")
                {
                    self.training
                        .personal
                        .db
                        .execute_batch("ROLLBACK TO native_learning; RELEASE native_learning")?;
                    return Err(error.into());
                }
                Ok(v)
            }
            Err(error) => {
                self.training
                    .personal
                    .db
                    .execute_batch("ROLLBACK TO native_learning; RELEASE native_learning")?;
                Err(error)
            }
        }
    }
    pub fn refresh(&mut self) -> Result<Value, ApiError> {
        self.atomic(None)
    }
    pub fn update(&mut self, body: &Value) -> Result<Value, ApiError> {
        self.atomic(Some(body))
    }
    fn rows(&self) -> Result<Vec<Value>, ApiError> {
        let mut data = self.training.catalogue.data(true, "")?;
        Ok(serde_json::from_value(data["rows"].take())?)
    }
    fn records(&self) -> Result<Vec<Value>, ApiError> {
        Ok(serde_json::from_value(self.training.personal.rows(
            "SELECT * FROM submissions WHERE mode='submit' ORDER BY submitted_at,rowid",
            [],
        )?)?)
    }
    fn facts(&self, state: &Value, records: &[Value]) -> Result<Vec<Value>, ApiError> {
        self.scope()?;
        let ui = self.training.personal.document("ui")?.unwrap_or(json!({}));
        let mut out = Vec::new();
        for topic in self.definitions()? {
            let checked = &state["checks"][text(topic, "id")];
            if truth(checked) && !checked.is_object() {
                return Err(invalid());
            }
            let drills = self
                .builtins
                .iter()
                .find(|v| v["id"] == topic["template"])
                .map(|v| array(&v["practiceIds"]))
                .unwrap_or(&[]);
            let practice: Vec<_> = records
                .iter()
                .filter(|r| {
                    drills.contains(&r["problem_id"])
                        && r["scope"] == "template"
                        && r["verdict"] == "AC"
                        && truth(&r["finished_at"])
                })
                .collect();
            let read = truth(&checked["read"])
                || array(&ui["learnedLectures"])
                    .iter()
                    .any(|id| array(&topic["lectures"]).contains(id));
            let level = if practice.iter().any(|r| r["solution_seen"] == 0) {
                4
            } else if !practice.is_empty() {
                3
            } else if truth(&checked["concept"]) {
                2
            } else if read {
                1
            } else {
                0
            };
            out.push(json!({"id":topic["id"],"title":topic["title"],"level":level,"label":LEVELS[level],"independent":0,"publicAccepted":0,"retained":0,"evidence":[],"mixed":false,"lastAt":null}));
        }
        Ok(out)
    }
    fn tracks(&self, tracks: &Value) -> Result<Vec<String>, ApiError> {
        let v = array(tracks);
        let valid = self.definitions()?;
        let mut ids = HashSet::new();
        if !tracks.is_array()
            || v.is_empty()
            || v.len() > 5
            || v.iter().any(|id| {
                id.as_str().is_none()
                    || !valid.iter().any(|t| t["id"] == *id)
                    || !ids.insert(id.clone())
            })
        {
            return Err(ApiError::bad("请选择 1–5 条不同主线，共用每周总时间"));
        }
        Ok(v.iter().map(|v| v.as_str().unwrap().into()).collect())
    }
    fn default_tracks(&self, topics: &[Value]) -> Result<Vec<String>, ApiError> {
        let mut ready: HashSet<String> = topics
            .iter()
            .filter(|t| t["level"].as_u64().unwrap_or(0) >= 5)
            .map(|t| text(t, "id").into())
            .collect();
        let mut pending = ready.iter().cloned().collect::<Vec<_>>();
        while let Some(id) = pending.pop() {
            if let Some(t) = self.definitions()?.iter().find(|t| t["id"] == id) {
                for pre in array(&t["prerequisites"]).iter().filter_map(Value::as_str) {
                    if ready.insert(pre.into()) {
                        pending.push(pre.into())
                    }
                }
            }
        }
        if let Some(t) = self.definitions()?.iter().find(|t| {
            !ready.contains(text(t, "id"))
                && array(&t["prerequisites"])
                    .iter()
                    .all(|p| p.as_str().is_some_and(|p| ready.contains(p)))
        }) {
            return Ok(vec![text(t, "id").into()]);
        }
        topics
            .iter()
            .min_by_key(|t| (t["level"].as_u64().unwrap_or(0), text(t, "id")))
            .map(|t| vec![text(t, "id").into()])
            .ok_or_else(invalid)
    }
    fn config(&self, value: &Value, previous: &Value) -> Result<Value, ApiError> {
        let value = value
            .as_object()
            .filter(|v| {
                v.keys().all(|k| {
                    [
                        "goal",
                        "weekdayMinutes",
                        "weekendMinutes",
                        "restDays",
                        "team",
                        "role",
                    ]
                    .contains(&k.as_str())
                })
            })
            .ok_or_else(|| ApiError::bad("时间或目标设置无效"))?;
        let mut result = previous.clone();
        for (k, v) in value {
            result[k] = v.clone()
        }
        for k in ["weekdayMinutes", "weekendMinutes"] {
            if !result[k].as_i64().is_some_and(|n| (0..=720).contains(&n)) {
                return Err(ApiError::new(
                    422,
                    "VALIDATION",
                    "请填写工作日和周末可用分钟数（0–720）",
                ));
            }
        }
        if !result["restDays"]
            .as_array()
            .is_some_and(|v| v.len() <= 7 && v.iter().all(|d| d.as_u64().is_some_and(|n| n <= 6)))
        {
            return Err(ApiError::bad("休息日设置无效"));
        }
        if !result["team"].is_boolean()
            || !result["role"]
                .as_str()
                .is_some_and(|s| s.chars().count() <= 80)
        {
            return Err(ApiError::bad("队伍设置无效"));
        }
        let goal = &result["goal"];
        if !goal.as_object().is_some_and(|g| {
            g.keys()
                .all(|k| ["kind", "title", "deadline"].contains(&k.as_str()))
        }) || !matches!(
            goal["kind"].as_str(),
            Some("xcpc" | "cf" | "lanqiao" | "topic")
        ) || !goal["title"]
            .as_str()
            .is_some_and(|s| !s.trim().is_empty() && s.trim().chars().count() <= 160)
        {
            return Err(ApiError::bad("请填写一个具体总目标"));
        }
        if truth(&goal["deadline"]) {
            let deadline = date(
                goal["deadline"]
                    .as_str()
                    .ok_or_else(|| ApiError::bad("截止日期无效"))?,
            )
            .map_err(|_| ApiError::bad("截止日期无效"))?;
            if deadline < date(&day(self.training.now))? {
                return Err(ApiError::new(
                    422,
                    "VALIDATION",
                    "截止日期已过，请调整目标日期",
                ));
            }
        }
        Ok(result)
    }
    fn plan(
        &self,
        state: &Value,
        tracks: &[String],
        rows: &[Value],
        topics: &[Value],
        previous: Option<&Value>,
        pace: Option<&str>,
    ) -> Result<Value, ApiError> {
        let now = self.training.now;
        let week = monday(now);
        let today = day(now);
        let cfg = &state["config"];
        let pace = pace
            .or_else(|| previous.and_then(|p| p["pace"].as_str()))
            .unwrap_or("normal");
        if !["weekdayMinutes", "weekendMinutes"]
            .iter()
            .all(|k| cfg[*k].as_i64().is_some_and(|n| (0..=720).contains(&n)))
        {
            return Err(ApiError::new(422, "VALIDATION", "请先填写可用时间"));
        }
        let mut allocation=Allocation{days:(0..7).map(|d|json!({"date":(week+Duration::days(d)).to_string(),"minutes":if array(&cfg["restDays"]).contains(&json!(d)){0}else{cfg[if d<5{"weekdayMinutes"}else{"weekendMinutes"}].as_i64().unwrap()},"used":0})).collect(),tasks:Vec::new(),waiting:Vec::new(),used:HashSet::new(),today:today.clone(),now:stamp(now)};
        let prior = previous.unwrap_or(&Value::Null);
        if prior["week"] == week.to_string() {
            for done in array(&prior["tasks"])
                .iter()
                .filter(|t| t["status"] == "done")
            {
                allocation.used.insert(text(done, "key").into());
                if let Some(d) = allocation
                    .days
                    .iter_mut()
                    .find(|d| d["date"] == done["date"])
                {
                    d["used"] = json!(
                        d["used"].as_i64().unwrap_or(0)
                            + done["minutes"].as_i64().ok_or_else(invalid)?
                    )
                }
                allocation.tasks.push(done.clone())
            }
        }
        for item in array(&prior["tasks"])
            .iter()
            .chain(array(&prior["waiting"]))
            .filter(|t| {
                t["status"] != "done"
                    && (t["kind"] == "review"
                        || t["topicId"]
                            .as_str()
                            .is_some_and(|id| tracks.iter().any(|t| t == id)))
                    && t["kind"] != "mixed"
            })
        {
            allocation.add(item.clone())?;
        }
        if cfg["team"] == true {
            allocation.add(task(
                "reflection",
                json!(format!("team-{week}")),
                "按本人职责整理团队备赛复盘".into(),
                15,
                Value::Null,
                "记录本人职责内的训练结果与下一次队内配合安排",
            ))?
        }
        let definitions = self.definitions()?;
        let mut pool: Vec<&Value> = rows
            .iter()
            .filter(|r| {
                !truth(&r["catalogHidden"])
                    && !truth(&r["locked"])
                    && truth(&r["catalogStatementReady"])
                    && truth(&r["url"])
                    && definitions
                        .iter()
                        .any(|t| tracks.iter().any(|id| t["id"] == *id) && matches(r, t))
            })
            .collect();
        let rank = |r: &Value| {
            let name = format!(
                "{} {} {}",
                text(r, "contest"),
                text(r, "contestFullName"),
                text(r, "source")
            );
            if match cfg["goal"]["kind"].as_str() {
                Some("cf") => r["platform"] == "Codeforces",
                Some("lanqiao") => name.contains("蓝桥") || name.contains("lanqiao"),
                Some("xcpc") => name.contains("ICPC") || name.contains("CCPC"),
                _ => false,
            } {
                0
            } else {
                1
            }
        };
        pool.sort_by(|a, b| {
            rank(a)
                .cmp(&rank(b))
                .then(
                    a["difficulty"]
                        .as_f64()
                        .unwrap_or(10000.)
                        .total_cmp(&b["difficulty"].as_f64().unwrap_or(10000.)),
                )
                .then(text(a, "id").cmp(text(b, "id")))
        });
        let mut gaps = Vec::<String>::new();
        let mut mixed_minutes = allocation
            .days
            .iter()
            .filter(|d| text(d, "date") >= today.as_str())
            .map(|d| d["minutes"].as_i64().unwrap() - d["used"].as_i64().unwrap())
            .max()
            .unwrap_or(0)
            .min(45);
        if mixed_minutes >= 10 {
            mixed_minutes = (mixed_minutes - 10).max(5)
        }
        let mixed_pool: Vec<_> = pool
            .iter()
            .copied()
            .filter(|r| {
                r["difficulty"]
                    .as_f64()
                    .is_some_and(|n| n.is_finite() && n > 0.)
            })
            .collect();
        let mut mixed_originals = HashSet::new();
        if !mixed_pool.is_empty() && mixed_minutes != 0 {
            let mut chosen = Vec::<String>::new();
            for tid in tracks {
                let topic = definitions
                    .iter()
                    .find(|t| t["id"] == *tid)
                    .ok_or_else(invalid)?;
                if let Some(row) = mixed_pool
                    .iter()
                    .find(|r| matches(r, topic) && !mixed_originals.contains(&original(&r["url"])))
                {
                    mixed_originals.insert(original(&row["url"]));
                    chosen.push(text(row, "id").into())
                }
            }
            let count = tracks.len().max((mixed_minutes / 15).clamp(1, 3) as usize);
            for row in &mixed_pool {
                if chosen.len() >= count {
                    break;
                }
                if !mixed_originals.insert(original(&row["url"])) {
                    continue;
                }
                chosen.push(text(row, "id").into())
            }
            let mut mixed = task(
                "mixed",
                json!(week.to_string()),
                "本周无算法提示综合检验与复盘".into(),
                mixed_minutes,
                Value::Null,
                "独立计时交卷，并完成复盘；样例通过不等于正式 AC",
            );
            mixed["ids"] = json!(chosen);
            mixed["reflectionMinutes"] = json!(10.min(mixed_minutes / 3));
            if let Some(d) = allocation.days.iter().rev().find(|d| {
                text(d, "date") >= today.as_str()
                    && d["minutes"].as_i64().unwrap() - d["used"].as_i64().unwrap() >= mixed_minutes
            }) {
                mixed["notBefore"] = d["date"].clone()
            }
            allocation.add(mixed)?;
        } else if mixed_minutes != 0 {
            gaps.push("综合检验题面正在准备；已有课程与复习仍可继续".into())
        }
        for tid in tracks {
            let topic = definitions
                .iter()
                .find(|t| t["id"] == *tid)
                .ok_or_else(invalid)?;
            let proof = topics
                .iter()
                .find(|t| t["id"] == *tid)
                .ok_or_else(invalid)?;
            let level = proof["level"].as_u64().ok_or_else(invalid)?;
            if pace != "practice" && (level < 2 || pace == "foundation") {
                if pace == "foundation" || !truth(&state["checks"][tid]["read"]) {
                    if let Some(id) = array(&topic["lectures"]).first() {
                        let mut reading = task(
                            "lecture",
                            id.clone(),
                            format!(
                                "{}{}",
                                if pace == "foundation" {
                                    "复习："
                                } else {
                                    "阅读："
                                },
                                text(topic, "title")
                            ),
                            if pace == "foundation" { 10 } else { 15 },
                            json!(tid),
                            "读完后确认",
                        );
                        if pace == "foundation" {
                            reading["key"] =
                                json!(format!("{}:support:{week}", text(&reading, "key")))
                        }
                        allocation.add(reading)?
                    }
                }
                if self.quizzes.get(tid).is_some() {
                    allocation.add(task(
                        "quiz",
                        json!(tid),
                        format!("原理检查：{}", text(topic, "title")),
                        5,
                        json!(tid),
                        "回答适用条件或边界问题",
                    ))?
                }
            }
            if pace != "practice" && (level < 5 || pace == "foundation") {
                if truth(&topic["course"]) {
                    allocation.add(task(
                        "course",
                        topic["course"].clone(),
                        format!("实验与跟做：{}", text(topic, "title")),
                        20,
                        json!(tid),
                        "在课程内完成对应操作，再用脱离示例的实现验证",
                    ))?
                }
                if let Some(template) = self.builtins.iter().find(|t| t["id"] == topic["template"])
                {
                    if let Some(id) = array(&template["practiceIds"]).first() {
                        allocation.add(task(
                            "template-problem",
                            id.clone(),
                            format!("实现检查：{}", text(topic, "title")),
                            25,
                            json!(tid),
                            "本操作练习全部案例通过",
                        ))?
                    }
                }
            }
            let actual_mixed: HashSet<_> = allocation
                .tasks
                .iter()
                .filter(|t| t["kind"] == "mixed")
                .flat_map(|t| array(&t["ids"]))
                .filter_map(|id| rows.iter().find(|r| r["id"] == *id))
                .map(|r| original(&r["url"]))
                .collect();
            let candidates: Vec<_> = pool
                .iter()
                .filter(|r| matches(r, topic) && !actual_mixed.contains(&original(&r["url"])))
                .collect();
            for row in candidates.iter().take(2) {
                let mut t = task(
                    "problem",
                    row["id"].clone(),
                    text(row, "title").into(),
                    30,
                    json!(tid),
                    "原站正式 AC；本轮使用提示时另记辅助完成",
                );
                t["original"] =
                    json!(original(&row["url"]).unwrap_or_else(|| text(row, "id").into()));
                allocation.add(t)?
            }
            if candidates.is_empty() {
                gaps.push(format!(
                    "{}：需要补充完整、未做过的原题",
                    text(topic, "title")
                ))
            }
        }
        allocation.tasks.sort_by(|a, b| {
            text(a, "date")
                .cmp(text(b, "date"))
                .then(a["order"].as_i64().cmp(&b["order"].as_i64()))
        });
        for (i, t) in allocation.tasks.iter_mut().enumerate() {
            t["order"] = json!(i + 1)
        }
        let allocations:Vec<_>=tracks.iter().map(|id|json!({"id":id,"title":definitions.iter().find(|t|t["id"]==*id).unwrap()["title"],"minutes":allocation.tasks.iter().filter(|t|t["topicId"]==*id).filter_map(|t|t["minutes"].as_i64()).sum::<i64>()})).collect();
        Ok(
            json!({"id":uuid(),"week":week.to_string(),"stage":prior.get("stage").cloned().unwrap_or(json!(stage(topics))),"pace":pace,"tracks":tracks,"tasks":allocation.tasks,"waiting":allocation.waiting,"days":allocation.days,"allocations":allocations,"gaps":gaps,"createdAt":stamp(now),"configHash":digest(cfg)}),
        )
    }
    fn save(&self, state: &mut Value) -> Result<(), ApiError> {
        state["revision"] = json!(uuid());
        PersonalStore::put(
            &self.training.personal.db,
            KEY,
            &state.to_string(),
            &stamp(self.training.now),
        )
    }
    fn archive(&self, state: &Value, reason: &str) -> Result<(), ApiError> {
        if array(&state["article"]).is_empty() {
            return Ok(());
        }
        let id = uuid();
        let value = json!({"id":id,"at":stamp(self.training.now),"reason":reason,"article":state["article"],"topics":state["topics"],"plan":if truth(&state["plan"]){state["plan"].clone()}else{json!({})}});
        PersonalStore::put(
            &self.training.personal.db,
            &format!("{HISTORY}{id}"),
            &value.to_string(),
            &stamp(self.training.now),
        )
    }
    fn article(&self, state: &Value) -> Result<Value, ApiError> {
        let plan = &state["plan"];
        let topics = array(&state["topics"]);
        let current = plan
            .get("stage")
            .and_then(Value::as_u64)
            .map(|n| n as usize)
            .unwrap_or_else(|| stage(topics));
        if current >= STAGES.len() {
            return Err(invalid());
        }
        let tracks = if truth(plan) {
            &plan["tracks"]
        } else {
            &state["recommendation"]["tracks"]
        };
        let active: Vec<_> = topics
            .iter()
            .filter(|t| array(tracks).contains(&t["id"]))
            .collect();
        let pending: Vec<_> = array(&plan["tasks"])
            .iter()
            .filter(|t| t["status"] != "done")
            .collect();
        let next = if let Some(t) = pending.first() {
            format!("{} · {} 分钟", text(t, "title"), t["minutes"])
        } else if !truth(plan) {
            "填写可用时间，按推荐开始。".into()
        } else {
            "本周任务已完成，接下来复习。".into()
        };
        let total = array(&plan["days"])
            .iter()
            .filter_map(|d| d["minutes"].as_i64())
            .sum::<i64>();
        let progress = active
            .iter()
            .map(|t| {
                format!(
                    "{}：{}",
                    text(t, "title"),
                    LEVELS[(t["level"].as_u64().unwrap_or(0) as usize + 1).min(6)]
                )
            })
            .collect::<Vec<_>>()
            .join("；");
        let focus = active
            .iter()
            .map(|t| text(t, "title"))
            .collect::<Vec<_>>()
            .join("、");
        let mut paragraphs = vec![
            (
                "stage",
                "当前重点",
                if focus.is_empty() {
                    STAGES[current].into()
                } else {
                    focus
                },
            ),
            ("progress", "这周进展", "新独立通过 0 道题。".into()),
            (
                "gaps",
                "接下来补",
                if progress.is_empty() {
                    "先做一次短检验。".into()
                } else {
                    progress
                },
            ),
            (
                "week",
                "本周安排",
                if truth(plan) {
                    format!("{} 项待完成，共 {total} 分钟。", pending.len())
                } else {
                    "填写每天可用时间，系统推荐学习安排。".into()
                },
            ),
            ("next", "现在做什么", next),
            (
                "route",
                "下一阶段",
                format!("{}。先通过当前专题检验。", STAGES[(current + 1).min(4)]),
            ),
            (
                "estimate",
                "剩余用时",
                if truth(plan) {
                    format!(
                        "{} 分钟，按实际完成情况调整。",
                        pending
                            .iter()
                            .filter_map(|t| t["minutes"].as_i64())
                            .sum::<i64>()
                    )
                } else {
                    "填写可用时间后安排。".into()
                },
            ),
            (
                "daily",
                "今天进度",
                format!(
                    "完成 {} 项计划任务。",
                    array(&plan["tasks"])
                        .iter()
                        .filter(|t| t["status"] == "done" && t["date"] == day(self.training.now))
                        .count()
                ),
            ),
        ];
        if let Some(d) = array(&state["diagnoses"]).last() {
            let (_, title, _) = DIAGNOSES
                .iter()
                .find(|(id, _, _)| *id == text(d, "reason"))
                .ok_or_else(invalid)?;
            paragraphs.push(("diagnosis", title, text(d, "advice").into()))
        }
        Ok(json!(
            paragraphs
                .into_iter()
                .map(|(id, title, text)| {
                    let mut p = json!({"id":id,"title":title,"text":text});
                    p["hash"] = json!(digest(&p));
                    p
                })
                .collect::<Vec<_>>()
        ))
    }
    fn complete_task(
        &self,
        task: &Value,
        records: &[Value],
        state: &Value,
    ) -> Result<bool, ApiError> {
        if task["status"] == "done" {
            return Ok(true);
        }
        let kind = text(task, "kind");
        if ["lecture", "quiz", "reflection"].contains(&kind) {
            return Ok(truth(&state["completed"][text(task, "key")]));
        }
        if kind == "mixed" || kind == "course" {
            return Ok(false);
        }
        let ids = self.training.ids(text(task, "id"))?;
        let threshold = parsed(&task["createdAt"]);
        let minimum = parsed(&task["minimumAt"]);
        for r in records {
            if !r["problem_id"]
                .as_str()
                .is_some_and(|id| ids.iter().any(|v| v == id))
                || r["verdict"] != "AC"
                || !truth(&r["finished_at"])
            {
                continue;
            }
            let at = parsed(&r["submitted_at"]).ok_or_else(invalid)?;
            if threshold.is_some_and(|t| at < t)
                || minimum.is_some_and(|t| at < t)
                || truth(&task["notBefore"]) && day(at).as_str() < text(task, "notBefore")
            {
                continue;
            }
            if ["problem", "review"].contains(&kind) && r["scope"] != "official"
                || kind == "template-problem" && r["scope"] != "template"
                || kind == "review" && r["solution_seen"] != 0
            {
                continue;
            }
            return Ok(true);
        }
        Ok(false)
    }
    fn refresh_inner(&mut self, provided: Option<Value>) -> Result<Value, ApiError> {
        self.scope()?;
        let mut state = provided.map(Ok).unwrap_or_else(|| self.load())?;
        let before = digest(&state);
        let records = self.records()?;
        let topics = self.facts(&state, &records)?;
        let suggested = self.default_tracks(&topics)?;
        let recommended = topics
            .iter()
            .find(|t| t["id"] == suggested[0])
            .ok_or_else(invalid)?;
        state["topics"] = json!(topics);
        state["recommendation"] = json!({"tracks":suggested,"title":recommended["title"],"reason":"先用一小节确认起点。"});
        if truth(&state["plan"]) {
            let previous = state["plan"].clone();
            let mut plan = previous.clone();
            for task in plan["tasks"].as_array_mut().ok_or_else(invalid)? {
                if task["status"] != "done" && self.complete_task(task, &records, &state)? {
                    task["status"] = json!("done");
                    task["completedAt"] = json!(stamp(self.training.now))
                }
            }
            if let Some(waiting) = plan.get_mut("waiting").and_then(Value::as_array_mut) {
                for task in waiting {
                    if task["status"] != "done" && self.complete_task(task, &records, &state)? {
                        task["status"] = json!("done");
                        task["completedAt"] = json!(stamp(self.training.now))
                    }
                }
            }
            if plan["week"] != monday(self.training.now).to_string() {
                let mut history = state.clone();
                history["plan"] = previous;
                self.archive(&history, "周结束")?;
                let rows = self.rows()?;
                let tracks = self.tracks(&plan["tracks"])?;
                plan = self.plan(
                    &state,
                    &tracks,
                    &rows,
                    array(&state["topics"]),
                    Some(&plan),
                    None,
                )?
            }
            state["plan"] = plan;
        }
        let initial = array(&state["article"]).is_empty();
        state["article"] = self.article(&state)?;
        if initial {
            state["seen"] = json!(
                array(&state["article"])
                    .iter()
                    .map(|p| (text(p, "id").to_string(), p["hash"].clone()))
                    .collect::<serde_json::Map<_, _>>()
            )
        }
        let mut seconds = 0.;
        for value in self
            .training
            .personal
            .documents("effective-learning-day:")?
        {
            let mut intervals: Vec<[f64; 2]> = serde_json::from_value(value["intervals"].clone())?;
            seconds += learning::merge_intervals(&mut intervals)
                .iter()
                .map(|[a, b]| b - a)
                .sum::<f64>()
        }
        state["effectiveSeconds"] = json!(seconds.round_ties_even() as i64);
        let began = parsed(
            state["plan"]
                .get("acceptedAt")
                .unwrap_or(&state["plan"]["createdAt"]),
        )
        .unwrap_or(self.training.now);
        state["stalled"] = json!(
            truth(&state["plan"])
                && array(&state["plan"]["tasks"])
                    .iter()
                    .any(|t| t["status"] != "done")
                && (self.training.now - began).num_seconds() >= 3 * 86400
        );
        if digest(&state) != before {
            state["updatedAt"] = json!(stamp(self.training.now));
            self.save(&mut state)?
        }
        learning::snapshot(self.training.personal, self.curriculum, self.training.now)
    }
    fn task_index(state: &Value, key: &Value) -> Result<usize, ApiError> {
        array(&state["plan"]["tasks"])
            .iter()
            .position(|t| t["key"] == *key)
            .ok_or_else(|| ApiError::missing("任务已变化，请重新读取"))
    }
    fn update_inner(&mut self, body: &Value) -> Result<Value, ApiError> {
        let mut state = self.load()?;
        if body.get("revision") != state.get("revision") {
            return Err(ApiError::conflict("规划已更新，请读取后重试"));
        }
        let action = required_text(body, "action", 40)?;
        let running: bool = self.training.personal.db.query_row(
            "SELECT EXISTS(SELECT 1 FROM contests WHERE status='running')",
            [],
            |r| r.get(0),
        )?;
        if running {
            return Err(ApiError::conflict("请先完成当前限时训练，交卷后再调整规划"));
        }
        self.scope()?;
        match action {
            "configure" => {
                state["config"] = self.config(&body["config"], &state["config"])?;
                let records = self.records()?;
                let topics = self.facts(&state, &records)?;
                state["topics"] = json!(topics);
                let chosen = if body["recommended"] == true {
                    json!(self.default_tracks(&topics)?)
                } else if truth(&body["tracks"]) {
                    body["tracks"].clone()
                } else if truth(&state["plan"]["tracks"]) {
                    state["plan"]["tracks"].clone()
                } else {
                    json!(self.default_tracks(&topics)?)
                };
                let tracks = self.tracks(&chosen)?;
                let rows = self.rows()?;
                if truth(&state["plan"]) && chosen == state["plan"]["tracks"] {
                    self.archive(&state, "调整时间安排")?;
                    state["plan"] =
                        self.plan(&state, &tracks, &rows, &topics, Some(&state["plan"]), None)?
                } else {
                    state["proposal"] = self.plan(&state, &tracks, &rows, &topics, None, None)?;
                    state["proposal"]["reason"] =
                        json!("按照目标、学习证据与共享时间预算制定；采纳后执行")
                }
            }
            "propose" => {
                let tracks = self.tracks(&body["tracks"])?;
                if state["config"]["weekdayMinutes"].is_null() {
                    return Err(ApiError::new(422, "VALIDATION", "请先填写可用时间"));
                }
                let rows = self.rows()?;
                let topics = self.facts(&state, &self.records()?)?;
                state["proposal"] =
                    self.plan(&state, &tracks, &rows, &topics, Some(&state["plan"]), None)?;
                state["proposal"]["reason"] = if truth(&body["reason"]) {
                    body["reason"].clone()
                } else {
                    json!("调整学习主线；请核对时间重新分配与各主线节奏")
                };
            }
            "accept" => {
                if !truth(&state["proposal"])
                    || body.get("proposalId") != state["proposal"].get("id")
                {
                    return Err(ApiError::conflict("方案已变化，请重新查看"));
                }
                self.archive(&state, "采纳重新规划")?;
                state["plan"] = state["proposal"].take();
                state["plan"]["acceptedAt"] = json!(stamp(self.training.now));
            }
            "dismiss" => state["proposal"] = Value::Null,
            "complete" => {
                let index = Self::task_index(&state, &body["key"])?;
                let task = state["plan"]["tasks"][index].clone();
                if !["lecture", "reflection"].contains(&text(&task, "kind")) {
                    return Err(ApiError::new(
                        422,
                        "VALIDATION",
                        "本任务须通过实际作答或原理检查完成",
                    ));
                }
                if state.get("completed").is_none() {
                    state["completed"] = json!({})
                }
                state["completed"][text(&task, "key")] = json!(stamp(self.training.now));
                state["plan"]["tasks"][index]["status"] = json!("done");
                if let Some(tid) = task["topicId"].as_str() {
                    if state["checks"].get(tid).is_none() {
                        state["checks"][tid] = json!({})
                    }
                    state["checks"][tid]["read"] = json!(stamp(self.training.now))
                }
            }
            "quiz" => {
                let tid = body["topicId"]
                    .as_str()
                    .ok_or_else(|| ApiError::bad("检查题目无效"))?;
                let quiz = self
                    .quizzes
                    .get(tid)
                    .filter(|q| q.is_array())
                    .ok_or_else(|| ApiError::bad("检查题目无效"))?;
                let answer = body["answer"]
                    .as_i64()
                    .ok_or_else(|| ApiError::bad("检查题目无效"))?;
                if quiz[2] != answer {
                    return Err(ApiError::new(
                        422,
                        "VALIDATION",
                        "尚未通过，请重新核对适用条件与边界",
                    ));
                }
                if state["checks"].get(tid).is_none() {
                    state["checks"][tid] = json!({})
                }
                state["checks"][tid]["concept"] = json!(stamp(self.training.now));
                if state.get("completed").is_none() {
                    state["completed"] = json!({})
                }
                state["completed"][format!("quiz:{tid}")] = json!(stamp(self.training.now));
            }
            "difficulty" => {
                let reason = body["reason"]
                    .as_str()
                    .ok_or_else(|| ApiError::bad("请选择遇到的困难"))?;
                let (_, _, advice) = DIAGNOSES
                    .iter()
                    .find(|(id, _, _)| *id == reason)
                    .ok_or_else(|| ApiError::bad("请选择遇到的困难"))?;
                let diagnoses = state["diagnoses"].as_array_mut().ok_or_else(invalid)?;
                diagnoses
                    .push(json!({"reason":reason,"at":stamp(self.training.now),"advice":advice}));
                if diagnoses.len() > 32 {
                    diagnoses.remove(0);
                }
                if ["hard", "easy", "forgot"].contains(&reason) && truth(&state["plan"]) {
                    let mut previous = state["plan"].clone();
                    previous["tasks"] = json!(
                        array(&previous["tasks"])
                            .iter()
                            .filter(|t| t["status"] == "done")
                            .cloned()
                            .collect::<Vec<_>>()
                    );
                    previous["waiting"] = json!([]);
                    let tracks = self.tracks(&previous["tracks"])?;
                    let rows = self.rows()?;
                    let topics = self.facts(&state, &self.records()?)?;
                    state["proposal"] = self.plan(
                        &state,
                        &tracks,
                        &rows,
                        &topics,
                        Some(&previous),
                        Some(if reason == "easy" {
                            "practice"
                        } else {
                            "foundation"
                        }),
                    )?;
                    state["proposal"]["reason"] = json!(if reason == "easy" {
                        "跳过讲解，直接用新题验证。"
                    } else {
                        "先补一节讲解，再做短练习。"
                    })
                }
            }
            "postpone" => {
                let index = Self::task_index(&state, &body["key"])?;
                let d = date(body["date"].as_str().unwrap_or(""))?;
                if d < date(&day(self.training.now))? {
                    return Err(ApiError::new(422, "VALIDATION", "请选择今天或之后的日期"));
                }
                state["plan"]["tasks"][index]["notBefore"] = json!(d.to_string());
                let rows = self.rows()?;
                let tracks = self.tracks(&state["plan"]["tracks"])?;
                let topics = self.facts(&state, &self.records()?)?;
                state["plan"] =
                    self.plan(&state, &tracks, &rows, &topics, Some(&state["plan"]), None)?;
            }
            "replace" => {
                let index = Self::task_index(&state, &body["key"])?;
                let task = &state["plan"]["tasks"][index];
                if task["kind"] != "problem" || task["status"] == "done" {
                    return Err(ApiError::new(
                        422,
                        "VALIDATION",
                        "只更换尚未完成的独立原题；复习可推迟",
                    ));
                }
                let topic = self
                    .definitions()?
                    .iter()
                    .find(|t| t["id"] == task["topicId"])
                    .ok_or_else(invalid)?;
                let seen: HashSet<String> = self
                    .records()?
                    .iter()
                    .map(|r| text(r, "problem_id").into())
                    .collect();
                let originals: HashSet<_> = array(&state["plan"]["tasks"])
                    .iter()
                    .chain(array(&state["plan"]["waiting"]))
                    .filter_map(|t| t["original"].as_str())
                    .collect();
                let rows = self.rows()?;
                let mut choices: Vec<_> = rows
                    .iter()
                    .filter(|r| {
                        truth(&r["catalogStatementReady"])
                            && !truth(&r["catalogHidden"])
                            && truth(&r["url"])
                            && !seen.contains(text(r, "id"))
                            && original(&r["url"])
                                .is_none_or(|key| !originals.contains(key.as_str()))
                            && matches(r, topic)
                    })
                    .collect();
                choices.sort_by(|a, b| {
                    a["difficulty"]
                        .as_f64()
                        .unwrap_or(10000.)
                        .total_cmp(&b["difficulty"].as_f64().unwrap_or(10000.))
                        .then(text(a, "id").cmp(text(b, "id")))
                });
                let row = choices.first().ok_or_else(|| {
                    ApiError::new(
                        422,
                        "VALIDATION",
                        "同类可执行原题正在补充，可以先保留此题或推迟",
                    )
                })?;
                let task = &mut state["plan"]["tasks"][index];
                task["id"] = row["id"].clone();
                task["key"] = json!(format!("problem:{}", text(row, "id")));
                task["title"] = row["title"].clone();
                task["original"] = json!(original(&row["url"]));
                task["createdAt"] = json!(stamp(self.training.now));
            }
            "assist" => {
                let index = Self::task_index(&state, &body["key"])?;
                let task = &state["plan"]["tasks"][index];
                let id = required_text(body, "problemId", 512)?;
                let row = crate::catalogue::row_or_portable(
                    self.training.catalogue,
                    self.training.personal,
                    id,
                )?;
                if let Some(topic) = self
                    .definitions()?
                    .iter()
                    .find(|t| t["id"] == task["topicId"])
                {
                    if ["lecture", "course", "template"].contains(&text(task, "kind"))
                        && matches(&row, topic)
                    {
                        self.training.mark_seen(id)?
                    }
                }
            }
            "reflect" => {
                Self::task_index(&state, &body["key"])?;
                return Err(ApiError::new(
                    422,
                    "VALIDATION",
                    "先完成限时检验，再确认复盘",
                ));
            }
            _ => return Err(ApiError::bad("不支持这个规划操作")),
        }
        self.save(&mut state)?;
        self.refresh_inner(Some(state))
    }
}

struct Allocation {
    days: Vec<Value>,
    tasks: Vec<Value>,
    waiting: Vec<Value>,
    used: HashSet<String>,
    today: String,
    now: String,
}
impl Allocation {
    fn add(&mut self, mut task: Value) -> Result<(), ApiError> {
        if truth(&task["original"]) {
            if let Some(existing) = self
                .tasks
                .iter_mut()
                .find(|t| t.get("original") == task.get("original"))
            {
                let mut purposes = if existing["purposes"].is_array() {
                    array(&existing["purposes"]).to_vec()
                } else {
                    vec![existing["topicId"].clone()]
                };
                purposes.push(task["topicId"].clone());
                purposes.sort_by_key(|v| {
                    if v.is_null() {
                        "None".into()
                    } else {
                        v.as_str()
                            .map(str::to_string)
                            .unwrap_or_else(|| v.to_string())
                    }
                });
                purposes.dedup();
                existing["purposes"] = json!(purposes);
                return Ok(());
            }
        }
        if !self.used.insert(text(&task, "key").into()) {
            return Ok(());
        }
        task["status"] = json!("pending");
        if !truth(&task["createdAt"]) {
            task["createdAt"] = json!(self.now)
        }
        let minutes = task["minutes"].as_i64().ok_or_else(invalid)?;
        let not_before = task["notBefore"].as_str().unwrap_or(&self.today);
        if let Some(day) = self.days.iter_mut().find(|d| {
            text(d, "date") >= self.today.as_str()
                && text(d, "date") >= not_before
                && d["minutes"].as_i64().unwrap_or(0) - d["used"].as_i64().unwrap_or(0) >= minutes
        }) {
            day["used"] = json!(day["used"].as_i64().unwrap_or(0) + minutes);
            task["date"] = day["date"].clone();
            task["order"] = json!(self.tasks.len() + 1);
            self.tasks.push(task)
        } else {
            self.waiting.push(task)
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{catalogue::Catalogue, library::Library};
    fn with_planner(run: impl FnOnce(&mut Planner<'_, '_>)) {
        let temp = tempfile::TempDir::new().unwrap();
        let mut personal = PersonalStore::open(&temp.path().join("private.sqlite3")).unwrap();
        let catalogue = Catalogue {
            db: rusqlite::Connection::open_in_memory().unwrap(),
        };
        let library = Library {
            db: rusqlite::Connection::open_in_memory().unwrap(),
        };
        let curriculum = json!({"topics":[{"id":"io-basics","title":"输入输出","prerequisites":[],"tags":["输入输出"],"lectures":[]}],"courses":{}});
        let quizzes = json!({"io-basics":["输出什么？",["和","地址"],0]});
        let training = Training {
            catalogue: &catalogue,
            library: &library,
            personal: &mut personal,
            now: DateTime::parse_from_rfc3339("2026-11-05T04:00:00Z")
                .unwrap()
                .with_timezone(&Utc),
        };
        run(&mut Planner {
            training,
            curriculum: &curriculum,
            quizzes: &quizzes,
            builtins: &[],
        });
    }
    #[test]
    fn refresh_does_not_guess_time_or_independent_mastery() {
        with_planner(|p| {
            let state = p.refresh().unwrap();
            assert!(state["plan"].is_null());
            assert!(state["config"]["weekdayMinutes"].is_null());
            assert_eq!(state["topics"][0]["level"], 0);
            let again = p.refresh().unwrap();
            assert_eq!(again["revision"], state["revision"]);
        });
    }
    #[test]
    fn wrong_check_does_not_create_evidence_and_correct_only_proves_concept() {
        with_planner(|p| {
            assert_eq!(
                p.update(&json!({"action":"quiz","revision":"","topicId":"io-basics","answer":1}))
                    .unwrap_err()
                    .status,
                422
            );
            assert!(p.training.personal.document(KEY).unwrap().is_none());
            let state = p
                .update(&json!({"action":"quiz","revision":"","topicId":"io-basics","answer":0}))
                .unwrap();
            assert_eq!(state["topics"][0]["level"], 2);
            assert_eq!(state["topics"][0]["independent"], 0);
            assert!(p.training.personal.db.is_autocommit());
        });
    }
    #[test]
    fn malformed_checks_preserve_state_and_connection_recovers() {
        with_planner(|p| {
            let mut state = learning::empty();
            state["checks"] = json!({"io-basics":42});
            p.training.personal.put_document(KEY, &state).unwrap();
            assert_eq!(p.refresh().unwrap_err().code, "INVALID_STORED_DATA");
            assert_eq!(p.training.personal.document(KEY).unwrap().unwrap(), state);
            assert!(p.training.personal.db.is_autocommit());
            p.training
                .personal
                .put_document(KEY, &learning::empty())
                .unwrap();
            assert!(p.refresh().is_ok());
        });
    }
    #[test]
    fn official_history_cannot_be_projected_as_empty_evidence() {
        with_planner(|p| {
            p.training.personal.db.execute("INSERT INTO submissions(id,problem_id,mode,code,scope,submitted_at,finished_at,verdict) VALUES('receipt','sample','submit','original source','official','2026-11-04T00:00:00Z','2026-11-04T00:00:01Z','AC')",[]).unwrap();
            assert_eq!(p.refresh().unwrap_err().code, "MIGRATION_PENDING");
            assert!(p.training.personal.document(KEY).unwrap().is_none());
            assert!(p.training.personal.db.is_autocommit());
        });
    }
}
