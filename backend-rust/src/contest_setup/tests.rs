use super::*;
use crate::{
    catalogue::Catalogue, library::Library, migration::logical_fingerprint, storage::PersonalStore,
};
use chrono::TimeZone;
use flate2::{Compression, write::ZlibEncoder};
use rusqlite::Connection;
use std::{
    io::Write,
    process::{Command, Stdio},
};

struct Fixture {
    personal: PersonalStore,
    catalogue: Catalogue,
    library: Library,
    rows: Vec<Value>,
    now: DateTime<Utc>,
}
fn zip(value: &Value) -> Vec<u8> {
    let mut z = ZlibEncoder::new(Vec::new(), Compression::default());
    z.write_all(value.to_string().as_bytes()).unwrap();
    z.finish().unwrap()
}
impl Fixture {
    fn new() -> Self {
        let db = Connection::open_in_memory().unwrap();
        db.execute_batch("CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT);CREATE TABLE catalogue(id TEXT PRIMARY KEY,position INTEGER,full BLOB,compact TEXT);CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);INSERT INTO metadata VALUES('categories','[]'),('statuses','[]'),('replayEvents','{\"events\":[]}')").unwrap();
        let rows=(0..26).map(|i|{
            let id=match i {24=>"ABC 478::D".into(),25=>"Div.4 1003::G".into(),_=>format!("fixture::{i:02}")};
            let platform=["Codeforces","AtCoder","牛客","洛谷"][i%4];let tag=["线性 DP","BFS","模拟"][i%3];
            json!({"id":id,"title":format!("原始题目 {i}"),"url":format!("https://example.org/problem/{i}"),"platform":platform,"contest":if i%4==0{"ICPC 2024 Fixture"}else{"Fixture 2024"},"series":if i%4==0{"XCPC"}else{"Fixture"},"problem":char::from(b'A'+(i%20) as u8).to_string(),"difficulty":800+(i%6)*200,"tags":[tag],"knowledgeCategories":["基础 / 数据结构"],"catalogContentReady":true,"catalogReplayReady":true,"solutionAvailable":false})
        }).collect::<Vec<_>>();
        for (i, row) in rows.iter().enumerate() {
            let id = text(row, "id");
            db.execute(
                "INSERT INTO catalogue VALUES(?,?,?,?)",
                params![id, i as i64, zip(row), row.to_string()],
            )
            .unwrap();
            for alias in [id.to_owned(), format!("alias::{i}")] {
                db.execute("INSERT INTO aliases VALUES(?,?)", params![alias, id])
                    .unwrap();
            }
        }
        Self {
            personal: PersonalStore::open(std::path::Path::new(":memory:")).unwrap(),
            catalogue: Catalogue { db },
            library: Library {
                db: Connection::open_in_memory().unwrap(),
            },
            rows,
            now: Utc.with_ymd_and_hms(2026, 11, 9, 4, 0, 0).unwrap(),
        }
    }
    fn training(&mut self) -> Training<'_> {
        Training {
            personal: &mut self.personal,
            catalogue: &self.catalogue,
            library: &self.library,
            now: self.now,
        }
    }
    fn fingerprint(&self) -> String {
        logical_fingerprint(&self.personal.db).unwrap()
    }
    fn patch(&mut self, index: usize, field: &str, value: Value) {
        self.rows[index][field] = value;
        let row = &self.rows[index];
        self.catalogue
            .db
            .execute(
                "UPDATE catalogue SET compact=?,full=? WHERE id=?",
                params![row.to_string(), zip(row), text(row, "id")],
            )
            .unwrap();
    }
    fn preview(&mut self, book: &mut PreviewBook, body: &Value) -> Value {
        book.preview_with(&self.training(), body, &mut || 0.5)
            .unwrap()
    }
}
fn single() -> Value {
    json!({"mode":"single","min":0,"max":10000,"duration":60})
}
fn start_body(plan: &Value) -> Value {
    json!({"ids":plan["slots"].as_array().unwrap().iter().map(|s|s["id"].clone()).collect::<Vec<_>>(),"duration":plan["duration"],"previewId":plan["previewId"]})
}

#[test]
fn options_validate_typed_switches_and_keep_topic_defaults_and_numeric_compatibility() {
    assert_eq!(
        options(&json!({"mode":"topic","topic":" BFS ","tags":null,"wrongPenalty":"30"})).unwrap(),
        json!({"strategy":"topic","tags":["BFS"],"platform":"","excludeSolved":false,"reviewedOnly":false,"rules":"acm","wrongPenalty":30,"compilePenalty":false})
    );
    for body in [
        json!([]),
        json!({"mode":"unknown"}),
        json!({"mode":"topic"}),
        json!({"mode":"topic","topic":"x".repeat(81)}),
        json!({"tags":[""]}),
        json!({"excludeSolved":1}),
        json!({"compilePenalty":1}),
        json!({"wrongPenalty":121}),
        json!({"rules":"other"}),
        json!({"platform":[1]}),
    ] {
        assert_eq!(options(&body).unwrap_err().status, 400, "{body}");
    }
}

