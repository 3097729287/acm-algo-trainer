use chrono::{TimeZone, Utc};
use serde_json::{Value, json};
use tempfile::TempDir;
use tobe_core::{api::ApiError, custom_lists, identity::canonical_url, storage::PersonalStore};

fn now() -> chrono::DateTime<Utc> {
    Utc.with_ymd_and_hms(2026, 11, 9, 17, 0, 0).unwrap()
}
fn fixture() -> (TempDir, PersonalStore) {
    let temp = TempDir::new().unwrap();
    let store = PersonalStore::open(&temp.path().join("personal.sqlite3")).unwrap();
    (temp, store)
}
fn resolve(_: &PersonalStore, id: &str) -> Result<Value, ApiError> {
    let (id, url) = match id {
        "A" | "alias-A" => (
            "A",
            "https://codeforces.com/contest/100/problem/A".to_owned(),
        ),
        "same-url-A" => (
            "alternate",
            "http://m1.codeforces.com/problemset/problem/100/a?locale=en".to_owned(),
        ),
        "B" => ("B", "https://www.luogu.com.cn/problem/P1001".to_owned()),
        "C" => (
            "C",
            "https://atcoder.jp/contests/abc001/tasks/abc001_1".to_owned(),
        ),
        _ if id.starts_with("large-") => (id, format!("https://qoj.ac/problem/{}", &id[6..])),
        _ => return Err(ApiError::missing("没有找到这道题")),
    };
    Ok(json!({"id":id,"problem":id,"url":url}))
}
fn save(store: &mut PersonalStore, body: Value) -> Value {
    custom_lists::save(store, &body, now(), resolve).unwrap()
}
fn id(value: &Value) -> &str {
    value["list"]["id"].as_str().unwrap()
}
fn preferences(store: &PersonalStore) -> Value {
    store
        .rows("SELECT * FROM account_preferences ORDER BY key", [])
        .unwrap()
}

