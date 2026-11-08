use chrono::{Duration, TimeZone, Utc};
use flate2::{Compression, write::ZlibEncoder};
use rusqlite::{Connection, params};
use serde_json::json;
use std::io::Write;
use tempfile::TempDir;
use tobe_core::{
    ability::{self, Observation},
    catalogue::Catalogue,
    library::Library,
    migration::logical_fingerprint,
    reviews,
    storage::PersonalStore,
    training::Training,
};

fn now() -> chrono::DateTime<Utc> {
    Utc.with_ymd_and_hms(2026, 11, 6, 4, 0, 0).unwrap()
}
struct Fixture {
    _folder: TempDir,
    personal: PersonalStore,
    catalogue: Catalogue,
    library: Library,
}
impl Fixture {
    fn new() -> Self {
        let folder = tempfile::tempdir().unwrap();
        let personal = PersonalStore::open(&folder.path().join("personal.sqlite3")).unwrap();
        let db = Connection::open_in_memory().unwrap();
        db.execute_batch("CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT);CREATE TABLE catalogue(id TEXT PRIMARY KEY,compact TEXT,full BLOB)").unwrap();
        for index in 0..12 {
            let id = format!("fixture::{index}");
            let row = json!({"id":id,"title":format!("原题 {index}"),"url":format!("https://codeforces.com/contest/999/problem/{}",char::from(b'A'+index)),"platform":"Codeforces","difficulty":1000+index as i64*100,"difficultySource":"Codeforces 官方 rating","contest":"Div.3 999","problem":format!("{}",char::from(b'A'+index)),"tags":[],"knowledge":""});
            let mut compressed = ZlibEncoder::new(Vec::new(), Compression::default());
            compressed.write_all(row.to_string().as_bytes()).unwrap();
            db.execute(
                "INSERT INTO catalogue VALUES(?,?,?)",
                params![id, row.to_string(), compressed.finish().unwrap()],
            )
            .unwrap();
            for alias in [id.clone(), format!("alias::{index}")] {
                db.execute("INSERT INTO aliases VALUES(?,?)", params![alias, id])
                    .unwrap();
            }
        }
        let library_db = Connection::open_in_memory().unwrap();
        Self {
            _folder: folder,
            personal,
            catalogue: Catalogue { db },
            library: Library { db: library_db },
        }
    }
    fn training(&mut self) -> Training<'_> {
        Training {
            catalogue: &self.catalogue,
            personal: &mut self.personal,
            library: &self.library,
            now: now(),
        }
    }
    fn receipt(&self, id: &str, problem: &str, verdict: &str, at: &str, seen: i64, code: &str) {
        self.personal.db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at,solution_seen) VALUES(?,?,'submit','official',?,?,?,?,?)",params![id,problem,verdict,code,at,at,seen]).unwrap();
    }
    fn activate(&self, id: &str) {
        self.personal
            .db
            .execute(
                "INSERT INTO training(id,active_at) VALUES(?,'2026-11-04T00:00:00Z')",
                [id],
            )
            .unwrap();
    }
}