#[test]
fn blind_previews_have_only_public_fields_and_do_not_write_the_personal_journal() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let before = f.fingerprint();
    let result = f.preview(
        &mut book,
        &json!({"mode":"comprehensive","count":4,"min":800,"max":2000}),
    );
    assert_eq!(result["available"], 26);
    assert_eq!(result["plan"]["slots"].as_array().unwrap().len(), 4);
    for slot in result["plan"]["slots"].as_array().unwrap() {
        assert_eq!(slot.as_object().unwrap().len(), 4);
        assert!(slot.get("difficulty").is_none() && slot.get("tags").is_none());
    }
    assert_eq!(f.fingerprint(), before);
    assert_eq!(book.previews.len(), 1);
    assert!(
        book.previews[0]
            .slots
            .windows(2)
            .all(|pair| difficulty(&pair[0]) < difficulty(&pair[1]))
    );
}

#[test]
fn single_and_topic_duration_defaults_and_untyped_legacy_defaults_are_preserved() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    for (body, expected) in [
        (json!({"mode":"single","count":19,"max":1400}), 30),
        (json!({"mode":"single","max":1700}), 45),
        (
            json!({"mode":"topic","tags":["BFS"],"count":3,"max":1400}),
            75,
        ),
        (json!({"count":3,"max":1400}), 120),
        (json!({"rules":"xcpc","count":3,"max":1400}), 300),
    ] {
        assert_eq!(
            f.preview(&mut book, &body)["plan"]["duration"],
            expected,
            "{body}"
        );
    }
}

#[test]
fn previews_deduplicate_original_urls_and_ignore_only_actual_official_solved_evidence() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let duplicate_url = f.rows[0]["url"].clone();
    f.patch(1, "url", duplicate_url);
    f.personal.db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES('pass','alias::2','submit','official','AC','actual source','2026-11-01T00:00:00Z','2026-11-01T00:01:00Z')",[]).unwrap();
    f.personal.db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES('sample','fixture::03','run','samples','SAMPLE_PASS','actual source','2026-11-01T00:00:00Z','2026-11-01T00:01:00Z')",[]).unwrap();
    assert_eq!(f.preview(&mut book, &single())["available"], 25);
    let mut body = single();
    body["excludeSolved"] = true.into();
    let before = f.fingerprint();
    assert_eq!(f.preview(&mut book, &body)["available"], 24);
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn tombstoned_papers_and_mirrors_are_exposure_and_repeated_previews_prefer_unseen_originals() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    f.personal.db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config,deleted_at) VALUES('old','old','finished','2026-11-01T00:00:00Z','2026-11-01T01:00:00Z',60,'[{\"id\":\"alias::0\"}]','{}','2026-11-02T00:00:00Z')",[]).unwrap();
    let before = f.fingerprint();
    let first = f.preview(&mut book, &single());
    assert_ne!(first["plan"]["slots"][0]["id"], "fixture::00");
    let second = f.preview(&mut book, &single());
    assert_ne!(first["plan"]["slots"], second["plan"]["slots"]);
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn comprehensive_papers_cover_existing_families_without_flattening_the_difficulty_progression() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    f.preview(
        &mut book,
        &json!({"mode":"comprehensive","count":3,"min":800,"max":2000}),
    );
    let paper = &book.previews[0];
    let mut all = HashSet::new();
    for slot in &paper.slots {
        let row = f.rows.iter().find(|r| r["id"] == slot["id"]).unwrap();
        all.extend(families(row).unwrap());
    }
    assert_eq!(all, HashSet::from(["dp", "graph", "basic"]));
    assert!(
        paper
            .slots
            .windows(2)
            .all(|pair| difficulty(&pair[0]) < difficulty(&pair[1]))
    );
}

