use chrono::{TimeZone, Utc};
use flate2::{Compression, write::ZlibEncoder};
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::io::Write;
use tempfile::TempDir;
use tobe_core::{
    catalogue::Catalogue, contest_history, library::Library, migration::logical_fingerprint,
    storage::PersonalStore, training::Training,
};

const START: &str = "2026-11-04T04:00:00Z";
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
        for index in 0..8 {
            let id = format!("fixture::{index}");
            let row = json!({"id":id,"title":format!("原题 {index}"),"platform":"Codeforces","difficulty":1200,"contest":"Div.3 999","contestFullName":"Codeforces Round 999 (Div. 3)","problem":"A","tags":[]});
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
        Self {
            _folder: folder,
            personal,
            catalogue: Catalogue { db },
            library: Library {
                db: Connection::open_in_memory().unwrap(),
            },
        }
    }
    fn training(&mut self) -> Training<'_> {
        Training {
            catalogue: &self.catalogue,
            personal: &mut self.personal,
            library: &self.library,
            now: Utc.with_ymd_and_hms(2026, 11, 6, 4, 0, 0).unwrap(),
        }
    }
    fn slot(index: usize) -> Value {
        json!({"id":format!("fixture::{index}"),"title":format!("题目 {index}"),"letter":char::from(b'A'+index as u8).to_string(),"difficulty":1200,"tags":["模拟"],"judgeScope":"official","statementAvailable":true,"trainingAdded":true,"trainingBefore":{"active":false}})
    }
    fn contest(&self, id: &str, status: &str, slots: Value, config: Value) {
        self.personal.db.execute("INSERT INTO contests(id,name,status,started_at,deadline,finished_at,duration,slots,config) VALUES(?,?,?,?,'2026-11-04T06:00:00Z','2026-11-04T05:00:00Z',120,?,?)", params![id,"重现赛 · Div.3 999",status,START,slots.to_string(),config.to_string()]).unwrap();
    }
    fn activate(&self, index: usize) {
        self.personal
            .db
            .execute(
                "INSERT INTO training(id,active_at) VALUES(?,?)",
                params![format!("fixture::{index}"), START],
            )
            .unwrap();
    }
    fn submission(&self, id: &str, verdict: &str, scope: &str, at: &str) {
        self.personal.db.execute("INSERT INTO submissions(id,problem_id,contest_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES(?,'alias::0','history','submit',?,?,'preserved code',?,?)",params![id,scope,verdict,at,at]).unwrap();
    }
}

#[test]
fn frozen_score_uses_official_replay_receipts_and_ce_configuration() {
    let mut f = Fixture::new();
    f.contest(
        "history",
        "finished",
        json!([Fixture::slot(0)]),
        json!({"strategy":"replay","contest":"Div.3 999","compilePenalty":true,"wrongPenalty":10}),
    );
    f.submission("ce", "CE", "official", "2026-11-04T04:01:00Z");
    f.submission("wa", "WA", "official", "2026-11-04T04:02:00Z");
    f.submission("sample", "SAMPLE_PASS", "local", "2026-11-04T04:03:00Z");
    let view = contest_history::get(&f.training(), "history").unwrap();
    assert_eq!(view["contest"]["accepted"], 0);
    assert_eq!(view["contest"]["slots"][0]["samplePassed"], true);
    f.submission("ac", "AC", "official", "2026-11-04T04:04:00Z");
    let before = logical_fingerprint(&f.personal.db).unwrap();
    let view = contest_history::get(&f.training(), "history").unwrap();
    assert_eq!(view["contest"]["accepted"], 1);
    assert_eq!(view["contest"]["penalty"], 24);
    assert_eq!(view["contest"]["elapsedSeconds"], 3600);
    assert_eq!(view["contest"]["slots"][0]["difficulty"], 1200);
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
}

#[test]
fn frozen_missing_slot_and_non_numeric_penalty_are_preserved_errors() {
    let mut f = Fixture::new();
    let mut slot = Fixture::slot(0);
    slot.as_object_mut().unwrap().remove("difficulty");
    f.contest(
        "history",
        "finished",
        json!([slot]),
        json!({"strategy":"replay"}),
    );
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert_eq!(
        contest_history::get(&f.training(), "history")
            .unwrap_err()
            .code,
        "INVALID_STORED_DATA"
    );
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
    f.personal
        .db
        .execute(
            "UPDATE contests SET slots=?,config=?",
            params![
                json!([Fixture::slot(0)]).to_string(),
                json!({"wrongPenalty":"20"}).to_string()
            ],
        )
        .unwrap();
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert_eq!(
        contest_history::get(&f.training(), "history")
            .unwrap_err()
            .code,
        "INVALID_STORED_DATA"
    );
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
}