#[test]
fn rasch_requires_five_distinct_independent_successes_and_keeps_support_ceiling() {
    let input = (0..6)
        .map(|i| Observation {
            id: i.to_string(),
            difficulty: [1200., 1600., 1800., 2000., 2300., 2600.][i],
            weight: 1.,
            solved: true,
            at: now() + Duration::days(i as i64),
        })
        .collect::<Vec<_>>();
    assert_eq!(ability::score_from_observations(&input[..4]), None);
    assert_eq!(ability::score_from_observations(&input), Some(1600));
    let repeated = vec![input[5].clone(); 20];
    assert_eq!(ability::score_from_observations(&repeated), None);
    let mut failures = input;
    for i in 0..40 {
        failures.push(Observation {
            id: format!("failed-{i}"),
            difficulty: 1000.,
            weight: 1.,
            solved: false,
            at: now() + Duration::days(10 + i),
        });
    }
    assert!(ability::score_from_observations(&failures).unwrap() < 1600);
}
#[test]
fn rating_requires_an_exact_official_mirror_reference_and_keeps_uncertain_bands() {
    let mut row = json!({"platform":"洛谷","url":"https://www.luogu.com.cn/problem/CF123A","difficulty":1600,"difficultySource":"Codeforces 官方 rating"});
    assert_eq!(ability::rating(&row).unwrap().weight, 0.25);
    row["difficultyOfficialReference"] = json!({"contestId":123,"index":"A","source":"https://codeforces.com/contest/123/problem/A","metadataSource":"https://codeforces.com/api/problemset.problems"});
    assert_eq!(ability::rating(&row).unwrap().weight, 1.);
    row["url"] = json!("https://www.luogu.com.cn/problem/P123");
    assert_eq!(ability::rating(&row).unwrap().lower, 1200.);
    row["difficultySource"] = json!("AtCoder Problems 映射");
    row["difficultyBand"] = json!([1500, 1700]);
    let rating = ability::rating(&row).unwrap();
    assert_eq!(
        (rating.lower, rating.upper, rating.weight),
        (1300., 1900., 0.5)
    );
}
#[test]
fn journal_aliases_and_missing_source_cannot_multiply_independent_ability() {
    let mut f = Fixture::new();
    for i in 0..5 {
        f.receipt(
            &format!("receipt-{i}"),
            &format!("fixture::{i}"),
            "AC",
            "2026-11-04T00:00:00Z",
            0,
            "original source",
        );
    }
    let records = f.personal.rows("SELECT * FROM submissions", []).unwrap();
    assert!(
        ability::score(&f.training(), records.as_array().unwrap())
            .unwrap()
            .is_some()
    );
    f.personal
        .db
        .execute(
            "UPDATE submissions SET problem_id='alias::0' WHERE id='receipt-4'",
            [],
        )
        .unwrap();
    let records = f.personal.rows("SELECT * FROM submissions", []).unwrap();
    assert_eq!(
        ability::score(&f.training(), records.as_array().unwrap()).unwrap(),
        None
    );
    f.personal
        .db
        .execute(
            "UPDATE submissions SET problem_id='fixture::4',code='' WHERE id='receipt-4'",
            [],
        )
        .unwrap();
    let records = f.personal.rows("SELECT * FROM submissions", []).unwrap();
    assert_eq!(
        ability::score(&f.training(), records.as_array().unwrap()).unwrap(),
        None
    );
    f.personal
        .db
        .execute_batch(
            "CREATE TABLE account_sync_code_refs(submission_id TEXT PRIMARY KEY,reference TEXT)",
        )
        .unwrap();
    let reference = format!(
        "\0TB-CODE-V2:{}",
        json!({"root":"a".repeat(64),"sha256":"b".repeat(64),"bytes":123})
    );
    f.personal
        .db
        .execute(
            "INSERT INTO account_sync_code_refs VALUES('receipt-4',?)",
            [reference],
        )
        .unwrap();
    let records = f.personal.rows("SELECT * FROM submissions", []).unwrap();
    assert!(
        ability::score(&f.training(), records.as_array().unwrap())
            .unwrap()
            .is_some()
    );
    f.personal
        .db
        .execute(
            "UPDATE submissions SET solution_seen=1 WHERE id='receipt-4'",
            [],
        )
        .unwrap();
    let records = f.personal.rows("SELECT * FROM submissions", []).unwrap();
    assert_eq!(
        ability::score(&f.training(), records.as_array().unwrap()).unwrap(),
        None
    );
}
#[test]
fn next_beijing_day_review_uses_actual_wa_and_one_existing_receipt_reward() {
    let mut f = Fixture::new();
    f.activate("fixture::0");
    f.receipt(
        "wrong",
        "alias::0",
        "WA",
        "2026-11-04T16:01:00Z",
        0,
        "failed source",
    );
    let plan = reviews::plan(&f.training()).unwrap();
    assert_eq!(plan["tasks"][0]["due"], "2026-11-06");
    assert_eq!(plan["dueCount"], 1);
    let task_id = plan["tasks"][0]["id"].as_str().unwrap().to_owned();
    assert_eq!(
        reviews::task(&f.training(), "fixture::1", Some(&task_id), true)
            .unwrap_err()
            .status,
        404
    );
    reviews::task(&f.training(), "fixture::0", Some(&task_id), true).unwrap();
    f.receipt(
        "fresh",
        "fixture::0",
        "AC",
        "2026-11-06T04:00:00.000000Z",
        0,
        "fresh rewritten source",
    );
    let done = reviews::plan(&f.training()).unwrap();
    assert_eq!(done["dueCount"], 0);
    let task = f
        .personal
        .document(&format!("review-task:{task_id}"))
        .unwrap()
        .unwrap();
    assert_eq!(task["rewardReceiptId"], "fresh");
    assert_eq!(task["rewardXp"], 20);
    let before = logical_fingerprint(&f.personal.db).unwrap();
    reviews::plan(&f.training()).unwrap();
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
    assert_eq!(f.personal.documents("review-reward:").unwrap().len(), 1);
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM official_first_xp_awards", [], |r| r
                .get::<_, i64>(
                0
            ))
            .unwrap(),
        0
    );
}
#[test]
fn compiler_errors_clean_accepts_samples_and_removed_today_do_not_create_rewrites() {
    let mut f = Fixture::new();
    for (i, verdict) in ["CE", "RE", "TLE", "AC"].into_iter().enumerate() {
        f.activate(&format!("fixture::{i}"));
        f.receipt(
            &format!("receipt-{i}"),
            &format!("fixture::{i}"),
            verdict,
            "2026-11-04T00:00:00Z",
            0,
            "source",
        );
    }
    assert_eq!(reviews::plan(&f.training()).unwrap()["dueCount"], 0);
    f.activate("fixture::5");
    f.receipt(
        "wa",
        "fixture::5",
        "WA",
        "2026-11-04T00:00:00Z",
        0,
        "source",
    );
    f.personal
        .db
        .execute(
            "UPDATE training SET active=0,removed_at='2026-11-06T00:00:00Z' WHERE id='fixture::5'",
            [],
        )
        .unwrap();
    assert_eq!(reviews::plan(&f.training()).unwrap()["dueCount"], 0);
    f.personal
        .db
        .execute(
            "UPDATE training SET removed_at='2026-11-05T00:00:00Z' WHERE id='fixture::5'",
            [],
        )
        .unwrap();
    assert_eq!(reviews::plan(&f.training()).unwrap()["dueCount"], 1);
}
#[test]
fn failed_review_writes_rollback_task_receipt_reward_and_allocation() {
    let mut f = Fixture::new();
    f.activate("fixture::0");
    f.receipt(
        "wrong",
        "fixture::0",
        "WA",
        "2026-11-04T00:00:00Z",
        0,
        "source",
    );
    let before = logical_fingerprint(&f.personal.db).unwrap();
    f.personal.db.execute_batch("CREATE TRIGGER reject_review_state BEFORE INSERT ON account_preferences WHEN NEW.key LIKE 'review-state:%' BEGIN SELECT RAISE(ABORT,'test durable write failure'); END").unwrap();
    assert_eq!(
        reviews::plan(&f.training()).unwrap_err().code,
        "STORAGE_ERROR"
    );
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
    f.personal
        .db
        .execute_batch("DROP TRIGGER reject_review_state")
        .unwrap();
    assert_eq!(reviews::plan(&f.training()).unwrap()["dueCount"], 1);
    let key = f
        .personal
        .rows(
            "SELECT key FROM account_preferences WHERE key LIKE 'review-task:%' LIMIT 1",
            [],
        )
        .unwrap()[0]["key"]
        .as_str()
        .unwrap()
        .to_owned();
    f.personal
        .db
        .execute(
            "UPDATE account_preferences SET value='{broken' WHERE key=?",
            [key],
        )
        .unwrap();
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert!(reviews::plan(&f.training()).is_err());
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
}