#[test]
fn start_revalidates_preview_identity_conditions_and_current_sources_before_consuming_it() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let plan = f.preview(&mut book, &single())["plan"].clone();
    let original = start_body(&plan);
    let before = f.fingerprint();
    for (field, value) in [
        ("previewId", json!("obsolete")),
        ("duration", json!(61)),
        ("count", json!(9)),
        ("min", json!(999)),
        ("rules", json!("xcpc")),
        ("tags", json!(["BFS"])),
        ("name", json!("x".repeat(101))),
    ] {
        let mut body = original.clone();
        body[field] = value;
        assert!(book.start(&f.training(), &body).is_err(), "{body}");
        assert_eq!(f.fingerprint(), before);
        assert_eq!(book.previews.len(), 1);
    }
    let chosen = f
        .rows
        .iter()
        .position(|r| r["id"] == plan["slots"][0]["id"])
        .unwrap();
    f.patch(chosen, "catalogContentReady", false.into());
    assert_eq!(
        book.start(&f.training(), &original).unwrap_err().status,
        409
    );
    assert_eq!(f.fingerprint(), before);
    assert_eq!(book.previews.len(), 1);
}

#[test]
fn preview_expiry_and_process_restart_require_a_new_confirmation_without_changing_any_records() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let plan = f.preview(&mut book, &single())["plan"].clone();
    let before = f.fingerprint();
    f.now += Duration::minutes(30) + Duration::milliseconds(1);
    assert_eq!(
        book.start(&f.training(), &start_body(&plan))
            .unwrap_err()
            .status,
        409
    );
    assert_eq!(f.fingerprint(), before);
    assert_eq!(
        PreviewBook::default()
            .start(&f.training(), &start_body(&plan))
            .unwrap_err()
            .status,
        409
    );
    assert_eq!(f.fingerprint(), before);
}

#[test]
fn a_new_paper_uses_server_time_and_only_a_real_exam_edit_activates_a_training_row() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let plan = f.preview(
        &mut book,
        &json!({"mode":"comprehensive","count":3,"duration":60,"min":800,"max":2000}),
    )["plan"]
        .clone();
    let mut body = start_body(&plan);
    body["deadline"] = json!("2099-01-01T00:00:00Z");
    body["name"] = json!("实际创建的本地考场");
    let now = f.now;
    let value = book.start(&f.training(), &body).unwrap();
    let contest = &value["contest"];
    assert_eq!(contest["deadline"], stamp(now + Duration::minutes(60)));
    assert_eq!(contest["startedAt"], stamp(now));
    assert_eq!(contest["name"], body["name"]);
    assert_eq!(contest["accepted"], 0);
    assert_eq!(contest["constraints"]["editedTrainingOnly"], true);
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT count(*) FROM training", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        0
    );
    assert!(book.previews.is_empty());
    let id = contest["slots"][0]["id"].clone();
    f.training()
        .save_draft(&json!({"id":id,"contestId":contest["id"],"code":"","language":"python3"}))
        .unwrap();
    assert_eq!(
        f.personal
            .db
            .query_row("SELECT count(*) FROM training", [], |row| row
                .get::<_, i64>(0))
            .unwrap(),
        1
    );
    assert_eq!(
        f.personal.draft(id.as_str().unwrap(), "").unwrap()["draftSavedAt"],
        Value::Null
    );
}

#[test]
fn a_later_workspace_failure_rolls_back_the_paper_and_keeps_the_same_preview_reusable() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let plan = f.preview(&mut book, &single())["plan"].clone();
    // The insert is valid, but reconstructing the retained history then fails.
    // This must roll the new paper back rather than consume its confirmation.
    f.personal.db.execute("INSERT INTO contests(id,name,status,started_at,deadline,finished_at,duration,slots,config) VALUES('retained','原历史','finished','2026-11-01T00:00:00Z','2026-11-01T01:00:00Z','2026-11-01T01:00:00Z',60,'[]','{\"wrongPenalty\":\"broken\"}')",[]).unwrap();
    let before = f.fingerprint();
    assert!(book.start(&f.training(), &start_body(&plan)).is_err());
    assert_eq!(f.fingerprint(), before);
    assert_eq!(book.previews.len(), 1);
    f.personal
        .db
        .execute("UPDATE contests SET config='{}' WHERE id='retained'", [])
        .unwrap();
    assert!(book.start(&f.training(), &start_body(&plan)).is_ok());
}

