use chrono::{DateTime, Duration, TimeZone, Utc};
use flate2::{Compression, write::ZlibEncoder};
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::{collections::HashSet, io::Write};
use tempfile::TempDir;
use tobe_core::{
    catalogue::Catalogue, goals, library::Library, migration::logical_fingerprint,
    storage::PersonalStore, training::Training,
};

struct Fixture {
    folder: TempDir,
    personal: PersonalStore,
    catalogue: Catalogue,
    library: Library,
    now: DateTime<Utc>,
}
impl Fixture {
    fn new() -> Self {
        let folder = tempfile::tempdir().unwrap();
        let personal = PersonalStore::open(&folder.path().join("personal.sqlite3")).unwrap();
        let db = Connection::open_in_memory().unwrap();
        db.execute_batch("CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT);CREATE TABLE catalogue(id TEXT PRIMARY KEY,position INTEGER,full BLOB,compact TEXT)").unwrap();
        for i in 0..32 {
            let id = format!("fixture::{i}");
            let contest = 900 + i / 8;
            let letter = char::from(b'A' + (i % 8) as u8).to_string();
            let row = json!({"id":id,"title":format!("独立题目 {i}"),"platform":"Codeforces","url":format!("https://codeforces.com/contest/{contest}/problem/{letter}"),"contest":format!("Div.3 {contest}"),"contestFullName":format!("Codeforces Round {contest} (Div. 3)"),"problem":letter,"difficulty":1000+(i%12)*50,"difficultySource":"Codeforces 官方 rating","tags":[],"addedAt":"2026-11-06T02:00:00Z","endedAt":"2026-11-05T04:00:00Z"});
            let mut z = ZlibEncoder::new(Vec::new(), Compression::default());
            z.write_all(row.to_string().as_bytes()).unwrap();
            db.execute(
                "INSERT INTO catalogue VALUES(?,?,?,?)",
                params![id, i, z.finish().unwrap(), row.to_string()],
            )
            .unwrap();
            for alias in [id.clone(), format!("alias::{i}")] {
                db.execute("INSERT INTO aliases VALUES(?,?)", params![alias, id])
                    .unwrap();
            }
        }
        Self {
            folder,
            personal,
            catalogue: Catalogue { db },
            library: Library {
                db: Connection::open_in_memory().unwrap(),
            },
            now: Utc.with_ymd_and_hms(2026, 11, 6, 4, 0, 0).unwrap(),
        }
    }
    fn training(&mut self) -> Training<'_> {
        Training {
            catalogue: &self.catalogue,
            personal: &mut self.personal,
            library: &self.library,
            now: self.now,
        }
    }
    fn body(title: &str) -> Value {
        json!({"title":title,"kind":"custom","deadline":"2026-11-07","totalProblems":4,"dailyMinutes":90})
    }
    fn save(&mut self, title: &str) -> Value {
        goals::save(&self.training(), &Self::body(title)).unwrap()
    }
    fn two(&mut self) -> (String, String) {
        let first = self.save("第一目标")["goals"][0]["id"]
            .as_str()
            .unwrap()
            .to_owned();
        self.now += Duration::seconds(1);
        let second = self.save("第二目标")["goals"]
            .as_array()
            .unwrap()
            .iter()
            .find(|goal| goal["title"] == "第二目标")
            .unwrap()["id"]
            .as_str()
            .unwrap()
            .to_owned();
        (first, second)
    }
    fn receipt(&self, id: &str, problem: &str, verdict: &str, scope: &str, at: DateTime<Utc>) {
        let at = at.to_rfc3339();
        self.personal.db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES(?,?,'submit',?,?,'generated original source',?,?)",params![id,problem,scope,verdict,at,at]).unwrap();
    }
    fn fingerprint(&self) -> String {
        logical_fingerprint(&self.personal.db).unwrap()
    }
}
fn goal<'a>(v: &'a Value, id: &str) -> &'a Value {
    v["goals"]
        .as_array()
        .unwrap()
        .iter()
        .find(|goal| goal["id"] == id)
        .unwrap()
}
fn ids(goal: &Value) -> Vec<String> {
    goal["dailyTask"]["problems"]
        .as_array()
        .unwrap()
        .iter()
        .map(|row| row["id"].as_str().unwrap().into())
        .collect()
}

