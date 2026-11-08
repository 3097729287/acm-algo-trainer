use chrono::{DateTime, Duration, TimeZone, Utc};
use flate2::{Compression, write::ZlibEncoder};
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::io::Write;
use tobe_core::{
    catalogue::Catalogue, contest_lifecycle as lifecycle, library::Library,
    migration::logical_fingerprint, storage::PersonalStore, training::Training,
};

struct Fixture {
    personal: PersonalStore,
    catalogue: Catalogue,
    library: Library,
    now: DateTime<Utc>,
}
impl Fixture {
    fn new() -> Self {
        let personal = PersonalStore::open(&std::path::PathBuf::from(":memory:")).unwrap();
        let db = Connection::open_in_memory().unwrap();
        db.execute_batch("CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT);CREATE TABLE catalogue(id TEXT PRIMARY KEY,position INTEGER,full BLOB,compact TEXT)").unwrap();
        for i in 0..8 {
            let id = format!("fixture::{i}");
            let row = json!({"id":id,"title":format!("原题 {i}"),"platform":"Codeforces","url":format!("https://codeforces.com/contest/900/problem/{}",char::from(b'A'+i)),"contest":"Div.3 900","problem":char::from(b'A'+i).to_string(),"difficulty":1000+i as i64*100,"difficultySource":"Codeforces 官方 rating","tags":[]});
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
            library: &self.library,
            personal: &mut self.personal,
            now: self.now,
        }
    }
    fn slot(index: u8) -> Value {
        json!({"id":format!("fixture::{index}"),"letter":char::from(b'A'+index).to_string(),"title":format!("原题 {index}"),"difficulty":1000+index as i64*100,"tags":[],"judgeScope":"official","statementAvailable":true})
    }
    fn contest(&self, id: &str, status: &str, slots: Vec<Value>, config: Value) {
        self.personal.db.execute("INSERT INTO contests(id,name,status,started_at,deadline,finished_at,duration,slots,config) VALUES(?,'重现赛 · Div.3 900',?,'2026-11-06T03:00:00.000000Z','2026-11-06T05:00:00.000000Z',?,120,?,?)",params![id,status,if status=="finished"{Some("2026-11-06T04:00:00.000000Z")}else{None},json!(slots).to_string(),config.to_string()]).unwrap();
    }
    fn active(&self, index: u8, at: &str) {
        self.personal.db.execute("INSERT INTO training(id,active_at,mock_due,mock_due_at,mock_due_context) VALUES(?,?,1,'2026-11-06T03:30:00Z','paper')",params![format!("fixture::{index}"),at]).unwrap();
    }
    fn receipt(
        &self,
        id: &str,
        index: u8,
        context: Option<&str>,
        scope: &str,
        verdict: &str,
        finished: bool,
    ) {
        self.personal.db.execute("INSERT INTO submissions(id,problem_id,contest_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES(?,?,?,'submit',?,?,'generated original source','2026-11-06T03:10:00.000000Z',?)",params![id,format!("alias::{index}"),context,scope,verdict,if finished{Some("2026-11-06T03:10:00.000000Z")}else{None}]).unwrap();
    }
    fn fingerprint(&self) -> String {
        logical_fingerprint(&self.personal.db).unwrap()
    }
    fn flag(&self, index: u8, field: &str) -> i64 {
        self.personal
            .db
            .query_row(
                &format!("SELECT {field} FROM training WHERE id=?"),
                [format!("fixture::{index}")],
                |r| r.get(0),
            )
            .unwrap()
    }
    fn config() -> Value {
        json!({"strategy":"replay","contest":"Div.3 900","editedTrainingOnly":true})
    }
}

