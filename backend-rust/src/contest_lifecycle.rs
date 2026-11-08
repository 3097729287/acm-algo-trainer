//! Durable local contest transitions. No browser submission or shared-room
//! authority is invented by finalizing a local journal record.
use crate::{api::ApiError, learning::stamp, storage, training::Training};
use rusqlite::params;
use serde_json::{Value, json};
use std::collections::HashSet;

fn text<'a>(value: &'a Value, field: &str) -> &'a str {
    value[field].as_str().unwrap_or("")
}
fn invalid() -> ApiError {
    ApiError::new(500, "INVALID_STORED_DATA", "比赛记录格式异常，原数据已保留")
}
fn object(raw: &str) -> Result<Value, ApiError> {
    let value: Value = serde_json::from_str(if raw.is_empty() { "{}" } else { raw })?;
    value.is_object().then_some(value).ok_or_else(invalid)
}
fn slots(record: &Value) -> Result<Vec<Value>, ApiError> {
    let values: Vec<Value> = serde_json::from_str(text(record, "slots"))?;
    if values.iter().any(|slot| text(slot, "id").is_empty()) {
        return Err(invalid());
    }
    Ok(values)
}
fn list_ids(raw: &str) -> Result<Vec<String>, ApiError> {
    serde_json::from_str(raw).map_err(Into::into)
}
fn raw_record(t: &Training<'_>, identity: &str) -> Result<Value, ApiError> {
    if identity.is_empty() || identity.len() > 512 {
        return Err(ApiError::bad("缺少模拟赛编号"));
    }
    t.personal
        .rows("SELECT * FROM contests WHERE id=?", [identity])?
        .as_array()
        .unwrap()
        .first()
        .cloned()
        .ok_or_else(|| ApiError::missing("没有找到这场模拟赛"))
}
fn local_facts_supported(t: &Training<'_>) -> Result<(), ApiError> {
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

fn finalization_supported(record: &Value) -> Result<Value, ApiError> {
    let config = object(text(record, "config"))?;
    if config["strategy"] == "team" || config.get("backgroundReward").is_some_and(|v| !v.is_null())
    {
        // The coordinator and owner-bound reward envelope are still separate
        // migrations. Keep the original running journal intact until then.
        return Err(ApiError::pending());
    }
    crate::training::parse(text(record, "started_at"))?;
    crate::training::parse(text(record, "deadline"))?;
    slots(record)?;
    Ok(config)
}

fn finish_record(t: &Training<'_>, record: &Value, ended: &str) -> Result<(), ApiError> {
    let config = finalization_supported(record)?;
    let replay = config["strategy"] == "replay";
    let mut solved = HashSet::new();
    for receipt in t.personal.rows("SELECT problem_id,scope,verdict FROM submissions WHERE contest_id=? AND mode='submit' AND finished_at IS NOT NULL", [text(record,"id")])?.as_array().unwrap() {
        let accepted = receipt["scope"] == "official" && receipt["verdict"] == "AC"
            || !replay && receipt["scope"] == "local" && ["AC", "SAMPLE_PASS"].contains(&text(receipt,"verdict"));
        if accepted {
            let id = text(receipt, "problem_id");
            solved.insert(if replay { t.canonical(id)? } else { id.to_owned() });
        }
    }
    t.personal.db.execute(
        "UPDATE contests SET status='finished',finished_at=? WHERE id=? AND status='running'",
        params![ended, text(record, "id")],
    )?;
    for slot in slots(record)? {
        let id = text(&slot, "id");
        let canonical = if replay {
            t.canonical(id)?
        } else {
            id.to_owned()
        };
        if slot["statementAvailable"] != false && !solved.contains(&canonical) {
            // Starting/reading an exam never introduces an ordinary training
            // row. Only an existing independently owned row can become due.
            t.personal.db.execute(
                "UPDATE training SET mock_due=1,mock_due_at=?,mock_due_context=? WHERE id=?",
                params![ended, text(record, "id"), id],
            )?;
        }
    }
    Ok(())
}

pub(crate) fn expiry_records(t: &Training<'_>) -> Result<Vec<Value>, ApiError> {
    let records = t.personal.rows(
        "SELECT * FROM contests WHERE status='running' AND deadline<=?",
        [stamp(t.now)],
    )?;
    let records = records.as_array().unwrap();
    if !records.is_empty() {
        local_facts_supported(t)?;
    }
    for record in records {
        let config = finalization_supported(record)?;
        // Read validation is also used before a public resource transfer.
        // Validate the closed projection without changing the stored journal.
        let mut closed = record.clone();
        closed["status"] = json!("finished");
        closed["finished_at"] = record["deadline"].clone();
        t.contest_projection(&closed)?;
        if config["strategy"] == "replay" && !text(&config, "contest").is_empty() {
            crate::contest_history::display_name(t, text(&config, "contest"))?;
        }
    }
    Ok(records.clone())
}

pub fn expire(t: &Training<'_>) -> Result<(), ApiError> {
    let records = expiry_records(t)?;
    if records.is_empty() {
        return Ok(());
    }
    storage::atomic(&t.personal.db, |_| {
        for record in &records {
            finish_record(t, record, text(record, "deadline"))?;
        }
        Ok(())
    })
}

pub fn validate_running(t: &Training<'_>) -> Result<(), ApiError> {
    for record in t
        .personal
        .rows("SELECT * FROM contests WHERE status='running'", [])?
        .as_array()
        .unwrap()
    {
        let config = object(text(record, "config"))?;
        if config["strategy"] == "team" || slots(record)?.is_empty() {
            return Err(ApiError::pending());
        }
        crate::training::parse(text(record, "started_at"))?;
        crate::training::parse(text(record, "deadline"))?;
    }
    Ok(())
}

pub fn finish(t: &Training<'_>, identity: &str) -> Result<Value, ApiError> {
    local_facts_supported(t)?;
    let prior = raw_record(t, identity)?;
    if object(text(&prior, "config"))?["strategy"] == "team" {
        return Err(ApiError::conflict("请由队长在团队训练中结束比赛"));
    }
    if object(text(&prior, "config"))?
        .get("backgroundReward")
        .is_some_and(|v| !v.is_null())
    {
        return Err(ApiError::pending());
    }
    storage::atomic(&t.personal.db, |_| {
        expire(t)?;
        let record = raw_record(t, identity)?;
        if record["status"] == "running" {
            finish_record(t, &record, &stamp(t.now))?;
        }
        let record = raw_record(t, identity)?;
        Ok(json!({"contest":t.contest_projection(&record)?,"workspace":t.workspace()?}))
    })
}

fn references(t: &Training<'_>) -> Result<HashSet<String>, ApiError> {
    let mut ids = HashSet::new();
    for record in t
        .personal
        .rows("SELECT slots FROM contests WHERE deleted_at IS NULL", [])?
        .as_array()
        .unwrap()
    {
        for slot in slots(record)? {
            ids.insert(text(&slot, "id").to_owned());
        }
    }
    for record in t
        .personal
        .rows("SELECT ids FROM practice_sets", [])?
        .as_array()
        .unwrap()
    {
        ids.extend(list_ids(text(record, "ids"))?);
    }
    Ok(ids)
}

pub fn cancel(t: &Training<'_>, identity: &str) -> Result<Value, ApiError> {
    if identity.is_empty() || identity.len() > 512 {
        return Err(ApiError::bad("比赛编号无效"));
    }
    local_facts_supported(t)?;
    let record = raw_record(t, identity)?;
    if object(text(&record, "config"))?["strategy"] == "team" {
        return Err(ApiError::conflict("请在团队训练中管理这场比赛"));
    }
    if record["status"] == "cancelled" {
        return Ok(json!({"cancelled":true,"workspace":t.workspace()?}));
    }
    if record["status"] != "running" {
        return Err(ApiError::conflict("比赛已经结束，不能再取消"));
    }
    let frozen = slots(&record)?;
    storage::atomic(&t.personal.db, |db| {
        let now = stamp(t.now);
        db.execute(
            "UPDATE contests SET status='cancelled',deleted_at=? WHERE id=?",
            params![now, identity],
        )?;
        let referenced = references(t)?;
        for slot in &frozen {
            let id = text(slot, "id");
            if t.ids(id)?.iter().any(|id| referenced.contains(id)) {
                continue;
            }
            match slot.get("trainingBefore") {
                Some(previous) if !previous.is_null() => {
                    let active = match previous["active"].as_i64() {
                        Some(value @ (0 | 1)) => value,
                        _ => return Err(invalid()),
                    };
                    let active_at = previous["active_at"].as_str().ok_or_else(invalid)?;
                    let removed = match previous.get("removed_at") {
                        None | Some(Value::Null) => None,
                        Some(Value::String(value)) => Some(value.as_str()),
                        _ => return Err(invalid()),
                    };
                    db.execute(
                        "UPDATE training SET active=?,active_at=?,removed_at=? WHERE id=?",
                        params![active, active_at, removed, id],
                    )?;
                }
                _ if slot["trainingAdded"] == true => {
                    db.execute(
                        "UPDATE training SET active=0,removed_at=? WHERE id=?",
                        params![now, id],
                    )?;
                }
                _ => {}
            }
            db.execute("UPDATE training SET mock_due=0,mock_due_at=NULL,mock_due_context=NULL WHERE id=? AND mock_due_context=?", params![id,identity])?;
        }
        Ok(json!({"cancelled":true,"workspace":t.workspace()?}))
    })
}

pub fn delete(t: &Training<'_>, body: &Value) -> Result<Value, ApiError> {
    let all = match body.get("all") {
        None => false,
        Some(Value::Bool(value)) => *value,
        _ => return Err(ApiError::bad("请选择要删除的模拟赛记录")),
    };
    let identity = text(body, "id");
    if !all && identity.is_empty() {
        return Err(ApiError::bad("请选择要删除的模拟赛记录"));
    }
    local_facts_supported(t)?;
    storage::atomic(&t.personal.db, |db| {
        expire(t)?;
        if !all && raw_record(t, identity)?["status"] == "running" {
            return Err(ApiError::conflict("请先交卷，再删除这场模拟赛记录"));
        }
        let records = t.personal.rows(
            "SELECT * FROM contests WHERE status='finished' AND deleted_at IS NULL AND (? OR id=?)",
            params![all, identity],
        )?;
        let records = records.as_array().unwrap();
        let now = stamp(t.now);
        for record in records {
            db.execute(
                "UPDATE contests SET deleted_at=? WHERE id=?",
                params![now, text(record, "id")],
            )?;
        }
        let referenced = references(t)?;
        let mut removed = HashSet::new();
        for record in records {
            if object(text(record, "config"))?["strategy"] != "replay" {
                continue;
            }
            for slot in slots(record)? {
                let id = text(&slot, "id");
                let equivalents = t.ids(id)?;
                if equivalents.iter().any(|id| referenced.contains(id))
                    || slot["trainingAdded"] == false
                {
                    continue;
                }
                let ids = json!(equivalents).to_string();
                if slot.get("trainingAdded").is_none() {
                    let earlier:bool=db.query_row("SELECT EXISTS(SELECT 1 FROM training WHERE id IN(SELECT value FROM json_each(?)) AND active_at<?)",params![ids,text(record,"started_at")],|row|row.get(0))?;
                    let ordinary:bool=db.query_row("SELECT EXISTS(SELECT 1 FROM drafts WHERE problem_id IN(SELECT value FROM json_each(?)) AND context='' AND code<>'')",[&ids],|row|row.get(0))?;
                    let external:bool=db.query_row("SELECT EXISTS(SELECT 1 FROM submissions WHERE problem_id IN(SELECT value FROM json_each(?)) AND (contest_id IS NULL OR contest_id<>?))",params![ids,text(record,"id")],|row|row.get(0))?;
                    if earlier || ordinary || external {
                        continue;
                    }
                }
                let pending:bool=db.query_row("SELECT EXISTS(SELECT 1 FROM submissions WHERE problem_id IN(SELECT value FROM json_each(?)) AND finished_at IS NULL)",[&ids],|row|row.get(0))?;
                if pending {
                    continue;
                }
                db.execute("UPDATE training SET active=0,removed_at=?,mock_due=0,mock_due_at=NULL,mock_due_context=NULL WHERE id IN(SELECT value FROM json_each(?)) AND active=1", params![now,ids])?;
                removed.insert(id.to_owned());
            }
        }
        Ok(
            json!({"deleted":records.len(),"removedTraining":removed.len(),"workspace":t.workspace()?}),
        )
    })
}