#[test]
fn two_goals_freeze_independent_daily_selections_and_only_official_evidence_completes_them() {
    let mut f = Fixture::new();
    let (first, second) = f.two();
    let value = goals::list(&f.training(), false).unwrap();
    let a = ids(goal(&value, &first));
    let b = ids(goal(&value, &second));
    assert_eq!((a.len(), b.len()), (2, 2));
    assert!(a.iter().all(|id| !b.contains(id)));
    f.now += Duration::seconds(1);
    f.receipt("local", &a[0], "AC", "local", f.now);
    assert_eq!(
        goal(&goals::list(&f.training(), false).unwrap(), &first)["dailyTask"]["progress"],
        0
    );
    for (i, id) in b.iter().enumerate() {
        f.now += Duration::seconds(1);
        f.receipt(&format!("official-{i}"), id, "AC", "official", f.now);
    }
    let value = goals::list(&f.training(), true).unwrap();
    assert_eq!(ids(goal(&value, &first)), a);
    assert_eq!(goal(&value, &first)["dailyTask"]["progress"], 0);
    assert_eq!(goal(&value, &second)["dailyTask"]["progress"], 2);
    assert_eq!(goal(&value, &second)["dailyTask"]["target"], 2);
    assert!(ids(goal(&value, &second)).is_empty());
    f.personal = PersonalStore::open(&f.folder.path().join("personal.sqlite3")).unwrap();
    assert_eq!(goals::list(&f.training(), false).unwrap(), value);
    f.now += Duration::days(1);
    let next = goals::list(&f.training(), true).unwrap();
    let all = next["goals"]
        .as_array()
        .unwrap()
        .iter()
        .flat_map(ids)
        .collect::<Vec<_>>();
    assert!(all.iter().all(|id| !b.contains(id)));
    assert_eq!(all.iter().collect::<HashSet<_>>().len(), all.len());
}