#[test]
fn future_or_minimum_time_review_cannot_open_or_change_its_journal() {
    let mut f = Fixture::new();
    f.activate("fixture::0");
    f.receipt(
        "today-wa",
        "fixture::0",
        "WA",
        "2026-11-06T00:00:00Z",
        0,
        "source",
    );
    let plan = reviews::plan(&f.training()).unwrap();
    assert_eq!(plan["dueCount"], 0);
    let mut task = f.personal.documents("review-task:").unwrap().pop().unwrap();
    let id = task["id"].as_str().unwrap().to_owned();
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert_eq!(
        reviews::task(&f.training(), "fixture::0", Some(&id), true)
            .unwrap_err()
            .status,
        409
    );
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
    task["due"] = json!("2026-11-06");
    task["minimumAt"] = json!("2026-11-07T00:00:00Z");
    f.personal
        .put_document(&format!("review-task:{id}"), &task)
        .unwrap();
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert_eq!(
        reviews::task(&f.training(), "fixture::0", Some(&id), true)
            .unwrap_err()
            .status,
        409
    );
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
}

#[test]
fn review_draft_does_not_overwrite_or_reactivate_ordinary_training() {
    let mut f = Fixture::new();
    f.activate("fixture::0");
    f.receipt(
        "past-wa",
        "fixture::0",
        "WA",
        "2026-11-04T00:00:00Z",
        0,
        "source",
    );
    let plan = reviews::plan(&f.training()).unwrap();
    let id = plan["tasks"][0]["id"].as_str().unwrap().to_owned();
    f.personal
        .save_draft_at(
            &json!({"id":"fixture::0","code":"ordinary source","language":"python3"}),
            "2026-11-04T12:00:00Z",
        )
        .unwrap();
    f.personal
        .db
        .execute("UPDATE training SET active=0", [])
        .unwrap();
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert_eq!(
        f.training()
            .save_draft(&json!({"id":"fixture::0","reviewId":id,"code":"中".repeat(30000)}))
            .unwrap_err()
            .status,
        400
    );
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
    f.training()
        .save_draft(
            &json!({"id":"fixture::0","reviewId":id,"code":"review source 😀","language":"cpp17"}),
        )
        .unwrap();
    assert_eq!(
        f.personal.draft("fixture::0", "").unwrap()["draft"],
        "ordinary source"
    );
    assert_eq!(
        f.personal
            .draft("fixture::0", &format!("review:{id}"))
            .unwrap()["draft"],
        "review source 😀"
    );
    assert_eq!(
        f.personal
            .db
            .query_row(
                "SELECT active FROM training WHERE id='fixture::0'",
                [],
                |row| row.get::<_, i64>(0)
            )
            .unwrap(),
        0
    );
}

