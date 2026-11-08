//! Account-owned spaced review tasks derived from actual official receipts.
//! Existing keys, task identities and one-problem/day reward ledgers are kept.
use crate::{
    ability,
    api::ApiError,
    catalogue::row_or_portable,
    identity::canonical_url,
    learning::{day, stamp},
    storage::PersonalStore,
    training::Training,
};
use chrono::{Duration, NaiveDate};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, HashMap, HashSet};

fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v[key].as_str().unwrap_or("")
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
    ApiError::new(500, "INVALID_STORED_DATA", "复习记录格式异常，原数据已保留")
}
fn at(v: &str) -> Result<chrono::DateTime<chrono::Utc>, ApiError> {
    ability::time(v).ok_or_else(invalid)
}
fn date(v: &str) -> Result<NaiveDate, ApiError> {
    NaiveDate::parse_from_str(v, "%Y-%m-%d").map_err(|_| invalid())
}
fn add_days(v: &str, days: i64) -> Result<String, ApiError> {
    Ok((date(v)? + Duration::days(days)).to_string())
}
fn hash(value: &str) -> String {
    format!("{:x}", Sha256::digest(value.as_bytes()))
}
fn array<'a>(v: &'a Value, key: &str) -> Result<&'a Vec<Value>, ApiError> {
    v[key].as_array().ok_or_else(invalid)
}
fn create_task(
    state: &mut Value,
    anchor: &str,
    due: &str,
    identity: &str,
    preferences: &mut BTreeMap<String, Value>,
    updates: &mut BTreeMap<String, Value>,
) {
    let task_id = hash(&format!("{}\0{anchor}", text(state, "key")))[..32].to_owned();
    state["taskId"] = json!(task_id);
    state["due"] = json!(due);
    state["anchor"] = json!(anchor);
    let key = format!("review-task:{task_id}");
    if !preferences.contains_key(&key) {
        let task = json!({"id":task_id,"problemId":identity,"problemKey":state["key"],"due":due,"openedAt":null,"completedAt":null,"failures":[],"processed":[],"triggerDay":state.get("triggerDay").cloned().unwrap_or(Value::Null)});
        preferences.insert(key.clone(), task.clone());
        updates.insert(key, task);
    }
}
pub fn interval_after_pass(
    stability: f64,
    difficulty: Option<f64>,
    ability: Option<i64>,
    failures: usize,
    assisted: bool,
) -> (f64, i64) {
    if assisted {
        return (1., 1);
    }
    let relative = difficulty.zip(ability).map_or(0., |(d, a)| d - a as f64);
    let factor = (2.6 - relative / 650.).clamp(1.5, 3.2) * 0.78f64.powi(failures.min(3) as i32);
    let stability = (stability * factor.max(1.2)).clamp(1.1, 75.);
    (
        (stability * 1000.).round_ties_even() / 1000.,
        (stability * 1.2).round_ties_even().clamp(1., 90.) as i64,
    )
}

pub fn task(
    t: &Training<'_>,
    identity: &str,
    review_id: Option<&str>,
    open: bool,
) -> Result<Option<Value>, ApiError> {
    let Some(review_id) = review_id.filter(|id| !id.is_empty()) else {
        return Ok(None);
    };
    if review_id.chars().count() != 32 {
        return Err(ApiError::bad("复习上下文无效"));
    }
    let key = format!("review-task:{review_id}");
    let mut item = t
        .personal
        .document(&key)?
        .filter(Value::is_object)
        .ok_or_else(|| ApiError::missing("没有找到这次复习"))?;
    if item["id"] != review_id {
        return Err(invalid());
    }
    if !t.ids(identity)?.iter().any(|id| item["problemId"] == *id) {
        return Err(ApiError::missing("没有找到这次复习"));
    }
    if !truth(&item["openedAt"]) && open {
        if truth(&item["minimumAt"]) && at(text(&item, "minimumAt"))? > t.now {
            return Err(ApiError::conflict("请在上次通过至少 24 小时后开始这轮检验"));
        }
        if text(&item, "due") > day(t.now).as_str() {
            return Err(ApiError::conflict("这道题还未到复习时间"));
        }
        date(text(&item, "due"))?;
        item["openedAt"] = json!(stamp(t.now));
        PersonalStore::put(&t.personal.db, &key, &item.to_string(), &stamp(t.now))?;
    }
    Ok(Some(item))
}
pub fn set_cancelled(
    t: &Training<'_>,
    identity: &str,
    review_id: &str,
    cancelled: bool,
) -> Result<(), ApiError> {
    let mut item = task(t, identity, Some(review_id), false)?.ok_or_else(invalid)?;
    if truth(&item["completedAt"]) {
        return Err(ApiError::conflict("这次复习已经完成"));
    }
    item["cancelledAt"] = if cancelled {
        json!(stamp(t.now))
    } else {
        Value::Null
    };
    PersonalStore::put(
        &t.personal.db,
        &format!("review-task:{review_id}"),
        &item.to_string(),
        &stamp(t.now),
    )
}
#[derive(Clone)]
struct Candidate {
    value: Value,
    opened: bool,
    retention: f64,
    lapses: i64,
    relative: f64,
    key: String,
}

