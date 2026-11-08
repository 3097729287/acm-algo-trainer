use rusqlite::Connection;
use serde_json::{Value, json};
use tobe_core::{catalogue::Catalogue, migration::logical_fingerprint, storage::PersonalStore};

fn catalogue(value: Option<&Value>) -> Catalogue {
    let db = Connection::open_in_memory().unwrap();
    db.execute(
        "CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL)",
        [],
    )
    .unwrap();
    if let Some(value) = value {
        db.execute(
            "INSERT INTO metadata VALUES('replayEvents',?)",
            [value.to_string()],
        )
        .unwrap();
    }
    Catalogue { db }
}

#[test]
fn incomplete_public_rosters_are_preserved_and_private_facts_never_disappear() {
    let folder = tempfile::tempdir().unwrap();
    let personal = PersonalStore::open(&folder.path().join("personal.sqlite3")).unwrap();
    let value = json!({"events":[{"name":"partial fixture","complete":false,"expectedCount":3,"availableLetters":["A","C"],"missingLetters":["B"]}]});
    let catalogue = catalogue(Some(&value));
    let before = logical_fingerprint(&personal.db).unwrap();
    assert_eq!(catalogue.replay_events(&personal).unwrap(), value);
    assert_eq!(before, logical_fingerprint(&personal.db).unwrap());
    personal.db.execute("INSERT INTO account_problem_facts VALUES('private-task','{\"row\":{\"id\":\"private-task\"}}','now')",[]).unwrap();
    let before = logical_fingerprint(&personal.db).unwrap();
    assert_eq!(
        catalogue.replay_events(&personal).unwrap_err().code,
        "MIGRATION_PENDING"
    );
    assert_eq!(before, logical_fingerprint(&personal.db).unwrap());
}

#[test]
fn missing_or_corrupt_public_event_metadata_is_not_an_empty_contest_list() {
    let folder = tempfile::tempdir().unwrap();
    let personal = PersonalStore::open(&folder.path().join("personal.sqlite3")).unwrap();
    let catalogue = catalogue(None);
    assert_eq!(
        catalogue.replay_events(&personal).unwrap_err().code,
        "MIGRATION_PENDING"
    );
    catalogue
        .db
        .execute("INSERT INTO metadata VALUES('replayEvents','{broken')", [])
        .unwrap();
    assert!(catalogue.replay_events(&personal).is_err());
    catalogue
        .db
        .execute("UPDATE metadata SET value='{\"events\":null}'", [])
        .unwrap();
    assert_eq!(
        catalogue.replay_events(&personal).unwrap_err().code,
        "CATALOGUE_FORMAT"
    );
}