#[test]
fn same_day_removal_and_legacy_null_target_repair_do_not_reactivate_a_frozen_task() {
    let mut f = Fixture::new();
    let value = f.save("保持移除");
    let id = value["goals"][0]["id"].as_str().unwrap().to_owned();
    let selected = ids(&value["goals"][0]);
    f.training().remove(&json!({"id":selected[0]})).unwrap();
    f.personal
        .db
        .execute("UPDATE goal_daily_assignments SET target=NULL", [])
        .unwrap();
    let repaired = goals::list(&f.training(), true).unwrap();
    assert_eq!(goal(&repaired, &id)["dailyTask"]["target"], 2);
    assert_eq!(ids(goal(&repaired, &id)), selected);
    assert_eq!(
        f.personal
            .db
            .query_row(
                "SELECT active FROM training WHERE id=?",
                [&selected[0]],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
        0
    );
    let before = f.fingerprint();
    goals::list(&f.training(), true).unwrap();
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn legacy_shared_alias_assignments_are_reserved_for_one_goal_and_repaired_without_duplicate_credit()
{
    let mut f = Fixture::new();
    let (first, second) = f.two();
    let value = goals::list(&f.training(), false).unwrap();
    let original = ids(goal(&value, &first));
    let aliases = original
        .iter()
        .map(|id| id.replace("fixture::", "alias::"))
        .collect::<Vec<_>>();
    f.personal
        .db
        .execute(
            "UPDATE goal_daily_assignments SET ids=?,target=NULL",
            [json!(aliases).to_string()],
        )
        .unwrap();
    let value = goals::list(&f.training(), true).unwrap();
    let a = ids(goal(&value, &first));
    let b = ids(goal(&value, &second));
    let canonical = |ids: Vec<String>| {
        ids.into_iter()
            .map(|id| f.catalogue.canonical(&id).unwrap().unwrap())
            .collect::<HashSet<_>>()
    };
    assert!(canonical(a.clone()).is_disjoint(&canonical(b)));
    assert_eq!(a, aliases);
    f.now += Duration::seconds(1);
    for (i, id) in original.iter().enumerate() {
        f.receipt(&format!("pass-{i}"), id, "AC", "official", f.now);
    }
    let value = goals::list(&f.training(), false).unwrap();
    assert_eq!(goal(&value, &first)["dailyTask"]["progress"], 2);
    assert_eq!(goal(&value, &second)["dailyTask"]["progress"], 0);
}

#[test]
fn recent_contest_groups_keep_ids_created_time_and_manual_clear_through_refresh() {
    let mut f = Fixture::new();
    let saved = f.save("最近比赛");
    let id = saved["goals"][0]["id"].as_str().unwrap().to_owned();
    f.personal.db.execute("UPDATE goals SET created_at='2026-11-01T00:00:00Z',config=json_set(config,'$.totalProblems',20)",[]).unwrap();
    let value = goals::list(&f.training(), true).unwrap();
    assert!(!value["goalTasks"].as_array().unwrap().is_empty());
    let groups = f
        .personal
        .rows(
            "SELECT * FROM practice_sets WHERE id LIKE 'goal-contest:%' ORDER BY id",
            [],
        )
        .unwrap();
    assert!(!groups.as_array().unwrap().is_empty());
    let workspace = f.training().workspace().unwrap();
    let active = workspace["training"]
        .as_array()
        .unwrap()
        .iter()
        .map(|row| row["id"].clone())
        .collect::<Vec<_>>();
    f.training().clear(&json!({"ids":active})).unwrap();
    assert!(
        f.training().workspace().unwrap()["training"]
            .as_array()
            .unwrap()
            .is_empty()
    );
    assert_eq!(
        f.personal
            .rows(
                "SELECT * FROM practice_sets WHERE id LIKE 'goal-contest:%' ORDER BY id",
                []
            )
            .unwrap(),
        groups
    );
    assert!(
        goals::list(&f.training(), true).unwrap()["goals"]
            .as_array()
            .unwrap()
            .iter()
            .any(|goal| goal["id"] == id)
    );
    assert_eq!(
        f.personal
            .rows(
                "SELECT * FROM practice_sets WHERE id LIKE 'goal-contest:%' ORDER BY id",
                []
            )
            .unwrap(),
        groups
    );
}

#[test]
fn active_goals_share_the_real_remaining_review_budget() {
    let mut f = Fixture::new();
    for title in ["第一预算", "第二预算"] {
        let mut body = Fixture::body(title);
        body["kind"] = json!("cf");
        body["dailyMinutes"] = json!(240);
        goals::save(&f.training(), &body).unwrap();
        f.now += Duration::seconds(1);
    }
    for i in 0..14 {
        let problem = format!("fixture::{i}");
        f.personal.db.execute("INSERT INTO training(id,active_at) VALUES(?,'2026-11-05T00:00:00Z') ON CONFLICT(id) DO NOTHING",[&problem]).unwrap();
        f.receipt(
            &format!("wa-{i}"),
            &problem,
            "WA",
            "official",
            f.now - Duration::days(1),
        );
    }
    let review = tobe_core::reviews::plan(&f.training()).unwrap();
    assert!(review["minutes"].as_i64().unwrap() > 0);
    let value = goals::list(&f.training(), true).unwrap();
    let minutes = value["goals"]
        .as_array()
        .unwrap()
        .iter()
        .map(|goal| {
            goal["dailyTask"]["target"].as_i64().unwrap()
                * goal["minutesPerProblem"].as_i64().unwrap()
        })
        .sum::<i64>();
    assert!(minutes <= review["newMinutes"].as_i64().unwrap());
    let before = f.fingerprint();
    assert_eq!(goals::list(&f.training(), true).unwrap(), value);
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn failed_goal_assignment_rolls_back_goal_review_allocation_and_training_together() {
    let mut f = Fixture::new();
    f.personal
        .db
        .execute(
            "INSERT INTO training(id,active_at) VALUES('fixture::0','2026-11-05T00:00:00Z')",
            [],
        )
        .unwrap();
    f.receipt(
        "wrong",
        "fixture::0",
        "WA",
        "official",
        f.now - Duration::days(1),
    );
    f.personal.db.execute_batch("CREATE TRIGGER fail_goal BEFORE INSERT ON goal_daily_assignments BEGIN SELECT RAISE(ABORT,'generated storage fault'); END").unwrap();
    let before = f.fingerprint();
    assert!(goals::save(&f.training(), &Fixture::body("保存失败")).is_err());
    assert_eq!(f.fingerprint(), before);
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM goals", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        0
    );
}

#[test]
fn malformed_existing_goal_blocks_training_writes_but_archiving_keeps_its_original_record() {
    let mut f = Fixture::new();
    f.personal
        .db
        .execute(
            "INSERT INTO goals VALUES('bad','2026-11-01T00:00:00Z','{}',0)",
            [],
        )
        .unwrap();
    let before = f.fingerprint();
    assert_eq!(
        f.training()
            .start(&json!({"id":"fixture::0"}))
            .unwrap_err()
            .code,
        "INVALID_STORED_DATA"
    );
    assert_eq!(f.fingerprint(), before);
    assert!(
        goals::archive(&f.training(), "bad").unwrap()["goals"]
            .as_array()
            .unwrap()
            .is_empty()
    );
    assert_eq!(
        f.personal
            .db
            .query_row(
                "SELECT config,archived FROM goals WHERE id='bad'",
                [],
                |r| Ok((r.get::<_, String>(0)?, r.get::<_, i64>(1)?))
            )
            .unwrap(),
        ("{}".into(), 1)
    );
}

#[test]
fn invalid_inputs_cannot_write_and_cf_titles_preserve_legacy_inference_and_archived_identity() {
    let mut f = Fixture::new();
    for patch in [
        json!({"title":""}),
        json!({"kind":"unknown"}),
        json!({"deadline":"2026-11-05"}),
        json!({"dailyMinutes":"9__0"}),
        json!({"currentRating":i64::MAX,"targetRating":i64::MIN}),
        json!({"totalProblems":0}),
    ] {
        let mut body = Fixture::body("无效参数");
        for (key, value) in patch.as_object().unwrap() {
            body[key] = value.clone();
        }
        let before = f.fingerprint();
        assert_eq!(goals::save(&f.training(), &body).unwrap_err().status, 422);
        assert_eq!(f.fingerprint(), before);
    }
    let value=goals::save(&f.training(),&json!({"title":"CF 1600","kind":"custom","deadline":"2026-11-07","targetRating":999,"currentRating":"1_000"})).unwrap();
    let goal = &value["goals"][0];
    assert_eq!(goal["kind"], "cf");
    assert_eq!(goal["targetRating"], 1600);
    assert_eq!(goal["totalProblems"], 180);
    let id = goal["id"].as_str().unwrap().to_owned();
    goals::archive(&f.training(), &id).unwrap();
    let mut body = Fixture::body("归档编辑");
    body["id"] = json!(id);
    assert!(
        goals::save(&f.training(), &body).unwrap()["goals"]
            .as_array()
            .unwrap()
            .is_empty()
    );
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT archived FROM goals WHERE id=?", [id], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
}

#[test]
fn adopted_learning_plan_suppresses_goal_rows_without_assigning_or_erasing_retained_goals() {
    let mut f = Fixture::new();
    let identity = f.save("保留的目标")["goals"][0]["id"]
        .as_str()
        .unwrap()
        .to_owned();
    let selections: String = f
        .personal
        .db
        .query_row(
            "SELECT ids FROM goal_daily_assignments WHERE goal_id=?",
            [&identity],
            |r| r.get(0),
        )
        .unwrap();
    f.now += Duration::days(1);
    let mainline = json!({"kind":"topic","title":"当前已采纳主线"});
    f.personal
        .put_document(
            tobe_core::learning::KEY,
            &json!({"config":{"goal":mainline},"plan":{"id":"generated-adopted-plan"}}),
        )
        .unwrap();
    let workspace = f.training().workspace().unwrap();
    assert_eq!(workspace["goalTasks"], json!([]));
    assert_eq!(workspace["goals"]["goalTasks"], json!([]));
    assert_eq!(workspace["goals"]["summaryGoal"], mainline);
    assert_eq!(workspace["goals"]["goals"][0]["id"], identity);
    assert_eq!(
        f.personal
            .db
            .query_row(
                "SELECT COUNT(*) FROM goal_daily_assignments WHERE goal_id=?",
                [&identity],
                |r| r.get::<_, i64>(0)
            )
            .unwrap(),
        1
    );
    assert_eq!(
        f.personal
            .db
            .query_row(
                "SELECT ids FROM goal_daily_assignments WHERE goal_id=?",
                [&identity],
                |r| r.get::<_, String>(0)
            )
            .unwrap(),
        selections
    );
}
