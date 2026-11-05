use crate::{
    api::{ApiError, ApiRequest, fields, required_text},
    catalogue::{Catalogue, row_or_portable},
    learning::{day, stamp},
    library::Library,
    storage::PersonalStore,
    templates,
};
use chrono::{DateTime, Utc};
use rusqlite::{OptionalExtension, params, params_from_iter, types::Value as SqlValue};
use serde_json::{Value, json};
use std::collections::{HashMap, HashSet};

fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v.get(key).and_then(Value::as_str).unwrap_or("")
}
fn truth(v: &Value) -> bool {
    match v {
        Value::Null => false,
        Value::Bool(v) => *v,
        Value::String(v) => !v.is_empty(),
        Value::Number(n) => n.as_f64() != Some(0.),
        Value::Array(v) => !v.is_empty(),
        Value::Object(v) => !v.is_empty(),
    }
}
pub fn parse(value: &str) -> Result<DateTime<Utc>, ApiError> {
    DateTime::parse_from_rfc3339(value)
        .map(|v| v.with_timezone(&Utc))
        .map_err(|_| ApiError::new(500, "INVALID_STORED_DATA", "历史日期格式异常，原数据已保留"))
}

pub struct Training<'a> {
    pub catalogue: &'a Catalogue,
    pub library: &'a Library,
    pub personal: &'a mut PersonalStore,
    pub now: DateTime<Utc>,
}
impl Training<'_> {
    pub fn canonical(&self, id: &str) -> Result<String, ApiError> {
        Ok(self.catalogue.canonical(id)?.unwrap_or_else(|| id.into()))
    }
    pub fn ids(&self, id: &str) -> Result<Vec<String>, ApiError> {
        self.catalogue.equivalent(id)
    }
    fn running(&self) -> Result<Option<Value>, ApiError> {
        Ok(self
            .personal
            .rows("SELECT * FROM contests WHERE status='running'", [])?
            .as_array()
            .unwrap()
            .first()
            .cloned())
    }
    pub fn locked(&self, id: &str) -> Result<bool, ApiError> {
        let Some(contest) = self.running()? else {
            return Ok(false);
        };
        let slots: Value = serde_json::from_str(text(&contest, "slots"))?;
        let target = self.canonical(id)?;
        for slot in slots
            .as_array()
            .ok_or_else(|| ApiError::new(500, "INVALID_STORED_DATA", "比赛题目记录格式异常"))?
        {
            if self.canonical(text(slot, "id"))? == target {
                return Ok(true);
            }
        }
        Ok(false)
    }
    pub fn assert_unlocked(&self, id: &str) -> Result<(), ApiError> {
        if self.locked(id)? {
            return Err(ApiError::new(
                403,
                "CONTEST_LOCKED",
                "模拟赛进行中，这道题的题解已锁定。交卷后可以复盘。",
            ));
        }
        Ok(())
    }
    pub fn history_visible(&self, id: &str, context: Option<&str>) -> Result<(), ApiError> {
        if let Some(contest) = self.running()? {
            if context != Some(text(&contest, "id")) && self.locked(id)? {
                return Err(ApiError::new(
                    403,
                    "CONTEST_LOCKED",
                    "这道题正在模拟赛中，请从当前考场打开；旧草稿和提交记录赛后恢复。",
                ));
            }
        }
        Ok(())
    }
    fn simple_workspace_supported(&self) -> Result<(), ApiError> {
        // Reviewed scheduling and legacy goals are a separate migration stage.
        // Refuse before any mutation when their facts would affect this view.
        let special:bool=self.personal.db.query_row("SELECT EXISTS(SELECT 1 FROM goals WHERE archived=0) OR EXISTS(SELECT 1 FROM submissions WHERE mode='submit' AND scope='official' AND finished_at IS NOT NULL) OR EXISTS(SELECT 1 FROM account_preferences WHERE key LIKE 'review-state:%' OR key LIKE 'review-task:%') OR EXISTS(SELECT 1 FROM contests)",[],|r|r.get(0))?;
        if special {
            return Err(ApiError::pending());
        }
        Ok(())
    }
    pub fn workspace(&self) -> Result<Value, ApiError> {
        self.simple_workspace_supported()?;
        let records=self.personal.rows("SELECT id,problem_id,contest_id,mode,submitted_at,finished_at,verdict,scope,solution_seen FROM submissions WHERE mode='submit' ORDER BY submitted_at,rowid",[])?;
        let mut grouped: HashMap<String, Vec<&Value>> = HashMap::new();
        for r in records.as_array().unwrap() {
            grouped
                .entry(self.canonical(text(r, "problem_id"))?)
                .or_default()
                .push(r);
        }
        let activity=self.personal.rows("SELECT problem_id,submitted_at AS at FROM submissions UNION ALL SELECT problem_id,saved_at AS at FROM drafts",[])?;
        let mut latest_activity = HashMap::<String, String>::new();
        for r in activity.as_array().unwrap() {
            let key = self.canonical(text(r, "problem_id"))?;
            let entry = latest_activity.entry(key).or_default();
            if text(r, "at") > entry.as_str() {
                *entry = text(r, "at").into();
            }
        }
        let rows = self.personal.rows(
            "SELECT * FROM training WHERE active=1 ORDER BY active_at,id",
            [],
        )?;
        let mut training: Vec<Value> = Vec::new();
        let mut positions = HashMap::<String, usize>::new();
        for record in rows.as_array().unwrap() {
            let original = text(record, "id");
            let id = self.canonical(original)?;
            let attempts = grouped.get(&id).cloned().unwrap_or_default();
            let completed = attempts
                .iter()
                .copied()
                .filter(|r| truth(&r["finished_at"]))
                .collect::<Vec<_>>();
            let latest = completed.last().copied();
            let last = attempts.last().copied();
            let is_drill = id.starts_with("template-drill:");
            let accepted = completed.iter().copied().find(|r| {
                r["verdict"] == "AC"
                    && (r["scope"] == "official" || is_drill && r["scope"] == "template")
            });
            let accepted_at = accepted
                .map(|r| r["submitted_at"].clone())
                .unwrap_or_else(|| record["accepted_at"].clone());
            let accepted = truth(&accepted_at);
            let mut queue = Value::Null;
            if latest.is_some_and(|r| {
                ["WA", "TLE", "MLE", "RE", "CE", "OLE", "ERROR"].contains(&text(r, "verdict"))
            }) || truth(&record["mock_due"])
            {
                queue = json!("fill");
            } else if latest.is_some_and(|r| r["verdict"] == "SAMPLE_PASS") && !accepted {
                queue = json!("verify");
            }
            let mut item = match row_or_portable(self.catalogue, self.personal, &id) {
                Ok(row) => row,
                Err(error) if error.status == 404 => {
                    json!({"id":original,"title":original,"contest":"","problem":"","difficulty":null,"tags":[],"knowledge":"","platform":""})
                }
                Err(e) => return Err(e),
            };
            let scope = if accepted {
                json!(if completed
                    .iter()
                    .any(|r| r["scope"] == "official" && r["verdict"] == "AC")
                {
                    "official"
                } else if is_drill {
                    "template"
                } else {
                    "local"
                })
            } else {
                last.map(|r| r["scope"].clone()).unwrap_or(Value::Null)
            };
            let last_at = [
                latest_activity.get(&id).map(String::as_str).unwrap_or(""),
                text(record, "active_at"),
                text(record, "solution_seen_at"),
            ]
            .into_iter()
            .max()
            .unwrap()
            .to_owned();
            let today = truth(&queue) || day(parse(&last_at)?) == day(self.now);
            for (key,value) in json!({"id":id,"accepted":accepted,"verdict":last.map(|r|r["verdict"].clone()),"scope":scope,"attempts":attempts.len(),"acceptedAt":accepted_at,"lastSubmittedAt":last.map(|r|r["submitted_at"].clone()),"queue":queue,"reviewCount":record["review_count"],"solutionSeen":truth(&record["solution_pending"])||truth(&record["rewrite_due"]),"activeAt":record["active_at"],"lastActivityAt":last_at,"today":today}).as_object().unwrap() {item[key]=value.clone();}
            if let Some(&index) = positions.get(&id) {
                let previous = &mut training[index];
                if !truth(&previous["queue"]) {
                    previous["queue"] = item["queue"].clone();
                }
                previous["solutionSeen"] =
                    json!(truth(&previous["solutionSeen"]) || truth(&item["solutionSeen"]));
                previous["reviewCount"] = json!(
                    previous["reviewCount"]
                        .as_i64()
                        .unwrap_or(0)
                        .max(item["reviewCount"].as_i64().unwrap_or(0))
                );
                previous["today"] = json!(truth(&previous["today"]) || truth(&item["today"]));
                if text(&item, "lastActivityAt") > text(previous, "lastActivityAt") {
                    previous["lastActivityAt"] = item["lastActivityAt"].clone();
                }
            } else {
                positions.insert(id, training.len());
                training.push(item);
            }
        }
        let active_ids = training
            .iter()
            .map(|v| text(v, "id"))
            .collect::<HashSet<_>>();
        let accepted_ids = training
            .iter()
            .filter(|v| v["accepted"] == true)
            .map(|v| text(v, "id"))
            .collect::<HashSet<_>>();
        let mut sets = Vec::new();
        for record in self.personal.rows("SELECT * FROM practice_sets WHERE id NOT LIKE 'goal-contest:%' ORDER BY created_at DESC,id",[])?.as_array().unwrap() {
            let values:Vec<String>=serde_json::from_str(text(record,"ids"))?;let mut ids=Vec::new();
            for id in values {let id=self.canonical(&id)?;if active_ids.contains(id.as_str())&&!ids.contains(&id) {ids.push(id);}}
            if !ids.is_empty(){sets.push(json!({"id":record["id"],"name":record["name"],"type":"practice","createdAt":record["created_at"],"accepted":ids.iter().filter(|id|accepted_ids.contains(id.as_str())).count(),"total":ids.len(),"ids":ids}));}
        }
        let mut contests = Vec::new();
        for record in self.personal.rows("SELECT * FROM contests WHERE deleted_at IS NULL ORDER BY started_at DESC,rowid DESC",[])?.as_array().unwrap() {contests.push(self.contest_projection(record)?);}
        let date = day(self.now);
        let mut goals = json!({"goals":[],"date":date,"contestPlan":{"contests":[],"total":0,"goalCount":0},"goalTasks":[]});
        if let Some(state) = self.personal.document(crate::learning::KEY)? {
            if truth(&state["plan"]) {
                goals["summaryGoal"] = state["config"]["goal"].clone();
            }
        }
        let reviews = json!({"date":date,"tasks":[],"dueCount":0,"deferredCount":0,"minutes":0,"dailyMinutes":90,"newMinutes":90,"reviewOnly":false,"abilityScore":null,"policyVersion":3});
        let pending: i64 = self.personal.db.query_row(
            "SELECT count(*) FROM submissions WHERE finished_at IS NULL",
            [],
            |r| r.get(0),
        )?;
        Ok(
            json!({"training":training,"sets":sets,"contests":contests,"completedReplayContests":[],"reviews":reviews,"goals":goals,"goalTasks":[],"activeContest":null,
            "summary":{"todayAccepted":0,"historicalAccepted":0,"beforeTodayAccepted":0,"total":training.len(),"accepted":accepted_ids.len(),"samplePassed":training.iter().filter(|r|r["verdict"]=="SAMPLE_PASS"&&r["accepted"]!=true).count(),"attempts":records.as_array().unwrap().len(),"due":training.iter().filter(|v|truth(&v["queue"])).count(),"streak":0,"pending":pending},"now":stamp(self.now)}),
        )
    }
    pub fn start(&mut self, body: &Value) -> Result<Value, ApiError> {
        let id = required_text(body, "id", 512)?;
        row_or_portable(self.catalogue, self.personal, id)?;
        if truth(&body["restoreReviewId"]) {
            return Err(ApiError::pending());
        }
        let deferred = body["deferWorkspace"] == true;
        let assisted = body["assisted"] == true;
        self.simple_workspace_supported()?;
        if assisted {
            self.assert_unlocked(id)?;
        }
        let ids = self.ids(id)?;
        let wrong:bool=self.personal.db.query_row("SELECT EXISTS(SELECT 1 FROM submissions WHERE problem_id IN(SELECT value FROM json_each(?)) AND mode='submit' AND scope='official' AND verdict='WA' AND finished_at IS NOT NULL)",[json!(ids).to_string()],|r|r.get(0))?;
        if wrong {
            return Err(ApiError::pending());
        }
        if body["deferActivation"] != true {
            self.activate(id)?;
        }
        if assisted {
            self.mark_seen(id)?;
        }
        if deferred && !assisted {
            return Ok(json!({"reviewTask":null}));
        }
        Ok(json!({"workspace":self.workspace()?,"reviewTask":null}))
    }
    pub fn activate(&mut self, id: &str) -> Result<(), ApiError> {
        let now = stamp(self.now);
        let ids = self.ids(id)?;
        let contests = self
            .personal
            .rows("SELECT id,slots FROM contests WHERE deleted_at IS NULL", [])?;
        let tx = self.personal.db.transaction()?;
        for contest in contests.as_array().unwrap() {
            let mut slots: Value = serde_json::from_str(text(contest, "slots"))?;
            let mut changed = false;
            for slot in slots
                .as_array_mut()
                .ok_or_else(|| ApiError::new(500, "INVALID_STORED_DATA", "比赛题目记录格式异常"))?
            {
                if ids.iter().any(|id| slot["id"] == *id) && slot["trainingAdded"] == true {
                    slot["trainingAdded"] = false.into();
                    changed = true;
                }
            }
            if changed {
                tx.execute(
                    "UPDATE contests SET slots=? WHERE id=?",
                    params![slots.to_string(), text(contest, "id")],
                )?;
            }
        }
        tx.execute("INSERT INTO training(id,active_at) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET active=1,removed_at=NULL,active_at=MAX(training.active_at,excluded.active_at)",params![id,now])?;
        tx.commit()?;
        self.recompute(id)
    }
    pub fn recompute(&mut self, id: &str) -> Result<(), ApiError> {
        let ids = json!(self.ids(id)?).to_string();
        let training = self.personal.rows(
            "SELECT * FROM training WHERE id IN(SELECT value FROM json_each(?))",
            [&ids],
        )?;
        let accepted=self.personal.rows("SELECT * FROM submissions WHERE problem_id IN(SELECT value FROM json_each(?)) AND mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid",[&ids])?;
        let done=self.personal.rows("SELECT submitted_at,contest_id FROM submissions WHERE problem_id IN(SELECT value FROM json_each(?)) AND mode='submit' AND scope='local' AND verdict IN('AC','SAMPLE_PASS') AND contest_id IS NOT NULL AND finished_at IS NOT NULL",[&ids])?;
        let accepted = accepted.as_array().unwrap();
        let mut reviews = 0;
        let mut review_at = Value::Null;
        if let Some(first) = accepted.first() {
            let mut cursor = parse(text(first, "submitted_at"))?;
            for r in accepted.iter().skip(1) {
                let at = parse(text(r, "submitted_at"))?;
                if !truth(&r["solution_seen"]) && (at - cursor).num_seconds() >= 86400 {
                    reviews += 1;
                    cursor = at;
                    review_at = r["submitted_at"].clone();
                }
            }
        }
        let tx = self.personal.db.transaction()?;
        for record in training.as_array().unwrap() {
            let mut mock = truth(&record["mock_due"]);
            if mock
                && accepted.iter().chain(done.as_array().unwrap()).any(|r| {
                    r["contest_id"] == record["mock_due_context"]
                        || !truth(&record["mock_due_at"])
                        || text(r, "submitted_at") >= text(record, "mock_due_at")
                })
            {
                mock = false;
            }
            if accepted.is_empty() {
                tx.execute("UPDATE training SET accepted_at=NULL,review_count=0,rewrite_due=CASE WHEN solution_pending=1 THEN 1 ELSE rewrite_due END,mock_due=? WHERE id=?",params![mock,text(record,"id")])?;
            } else {
                let first = &accepted[0];
                let last = accepted.last().unwrap();
                let rewrite = truth(&last["solution_seen"])
                    || truth(&record["solution_seen_at"])
                        && text(record, "solution_seen_at") >= text(last, "submitted_at");
                tx.execute("UPDATE training SET accepted_at=?,last_local_at=?,last_review_at=?,review_count=?,rewrite_due=?,solution_pending=?,mock_due=? WHERE id=?",params![text(first,"submitted_at"),text(last,"submitted_at"),review_at.as_str(),reviews,rewrite,rewrite,mock,text(record,"id")])?;
            }
        }
        tx.commit()?;
        Ok(())
    }
    pub fn remove(&mut self, body: &Value) -> Result<Value, ApiError> {
        let id = required_text(body, "id", 512)?;
        row_or_portable(self.catalogue, self.personal, id)?;
        self.assert_unlocked(id)?;
        self.simple_workspace_supported()?;
        let ids = json!(self.ids(id)?).to_string();
        let pending:bool=self.personal.db.query_row("SELECT EXISTS(SELECT 1 FROM submissions WHERE problem_id IN(SELECT value FROM json_each(?)) AND finished_at IS NULL)",[&ids],|r|r.get(0))?;
        if pending {
            return Err(ApiError::conflict(
                "这道题还有评测任务，请等待结果后取消训练",
            ));
        }
        self.personal.db.execute("UPDATE training SET active=0,removed_at=? WHERE id IN(SELECT value FROM json_each(?)) AND active=1",params![stamp(self.now),ids])?;
        Ok(json!({"workspace":self.workspace()?,"cancelledReviewId":null}))
    }
    pub fn clear(&mut self, body: &Value) -> Result<Value, ApiError> {
        fields(body, &["ids"])?;
        self.simple_workspace_supported()?;
        let ids = body.get("ids");
        if ids.is_some_and(|v| {
            !v.is_null()
                && !v.as_array().is_some_and(|a| {
                    a.len() <= 20000
                        && a.iter().all(|v| {
                            v.as_str()
                                .is_some_and(|s| !s.is_empty() && s.chars().count() <= 400)
                        })
                })
        }) {
            return Err(ApiError::bad("训练题目列表无效"));
        }
        let pending: bool = self.personal.db.query_row(
            "SELECT EXISTS(SELECT 1 FROM submissions WHERE finished_at IS NULL)",
            [],
            |r| r.get(0),
        )?;
        if pending {
            return Err(ApiError::conflict("还有评测任务，请等待结果后清空训练"));
        }
        let workspace = self.workspace()?;
        let visible = workspace["training"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| text(v, "id").to_owned())
            .collect::<HashSet<_>>();
        let targets = if let Some(ids) = ids.and_then(Value::as_array) {
            ids.iter()
                .map(|v| self.canonical(v.as_str().unwrap()))
                .collect::<Result<HashSet<_>, _>>()?
                .intersection(&visible)
                .cloned()
                .collect::<HashSet<_>>()
        } else {
            visible
        };
        let records = self.personal.rows("SELECT id FROM training", [])?;
        let records = records
            .as_array()
            .unwrap()
            .iter()
            .filter_map(|r| match self.canonical(text(r, "id")) {
                Ok(id) if targets.contains(&id) => Some(Ok(r["id"].clone())),
                Ok(_) => None,
                Err(e) => Some(Err(e)),
            })
            .collect::<Result<Vec<_>, ApiError>>()?;
        if !targets.is_empty() {
            self.personal.db.execute("UPDATE training SET active=0,removed_at=? WHERE id IN(SELECT value FROM json_each(?))",params![stamp(self.now),json!(records).to_string()])?;
        }
        Ok(json!({"cleared":targets.len(),"workspace":self.workspace()?}))
    }
    pub fn mark_seen(&mut self, id: &str) -> Result<(), ApiError> {
        self.assert_unlocked(id)?;
        let ids = json!(self.ids(id)?).to_string();
        let count: i64 = self.personal.db.query_row(
            "SELECT count(*) FROM training WHERE id IN(SELECT value FROM json_each(?))",
            [&ids],
            |r| r.get(0),
        )?;
        if count > 0 {
            self.personal.db.execute("UPDATE training SET solution_pending=1,solution_seen_at=? WHERE id IN(SELECT value FROM json_each(?))",params![stamp(self.now),ids])?;
            self.recompute(id)?;
        } else {
            self.personal.db.execute("INSERT INTO training(id,active_at,active,solution_pending,solution_seen_at) VALUES(?,?,0,1,?)",params![id,stamp(self.now),stamp(self.now)])?;
        }
        Ok(())
    }
    pub fn contest_projection(&self, record: &Value) -> Result<Value, ApiError> {
        let config: Value = serde_json::from_str(text(record, "config"))?;
        let frozen: Vec<Value> = serde_json::from_str(text(record, "slots"))?;
        let rows=self.personal.rows("SELECT * FROM submissions WHERE contest_id=? AND mode='submit' ORDER BY submitted_at,rowid",[text(record,"id")])?;
        let mut slots = Vec::new();
        let mut penalty = 0;
        for frozen in frozen {
            let canonical = self.canonical(text(&frozen, "id"))?;
            let attempts = rows
                .as_array()
                .unwrap()
                .iter()
                .filter_map(|r| match self.canonical(text(r, "problem_id")) {
                    Ok(id) if id == canonical => Some(Ok(r)),
                    Ok(_) => None,
                    Err(e) => Some(Err(e)),
                })
                .collect::<Result<Vec<_>, ApiError>>()?;
            let accepted = attempts.iter().position(|r| {
                truth(&r["finished_at"])
                    && (r["scope"] == "official" && r["verdict"] == "AC"
                        || config["strategy"] != "replay"
                            && r["scope"] == "local"
                            && ["AC", "SAMPLE_PASS"].contains(&text(r, "verdict")))
            });
            let latest = attempts.last();
            let mut slot = json!({"letter":frozen["letter"],"id":frozen["id"],"title":frozen["title"],"accepted":accepted.is_some(),"samplePassed":accepted.is_some()||attempts.iter().any(|r|truth(&r["finished_at"])&&r["verdict"]=="SAMPLE_PASS"),"verdict":latest.map(|r|r["verdict"].clone()),"attempts":attempts.len(),"solvedAt":accepted.map(|i|attempts[i]["submitted_at"].clone())});
            if record["status"] == "finished" {
                for key in ["difficulty", "tags", "judgeScope"] {
                    slot[key] = frozen[key].clone();
                }
            }
            if let Some(index) = accepted {
                let minutes = (parse(text(attempts[index], "submitted_at"))?
                    - parse(text(record, "started_at"))?)
                .num_seconds()
                .div_euclid(60)
                .max(0);
                let wrong = attempts[..index]
                    .iter()
                    .filter(|r| {
                        ["WA", "TLE", "MLE", "RE", "OLE"].contains(&text(r, "verdict"))
                            || config["compilePenalty"] == true && r["verdict"] == "CE"
                    })
                    .count() as i64;
                penalty += minutes + config["wrongPenalty"].as_i64().unwrap_or(20) * wrong;
            }
            slots.push(slot);
        }
        let end = parse(if truth(&record["finished_at"]) {
            text(record, "finished_at")
        } else {
            text(record, "deadline")
        })?;
        let elapsed = (self.now.min(end) - parse(text(record, "started_at"))?)
            .num_seconds()
            .max(0);
        Ok(
            json!({"id":record["id"],"name":record["name"],"status":record["status"],"startedAt":record["started_at"],"deadline":record["deadline"],"finishedAt":record["finished_at"],"duration":record["duration"],"accepted":slots.iter().filter(|s|s["accepted"]==true).count(),"total":slots.len(),"slots":slots,"penalty":penalty,"elapsedSeconds":elapsed,"strategy":config.get("strategy").cloned().unwrap_or(json!("comprehensive")),"constraints":config}),
        )
    }
    pub fn submission_projection(&self, record: &Value, compact: bool) -> Result<Value, ApiError> {
        let mut value = json!({});
        for (from, to) in [
            ("id", "id"),
            ("problem_id", "problemId"),
            ("contest_id", "contestId"),
            ("mode", "mode"),
            ("verdict", "verdict"),
            ("scope", "scope"),
            ("submitted_at", "submittedAt"),
            ("finished_at", "finishedAt"),
            ("time_ms", "timeMs"),
            ("memory_kb", "memoryKb"),
            ("passed", "passed"),
            ("total", "total"),
        ] {
            value[to] = record[from].clone();
        }
        value["sampleRun"] = json!(truth(&record["sample_run"]));
        value["verdictDetail"] = json!(if record["scope"] == "official" {
            text(record, "message")
                .split_once('\n')
                .map(|(_, v)| v.chars().take(500).collect::<String>())
                .unwrap_or_default()
        } else {
            String::new()
        });
        value["codePending"] = json!(compact);
        if !compact {
            for key in ["code", "output", "stderr", "message"] {
                value[key] = record[key].clone();
            }
            value["caseResults"] = serde_json::from_str(text(record, "case_results"))?;
            value["language"] = json!(
                self.personal
                    .pref(&format!("submission-language:{}", text(record, "id")))?
                    .filter(|s| ["cpp17", "python3"].contains(&s.as_str()))
                    .unwrap_or_else(|| "cpp17".into())
            );
            if text(record, "code").is_empty() {
                let cold_table:bool=self.personal.db.query_row("SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name='account_sync_code_refs')",[],|r|r.get(0))?;
                if cold_table {
                    let cold: bool = self.personal.db.query_row(
                        "SELECT EXISTS(SELECT 1 FROM account_sync_code_refs WHERE submission_id=?)",
                        [text(record, "id")],
                        |r| r.get(0),
                    )?;
                    value["codePending"] = json!(cold);
                }
            }
            let receipt = self
                .personal
                .document(&format!("review-receipt:{}", text(record, "id")))?;
            let mut reward = 0;
            if record["scope"] == "official" && record["verdict"] == "AC" {
                if let Some(id) = receipt.and_then(|v| v.as_str().map(String::from)) {
                    if let Some(task) = self.personal.document(&format!("review-task:{id}"))? {
                        if task["rewardReceiptId"] == record["id"] {
                            if let Some(claim) =
                                self.personal.document(text(&task, "rewardClaim"))?
                            {
                                if claim["receiptId"] == record["id"] && claim["xp"] == 20 {
                                    reward = 20;
                                }
                            }
                        }
                    }
                }
            }
            value["reviewRewardXp"] = json!(reward);
        }
        Ok(value)
    }
    pub fn submission(&self, id: &str) -> Result<Value, ApiError> {
        let rows = self
            .personal
            .rows("SELECT * FROM submissions WHERE id=?", [id])?;
        let record = rows
            .as_array()
            .unwrap()
            .first()
            .ok_or_else(|| ApiError::missing("没有找到这次提交"))?;
        self.history_visible(text(record, "problem_id"), record["contest_id"].as_str())?;
        let submission = self.submission_projection(record, false)?;
        if submission["codePending"] == true {
            return Err(ApiError::new(
                503,
                "HISTORY_CODE_PENDING",
                "这份历史代码需要账号同步，原本机记录已保留",
            ));
        }
        let mut result = json!({"submission":submission});
        if truth(&record["finished_at"]) && record["mode"] != "run" {
            match self.workspace() {
                Ok(workspace) => result["workspace"] = workspace,
                Err(error) if error.code == "MIGRATION_PENDING" => {
                    result["workspacePending"] = true.into()
                }
                Err(e) => return Err(e),
            }
        }
        Ok(result)
    }
    pub fn submissions(&self, request: &ApiRequest, exact: bool) -> Result<Value, ApiError> {
        let limit = request
            .param("limit")
            .unwrap_or("100")
            .parse::<i64>()
            .map_err(|_| ApiError::bad("提交记录分页参数无效"))?;
        let offset = request
            .param("offset")
            .unwrap_or("0")
            .parse::<i64>()
            .map_err(|_| ApiError::bad("提交记录分页参数无效"))?;
        if !(1..=100).contains(&limit) || offset < 0 {
            return Err(ApiError::bad("每页提交记录须为 1–100 条，偏移量不能为负"));
        }
        let query = request.param("q").unwrap_or("");
        let order = request.param("order").unwrap_or("desc");
        if query.chars().count() > 120 || !["asc", "desc"].contains(&order) {
            return Err(ApiError::bad("提交记录查询参数无效"));
        }
        let verdict = request.param("verdict").unwrap_or("");
        if ![
            "", "AC", "WA", "CE", "TLE", "MLE", "RE", "OLE", "ERROR", "QUEUED", "RUNNING",
        ]
        .contains(&verdict)
        {
            return Err(ApiError::bad("提交结果筛选无效"));
        }
        let platform = request.param("platform").unwrap_or("");
        if platform.chars().count() > 80 {
            return Err(ApiError::bad("提交记录平台筛选无效"));
        }
        let compact = request.param("compact") == Some("1");
        let mut clauses = Vec::<String>::new();
        let mut values = Vec::<SqlValue>::new();
        if let Some(id) = request.param("id") {
            self.history_visible(id, request.param("contestId"))?;
            clauses.push("problem_id IN(SELECT value FROM json_each(?))".into());
            values.push(json!(self.ids(id)?).to_string().into());
        }
        if let Some(context) = request.param("contestId") {
            if self
                .personal
                .db
                .query_row("SELECT 1 FROM contests WHERE id=?", [context], |_| Ok(()))
                .optional()?
                .is_none()
            {
                return Err(ApiError::missing("没有找到这场模拟赛"));
            }
            clauses.push("contest_id=?".into());
            values.push(context.to_owned().into());
        } else if exact {
            clauses.push("contest_id IS NULL".into());
        }
        if !verdict.is_empty() {
            clauses.push("verdict=?".into());
            values.push(verdict.to_owned().into());
        }
        if request.param("resultsOnly") == Some("1") {
            clauses.push("mode='submit' AND sample_run=0 AND verdict!='SAMPLE_PASS' AND scope IN('official','local')".into());
        }
        if request.param("reviewId").is_some() {
            return Err(ApiError::pending());
        }
        // Search/filter the public metadata once, before pagination and COUNT.
        if !platform.is_empty() || !query.trim().is_empty() {
            let ids = self
                .personal
                .rows("SELECT DISTINCT problem_id FROM submissions", [])?;
            let mut matching = Vec::new();
            let tokens = query
                .to_lowercase()
                .split_whitespace()
                .map(String::from)
                .collect::<Vec<_>>();
            for r in ids.as_array().unwrap() {
                let id = text(r, "problem_id");
                let row = match row_or_portable(self.catalogue, self.personal, id) {
                    Ok(r) => r,
                    Err(e) if e.status == 404 => json!({}),
                    Err(e) => return Err(e),
                };
                let platform_match = platform.is_empty()
                    || normalize_platform(text(&row, "platform")) == normalize_platform(platform);
                let haystack = format!(
                    "{} {} {} {}",
                    text(&row, "id"),
                    text(&row, "title"),
                    text(&row, "contest"),
                    text(&row, "problem")
                )
                .to_lowercase();
                if platform_match {
                    matching.push((id.to_owned(), haystack));
                }
            }
            clauses.push("problem_id IN(SELECT value FROM json_each(?))".into());
            values.push(
                json!(matching.iter().map(|(id, _)| id).collect::<Vec<_>>())
                    .to_string()
                    .into(),
            );
            for token in tokens {
                let ids = matching
                    .iter()
                    .filter(|(_, h)| h.contains(&token))
                    .map(|(id, _)| id)
                    .collect::<Vec<_>>();
                clauses.push("(problem_id IN(SELECT value FROM json_each(?)) OR instr(lower(verdict),?)>0 OR instr(lower(problem_id),?)>0)".into());
                values.push(json!(ids).to_string().into());
                values.push(token.clone().into());
                values.push(token.into());
            }
        }
        if let Some(contest) = self.running()? {
            let slots: Vec<Value> = serde_json::from_str(text(&contest, "slots"))?;
            let mut ids = Vec::new();
            for slot in slots {
                ids.extend(self.ids(text(&slot, "id"))?);
            }
            clauses
                .push("(problem_id NOT IN(SELECT value FROM json_each(?)) OR contest_id=?)".into());
            values.push(json!(ids).to_string().into());
            values.push(text(&contest, "id").to_owned().into());
        }
        let where_sql = if clauses.is_empty() {
            String::new()
        } else {
            format!(" WHERE {}", clauses.join(" AND "))
        };
        let total: i64 = self.personal.db.query_row(
            &format!("SELECT count(*) FROM submissions{where_sql}"),
            params_from_iter(values.iter()),
            |r| r.get(0),
        )?;
        let direction = if order == "asc" { "ASC" } else { "DESC" };
        let columns = if compact {
            "id,problem_id,contest_id,mode,verdict,scope,submitted_at,finished_at,time_ms,memory_kb,passed,total,sample_run,message"
        } else {
            "*"
        };
        values.push(limit.into());
        values.push(offset.into());
        let rows=self.personal.rows(&format!("SELECT {columns} FROM submissions{where_sql} ORDER BY submitted_at {direction},rowid {direction} LIMIT ? OFFSET ?"),params_from_iter(values.iter()))?;
        let mut submissions = Vec::new();
        for record in rows.as_array().unwrap() {
            let mut value = self.submission_projection(record, compact)?;
            match row_or_portable(self.catalogue, self.personal, text(record, "problem_id")) {
                Ok(row) => {
                    value["canonicalProblemId"] =
                        json!(self.canonical(text(record, "problem_id"))?);
                    for (from, to) in [
                        ("title", "title"),
                        ("contest", "contestName"),
                        ("problem", "problem"),
                        ("url", "url"),
                    ] {
                        value[to] = row[from].clone();
                    }
                    value["platform"] = json!(normalize_platform(text(&row, "platform")));
                }
                Err(e) if e.status == 404 => {}
                Err(e) => return Err(e),
            }
            submissions.push(value);
        }
        let has_more = offset + (submissions.len() as i64) < total;
        Ok(
            json!({"total":total,"offset":offset,"limit":limit,"hasMore":has_more,"submissions":submissions}),
        )
    }
    pub fn problem(&self, r: &ApiRequest) -> Result<Value, ApiError> {
        let id = r.param("id").ok_or_else(|| ApiError::bad("题目编号无效"))?;
        let row = row_or_portable(self.catalogue, self.personal, id)?;
        if r.param("contestId").is_some() || r.param("reviewId").is_some() {
            return Err(ApiError::pending());
        }
        self.history_visible(id, None)?;
        let canonical = self.canonical(id)?;
        let mut problem = self.library.statement(&canonical)?;
        let knowledge = self
            .catalogue
            .problem_projection(&canonical, &mut problem)?;
        self.library
            .hydrate_with(&mut problem, Some(&self.catalogue.db))?;
        let allowed = [
            "id",
            "title",
            "markdown",
            "url",
            "samples",
            "limits",
            "judge",
            "statementAvailable",
            "statementError",
            "statementLoading",
            "statementVersion",
            "statementPdf",
            "currentSourceMarkdown",
            "statementSupplement",
            "images",
            "attachments",
            "problemType",
            "localJudgeSupported",
            "translation",
            "translationAvailable",
            "autoTranslate",
            "templatePractice",
        ];
        problem
            .as_object_mut()
            .unwrap()
            .retain(|k, _| allowed.contains(&k.as_str()));
        problem["id"] = json!(id);
        problem
            .as_object_mut()
            .unwrap()
            .entry("title")
            .or_insert_with(|| row["title"].clone());
        problem["locked"] = json!(self.locked(id)?);
        problem["solutionMethods"] = self.library.solution_summary(&canonical)?;
        let ids = self.ids(id)?;
        let draft=self.personal.rows("SELECT problem_id,context,code,saved_at FROM drafts WHERE problem_id IN(SELECT value FROM json_each(?)) AND context='' ORDER BY saved_at DESC LIMIT 1",[json!(ids).to_string()])?;
        let draft = if let Some(record) = draft.as_array().unwrap().first() {
            self.personal
                .draft(text(record, "problem_id"), text(record, "context"))?
        } else {
            self.personal.draft(id, "")?
        };
        for (key, value) in draft.as_object().unwrap() {
            problem[key] = value.clone();
        }
        problem["initialCode"] = templates::initial_selected(self.personal)?;
        let mut history = r.clone();
        history.path = "submissions".into();
        problem["submissions"] = self.submissions(&history, true)?["submissions"].clone();
        for key in ["tags", "knowledge", "knowledgeAnalysis"] {
            if let Some(value) = knowledge.get(key) {
                problem[key] = value.clone();
            }
        }
        problem["formattingAvailable"] = false.into();
        Ok(problem)
    }
}
pub fn normalize_platform(value: &str) -> &str {
    let trimmed = value.trim();
    match trimmed.to_ascii_lowercase().as_str() {
        "codeforces" | "cf" => "Codeforces",
        "atcoder" | "ac" => "AtCoder",
        "nowcoder" => "牛客",
        "luogu" => "洛谷",
        "qoj" => "QOJ",
        _ => trimmed,
    }
}
