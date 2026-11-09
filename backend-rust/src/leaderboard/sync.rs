//! Three-stage synchronization: prepare under a short journal read, execute
//! without DB locks, then commit validated acknowledgments under a short write.
//! Public growth is supplied by the real growth service, never invented here.
use super::{
    AuthContext, LeaderboardClient, Scope, checked, invalid_receipt, sha, validate_avatar,
};
use crate::{
    api::{ApiError, fields},
    catalogue::{Catalogue, row_or_portable},
    identity::canonical_url,
    storage::{PersonalStore, atomic},
};
use chrono::{DateTime, SecondsFormat, Utc};
use reqwest::Method;
use rusqlite::{OptionalExtension, params};
use serde_json::{Value, json};
use std::collections::HashMap;

/// Neither the plan nor the receipt is deserializable from frontend input.
pub struct SyncPlan {
    scope: Scope,
    events: Vec<Value>,
    public_profile: Option<Value>,
}
impl SyncPlan {
    pub fn event_count(&self) -> usize {
        self.events.len()
    }
    pub fn publishes_progress(&self) -> bool {
        self.public_profile.is_some()
    }
}
pub struct SyncReceipt {
    scope: Scope,
    events: Vec<Value>,
    rewards: Value,
    at: DateTime<Utc>,
    complete: bool,
    result: Value,
}

fn stamp(value: &str) -> Option<DateTime<Utc>> {
    crate::ability::time(value)
}
fn stored() -> ApiError {
    ApiError::new(500, "INVALID_STORED_DATA", "通过记录格式异常，原记录已保留")
}
fn string<'a>(v: &'a Value, key: &str) -> &'a str {
    v[key].as_str().unwrap_or("")
}