#[test]
fn lists_survive_restart_and_record_one_actual_beijing_day_creation() {
    let (temp, mut store) = fixture();
    let value = save(
        &mut store,
        json!({"title":"  我的算法题单 🦀  ","problemIds":["A","alias-A","B"]}),
    );
    assert_eq!(value["list"]["title"], "我的算法题单 🦀");
    assert_eq!(value["list"]["problems"].as_array().unwrap().len(), 2);
    assert!(value["list"]["id"].as_str().unwrap().starts_with("custom:"));
    let actions = store
        .document("activity-actions:2026-11-10")
        .unwrap()
        .unwrap();
    assert_eq!(actions.as_object().unwrap().len(), 1);
    assert_eq!(
        actions.as_object().unwrap().values().next().unwrap()["kind"],
        "create-list"
    );
    drop(store);
    let store = PersonalStore::open(&temp.path().join("personal.sqlite3")).unwrap();
    assert_eq!(
        custom_lists::read(&store).unwrap(),
        vec![value["list"].clone()]
    );
}
#[test]
fn rename_and_reorder_preserve_original_added_times_and_missing_legacy_time() {
    let (_temp, mut store) = fixture();
    let value = save(&mut store, json!({"title":"原题单","problemIds":["A","B"]}));
    let name = id(&value).to_owned();
    let mut legacy = value["list"].clone();
    legacy["problems"][0]
        .as_object_mut()
        .unwrap()
        .remove("addedAt");
    PersonalStore::put(
        &store.db,
        &format!("custom-training-list:{name}"),
        &legacy.to_string(),
        "old",
    )
    .unwrap();
    let later = now() + chrono::Duration::days(1);
    let changed = custom_lists::save(
        &mut store,
        &json!({"id":name,"title":"改名","problemIds":["B","A","C"]}),
        later,
        resolve,
    )
    .unwrap();
    assert_eq!(
        changed["list"]["problems"][0]["addedAt"],
        value["list"]["problems"][1]["addedAt"]
    );
    assert!(changed["list"]["problems"][1].get("addedAt").is_none());
    assert_ne!(
        changed["list"]["problems"][2]["addedAt"],
        value["list"]["problems"][1]["addedAt"]
    );
    assert_eq!(store.document("activity-actions:2026-11-11").unwrap(), None);
}
#[test]
fn batch_adds_to_all_destinations_once_and_deduplicates_aliases_and_judge_urls() {
    let (_temp, mut store) = fixture();
    let first = save(&mut store, json!({"title":"一","problemIds":["B"]}));
    let second = save(&mut store, json!({"title":"二"}));
    let body = json!({"listIds":[id(&first),id(&second),id(&first)],"problemIds":["A","alias-A","same-url-A","B"]});
    let result = custom_lists::add(&mut store, &body, now(), resolve).unwrap();
    assert_eq!(result["added"][id(&first)], 1);
    assert_eq!(result["added"][id(&second)], 2);
    let snapshot = preferences(&store);
    let repeated = custom_lists::add(
        &mut store,
        &body,
        now() + chrono::Duration::days(1),
        resolve,
    )
    .unwrap();
    assert_eq!(repeated["added"][id(&first)], 0);
    assert_eq!(preferences(&store), snapshot);
}
#[test]
fn invalid_batches_leave_every_destination_and_action_unchanged() {
    let (_temp, mut store) = fixture();
    let first = save(&mut store, json!({"title":"一","problemIds":["A"]}));
    let before = preferences(&store);
    for body in [
        json!({"listIds":[id(&first),"public-list"],"problemIds":["B"]}),
        json!({"listIds":[id(&first)],"problemIds":["B","missing"]}),
        json!({"listIds":[],"problemIds":["B"]}),
        json!({"listIds":[id(&first)],"problemIds":[]}),
        json!({"listIds":[id(&first)],"problemIds":["B"],"owner":"someone-else"}),
    ] {
        assert!(custom_lists::add(&mut store, &body, now(), resolve).is_err());
        assert_eq!(preferences(&store), before);
    }
}
#[test]
fn transaction_failure_rolls_back_an_earlier_destination_and_creation_action() {
    let (_temp, mut store) = fixture();
    let first = save(&mut store, json!({"title":"一"}));
    let second = save(&mut store, json!({"title":"二"}));
    let before = preferences(&store);
    store.db.execute_batch(&format!("CREATE TEMP TRIGGER reject_second BEFORE UPDATE ON account_preferences WHEN NEW.key='custom-training-list:{}' BEGIN SELECT RAISE(ABORT,'fixture rejection'); END;",id(&second))).unwrap();
    assert!(
        custom_lists::add(
            &mut store,
            &json!({"listIds":[id(&first),id(&second)],"problemIds":["B"]}),
            now(),
            resolve
        )
        .is_err()
    );
    assert_eq!(preferences(&store), before);
    store.db.execute_batch("CREATE TEMP TRIGGER reject_new BEFORE INSERT ON account_preferences WHEN NEW.key LIKE 'custom-training-list:%' BEGIN SELECT RAISE(ABORT,'fixture rejection'); END;").unwrap();
    assert!(
        custom_lists::save(
            &mut store,
            &json!({"title":"不会保存"}),
            now() + chrono::Duration::days(1),
            resolve
        )
        .is_err()
    );
    assert_eq!(preferences(&store), before);
}
#[test]
fn deletion_preserves_original_record_and_other_account_cannot_edit_it() {
    let (_temp, mut store) = fixture();
    let value = save(&mut store, json!({"title":"保留原记录","problemIds":["A"]}));
    let (_other, mut other) = fixture();
    assert!(
        custom_lists::save(
            &mut other,
            &json!({"id":id(&value),"title":"侵入"}),
            now(),
            resolve
        )
        .is_err()
    );
    assert!(custom_lists::read(&other).unwrap().is_empty());
    let deleted = custom_lists::save(
        &mut store,
        &json!({"id":id(&value),"deleted":true}),
        now(),
        resolve,
    )
    .unwrap();
    assert_eq!(deleted["list"]["problems"], value["list"]["problems"]);
    assert_eq!(deleted["list"]["title"], value["list"]["title"]);
    assert!(custom_lists::read(&store).unwrap().is_empty());
    assert!(
        custom_lists::add(
            &mut store,
            &json!({"listIds":[id(&value)],"problemIds":["B"]}),
            now(),
            resolve
        )
        .is_err()
    );
}
#[test]
fn destination_limit_is_validated_before_any_write_and_large_batches_work() {
    let (_temp, mut store) = fixture();
    let first = save(&mut store, json!({"title":"空"}));
    let second = save(&mut store, json!({"title":"满"}));
    let mut full = second["list"].clone();
    full["problems"] = json!(vec![
        json!({"problemId":"legacy","url":null});
        custom_lists::MAX_PROBLEMS
    ]);
    PersonalStore::put(
        &store.db,
        &format!("custom-training-list:{}", id(&second)),
        &full.to_string(),
        "old",
    )
    .unwrap();
    let before = preferences(&store);
    assert!(
        custom_lists::add(
            &mut store,
            &json!({"listIds":[id(&first),id(&second)],"problemIds":["B"]}),
            now(),
            resolve
        )
        .is_err()
    );
    assert_eq!(preferences(&store), before);
    let ids = (1..=1300).map(|i| format!("large-{i}")).collect::<Vec<_>>();
    let answer = custom_lists::add(
        &mut store,
        &json!({"listIds":[id(&first)],"problemIds":ids}),
        now(),
        resolve,
    )
    .unwrap();
    assert_eq!(answer["added"][id(&first)], 1300);
}
#[test]
fn invalid_names_ids_and_oversized_input_do_not_create_records() {
    let (_temp, mut store) = fixture();
    for body in [
        json!({"title":""}),
        json!({"title":"x".repeat(81)}),
        json!({"title":"bad\nname"}),
        json!({"title":false}),
        json!({"title":"x","owner":"other"}),
        json!({"title":"x","id":"custom:00000000000000000000000000000000"}),
        json!({"title":"x","deleted":"false"}),
        json!({"title":"x","problemIds":vec!["A";custom_lists::MAX_PROBLEMS+1]}),
    ] {
        assert!(custom_lists::save(&mut store, &body, now(), resolve).is_err());
        assert!(custom_lists::read(&store).unwrap().is_empty());
        assert_eq!(preferences(&store), json!([]));
    }
}
#[test]
fn corrupt_documents_stay_intact_and_cannot_redirect_a_write() {
    let (_temp, mut store) = fixture();
    let value = save(&mut store, json!({"title":"合法"}));
    let name = id(&value);
    let mut corrupt = value["list"].clone();
    corrupt["id"] = json!("custom:00000000-0000-0000-0000-000000000000");
    PersonalStore::put(
        &store.db,
        &format!("custom-training-list:{name}"),
        &corrupt.to_string(),
        "old",
    )
    .unwrap();
    PersonalStore::put(&store.db, "custom-training-list:unknown", "{", "old").unwrap();
    let before = preferences(&store);
    assert!(
        custom_lists::save(
            &mut store,
            &json!({"id":name,"title":"不能覆盖"}),
            now(),
            resolve
        )
        .is_err()
    );
    assert_eq!(preferences(&store), before);
}
#[test]
fn canonical_urls_keep_judge_query_ids_separate_and_normalize_known_aliases() {
    for (source, expected) in [
        (
            "http://m2.codeforces.com/problemset/problem/100/a?locale=ru",
            "codeforces.com/contest/100/problem/A",
        ),
        (
            "https://codeforces.com/gym/102835/problem/g/",
            "codeforces.com/gym/102835/problem/G",
        ),
        (
            "https://www.luogu.com.cn/problem/p1001",
            "luogu.com.cn/problem/P1001",
        ),
        (
            "https://atcoder.jp/contests/ABC001/tasks/ABC001_1",
            "atcoder.jp/contests/abc001/tasks/abc001_1",
        ),
        (
            "https://qoj.ac/contest/1/problem/123/statement/zh_cn",
            "qoj.ac/problem/123",
        ),
        (
            "https://ac.nowcoder.com/acm/contest/1/a",
            "ac.nowcoder.com/acm/contest/1/A",
        ),
        (
            "https://onlinejudge.org/index.php?problem=&problem=123",
            "onlinejudge.org/problem/123",
        ),
        (
            "http://acm.hdu.edu.cn/showproblem.php?pid=1000",
            "acm.hdu.edu.cn/problem/1000",
        ),
        ("http://poj.org/problem?id=1000", "poj.org/problem/1000"),
        (
            "https://www.spoj.com/problems/test/",
            "spoj.com/problems/TEST",
        ),
        ("https://example.com/a/../b", "example.com/a/../b"),
        ("https://例子.测试/题目/", "例子.测试/题目"),
        (
            "https://example.com/%E9%A2%98%E7%9B%AE/",
            "example.com/题目",
        ),
    ] {
        assert_eq!(canonical_url(source), Some(expected.into()), "{source}");
    }
    assert_ne!(
        canonical_url("https://onlinejudge.org/index.php?problem=1"),
        canonical_url("https://onlinejudge.org/index.php?problem=2")
    );
    assert_eq!(canonical_url("javascript:alert(1)"), None);
}
