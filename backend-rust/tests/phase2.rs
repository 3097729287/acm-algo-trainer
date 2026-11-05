use chrono::{TimeZone, Utc};
use serde_json::{Value, json};
use tempfile::TempDir;
use tobe_core::{learning, preferences, storage::PersonalStore, usage};

fn now() -> chrono::DateTime<Utc> {
    Utc.with_ymd_and_hms(2026, 11, 5, 4, 0, 0).unwrap()
}
fn store(temp: &TempDir) -> PersonalStore {
    PersonalStore::open(&temp.path().join("private.sqlite3")).unwrap()
}

#[test]
fn preferences_preserve_monotonic_acknowledgements_and_layouts() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    preferences::save(&mut store,None,&json!({"preferences":{"seenAchievements":["first-ac"],"onboardingCompleted":true,"onboardingGuideVersion":3,"onboardingUnlockedPages":["wiki"],"levelNoticeVersion":1,"levelNoticeSeen":8,"levelNoticePending":9,"learningPaths":{"sectionWorkspaces":{"training":{"groups":[1,2]}}}}}),now()).unwrap();
    let answer=preferences::save(&mut store,None,&json!({"preferences":{"seenAchievements":["second-ac"],"onboardingCompleted":false,"onboardingGuideVersion":1,"onboardingUnlockedPages":["templates"],"levelNoticeVersion":1,"levelNoticeSeen":7,"levelNoticePending":8,"learningPaths":{"sectionWorkspaces":{"training":{"groups":[1,2]}}}}}),now()).unwrap();
    let p = &answer["preferences"];
    assert_eq!(p["onboardingCompleted"], true);
    assert_eq!(p["onboardingGuideVersion"], 3);
    assert_eq!(p["seenAchievements"], json!(["first-ac", "second-ac"]));
    assert_eq!(p["onboardingUnlockedPages"], json!(["templates", "wiki"]));
    assert_eq!(p["levelNoticeSeen"], 8);
    assert_eq!(p["levelNoticePending"], 9);
    assert_eq!(
        p["learningPaths"]["sectionWorkspaces"]["training"]["groups"],
        json!([1, 2])
    );
}
#[test]
fn invalid_preference_batches_preserve_prior_state() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    preferences::save(
        &mut store,
        None,
        &json!({"preferences":{"fontSize":16}}),
        now(),
    )
    .unwrap();
    for value in [
        json!({"fontSize":true}),
        json!({"fontSize":23}),
        json!({"libraryPageSize":9}),
        json!({"hiddenNavPages":["settings"]}),
        json!({"unknown":"value"}),
        json!({"widgets":"yes"}),
        json!({"shortcuts":{"run":"bad\nvalue"}}),
        json!({"pageOpacities":{"editor":-1}}),
        json!({"learningPaths":{"browserV1":{"version":2,"tabs":[]}}}),
    ] {
        assert!(preferences::save(&mut store, None, &json!({"preferences":value}), now()).is_err());
        assert_eq!(
            store.preferences().unwrap()["preferences"],
            json!({"fontSize":16})
        );
    }
}
#[test]
fn preference_size_limit_excludes_original_avatar_and_browser_document() {
    assert!(preferences::validate(&json!({"views":["x".repeat(131072)]})).is_err());
    assert!(preferences::validate(&json!({"learningPaths":{"browserV1":{"version":1,"tabs":[{"content":"x".repeat(140000)}]}}})).is_ok());
    assert!(
        preferences::validate(
            &json!({"learningPaths":{"browserV1":{"version":1,"tabs":vec![json!({});65]}}})
        )
        .is_err()
    );
}
#[test]
fn avatars_require_correct_original_raster_signature() {
    for avatar in [
        "data:image/svg+xml;base64,PHN2Zz4=",
        "data:image/png;base64,bm90IGEgcG5n",
        "https://example.com/picture.png",
    ] {
        assert!(preferences::validate(&json!({"avatarData":avatar})).is_err());
    }
    assert!(preferences::validate(&json!({"avatarData":""})).is_ok());
}
#[test]
fn action_journal_uses_beijing_day_and_deduplicates_same_action() {
    let temp = TempDir::new().unwrap();
    let store = store(&temp);
    let at = Utc.with_ymd_and_hms(2026, 11, 5, 17, 0, 0).unwrap();
    preferences::action(&store.db, "learn", "lecture-one", at).unwrap();
    preferences::action(&store.db, "learn", "lecture-one", at).unwrap();
    let value = store
        .document("activity-actions:2026-11-06")
        .unwrap()
        .unwrap();
    assert_eq!(value.as_object().unwrap().len(), 1);
    preferences::action(&store.db, "favorite", "lecture-one", at).unwrap();
    assert_eq!(
        store
            .document("activity-actions:2026-11-06")
            .unwrap()
            .unwrap()
            .as_object()
            .unwrap()
            .len(),
        2
    );
}
#[test]
fn action_journal_retains_existing_entries_at_capacity() {
    let temp = TempDir::new().unwrap();
    let store = store(&temp);
    let mut events = json!({});
    for n in 0..512 {
        events[n.to_string()] = json!({"kind":"learn","key":n});
    }
    store
        .put_document("activity-actions:2026-11-05", &events)
        .unwrap();
    preferences::action(&store.db, "learn", "new", now()).unwrap();
    assert_eq!(
        store
            .document("activity-actions:2026-11-05")
            .unwrap()
            .unwrap(),
        events
    );
}
#[test]
fn usage_heartbeat_retries_and_overlaps_do_not_duplicate_time() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let id = "12345678-1234-1234-1234-123456789abc";
    for sequence in [1, 1, 2] {
        usage::record(
            &mut store,
            &json!({"sessionId":id,"sequence":sequence,"seconds":30,"learning":true}),
            now(),
        )
        .unwrap();
    }
    assert_eq!(usage::snapshot(&store).unwrap()["totalSeconds"], 30);
    assert_eq!(
        store.document("learning-usage-v1").unwrap().unwrap()["days"]["2026-11-05"]["seconds"],
        30.0
    );
}
#[test]
fn usage_splits_midnight_and_preserves_rounded_per_day_totals() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let at = Utc.with_ymd_and_hms(2026, 11, 5, 16, 0, 20).unwrap();
    usage::record(
        &mut store,
        &json!({"sessionId":"12345678-1234-1234-1234-123456789abc","sequence":1,"seconds":50}),
        at,
    )
    .unwrap();
    let view = usage::snapshot(&store).unwrap();
    assert_eq!(
        view["days"],
        json!([{"date":"2026-11-05","seconds":30},{"date":"2026-11-06","seconds":20}])
    );
    assert_eq!(view["totalSeconds"], 50);
    assert_eq!(view["maxDailyDate"], "2026-11-05");
}
#[test]
fn invalid_usage_does_not_create_time_or_sessions() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    for seconds in [json!(0), json!(61), json!(true), Value::Null] {
        assert!(usage::record(&mut store,&json!({"sessionId":"12345678-1234-1234-1234-123456789abc","sequence":1,"seconds":seconds}),now()).is_err());
    }
    assert!(store.document("usage-v1").unwrap().is_none());
}
#[test]
fn usage_session_cursor_retention_is_bounded() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    for n in 0..70 {
        usage::record(&mut store,&json!({"sessionId":format!("00000000-0000-0000-0000-{n:012x}"),"sequence":1,"seconds":1}),now()+chrono::Duration::seconds(n)).unwrap();
    }
    assert_eq!(
        store.document("usage-v1").unwrap().unwrap()["sessions"]
            .as_object()
            .unwrap()
            .len(),
        64
    );
}
#[test]
fn malformed_usage_is_reported_without_overwriting_history() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let body =
        json!({"sessionId":"12345678-1234-1234-1234-123456789abc","sequence":1,"seconds":15});
    for saved in [
        json!({"version":1,"days":[],"sessions":{}}),
        json!({"version":1,"days":{"2026-11-04":42},"sessions":{}}),
        json!({"version":1,"days":{},"sessions":[]}),
    ] {
        store.put_document("usage-v1", &saved).unwrap();
        assert_eq!(
            usage::record(&mut store, &body, now()).unwrap_err().code,
            "INVALID_STORED_DATA"
        );
        assert_eq!(store.document("usage-v1").unwrap().unwrap(), saved);
        assert!(usage::snapshot(&store).is_err());
    }
}
#[test]
fn usage_storage_errors_are_propagated() {
    let temp = TempDir::new().unwrap();
    let store = store(&temp);
    store
        .db
        .execute_batch("DROP TABLE account_preferences")
        .unwrap();
    assert!(usage::snapshot(&store).is_err());
}
#[test]
fn effective_learning_unions_retries_across_midnight() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let at = Utc.with_ymd_and_hms(2026, 11, 5, 16, 1, 0).unwrap();
    let seconds = at.timestamp() as f64;
    let body = json!({"intervals":[[seconds-120.,seconds-20.],[seconds-90.,seconds-30.]]});
    for _ in 0..2 {
        assert_eq!(
            learning::effective(&mut store, &body, at).unwrap()["totalSeconds"],
            100
        );
    }
    let before = store
        .document("effective-learning-day:2026-11-05")
        .unwrap()
        .unwrap();
    let after = store
        .document("effective-learning-day:2026-11-06")
        .unwrap()
        .unwrap();
    assert_eq!(
        before["intervals"][0][1].as_f64().unwrap() - before["intervals"][0][0].as_f64().unwrap(),
        60.
    );
    assert_eq!(
        after["intervals"][0][1].as_f64().unwrap() - after["intervals"][0][0].as_f64().unwrap(),
        40.
    );
}
#[test]
fn effective_learning_validates_entire_batch_before_any_write() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let s = now().timestamp();
    let error = learning::effective(
        &mut store,
        &json!({"intervals":[[s-60,s-30],[s-300,s]]}),
        now(),
    )
    .unwrap_err();
    assert_eq!(error.status, 400);
    assert_eq!(store.db.query_row("SELECT count(*) FROM account_preferences WHERE key LIKE 'effective-learning-day:%'",[],|r|r.get::<_,i64>(0)).unwrap(),0);
}
#[test]
fn empty_history_is_read_without_inventing_current_tasks() {
    let temp = TempDir::new().unwrap();
    let store = store(&temp);
    let old = json!({"id":"first","at":"old","reason":"首次规划"});
    store
        .put_document("learning-summary-history:first", &old)
        .unwrap();
    assert_eq!(learning::history(&store, "first").unwrap(), old);
    let snapshot = learning::snapshot(&store, &json!({"topics":[]}), now()).unwrap();
    assert_eq!(snapshot["history"][0]["week"], Value::Null);
    assert_eq!(snapshot["plan"], Value::Null);
}
#[test]
fn history_deletion_is_a_tombstone_and_current_plan_is_preserved() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    store
        .put_document(
            "learning-summary-history:first",
            &json!({"id":"first","at":"old","reason":"old","plan":{"tasks":[1]}}),
        )
        .unwrap();
    let mut current = learning::empty();
    current["plan"] = json!({"id":"current","tasks":[{"key":"do","status":"pending"}]});
    store.put_document(learning::KEY, &current).unwrap();
    let result = learning::update(
        &mut store,
        &json!({"action":"delete-history","revision":"","id":"first"}),
        &json!({"topics":[]}),
        now(),
    )
    .unwrap();
    assert_eq!(result["plan"], current["plan"]);
    assert_eq!(
        store
            .document("learning-summary-history:first")
            .unwrap()
            .unwrap()["deleted"],
        true
    );
    assert!(learning::history(&store, "first").is_err());
}
#[test]
fn stale_learning_revision_does_not_mutate_state() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let mut state = learning::empty();
    state["revision"] = json!("current");
    store.put_document(learning::KEY, &state).unwrap();
    let error = learning::update(
        &mut store,
        &json!({"action":"view","revision":"old","view":{"mode":"full"}}),
        &json!({"topics":[]}),
        now(),
    )
    .unwrap_err();
    assert_eq!(error.status, 409);
    assert_eq!(store.document(learning::KEY).unwrap().unwrap(), state);
}
#[test]
fn unsupported_planning_mutation_does_not_create_completion_evidence() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let error = learning::update(
        &mut store,
        &json!({"action":"complete","revision":"","key":"task"}),
        &json!({"topics":[]}),
        now(),
    )
    .unwrap_err();
    assert_eq!(error.code, "MIGRATION_PENDING");
    assert!(store.document(learning::KEY).unwrap().is_none());
}
#[test]
fn viewed_paragraph_requires_the_original_hash() {
    let temp = TempDir::new().unwrap();
    let mut store = store(&temp);
    let mut state = learning::empty();
    state["article"] = json!([{"id":"main","hash":"trusted","text":"original"}]);
    store.put_document(learning::KEY, &state).unwrap();
    let answer = learning::update(
        &mut store,
        &json!({"action":"seen","revision":"","paragraphs":{"main":"forged","missing":"value"}}),
        &json!({"topics":[]}),
        now(),
    )
    .unwrap();
    assert_eq!(answer["seen"], json!({}));
}
#[test]
fn quiz_projection_never_exposes_the_answer() {
    let result = learning::quiz(&json!({"test":["Question",["A","B"],1]}), "test").unwrap();
    assert_eq!(
        result,
        json!({"topicId":"test","question":"Question","options":["A","B"]})
    );
    assert!(result.get("answer").is_none());
}