#[test]
fn closed_context_uses_exact_frozen_membership_and_refuses_writes() {
    let mut f = Fixture::new();
    f.contest(
        "history",
        "cancelled",
        json!([Fixture::slot(0)]),
        json!({"strategy":"replay"}),
    );
    contest_history::assert_problem_context(&f.training(), "fixture::0", "history", false).unwrap();
    assert_eq!(
        contest_history::assert_problem_context(&f.training(), "alias::0", "history", false)
            .unwrap_err()
            .status,
        403
    );
    assert_eq!(
        contest_history::assert_problem_context(&f.training(), "fixture::0", "history", true)
            .unwrap_err()
            .status,
        409
    );
    f.personal
        .db
        .execute("UPDATE contests SET status='running'", [])
        .unwrap();
    let expired = contest_history::get(&f.training(), "history").unwrap();
    assert_eq!(expired["contest"]["status"], "finished");
    assert_eq!(expired["contest"]["finishedAt"], "2026-11-04T06:00:00Z");
    assert_eq!(
        contest_history::assert_problem_context(&f.training(), "fixture::0", "history", true)
            .unwrap_err()
            .status,
        409
    );
}

#[test]
fn completed_replay_names_include_tombstones_and_reject_unknown_provenance() {
    let mut f = Fixture::new();
    f.contest(
        "history",
        "finished",
        json!([Fixture::slot(0)]),
        json!({"strategy":"replay","contest":"Codeforces Round 999 (Div. 3)"}),
    );
    f.personal
        .db
        .execute("UPDATE contests SET deleted_at='2026-11-05T00:00:00Z'", [])
        .unwrap();
    assert_eq!(
        contest_history::completed_replays(&f.training()).unwrap(),
        vec!["Div.3 999"]
    );
    f.personal
        .db
        .execute(
            "UPDATE contests SET config=?",
            [json!({"strategy":"replay","contest":"Unknown private retained event"}).to_string()],
        )
        .unwrap();
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert_eq!(
        contest_history::completed_replays(&f.training())
            .unwrap_err()
            .code,
        "MIGRATION_PENDING"
    );
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
}

#[test]
fn legacy_automatic_cleanup_preserves_even_empty_drafts_and_all_manual_evidence() {
    let mut f = Fixture::new();
    f.contest(
        "history",
        "finished",
        json!((0..7).map(Fixture::slot).collect::<Vec<_>>()),
        json!({"strategy":"replay"}),
    );
    for i in 0..7 {
        f.activate(i);
    }
    f.personal
        .db
        .execute(
            "INSERT INTO drafts(problem_id,context,code,saved_at) VALUES('alias::1','','',?)",
            [START],
        )
        .unwrap();
    f.personal.db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at) VALUES('queued','fixture::2','run','samples','QUEUED','',?)",[START]).unwrap();
    f.personal.db.execute("INSERT INTO practice_sets(id,name,created_at,ids) VALUES('keep','保留题单',?,'[\"fixture::3\"]')",[START]).unwrap();
    f.personal
        .db
        .execute(
            "UPDATE training SET active_at='2026-11-03T00:00:00Z' WHERE id='fixture::4'",
            [],
        )
        .unwrap();
    f.personal
        .db
        .execute(
            "UPDATE training SET last_review_at=? WHERE id='fixture::5'",
            [START],
        )
        .unwrap();
    let mut slots: Vec<Value> = (0..7).map(Fixture::slot).collect();
    slots[6]["trainingAdded"] = json!(false);
    f.personal
        .db
        .execute("UPDATE contests SET slots=?", [json!(slots).to_string()])
        .unwrap();
    contest_history::prune_legacy_joins(&f.training()).unwrap();
    let retired: i64 = f
        .personal
        .db
        .query_row(
            "SELECT COUNT(*) FROM training WHERE active=0 AND id='fixture::0'",
            [],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(retired, 1);
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM training WHERE active=1", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        6
    );
    assert_eq!(
        f.personal
            .db
            .query_row(
                "SELECT code FROM drafts WHERE problem_id='alias::1'",
                [],
                |r| r.get::<_, String>(0)
            )
            .unwrap(),
        ""
    );
    let before = logical_fingerprint(&f.personal.db).unwrap();
    contest_history::prune_legacy_joins(&f.training()).unwrap();
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
}

#[test]
fn legacy_cleanup_rolls_back_flags_and_marker_when_a_write_fails() {
    let mut f = Fixture::new();
    f.contest(
        "history",
        "finished",
        json!([Fixture::slot(0), Fixture::slot(1)]),
        json!({"strategy":"replay"}),
    );
    f.activate(0);
    f.activate(1);
    f.personal.db.execute_batch("CREATE TRIGGER fail_cleanup BEFORE UPDATE ON training WHEN NEW.id='fixture::1' BEGIN SELECT RAISE(ABORT,'test storage fault'); END;").unwrap();
    let before = logical_fingerprint(&f.personal.db).unwrap();
    assert!(contest_history::prune_legacy_joins(&f.training()).is_err());
    assert_eq!(logical_fingerprint(&f.personal.db).unwrap(), before);
    assert_eq!(f.personal.pref("contest-edited-training-v1").unwrap(), None);
}
