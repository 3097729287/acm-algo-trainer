use serde_json::json;
use tobe_core::{migration::logical_fingerprint, storage::PersonalStore, templates};

#[test]
fn customized_defaults_survive_restart_without_replacing_selected_code_or_drafts() {
    let directory = tempfile::tempdir().unwrap();
    let path = directory.path().join("personal.sqlite3");
    let mut store = PersonalStore::open(&path).unwrap();
    let custom = templates::initial_save(
        &mut store,
        &json!({"title":"我的起始程序","language":"cpp17","code":"custom"}),
    )
    .unwrap()["template"]
        .clone();
    templates::initial_choose(
        &store,
        &json!({"id":custom["id"],"language":"cpp17","revision":""}),
    )
    .unwrap();
    store
        .save_draft(&json!({"id":"problem","code":"existing draft"}))
        .unwrap();
    let before = templates::initial_selected(&store).unwrap();
    let saved=templates::initial_save(&mut store,&json!({"id":"default","title":"默认","language":"cpp17","code":"// 中文默认程序\nint main() {}","revision":""})).unwrap()["template"].clone();
    assert_eq!(saved["id"], "default");
    assert_eq!(saved["customized"], true);
    assert_ne!(saved["revision"], "");
    let selected = templates::initial_selected(&store).unwrap();
    assert_eq!(selected, before);
    assert_eq!(
        store.draft("problem", "").unwrap()["draft"],
        "existing draft"
    );
    let py = templates::initial_catalog(&store).unwrap()["templates"][1].clone();
    assert_eq!(py["revision"], "");
    assert_eq!(py["code"], templates::default_code("python3").unwrap());
    drop(store);
    let store = PersonalStore::open(&path).unwrap();
    assert_eq!(
        templates::initial_catalog(&store).unwrap()["templates"][0],
        saved
    );
    assert_eq!(
        store.draft("problem", "").unwrap()["draft"],
        "existing draft"
    );
}

#[test]
fn stale_or_invalid_default_edits_and_failed_writes_preserve_original() {
    let directory = tempfile::tempdir().unwrap();
    let mut store = PersonalStore::open(&directory.path().join("personal.sqlite3")).unwrap();
    let saved=templates::initial_save(&mut store,&json!({"id":"default","title":"默认","language":"python3","code":"print(1)","revision":""})).unwrap()["template"].clone();
    let baseline = logical_fingerprint(&store.db).unwrap();
    for change in [
        json!({"revision":"stale"}),
        json!({"title":"renamed"}),
        json!({"delete":true}),
        json!({"code":"\0"}),
        json!({"code":"界".repeat(21846)}),
    ] {
        let mut body = json!({"id":"default","title":"默认","language":"python3","code":"changed","revision":saved["revision"]});
        body.as_object_mut()
            .unwrap()
            .extend(change.as_object().unwrap().clone());
        assert!(templates::initial_save(&mut store, &body).is_err());
        assert_eq!(baseline, logical_fingerprint(&store.db).unwrap());
    }
    store.db.execute_batch("CREATE TRIGGER reject_default BEFORE INSERT ON account_preferences WHEN NEW.key='initial-code-default:python3' BEGIN SELECT RAISE(ABORT,'test write failure'); END;").unwrap();
    let baseline = logical_fingerprint(&store.db).unwrap();
    assert!(templates::initial_save(&mut store,&json!({"id":"default","title":"默认","language":"python3","code":"print(2)","revision":saved["revision"]})).is_err());
    assert_eq!(baseline, logical_fingerprint(&store.db).unwrap());
    assert_eq!(
        templates::initial_catalog(&store).unwrap()["templates"][1],
        saved
    );
}