impl LeaderboardClient {
    /// Selects metadata only; source-code blobs and private hub summaries are not read.
    /// `public_profile=None` explicitly defers growth publication, not synchronization.
    pub fn prepare_sync(
        &self,
        auth: &AuthContext<'_>,
        personal: &PersonalStore,
        catalogue: &Catalogue,
        public_profile: Option<&Value>,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<SyncPlan, ApiError> {
        let scope = self.scope(auth, guard)?;
        require_journal(personal, &scope)?;
        if let Some(profile) = public_profile {
            validate_public_profile(profile)?;
        }
        let records=personal.rows("SELECT id,problem_id,submitted_at,finished_at FROM submissions WHERE mode='submit' AND verdict='AC' AND scope='official' AND finished_at IS NOT NULL ORDER BY submitted_at,id",[])?;
        let mut receipts = HashMap::new();
        let mut query = personal
            .db
            .prepare("SELECT event_id,accepted_at FROM ranking_receipts WHERE endpoint=?")?;
        for item in query.query_map([&scope.endpoint], |r| {
            Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?))
        })? {
            let (id, at) = item?;
            if let Some(at) = stamp(&at) {
                receipts.insert(id, at);
            }
        }
        let mut metadata = HashMap::new();
        let mut first = HashMap::<String, (DateTime<Utc>, Option<f64>)>::new();
        for record in records.as_array().ok_or_else(stored)? {
            let id = string(record, "problem_id");
            let Some(at) = stamp(string(record, "submitted_at")) else {
                continue;
            };
            // Dates remain actual receipt dates. No undated public AC becomes today's event.
            if at.timestamp() < 946684800 || at > now + chrono::Duration::minutes(5) {
                return Err(stored());
            }
            if !metadata.contains_key(id) {
                let row = match row_or_portable(catalogue, personal, id) {
                    Ok(v) => v,
                    Err(e) if e.status == 404 => Value::Null,
                    Err(e) => return Err(e),
                };
                metadata.insert(id.to_owned(), row);
            }
            let row = &metadata[id];
            let key = canonical_url(string(row, "url")).unwrap_or_else(|| id.to_owned());
            let difficulty = row["difficulty"]
                .as_f64()
                .filter(|v| v.is_finite() && (0.0..=5000.0).contains(v));
            if first.get(&key).is_none_or(|(old, _)| at < *old) {
                first.insert(key, (at, difficulty));
            }
        }
        let mut sorted = first.into_iter().collect::<Vec<_>>();
        sorted.sort_by(|(ak, (at, _)), (bk, (bt, _))| at.cmp(bt).then(ak.cmp(bk)));
        let mut events = Vec::new();
        for (key, (at, difficulty)) in sorted {
            let problem = sha(key.as_bytes());
            let event = sha(format!("official-v1\0{}\0{problem}", scope.owner).as_bytes());
            if receipts.get(&event).is_some_and(|old| *old <= at) {
                continue;
            }
            events.push(json!({"eventId":event,"problemKey":problem,"acceptedAt":at.to_rfc3339_opts(SecondsFormat::Micros,true),"scope":"official","difficulty":difficulty}));
        }
        checked(guard)?;
        Ok(SyncPlan {
            scope,
            events,
            public_profile: public_profile.cloned(),
        })
    }

    /// Does not hold or acquire a SQLite connection. Writes are attempted once.
    /// A partial success can safely be re-prepared: official event IDs are stable.
    pub fn execute_sync(
        &self,
        auth: &AuthContext<'_>,
        plan: &SyncPlan,
        now: DateTime<Utc>,
        guard: &dyn Fn() -> bool,
    ) -> Result<SyncReceipt, ApiError> {
        let scope = self.scope(auth, guard)?;
        if scope != plan.scope {
            return Err(ApiError::new(409, "OWNER_CHANGED", "账号已切换"));
        }
        let registered = self.verified_profile(auth, now, guard)?;
        let mut progress_published = false;
        if let Some(profile) = &plan.public_profile {
            if registered["publicProgressProtocol"] == 1 {
                let mut payload = profile.clone();
                if registered["publicAppearanceProtocol"] != 1 {
                    payload.as_object_mut().unwrap().remove("avatarData");
                }
                if payload["avatarData"]
                    .as_str()
                    .is_some_and(|v| v.len() > 48 * 1024)
                    && registered["originalAvatarProtocol"] != 1
                {
                    payload.as_object_mut().unwrap().remove("avatarData");
                }
                let answer = self.request(
                    auth,
                    Method::PUT,
                    "/v1/profile",
                    Some(&payload),
                    super::SMALL_LIMIT,
                    guard,
                )?;
                if answer["userId"] != auth.owner
                    || answer["publicProgress"] != payload["publicProgress"]
                {
                    let mut e = invalid_receipt();
                    e.uncertain = true;
                    return Err(e);
                }
                if let Some(avatar) = payload["avatarData"].as_str() {
                    let hash = if avatar.is_empty() {
                        Value::Null
                    } else {
                        json!(sha(avatar.as_bytes()))
                    };
                    if answer["avatarHash"] != hash {
                        let mut e = invalid_receipt();
                        e.uncertain = true;
                        return Err(e);
                    }
                }
                progress_published = true;
            }
        }
        for events in plan.events.chunks(100) {
            let answer = self.request(
                auth,
                Method::POST,
                "/v1/events",
                Some(&json!({"events":events})),
                super::SMALL_LIMIT,
                guard,
            )?;
            if answer["processed"].as_u64() != Some(events.len() as u64)
                || answer["scope"] != "official"
            {
                let mut e = invalid_receipt();
                e.uncertain = true;
                return Err(e);
            }
        }
        // Force a new read after upload, retaining the prior successful range
        // if metadata transport fails. Failure must never become a zero board.
        let mut boards = serde_json::Map::new();
        let mut failures = Vec::new();
        for period in ["daily", "weekly", "total"] {
            let board = self.fetch_rankings(auth, period, now, guard, true)?;
            if board["status"] != "ready" {
                failures.push(
                    board["error"]
                        .as_str()
                        .unwrap_or("排行榜尚未刷新")
                        .to_owned(),
                );
            }
            boards.insert(period.to_owned(), board);
        }
        let rewards = self.request(
            auth,
            Method::GET,
            "/v1/rewards",
            None,
            super::SMALL_LIMIT,
            guard,
        )?;
        if rewards["userId"] != auth.owner
            || rewards["totalXp"]
                .as_u64()
                .is_none_or(|v| v > 1_000_000_000)
            || !rewards["awards"].as_array().is_some_and(|v| v.len() <= 50)
        {
            return Err(invalid_receipt());
        }
        checked(guard)?;
        let complete = failures.is_empty();
        let result = json!({"configured":true,"status":if complete{"ready"}else{"error"},"endpoint":scope.endpoint,"error":failures.first().map(String::as_str).unwrap_or(""),"lastSyncedAt":if complete{Some(now.to_rfc3339_opts(SecondsFormat::Micros,true))}else{None},"processed":plan.events.len(),"publicProgressPublished":progress_published,"boards":boards});
        Ok(SyncReceipt {
            scope,
            events: plan.events.clone(),
            rewards,
            at: now,
            complete,
            result,
        })
    }
    /// Invoke after reacquiring the same lease's journal lock. No network runs here.
    pub fn commit_sync(
        &self,
        auth: &AuthContext<'_>,
        personal: &PersonalStore,
        receipt: SyncReceipt,
        guard: &dyn Fn() -> bool,
    ) -> Result<Value, ApiError> {
        let scope = self.scope(auth, guard)?;
        if scope != receipt.scope {
            return Err(ApiError::new(409, "OWNER_CHANGED", "账号已切换"));
        }
        atomic(&personal.db, |db| {
            checked(guard)?;
            require_journal(personal, &scope)?;
            for event in &receipt.events {
                // Never replace a previously acknowledged earlier acceptance.
                let old: Option<String> = db
                    .query_row(
                        "SELECT accepted_at FROM ranking_receipts WHERE endpoint=? AND event_id=?",
                        params![scope.endpoint, event["eventId"].as_str()],
                        |r| r.get(0),
                    )
                    .optional()?;
                if old
                    .as_deref()
                    .and_then(stamp)
                    .zip(stamp(string(event, "acceptedAt")))
                    .is_some_and(|(a, b)| a <= b)
                {
                    continue;
                }
                db.execute("INSERT INTO ranking_receipts(endpoint,event_id,accepted_at) VALUES(?,?,?) ON CONFLICT(endpoint,event_id) DO UPDATE SET accepted_at=excluded.accepted_at",params![scope.endpoint,event["eventId"].as_str(),event["acceptedAt"].as_str()])?;
            }
            db.execute("INSERT INTO ranking_reward_totals(endpoint,user_id,total_xp,awards,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(endpoint,user_id) DO UPDATE SET total_xp=excluded.total_xp,awards=excluded.awards,updated_at=excluded.updated_at",params![scope.endpoint,scope.owner,receipt.rewards["totalXp"].as_i64(),receipt.rewards["awards"].to_string(),receipt.at.to_rfc3339_opts(SecondsFormat::Micros,true)])?;
            if receipt.complete {
                db.execute("UPDATE ranking_profile SET last_synced_at=? WHERE singleton=1 AND user_id=? AND endpoint=?",params![receipt.at.to_rfc3339_opts(SecondsFormat::Micros,true),scope.owner,scope.endpoint])?;
            }
            checked(guard)?;
            Ok(())
        })?;
        Ok(receipt.result)
    }
}
fn require_journal(personal: &PersonalStore, scope: &Scope) -> Result<(), ApiError> {
    let profile: Option<(String, String)> = personal
        .db
        .query_row(
            "SELECT user_id,endpoint FROM ranking_profile WHERE singleton=1",
            [],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .optional()?;
    if !profile.is_some_and(|(owner, endpoint)| {
        owner == scope.owner
            && super::validate_endpoint(&endpoint).ok().as_deref() == Some(&scope.endpoint)
    }) {
        return Err(ApiError::new(409, "OWNER_CHANGED", "账号已切换"));
    }
    Ok(())
}
fn display(v: &Value, max: usize) -> bool {
    v.as_str().is_some_and(|s| {
        !s.is_empty()
            && s.trim() == s
            && s.chars().count() <= max
            && !s.chars().any(char::is_control)
    })
}
fn integer(v: &Value, min: u64, max: u64) -> bool {
    v.as_u64().is_some_and(|n| min <= n && n <= max)
}
fn validate_public_profile(value: &Value) -> Result<(), ApiError> {
    fields(value, &["publicProgress", "avatarData"])?;
    if let Some(avatar) = value.get("avatarData") {
        validate_avatar(
            avatar
                .as_str()
                .ok_or_else(|| ApiError::bad("头像图片格式无效"))?,
        )?;
    }
    let p = &value["publicProgress"];
    fields(
        p,
        &[
            "level",
            "tier",
            "rankTier",
            "rankScore",
            "titles",
            "currentLevelXp",
            "nextLevelXp",
        ],
    )?;
    let reject = || ApiError::bad("公开成长资料无效");
    if !["level", "tier", "rankTier", "rankScore", "titles"]
        .iter()
        .all(|k| p.get(k).is_some())
        || !integer(&p["level"], 1, 100)
        || !display(&p["tier"], 24)
        || p["rankTier"].is_null() != p["rankScore"].is_null()
        || !p["rankTier"].is_null()
            && (!display(&p["rankTier"], 24) || !integer(&p["rankScore"], 0, 1_000_000))
    {
        return Err(reject());
    }
    if p.get("currentLevelXp").is_some() || p.get("nextLevelXp").is_some() {
        if !integer(&p["currentLevelXp"], 0, 1_000_000_000)
            || !integer(&p["nextLevelXp"], 0, 1_000_000_000)
            || p["currentLevelXp"].as_u64() > p["nextLevelXp"].as_u64()
        {
            return Err(reject());
        }
    }
    let Some(titles) = p["titles"].as_array().filter(|v| v.len() <= 2) else {
        return Err(reject());
    };
    let mut kinds = Vec::new();
    for title in titles {
        fields(title, &["id", "name", "category", "target"])?;
        let id = title["id"].as_str().unwrap_or("");
        let category = title["category"].as_str().unwrap_or("");
        if title.as_object().map_or(0, |v| v.len()) != 4
            || id.is_empty()
            || id.len() > 48
            || !id.as_bytes()[0].is_ascii_lowercase()
            || !id
                .bytes()
                .all(|b| b.is_ascii_lowercase() || b.is_ascii_digit() || b == b'-')
            || !display(&title["name"], 24)
            || !["ac", "streak"].contains(&category)
            || kinds.contains(&category)
            || !integer(&title["target"], 1, 2000)
        {
            return Err(reject());
        }
        kinds.push(category);
    }
    Ok(())
}