#[test]
fn private_facts_replay_authority_and_an_existing_active_paper_cannot_be_silently_replaced() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let plan = f.preview(&mut book, &single())["plan"].clone();
    f.personal
        .db
        .execute(
            "INSERT INTO account_problem_facts VALUES('private','{}','2026-11-01T00:00:00Z')",
            [],
        )
        .unwrap();
    let before = f.fingerprint();
    assert_eq!(
        book.preview(&f.training(), &single()).unwrap_err().code,
        "MIGRATION_PENDING"
    );
    assert_eq!(
        book.start(&f.training(), &start_body(&plan))
            .unwrap_err()
            .code,
        "MIGRATION_PENDING"
    );
    assert_eq!(f.fingerprint(), before);
    f.personal
        .db
        .execute("DELETE FROM account_problem_facts", [])
        .unwrap();
    let before = f.fingerprint();
    assert_eq!(
        book.preview(
            &f.training(),
            &json!({"mode":"replay","contest":"original"})
        )
        .unwrap_err()
        .code,
        "MIGRATION_PENDING"
    );
    assert_eq!(f.fingerprint(), before);
    book.start(&f.training(), &start_body(&plan)).unwrap();
    let next = f.preview(&mut book, &single())["plan"].clone();
    let before = f.fingerprint();
    assert_eq!(
        book.start(&f.training(), &start_body(&next))
            .unwrap_err()
            .status,
        409
    );
    assert_eq!(f.fingerprint(), before);
    assert_eq!(book.previews.len(), 1);
}

#[test]
fn too_few_difficulty_bands_and_invalid_bounds_leave_the_preview_book_and_journal_unchanged() {
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let before = f.fingerprint();
    for (body, status) in [
        (
            json!({"mode":"comprehensive","count":7,"min":800,"max":2000}),
            422,
        ),
        (
            json!({"mode":"comprehensive","count":20,"min":800,"max":800}),
            422,
        ),
        (json!({"count":21}), 400),
        (json!({"min":2000,"max":1000}), 400),
        (json!({"duration":0}), 400),
    ] {
        assert_eq!(
            book.preview(&f.training(), &body).unwrap_err().status,
            status,
            "{body}"
        );
        assert!(book.previews.is_empty());
        assert_eq!(f.fingerprint(), before);
    }
}

#[test]
fn the_same_recorded_random_draws_match_the_actual_legacy_selector_including_rerolls() {
    let python = std::env::var("TB_NATIVE_TEST_PYTHON")
        .expect("Use scripts/native.ps1 -Action test -TestPython ...");
    let mut f = Fixture::new();
    let mut book = PreviewBook::default();
    let requests = vec![
        json!({"mode":"comprehensive","count":4,"min":800,"max":2000}),
        json!({"mode":"comprehensive","count":4,"min":800,"max":2000}),
        json!({"mode":"topic","topic":"BFS","tags":null,"count":3,"min":800,"max":2000}),
        json!({"mode":"single","count":17,"min":800,"max":2000}),
        json!({"mode":"comprehensive","count":2,"reviewedOnly":true,"min":0,"max":10000}),
        json!({"mode":"single","platform":"xcpc","min":800,"max":2000}),
        json!({"count":4,"min":800,"max":2000,"rules":"xcpc"}),
    ];
    let mut counter = 0;
    let mut answers = vec![];
    for body in &requests {
        let mut value = book
            .preview_with(&f.training(), body, &mut || {
                let value = ((counter * 37 + 11) % 101) as f64 / 101.;
                counter += 1;
                value
            })
            .unwrap();
        value["plan"].as_object_mut().unwrap().remove("previewId");
        answers.push(value);
    }
    let script = r#"import datetime as dt,json,sqlite3,sys,threading
from pathlib import Path
from types import SimpleNamespace
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'backend'),str(root/'backend/common')]
from training import TrainingService
from assets import AssetLibrary
payload=json.load(sys.stdin);connection=sqlite3.connect(':memory:',isolation_level=None);connection.row_factory=sqlite3.Row
connection.executescript((root/'backend-rust/schema/personal.sql').read_text('utf8'))
service=TrainingService.__new__(TrainingService);service.connection=connection;service.lock=threading.RLock();service.store=SimpleNamespace(extensions=None)
service._library=lambda:payload['rows'];service._asset_library=lambda:AssetLibrary.__new__(AssetLibrary);service._evidence=lambda:[]
service.previews={};service.previous_previews={};service.clock=lambda:dt.datetime(2026,11,9,4,tzinfo=dt.timezone.utc)
class Draws:
 def __init__(self):self.at=0
 def random(self):value=((self.at*37+11)%101)/101;self.at+=1;return value
service.rng=Draws();result=[]
for request in payload['requests']:
 value=service.preview_contest(request);value['plan'].pop('previewId');result.append(value)
json.dump(result,sys.stdout,ensure_ascii=False)
"#;
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let mut child = Command::new(python)
        .args(["-c", script])
        .arg(root)
        .env("PYTHONUTF8", "1")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(
            json!({"rows":f.rows,"requests":requests})
                .to_string()
                .as_bytes(),
        )
        .unwrap();
    let output = child.wait_with_output().unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let legacy: Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(json!(answers), legacy);
}