#[test]
fn actual_official_alias_passes_finish_without_turning_public_samples_or_missing_slots_into_solves()
{
    let mut f = Fixture::new();
    for i in 0..3 {
        f.active(i, "2026-11-06T02:00:00Z");
    }
    let mut slots = (0..4).map(Fixture::slot).collect::<Vec<_>>();
    slots[2]["statementAvailable"] = json!(false);
    f.contest("paper", "running", slots, Fixture::config());
    f.receipt("sample", 0, Some("paper"), "samples", "SAMPLE_PASS", true);
    f.receipt("actual-ac", 1, Some("paper"), "official", "AC", true);
    f.personal
        .db
        .execute(
            "UPDATE training SET mock_due=0,mock_due_at=NULL,mock_due_context=NULL",
            [],
        )
        .unwrap();
    let value = lifecycle::finish(&f.training(), "paper").unwrap();
    assert_eq!(value["contest"]["status"], "finished");
    assert_eq!(value["contest"]["accepted"], 1);
    assert_eq!(value["contest"]["penalty"], 10);
    assert_eq!(value["contest"]["slots"][2]["statementAvailable"], false);
    assert_eq!(f.flag(0, "mock_due"), 1);
    assert_eq!(f.flag(1, "mock_due"), 0);
    assert_eq!(f.flag(2, "mock_due"), 0);
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM training", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        3
    );
    let before = f.fingerprint();
    lifecycle::finish(&f.training(), "paper").unwrap();
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn overdue_finish_uses_original_deadline_and_is_idempotent_after_restart_boundary() {
    let mut f = Fixture::new();
    f.active(0, "2026-11-06T02:00:00Z");
    f.contest(
        "paper",
        "running",
        vec![Fixture::slot(0)],
        Fixture::config(),
    );
    f.now += Duration::hours(3);
    let value = lifecycle::finish(&f.training(), "paper").unwrap();
    assert_eq!(
        value["contest"]["finishedAt"],
        "2026-11-06T05:00:00.000000Z"
    );
    assert_eq!(value["contest"]["elapsedSeconds"], 7200);
    let due: String = f
        .personal
        .db
        .query_row("SELECT mock_due_at FROM training", [], |r| r.get(0))
        .unwrap();
    assert_eq!(due, "2026-11-06T05:00:00.000000Z");
    let before = f.fingerprint();
    f.now += Duration::days(1);
    lifecycle::expire(&f.training()).unwrap();
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn cancellation_restores_prior_flags_and_preserves_exam_code_and_independent_alias_references() {
    let mut f = Fixture::new();
    for i in 0..4 {
        f.active(i, "2026-11-06T03:00:00Z");
    }
    let mut frozen = (0..4).map(Fixture::slot).collect::<Vec<_>>();
    frozen[0]["trainingBefore"] =
        json!({"active":1,"active_at":"2026-11-01T00:00:00Z","removed_at":null});
    frozen[1]["trainingBefore"] =
        json!({"active":0,"active_at":"2026-11-02T00:00:00Z","removed_at":"2026-11-03T00:00:00Z"});
    frozen[2]["trainingAdded"] = json!(true);
    frozen[2]["trainingBefore"] = Value::Null;
    frozen[3]["trainingAdded"] = json!(true);
    f.contest("paper", "running", frozen, Fixture::config());
    f.personal
        .db
        .execute(
            "INSERT INTO practice_sets VALUES('separate','单独保留',?,'2026-11-01T00:00:00Z')",
            [json!(["alias::3"]).to_string()],
        )
        .unwrap();
    for (context, code) in [("", "normal draft"), ("paper", "exam draft 😀")] {
        f.personal
            .db
            .execute(
                "INSERT INTO drafts VALUES('fixture::2',?,?,?)",
                params![context, code, "2026-11-06T03:20:00Z"],
            )
            .unwrap();
    }
    let value = lifecycle::cancel(&f.training(), "paper").unwrap();
    assert_eq!(value["cancelled"], true);
    assert_eq!(f.flag(0, "active"), 1);
    assert_eq!(f.flag(1, "active"), 0);
    assert_eq!(f.flag(2, "active"), 0);
    assert_eq!(f.flag(3, "active"), 1);
    assert_eq!(f.flag(0, "mock_due"), 0);
    assert_eq!(f.flag(3, "mock_due"), 1);
    assert_eq!(
        f.personal.draft("fixture::2", "paper").unwrap()["draft"],
        "exam draft 😀"
    );
    assert_eq!(
        f.personal.draft("fixture::2", "").unwrap()["draft"],
        "normal draft"
    );
    let before = f.fingerprint();
    lifecycle::cancel(&f.training(), "paper").unwrap();
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn deleting_a_replay_retires_only_unowned_training_and_keeps_receipts_code_and_reveal_history() {
    let mut f = Fixture::new();
    for i in 0..8 {
        f.active(
            i,
            if i == 2 {
                "2026-11-01T00:00:00Z"
            } else {
                "2026-11-06T03:00:00Z"
            },
        );
    }
    let mut frozen = (0..8).map(Fixture::slot).collect::<Vec<_>>();
    for i in [0, 5, 6, 7] {
        frozen[i]["trainingAdded"] = json!(true);
    }
    frozen[1]["trainingAdded"] = json!(false);
    f.contest("paper", "finished", frozen, Fixture::config());
    f.contest(
        "other",
        "finished",
        vec![Fixture::slot(7)],
        json!({"strategy":"comprehensive"}),
    );
    f.personal
        .db
        .execute(
            "INSERT INTO drafts VALUES('fixture::3','','independent code','2026-11-06T03:15:00Z')",
            [],
        )
        .unwrap();
    f.receipt("external", 4, None, "official", "WA", true);
    f.receipt("pending", 5, Some("paper"), "official", "RUNNING", false);
    f.personal
        .db
        .execute(
            "INSERT INTO practice_sets VALUES('separate','单独练习',?,'2026-11-01T00:00:00Z')",
            [json!(["alias::6"]).to_string()],
        )
        .unwrap();
    let value = lifecycle::delete(&f.training(), &json!({"id":"paper"})).unwrap();
    assert_eq!(value["deleted"], 1);
    assert_eq!(value["removedTraining"], 1);
    assert_eq!(f.flag(0, "active"), 0);
    for i in 1..8 {
        assert_eq!(f.flag(i, "active"), 1);
    }
    assert!(
        value["workspace"]["completedReplayContests"]
            .as_array()
            .unwrap()
            .contains(&json!("Div.3 900"))
    );
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM submissions", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        2
    );
    assert_eq!(
        f.personal.draft("fixture::3", "").unwrap()["draft"],
        "independent code"
    );
    let before = f.fingerprint();
    assert_eq!(
        lifecycle::delete(&f.training(), &json!({"id":"paper"})).unwrap()["deleted"],
        0
    );
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn deleting_all_records_tombstones_only_finished_records_without_physically_erasing_history() {
    let mut f = Fixture::new();
    for (id, status) in [
        ("one", "finished"),
        ("two", "finished"),
        ("withdrawn", "cancelled"),
    ] {
        f.contest(
            id,
            status,
            vec![Fixture::slot(0)],
            json!({"strategy":"comprehensive"}),
        );
    }
    let result = lifecycle::delete(&f.training(), &json!({"all":true})).unwrap();
    assert_eq!(result["deleted"], 2);
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM contests", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        3
    );
    assert_eq!(
        f.personal
            .db
            .query_row(
                "SELECT deleted_at FROM contests WHERE id='withdrawn'",
                [],
                |r| r.get::<_, Option<String>>(0)
            )
            .unwrap(),
        None
    );
}

#[test]
fn failed_due_write_rolls_back_finish_time_and_every_training_change() {
    let mut f = Fixture::new();
    for i in 0..2 {
        f.active(i, "2026-11-01T00:00:00Z");
    }
    f.contest(
        "paper",
        "running",
        vec![Fixture::slot(0), Fixture::slot(1)],
        Fixture::config(),
    );
    f.personal.db.execute_batch("CREATE TRIGGER reject_due BEFORE UPDATE OF mock_due ON training WHEN NEW.id='fixture::1' BEGIN SELECT RAISE(ABORT,'intentional storage failure'); END").unwrap();
    let before = f.fingerprint();
    assert!(lifecycle::finish(&f.training(), "paper").is_err());
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn unported_rewards_and_team_authority_and_unknown_reveal_sources_cannot_be_partially_applied() {
    let mut f = Fixture::new();
    f.contest(
        "reward",
        "running",
        vec![Fixture::slot(0)],
        json!({"strategy":"replay","backgroundReward":{"owner":"real-owner","version":1}}),
    );
    let before = f.fingerprint();
    assert_eq!(
        lifecycle::finish(&f.training(), "reward").unwrap_err().code,
        "MIGRATION_PENDING"
    );
    assert_eq!(f.fingerprint(), before);
    f.personal.db.execute("DELETE FROM contests", []).unwrap();
    f.contest(
        "team",
        "running",
        vec![Fixture::slot(0)],
        json!({"strategy":"team"}),
    );
    let before = f.fingerprint();
    assert_eq!(
        lifecycle::finish(&f.training(), "team").unwrap_err().status,
        409
    );
    assert_eq!(
        lifecycle::cancel(&f.training(), "team").unwrap_err().status,
        409
    );
    assert_eq!(f.fingerprint(), before);
    f.personal.db.execute("DELETE FROM contests", []).unwrap();
    f.contest(
        "unknown",
        "finished",
        vec![Fixture::slot(0)],
        json!({"strategy":"replay","contest":"Unresolved original provenance"}),
    );
    let before = f.fingerprint();
    assert_eq!(
        lifecycle::delete(&f.training(), &json!({"id":"unknown"}))
            .unwrap_err()
            .code,
        "MIGRATION_PENDING"
    );
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn malformed_previous_training_and_delete_parameters_leave_every_record_intact() {
    let mut f = Fixture::new();
    let mut slot = Fixture::slot(0);
    slot["trainingBefore"] = json!({"active":"broken","active_at":"2026-11-01T00:00:00Z"});
    f.active(0, "2026-11-06T03:00:00Z");
    f.contest("paper", "running", vec![slot], Fixture::config());
    let before = f.fingerprint();
    assert_eq!(
        lifecycle::cancel(&f.training(), "paper").unwrap_err().code,
        "INVALID_STORED_DATA"
    );
    assert_eq!(f.fingerprint(), before);
    for body in [json!({}), json!({"all":"true"}), json!({"id":12})] {
        assert_eq!(
            lifecycle::delete(&f.training(), &body).unwrap_err().status,
            400
        );
        assert_eq!(f.fingerprint(), before);
    }
}

#[test]
fn actual_ordinary_draft_claim_survives_deleting_a_previously_automatic_replay_link() {
    let mut f = Fixture::new();
    f.active(0, "2026-11-06T03:00:00Z");
    let mut slot = Fixture::slot(0);
    slot["trainingAdded"] = json!(true);
    slot["trainingBefore"] = Value::Null;
    f.contest("paper", "finished", vec![slot], Fixture::config());
    f.training()
        .save_draft(
            &json!({"id":"fixture::0","code":"independent actual code 😀","language":"python3"}),
        )
        .unwrap();
    let slots: String = f
        .personal
        .db
        .query_row("SELECT slots FROM contests WHERE id='paper'", [], |r| {
            r.get(0)
        })
        .unwrap();
    assert_eq!(
        serde_json::from_str::<Value>(&slots).unwrap()[0]["trainingAdded"],
        false
    );
    let removed = lifecycle::delete(&f.training(), &json!({"id":"paper"})).unwrap();
    assert_eq!(removed["removedTraining"], 0);
    assert_eq!(f.flag(0, "active"), 1);
    assert_eq!(
        f.personal.draft("fixture::0", "").unwrap()["draft"],
        "independent actual code 😀"
    );
}

#[test]
fn running_view_does_not_join_every_slot_and_an_actual_empty_exam_edit_has_its_own_context() {
    let mut f = Fixture::new();
    let mut slot = Fixture::slot(0);
    slot["trainingAdded"] = json!(true);
    slot["trainingBefore"] = Value::Null;
    let mut missing = Fixture::slot(1);
    missing["statementAvailable"] = json!(false);
    f.contest("paper", "running", vec![slot, missing], Fixture::config());
    let view = f.training().workspace().unwrap();
    assert_eq!(view["activeContest"]["id"], "paper");
    assert_eq!(view["training"], json!([]));
    assert_eq!(
        view["activeContest"]["slots"][1]["statementAvailable"],
        false
    );
    assert_eq!(
        tobe_core::contest_history::assert_problem_context(
            &f.training(),
            "fixture::1",
            "paper",
            false
        )
        .unwrap_err()
        .status,
        422
    );
    f.training()
        .save_draft(&json!({"id":"fixture::0","contestId":"paper","code":"","language":"python3"}))
        .unwrap();
    assert_eq!(f.flag(0, "active"), 1);
    assert_eq!(
        f.personal.draft("fixture::0", "paper").unwrap()["draftLanguage"],
        "python3"
    );
    assert_eq!(
        f.personal.draft("fixture::0", "").unwrap()["draftSavedAt"],
        Value::Null
    );
    let working = f.training().workspace().unwrap();
    assert_eq!(working["training"][0]["difficulty"], Value::Null);
    assert_eq!(working["training"][0]["tags"], json!([]));
    assert_eq!(working["training"][0]["knowledge"], "");
    assert_eq!(working["training"][0]["queue"], Value::Null);
    assert_eq!(working["training"][0]["today"], true);
    let before = f.fingerprint();
    f.training()
        .save_draft(&json!({"id":"fixture::0","contestId":"paper","code":"","language":"python3"}))
        .unwrap();
    assert_eq!(f.fingerprint(), before);
    assert_eq!(
        f.training()
            .save_draft(&json!({"id":"fixture::0","code":"outside exam"}))
            .unwrap_err()
            .status,
        403
    );
    assert_eq!(f.fingerprint(), before);
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM training", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        1
    );
}

#[test]
fn workspace_auto_expiry_and_failed_exam_draft_write_are_atomic_with_training_ownership() {
    let mut f = Fixture::new();
    f.contest(
        "paper",
        "running",
        vec![Fixture::slot(0)],
        Fixture::config(),
    );
    f.personal.db.execute_batch("CREATE TRIGGER reject_new_training BEFORE INSERT ON training BEGIN SELECT RAISE(ABORT,'intentional journal failure'); END").unwrap();
    let before = f.fingerprint();
    assert!(f.training().save_draft(&json!({"id":"fixture::0","contestId":"paper","code":"new exam code","language":"python3"})).is_err());
    assert_eq!(f.fingerprint(), before);
    f.personal
        .db
        .execute_batch("DROP TRIGGER reject_new_training")
        .unwrap();
    f.now += Duration::hours(2);
    let view = f.training().workspace().unwrap();
    assert_eq!(view["activeContest"], Value::Null);
    assert_eq!(view["contests"][0]["status"], "finished");
    assert_eq!(
        view["contests"][0]["finishedAt"],
        "2026-11-06T05:00:00.000000Z"
    );
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT COUNT(*) FROM training", [], |r| r.get::<_, i64>(0))
            .unwrap(),
        0
    );
}

#[test]
fn retained_private_alias_facts_block_lifecycle_changes_before_any_journal_write() {
    let mut f = Fixture::new();
    f.contest(
        "paper",
        "running",
        vec![Fixture::slot(0)],
        Fixture::config(),
    );
    f.personal.db.execute("INSERT INTO account_problem_facts VALUES('unported-original-alias',?,'2026-11-06T00:00:00Z')",[json!({"row":{"id":"unported-original-alias","url":"https://codeforces.com/contest/900/problem/A"}}).to_string()]).unwrap();
    let before = f.fingerprint();
    assert_eq!(
        lifecycle::finish(&f.training(), "paper").unwrap_err().code,
        "MIGRATION_PENDING"
    );
    assert_eq!(
        lifecycle::cancel(&f.training(), "paper").unwrap_err().code,
        "MIGRATION_PENDING"
    );
    assert_eq!(
        lifecycle::delete(&f.training(), &json!({"all":true}))
            .unwrap_err()
            .code,
        "MIGRATION_PENDING"
    );
    f.now += Duration::hours(3);
    assert_eq!(
        lifecycle::expire(&f.training()).unwrap_err().code,
        "MIGRATION_PENDING"
    );
    assert_eq!(f.fingerprint(), before);
}