#[test]
fn missing_review_projection_cannot_silently_reuse_the_ordinary_problem_analysis() {
    let f = Fixture::new();
    assert_eq!(
        f.catalogue.review_knowledge("fixture::0").unwrap_err().code,
        "MIGRATION_PENDING"
    );
    f.catalogue.db.execute_batch("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);INSERT INTO metadata VALUES('reviewKnowledgeVersion','1');CREATE TABLE review_knowledge(id TEXT PRIMARY KEY,content BLOB,error TEXT)").unwrap();
    let knowledge = json!({"tags":["模拟"],"knowledge":"模拟","knowledgeAnalysis":{"source":"archive-catalog"}});
    let mut encoder = ZlibEncoder::new(Vec::new(), Compression::default());
    encoder.write_all(knowledge.to_string().as_bytes()).unwrap();
    f.catalogue
        .db
        .execute(
            "INSERT INTO review_knowledge VALUES('fixture::0',?,NULL)",
            [encoder.finish().unwrap()],
        )
        .unwrap();
    assert_eq!(
        f.catalogue.review_knowledge("fixture::0").unwrap(),
        knowledge
    );
    f.catalogue
        .db
        .execute("UPDATE metadata SET value='2'", [])
        .unwrap();
    assert_eq!(
        f.catalogue.review_knowledge("fixture::0").unwrap_err().code,
        "MIGRATION_PENDING"
    );
    f.catalogue
        .db
        .execute("UPDATE metadata SET value='1'", [])
        .unwrap();
    f.catalogue
        .db
        .execute("UPDATE review_knowledge SET error='not fully cached'", [])
        .unwrap();
    assert_eq!(
        f.catalogue.review_knowledge("fixture::0").unwrap_err().code,
        "STATEMENT_NOT_READY"
    );
}