pub fn plan(t: &Training<'_>) -> Result<Value, ApiError> {
    let today = day(t.now);
    let mut active = HashSet::new();
    for record in t
        .personal
        .rows("SELECT id,active,removed_at FROM training", [])?
        .as_array()
        .unwrap()
    {
        if truth(&record["active"])
            || ability::time(text(record, "removed_at")).is_some_and(|at| day(at) < today)
        {
            active.insert(t.canonical(text(record, "id"))?);
        }
    }
    let mut locked = HashSet::new();
    for record in t
        .personal
        .rows("SELECT slots FROM contests WHERE status='running'", [])?
        .as_array()
        .unwrap()
    {
        let slots: Value = serde_json::from_str(text(record, "slots"))?;
        for slot in slots.as_array().ok_or_else(invalid)? {
            locked.insert(t.canonical(text(slot, "id"))?);
        }
    }
    let records=t.personal.rows("SELECT * FROM submissions WHERE mode='submit' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,rowid",[])?;
    let mut facts = Vec::<(String, Vec<Value>)>::new();
    let mut positions = HashMap::new();
    for record in records.as_array().unwrap() {
        if at(text(record, "submitted_at"))? > t.now {
            continue;
        }
        let id = t.canonical(text(record, "problem_id"))?;
        let position = *positions.entry(id.clone()).or_insert_with(|| {
            facts.push((id, Vec::new()));
            facts.len() - 1
        });
        facts[position].1.push(record.clone());
    }
    let ability_records = facts
        .iter()
        .flat_map(|(_, receipts)| receipts.iter().cloned())
        .collect::<Vec<_>>();
    let ability = ability::score(t, &ability_records)?;
    let mut preferences = BTreeMap::<String, Value>::new();
    for record in t
        .personal
        .rows(
            "SELECT key,value FROM account_preferences WHERE key LIKE 'review-%'",
            [],
        )?
        .as_array()
        .unwrap()
    {
        preferences.insert(
            text(record, "key").into(),
            serde_json::from_str(text(record, "value"))?,
        );
    }
    let mut updates = BTreeMap::new();
    let mut candidates = Vec::<Candidate>::new();
    for (identity, receipts) in &facts {
        if !active.contains(identity) {
            continue;
        }
        let wrong = receipts
            .iter()
            .filter(|r| r["verdict"] == "WA")
            .collect::<Vec<_>>();
        let Some(last_wrong) = wrong.last() else {
            continue;
        };
        let wrong_day = day(at(text(last_wrong, "submitted_at"))?);
        let row = match row_or_portable(t.catalogue, t.personal, identity) {
            Ok(row) => row,
            Err(e) if e.status == 404 => continue,
            Err(e) => return Err(e),
        };
        let difficulty = row["difficulty"]
            .as_f64()
            .filter(|d| d.is_finite() && *d > 0.);
        let problem_key = canonical_url(text(&row, "url")).unwrap_or_else(|| identity.clone());
        let state_key = format!("review-state:{}", hash(&problem_key));
        let mut state = preferences.get(&state_key).cloned().unwrap_or(Value::Null);
        let before = state.clone();
        if !state.is_object()
            || ![json!(1), json!(2)].contains(&state["version"])
            || state["version"] == 1 && !truth(&state["successes"])
        {
            let due = add_days(&wrong_day, 1)?;
            state = json!({"version":2,"key":problem_key,"stability":1.0,"successes":0,"lapses":0,"lastAt":last_wrong["submitted_at"],"parked":false,"triggerId":last_wrong["id"],"triggerDay":wrong_day});
            create_task(
                &mut state,
                text(last_wrong, "id"),
                &due,
                identity,
                &mut preferences,
                &mut updates,
            );
        } else if state["version"] == 1 {
            state["version"] = 2.into();
            state["triggerId"] = last_wrong["id"].clone();
            state["triggerDay"] = json!(wrong_day);
        }
        if state["key"] != problem_key
            || !state["stability"]
                .as_f64()
                .is_some_and(|v| v.is_finite() && v > 0.)
            || !state["successes"].is_i64()
            || !state["lapses"].is_i64()
        {
            return Err(invalid());
        }
        let mut task = preferences
            .get(&format!("review-task:{}", text(&state, "taskId")))
            .cloned()
            .unwrap_or(Value::Null);
        if !task.is_object() {
            let anchor = state
                .get("anchor")
                .and_then(Value::as_str)
                .unwrap_or_else(|| text(last_wrong, "id"))
                .to_owned();
            let due = state
                .get("due")
                .and_then(Value::as_str)
                .filter(|v| !v.is_empty())
                .unwrap_or(&today)
                .to_owned();
            create_task(
                &mut state,
                &anchor,
                &due,
                identity,
                &mut preferences,
                &mut updates,
            );
            task = preferences[&format!("review-task:{}", text(&state, "taskId"))].clone();
        }
        if !task["id"].is_string() || !task["due"].is_string() {
            return Err(invalid());
        }
        if task["id"] != state["taskId"]
            || task["problemKey"] != state["key"]
            || !t.ids(identity)?.iter().any(|id| task["problemId"] == *id)
        {
            return Err(invalid());
        }
        date(text(&task, "due"))?;
        array(&task, "processed")?;
        array(&task, "failures")?;
        let task_before = task.clone();
        if !truth(&task["completedAt"])
            && !truth(&task["cancelledAt"])
            && text(&task, "due") <= today.as_str()
        {
            for receipt in receipts {
                let binding = format!("review-receipt:{}", text(receipt, "id"));
                if receipt["verdict"] != "AC"
                    || truth(&receipt["contest_id"])
                    || text(receipt, "code").trim().is_empty()
                    || text(receipt, "message").contains("官网同步")
                    || preferences.get(&binding).is_some_and(|v| !v.is_null())
                    || day(at(text(receipt, "submitted_at"))?) != today
                    || text(receipt, "submitted_at") < text(&task, "openedAt")
                {
                    continue;
                }
                if !truth(&task["openedAt"]) {
                    task["openedAt"] = receipt["submitted_at"].clone();
                }
                preferences.insert(binding.clone(), task["id"].clone());
                updates.insert(binding, task["id"].clone());
                break;
            }
        }
        if truth(&task["openedAt"]) && !truth(&task["completedAt"]) && !truth(&task["cancelledAt"])
        {
            let processed = array(&task, "processed")?
                .iter()
                .cloned()
                .collect::<Vec<_>>();
            for receipt in receipts {
                if processed.contains(&receipt["id"])
                    || preferences.get(&format!("review-receipt:{}", text(receipt, "id")))
                        != Some(&task["id"])
                    || text(receipt, "submitted_at") < text(&task, "openedAt")
                {
                    continue;
                }
                task["processed"]
                    .as_array_mut()
                    .unwrap()
                    .push(receipt["id"].clone());
                if ["WA", "TLE", "MLE", "RE", "OLE"].contains(&text(receipt, "verdict")) {
                    task["failures"]
                        .as_array_mut()
                        .unwrap()
                        .push(receipt["id"].clone());
                    state["lapses"] = json!(state["lapses"].as_i64().ok_or_else(invalid)? + 1);
                }
                if receipt["verdict"] == "AC" {
                    let assisted = truth(&receipt["solution_seen"]);
                    let failures = array(&task, "failures")?.len();
                    let (stability, mut interval) = interval_after_pass(
                        state["stability"].as_f64().ok_or_else(invalid)?,
                        difficulty,
                        ability,
                        failures,
                        assisted,
                    );
                    state["stability"] = json!(stability);
                    state["successes"] = json!(if assisted {
                        0
                    } else {
                        state["successes"].as_i64().ok_or_else(invalid)? + 1
                    });
                    state["lastAt"] = receipt["submitted_at"].clone();
                    task["completedAt"] = receipt["finished_at"].clone();
                    task["independent"] = json!(!assisted);
                    let pass_day = day(at(text(receipt, "submitted_at"))?);
                    let trigger_day = text(&task, "triggerDay").to_owned();
                    if !trigger_day.is_empty() && text(&task, "due") == add_days(&trigger_day, 1)? {
                        let reward_key = format!(
                            "review-reward:{}",
                            hash(&format!("{problem_key}\0{pass_day}"))
                        );
                        let claim=preferences.get(&reward_key).filter(|v|!v.is_null()).cloned().unwrap_or_else(||json!({"version":1,"xp":20,"problemKey":problem_key,"day":pass_day,"taskId":task["id"],"receiptId":receipt["id"],"awardedAt":stamp(t.now)}));
                        if !preferences.get(&reward_key).is_some_and(|v| !v.is_null()) {
                            preferences.insert(reward_key.clone(), claim.clone());
                            updates.insert(reward_key.clone(), claim.clone());
                        }
                        if claim.is_object() && claim["receiptId"] == receipt["id"] {
                            task["rewardClaim"] = json!(reward_key);
                            task["rewardReceiptId"] = receipt["id"].clone();
                            task["rewardXp"] = 20.into();
                        }
                    }
                    let wa_today = wrong.iter().any(|r| {
                        day(at(text(r, "submitted_at")).unwrap()) == pass_day
                            && text(r, "submitted_at") <= text(receipt, "submitted_at")
                    });
                    interval = if wa_today { 1 } else { interval.max(2) };
                    state["triggerId"] = last_wrong["id"].clone();
                    state["triggerDay"] = json!(wrong_day);
                    let parked = difficulty
                        .zip(ability)
                        .is_some_and(|(d, a)| d <= a as f64 - 200.)
                        && !assisted
                        && failures == 0;
                    state["parked"] = json!(parked);
                    state["due"] = if parked {
                        Value::Null
                    } else {
                        json!(add_days(&pass_day, interval)?)
                    };
                    if let Some(due) = state["due"].as_str().map(str::to_owned) {
                        create_task(
                            &mut state,
                            text(receipt, "id"),
                            &due,
                            identity,
                            &mut preferences,
                            &mut updates,
                        );
                    }
                    break;
                }
            }
        }
        if task != task_before {
            let key = format!("review-task:{}", text(&task, "id"));
            preferences.insert(key.clone(), task.clone());
            updates.insert(key, task);
        }
        let current = preferences
            .get(&format!("review-task:{}", text(&state, "taskId")))
            .cloned()
            .unwrap_or(json!({}));
        if text(last_wrong, "submitted_at") > text(&state, "lastAt")
            && last_wrong["id"] != state["triggerId"]
            && !(truth(&current["openedAt"])
                && !truth(&current["completedAt"])
                && !truth(&current["cancelledAt"]))
        {
            state["parked"] = false.into();
            state["stability"] = json!(1.0);
            state["lastAt"] = last_wrong["submitted_at"].clone();
            state["triggerId"] = last_wrong["id"].clone();
            state["triggerDay"] = json!(wrong_day);
            create_task(
                &mut state,
                text(last_wrong, "id"),
                &add_days(&wrong_day, 1)?,
                identity,
                &mut preferences,
                &mut updates,
            );
        }
        if state != before {
            preferences.insert(state_key.clone(), state.clone());
            updates.insert(state_key, state.clone());
        }
        let current = preferences
            .get(&format!("review-task:{}", text(&state, "taskId")))
            .ok_or_else(invalid)?;
        if !locked.contains(identity)
            && truth(&state["due"])
            && text(&state, "due") <= today.as_str()
            && !truth(&current["completedAt"])
            && !truth(&current["cancelledAt"])
        {
            let elapsed = (t.now - at(text(&state, "lastAt"))?)
                .num_milliseconds()
                .max(0) as f64
                / 86_400_000.;
            let retention = 0.9f64.powf(
                (elapsed / state["stability"].as_f64().ok_or_else(invalid)?.max(0.4)).min(100.),
            );
            let relative = difficulty.zip(ability).map_or(0., |(d, a)| d - a as f64);
            let minutes = (15. + relative / 40.).round_ties_even().clamp(5., 40.) as i64;
            candidates.push(Candidate {value:json!({"id":current["id"],"problemId":identity,"due":state["due"],"openedAt":current.get("openedAt").cloned().unwrap_or(Value::Null),"stage":state["successes"],"minutes":minutes}),opened:truth(&current["openedAt"]),retention,lapses:state["lapses"].as_i64().ok_or_else(invalid)?.min(3),relative,key:problem_key});
        }
    }
    let configs = t
        .personal
        .rows("SELECT config FROM goals WHERE archived=0", [])?;
    let mut daily_minutes = 90;
    let mut budgets = Vec::new();
    let mut new_costs = Vec::new();
    for record in configs.as_array().unwrap() {
        let config: Value = serde_json::from_str(text(record, "config"))?;
        budgets.push(config["dailyMinutes"].as_i64().unwrap_or(90).clamp(15, 720));
        new_costs.push(config["minutesPerProblem"].as_i64().unwrap_or(45).max(5));
    }
    if let Some(minutes) = budgets.iter().max() {
        daily_minutes = *minutes;
    }
    candidates.sort_by(|a, b| {
        b.opened
            .cmp(&a.opened)
            .then(a.retention.total_cmp(&b.retention))
            .then(b.lapses.cmp(&a.lapses))
            .then(b.relative.total_cmp(&a.relative))
            .then(b.key.cmp(&a.key))
    });
    let allocation_key = format!("review-day:{today}");
    let allocation = preferences
        .get(&allocation_key)
        .cloned()
        .unwrap_or(json!({"ids":[]}));
    let saved = array(&allocation, "ids")?.clone();
    if saved.iter().any(|id| !id.is_string()) {
        return Err(invalid());
    }
    let mut selected = candidates
        .iter()
        .filter(|c| saved.contains(&c.value["id"]) || c.opened)
        .map(|c| c.value.clone())
        .collect::<Vec<_>>();
    let mut spent = candidates
        .iter()
        .filter(|c| saved.contains(&c.value["id"]))
        .map(|c| c.value["minutes"].as_i64().unwrap())
        .sum::<i64>();
    let unique_saved = saved
        .iter()
        .filter_map(Value::as_str)
        .collect::<HashSet<_>>();
    for id in &unique_saved {
        if preferences
            .get(&format!("review-task:{id}"))
            .is_some_and(|v| truth(&v["completedAt"]))
        {
            spent += allocation["minutes"][*id].as_i64().unwrap_or(15);
        }
    }
    let allowance = if candidates.len() >= 4 {
        daily_minutes
    } else {
        (daily_minutes as f64 * 0.6).round_ties_even() as i64
    }
    .max(15);
    for candidate in &candidates {
        if selected.contains(&candidate.value) {
            continue;
        }
        let cost = candidate.value["minutes"].as_i64().unwrap();
        if selected.len() >= 8 || spent + cost > allowance && !selected.is_empty() {
            continue;
        }
        if spent >= allowance {
            break;
        }
        selected.push(candidate.value.clone());
        spent += cost;
    }
    let mut planned = Vec::new();
    for id in &saved {
        if !planned.contains(id) {
            planned.push(id.clone());
        }
    }
    let mut costs = allocation.get("minutes").cloned().unwrap_or(json!({}));
    if !costs.is_object() {
        return Err(invalid());
    }
    for candidate in &selected {
        if !planned.contains(&candidate["id"]) {
            planned.push(candidate["id"].clone());
        }
        costs[text(candidate, "id")] = candidate["minutes"].clone();
    }
    if planned != saved {
        updates.insert(allocation_key, json!({"ids":planned,"minutes":costs}));
    }
    let pause =
        !candidates.is_empty() && daily_minutes - spent < new_costs.into_iter().min().unwrap_or(45);
    let result = json!({"date":today,"tasks":selected,"dueCount":candidates.len(),"deferredCount":candidates.len()-selected.len(),"minutes":spent,"dailyMinutes":daily_minutes,"newMinutes":(daily_minutes-spent).max(0),"reviewOnly":pause,"abilityScore":ability,"policyVersion":3});
    // Compute and validate the entire plan first. A failed write rolls back
    // task creation, receipt binding, reward ledger and daily allocation.
    if !updates.is_empty() {
        let tx = t.personal.db.unchecked_transaction()?;
        for (key, value) in updates {
            let payload = value.to_string();
            let prior: Option<String> = tx
                .query_row(
                    "SELECT value FROM account_preferences WHERE key=?",
                    [&key],
                    |r| r.get(0),
                )
                .optional()?;
            if prior.as_deref() != Some(&payload) {
                PersonalStore::put(&tx, &key, &payload, &stamp(t.now))?;
            }
        }
        tx.commit()?;
    }
    Ok(result)
}

use rusqlite::OptionalExtension;
