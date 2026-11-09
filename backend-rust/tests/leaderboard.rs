use chrono::{DateTime, Duration as CDuration, TimeZone, Utc};
use rusqlite::{Connection, params};
use serde_json::{Value, json};
use std::{
    io::{BufRead, BufReader, Write},
    process::{Child, ChildStdin, ChildStdout, Command, Stdio},
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::Duration,
};
use tempfile::TempDir;
use tobe_core::{
    catalogue::Catalogue,
    leaderboard::{AuthContext, LeaderboardClient, activity_after_input, validate_endpoint},
    storage::PersonalStore,
};

fn now() -> DateTime<Utc> {
    Utc.with_ymd_and_hms(2026, 11, 9, 7, 0, 0).unwrap()
}
fn client() -> LeaderboardClient {
    LeaderboardClient::new(Duration::from_secs(4)).unwrap()
}
struct Fixture {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
    info: Value,
}
impl Fixture {
    fn new() -> Self {
        let script = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .join("tests/fixtures/leaderboard-service.mjs");
        let mut child = Command::new("node")
            .arg(script)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .expect("local shared fixture must start");
        let input = child.stdin.take().unwrap();
        let mut output = BufReader::new(child.stdout.take().unwrap());
        let mut line = String::new();
        output.read_line(&mut line).unwrap();
        let info: Value =
            serde_json::from_str(&line).expect("local shared fixture must initialize");
        Self {
            child,
            input,
            output,
            info,
        }
    }
    fn auth(&self, index: usize) -> AuthContext<'_> {
        AuthContext {
            owner: self.info["owners"][index]["owner"].as_str().unwrap(),
            endpoint: self.info["endpoint"].as_str().unwrap(),
            bearer: self.info["owners"][index]["token"].as_str().unwrap(),
            admin: false,
        }
    }
    fn command(&mut self, op: Value) -> Value {
        writeln!(self.input, "{op}").unwrap();
        self.input.flush().unwrap();
        let mut line = String::new();
        self.output.read_line(&mut line).unwrap();
        let v: Value = serde_json::from_str(&line).expect("fixture control response");
        assert_ne!(v["fixtureError"], true, "local shared control failed");
        v
    }
    fn mode(&mut self, path: &str, mode: &str) {
        self.command(json!({"op":"mode","path":path,"mode":mode}));
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = writeln!(self.input, "{{\"op\":\"stop\"}}");
        let _ = self.input.flush();
        let _ = self.child.wait();
    }
}
const PNG: &str = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

#[test]
fn endpoint_policy_and_real_input_boundary_are_explicit() {
    for endpoint in [
        "https://example.com",
        "http://127.0.0.1:18001",
        "https://localhost:18443",
        "http://[::1]:18111",
        "https://example.com/relay",
        "   ",
    ] {
        assert!(validate_endpoint(endpoint).is_ok(), "{endpoint}");
    }
    for endpoint in [
        "http://example.com",
        "https://example.com:444",
        "https://user:pass@example.com",
        "https://example.com?q=x",
        "https://example.com/#x",
        "file:///x",
        "https://example.com/\r\nx",
        "https://example.com\\@localhost",
    ] {
        assert!(validate_endpoint(endpoint).is_err());
    }
    assert_eq!(
        validate_endpoint(" https://example.com/// ").unwrap(),
        "https://example.com"
    );
    assert_eq!(
        activity_after_input("rankings", now(), now() + CDuration::seconds(299)).unwrap(),
        "rankings"
    );
    assert_eq!(
        activity_after_input("rankings", now(), now() + CDuration::seconds(300)).unwrap(),
        "idle"
    );
    assert_eq!(
        activity_after_input("rankings", now(), now() + CDuration::seconds(700)).unwrap(),
        "idle"
    );
    assert!(activity_after_input("invalid", now(), now()).is_err());
    assert!(activity_after_input("rankings", now() + CDuration::seconds(1), now()).is_err());
}

#[test]
fn real_shared_social_inboxes_replies_likes_and_list_toggles_are_account_bound() {
    let mut f = Fixture::new();
    let c = client();
    let bob = f.auth(1).owner.to_owned();
    let alice = f.auth(0).owner.to_owned();
    let id = uuid::Uuid::new_v4().to_string();
    let value = c
        .social_write(
            &f.auth(0),
            "comments",
            &json!({"targetId":bob,"requestId":id,"text":"本地临时账号留言 🦀"}),
            now(),
            &|| true,
        )
        .unwrap();
    assert_eq!(value["id"], id);
    assert_eq!(value["created"], true);
    assert!(value.get("owner").is_none());
    let inbox = c.social(&f.auth(1), now(), &|| true).unwrap();
    assert_eq!(inbox["unreadCount"], 1);
    assert_eq!(inbox["notifications"][0]["recipient"]["userId"], bob);
    assert_eq!(
        c.social(&f.auth(2), now(), &|| true).unwrap()["notifications"],
        json!([])
    );
    c.social_write(&f.auth(0), "read", &json!({"ids":[id]}), now(), &|| true)
        .unwrap();
    assert_eq!(
        c.social(&f.auth(1), now(), &|| true).unwrap()["unreadCount"],
        1
    );
    let reply = uuid::Uuid::new_v4().to_string();
    c.social_write(
        &f.auth(1),
        "comments",
        &json!({"targetId":alice,"requestId":reply,"replyTo":id,"text":"只发到本地临时账号"}),
        now(),
        &|| true,
    )
    .unwrap();
    assert_eq!(
        c.social(&f.auth(0), now(), &|| true).unwrap()["notifications"][0]["replyTo"],
        id
    );
    c.social_write(&f.auth(1), "read", &json!({"all":true}), now(), &|| true)
        .unwrap();
    assert_eq!(
        c.social(&f.auth(1), now(), &|| true).unwrap()["unreadCount"],
        0
    );
    let like = c
        .social_write(
            &f.auth(0),
            "likes",
            &json!({"targetId":bob}),
            now(),
            &|| true,
        )
        .unwrap();
    assert_eq!(like["likes"]["likedToday"], true);
    let board = c.rankings(&f.auth(0), "weekly", now(), &|| true).unwrap();
    assert_eq!(
        board["entries"]
            .as_array()
            .unwrap()
            .iter()
            .find(|v| v["userId"] == bob)
            .unwrap()["likes"]["total"],
        1
    );
    let list = f.info["listId"].as_str().unwrap().to_owned();
    assert_eq!(
        c.list_like(
            &f.auth(0),
            &json!({"listId":list,"liked":true}),
            now(),
            &|| true
        )
        .unwrap()["likes"]["likedToday"],
        true
    );
    assert_eq!(
        c.list_likes(&f.auth(1), &[list.clone()], now(), &|| true)
            .unwrap()["likes"][&list],
        json!({"total":1,"likedToday":false})
    );
    assert_eq!(
        c.list_like(
            &f.auth(0),
            &json!({"listId":list,"liked":false}),
            now(),
            &|| true
        )
        .unwrap()["likes"]["total"],
        0
    );
    let wrong = AuthContext {
        owner: &bob,
        ..f.auth(0)
    };
    assert_eq!(c.social(&wrong, now(), &|| true).unwrap_err().status, 401);
    f.mode("/v1/social", "wrong-recipient");
    assert_eq!(
        c.social(&f.auth(1), now(), &|| true).unwrap_err().status,
        502
    );
    f.mode("/v1/social", "");
    for (action, body) in [
        (
            "comments",
            json!({"targetId":bob,"requestId":uuid::Uuid::new_v4().to_string(),"text":"猫".repeat(501)}),
        ),
        ("read", json!({"all":false})),
        ("likes", json!({"targetId":alice})),
    ] {
        assert_eq!(
            c.social_write(&f.auth(0), action, &body, now(), &|| true)
                .unwrap_err()
                .status,
            400
        );
    }
}

#[test]
fn cache_retains_only_same_owner_endpoint_period_and_beijing_date() {
    let mut f = Fixture::new();
    let c = client();
    f.command(json!({"op":"ac","user":0,"name":"real-old-official","at":"2026-11-08T06:00:00Z"}));
    let daily = c.rankings(&f.auth(0), "daily", now(), &|| true).unwrap();
    assert_eq!(daily["self"]["count"], 0);
    assert_eq!(daily["hasSnapshot"], true);
    let total = c.rankings(&f.auth(0), "total", now(), &|| true).unwrap();
    assert_eq!(total["self"]["count"], 1);
    f.mode("/v1/leaderboard", "fail");
    let later = now() + CDuration::seconds(10);
    let retained = c.rankings(&f.auth(0), "total", later, &|| true).unwrap();
    assert_eq!(retained["self"]["count"], 1);
    assert_eq!(retained["status"], "error");
    assert_eq!(retained["hasSnapshot"], true);
    assert_eq!(
        c.rankings(&f.auth(0), "daily", later, &|| true).unwrap()["self"]["count"],
        0
    );
    assert_eq!(
        c.rankings(&f.auth(0), "weekly", later, &|| true).unwrap()["hasSnapshot"],
        false
    );
    assert_eq!(
        c.rankings(&f.auth(1), "total", later, &|| true).unwrap()["hasSnapshot"],
        false
    );
    let mirror = format!("{}/mirror", f.auth(0).endpoint);
    let auth = AuthContext {
        endpoint: &mirror,
        ..f.auth(0)
    };
    assert_eq!(
        c.rankings(&auth, "total", later, &|| true).unwrap()["hasSnapshot"],
        false
    );
    assert_eq!(
        c.rankings(&f.auth(0), "total", now() + CDuration::hours(10), &|| true)
            .unwrap()["hasSnapshot"],
        false
    );
    f.mode("/v1/leaderboard", "");
    assert_eq!(
        c.rankings(&f.auth(0), "total", later, &|| true).unwrap()["status"],
        "ready"
    );
    f.command(json!({"op":"rotate","user":0}));
    assert_eq!(
        c.rankings(&f.auth(0), "total", later + CDuration::seconds(9), &|| true)
            .unwrap_err()
            .status,
        401
    );
    f.mode("/v1/leaderboard", "fail");
    assert_eq!(
        c.rankings(&f.auth(0), "total", later, &|| true)
            .unwrap_err()
            .status,
        401
    );
}

#[test]
fn avatar_revalidation_hash_signature_removal_and_epoch_are_checked() {
    let mut f = Fixture::new();
    let c = client();
    let bob = f.auth(1).owner.to_owned();
    let hash = f.command(json!({"op":"avatar","user":1,"value":PNG}))["hash"]
        .as_str()
        .unwrap()
        .to_owned();
    assert_eq!(
        c.avatar(&f.auth(0), &bob, &hash, now(), &|| true).unwrap()["avatarData"],
        PNG
    );
    // A second owner cannot satisfy a failed fetch with the first owner's cache.
    f.mode(&format!("/v1/avatars/{bob}"), "fail");
    assert!(c.avatar(&f.auth(2), &bob, &hash, now(), &|| true).is_err());
    f.mode(&format!("/v1/avatars/{bob}"), "avatar-hash");
    assert_eq!(
        c.avatar(
            &f.auth(0),
            &bob,
            &hash,
            now() + CDuration::seconds(14),
            &|| true
        )
        .unwrap()["avatarHash"],
        hash
    );
    assert_eq!(
        c.avatar(
            &f.auth(0),
            &bob,
            &hash,
            now() + CDuration::seconds(15),
            &|| true
        )
        .unwrap_err()
        .code,
        "AVATAR_INTEGRITY"
    );
    f.mode(&format!("/v1/avatars/{bob}"), "avatar-signature");
    assert_eq!(
        c.avatar(
            &f.auth(0),
            &bob,
            &hash,
            now() + CDuration::seconds(16),
            &|| true
        )
        .unwrap_err()
        .status,
        502
    );
    f.mode(&format!("/v1/avatars/{bob}"), "");
    f.command(json!({"op":"avatar","user":1,"value":""}));
    assert_eq!(
        c.avatar(
            &f.auth(0),
            &bob,
            &hash,
            now() + CDuration::seconds(17),
            &|| true
        )
        .unwrap(),
        json!({"avatarData":"","avatarHash":null})
    );
    f.mode(&format!("/v1/avatars/{bob}"), "fail");
    assert!(
        c.avatar(
            &f.auth(0),
            &bob,
            &hash,
            now() + CDuration::seconds(18),
            &|| true
        )
        .is_err()
    );
    assert_eq!(
        c.avatar(&f.auth(0), "not-a-user", &hash, now(), &|| true)
            .unwrap_err()
            .status,
        400
    );
    assert_eq!(
        c.avatar(&f.auth(0), &bob, "not-a-hash", now(), &|| true)
            .unwrap_err()
            .status,
        400
    );
}

#[test]
fn presence_never_treats_polling_as_input_and_actual_idle_exits_server_count() {
    let mut f = Fixture::new();
    let c = client();
    let started = now();
    for offset in [0, 25, 100, 299] {
        let now = started + CDuration::seconds(offset);
        f.command(json!({"op":"time","now":now.timestamp_millis()}));
        let activity = activity_after_input("problem", started, now).unwrap();
        assert_eq!(
            c.presence(&f.auth(0), &json!({"activity":activity}), now, &|| true)
                .unwrap()["count"],
            1
        );
    }
    let idle = started + CDuration::seconds(300);
    f.command(json!({"op":"time","now":idle.timestamp_millis()}));
    let reported = activity_after_input("problem", started, idle).unwrap();
    assert_eq!(reported, "idle");
    assert_eq!(
        c.presence(&f.auth(0), &json!({"activity":reported}), idle, &|| true)
            .unwrap()["count"],
        0
    );
    let board = c.rankings(&f.auth(0), "daily", idle, &|| true).unwrap();
    assert_eq!(board["self"]["online"], false);
    let resumed = idle + CDuration::seconds(1);
    f.command(json!({"op":"time","now":resumed.timestamp_millis()}));
    assert_eq!(
        c.presence(
            &f.auth(0),
            &json!({"activity":activity_after_input("rankings",resumed,resumed).unwrap()}),
            resumed,
            &|| true
        )
        .unwrap()["count"],
        1
    );
    f.mode("/v1/presence", "wrong-owner");
    assert_eq!(
        c.presence(&f.auth(0), &json!({"activity":"online"}), resumed, &|| true)
            .unwrap_err()
            .status,
        502
    );
}

#[test]
fn redirects_late_lease_completions_and_uncertain_writes_never_replay() {
    let mut f = Fixture::new();
    let c = client();
    let bob = f.auth(1).owner.to_owned();
    f.mode("/v1/profile", "redirect");
    assert_eq!(
        c.social(&f.auth(0), now(), &|| true).unwrap_err().code,
        "SHARED_REDIRECT"
    );
    assert_eq!(f.command(json!({"op":"stats"}))["leakRequests"], 0);
    f.mode("/v1/profile", "delay");
    let live = Arc::new(AtomicBool::new(true));
    let stop = live.clone();
    let thread = std::thread::spawn(move || {
        std::thread::sleep(Duration::from_millis(50));
        stop.store(false, Ordering::SeqCst);
    });
    assert_eq!(
        c.social(&f.auth(0), now(), &|| live.load(Ordering::SeqCst))
            .unwrap_err()
            .code,
        "OWNER_CHANGED"
    );
    thread.join().unwrap();
    f.mode("/v1/profile", "wrong-profile");
    assert_eq!(
        c.social(&f.auth(0), now(), &|| true).unwrap_err().status,
        502
    );
    f.mode("/v1/profile", "");
    f.mode("/v1/social/comments", "drop");
    let id = uuid::Uuid::new_v4().to_string();
    let issue = c
        .social_write(
            &f.auth(0),
            "comments",
            &json!({"targetId":bob,"requestId":id,"text":"仅本地断流验证"}),
            now(),
            &|| true,
        )
        .unwrap_err();
    assert!(issue.uncertain);
    let stats = f.command(json!({"op":"stats"}));
    assert_eq!(stats["counts"]["POST /v1/social/comments"], 1);
    assert_eq!(stats["commentCount"], 1);
    f.mode("/v1/social/comments", "");
    // Explicit user retry reuses the persisted request ID and is server-idempotent.
    assert_eq!(
        c.social_write(
            &f.auth(0),
            "comments",
            &json!({"targetId":bob,"requestId":id,"text":"仅本地断流验证"}),
            now(),
            &|| true
        )
        .unwrap()["created"],
        false
    );
    f.mode("/v1/social", "oversize");
    assert_eq!(
        c.social(&f.auth(0), now(), &|| true).unwrap_err().status,
        502
    );
    assert_eq!(
        c.social(
            &AuthContext {
                admin: true,
                ..f.auth(0)
            },
            now(),
            &|| true
        )
        .unwrap_err()
        .status,
        403
    );
}

fn journal(f: &Fixture) -> (TempDir, PersonalStore, Catalogue) {
    let temp = TempDir::new().unwrap();
    let p = PersonalStore::open(&temp.path().join("personal.sqlite3")).unwrap();
    p.db.execute("INSERT INTO ranking_profile(singleton,user_id,nickname,auth_token,endpoint,created_at) VALUES(1,?,'local','',?,'2026-11-09T07:00:00Z')",params![f.auth(0).owner,f.auth(0).endpoint]).unwrap();
    p.db.execute(
        "INSERT INTO drafts VALUES('keep','practice','private draft','old')",
        [],
    )
    .unwrap();
    let db = Connection::open_in_memory().unwrap();
    db.execute_batch("CREATE TABLE aliases(id TEXT PRIMARY KEY,canonical TEXT);CREATE TABLE catalogue(id TEXT PRIMARY KEY,compact TEXT,full BLOB);").unwrap();
    for (id, url) in [
        ("A", "https://codeforces.com/contest/100/problem/A"),
        (
            "alias-A",
            "https://m1.codeforces.com/problemset/problem/100/a",
        ),
        ("B", "https://www.luogu.com.cn/problem/P1001"),
    ] {
        db.execute(
            "INSERT INTO catalogue VALUES(?,?,NULL)",
            params![id, json!({"id":id,"url":url,"difficulty":1200}).to_string()],
        )
        .unwrap();
    }
    for (id, problem, mode, scope, verdict, at) in [
        (
            "good",
            "A",
            "submit",
            "official",
            "AC",
            "2026-11-09T06:00:00Z",
        ),
        (
            "dup",
            "alias-A",
            "submit",
            "official",
            "AC",
            "2026-11-09T06:01:00Z",
        ),
        (
            "sample",
            "B",
            "sample",
            "official",
            "AC",
            "2026-11-09T06:00:00Z",
        ),
        (
            "local",
            "B",
            "submit",
            "local",
            "AC",
            "2026-11-09T06:00:00Z",
        ),
        (
            "wa",
            "B",
            "submit",
            "official",
            "WA",
            "2026-11-09T06:00:00Z",
        ),
    ] {
        p.db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES(?,?,?,?,?,'private code',?,?)",params![id,problem,mode,scope,verdict,at,at]).unwrap();
    }
    (temp, p, Catalogue { db })
}
#[test]
fn real_sync_prepares_only_dated_first_official_ac_then_commits_validated_receipts() {
    let mut f = Fixture::new();
    let c = client();
    let (_temp, p, catalogue) = journal(&f);
    let profile = json!({"publicProgress":{"level":2,"tier":"黑铁","rankTier":null,"rankScore":null,"titles":[],"currentLevelXp":10,"nextLevelXp":100},"avatarData":PNG});
    let plan = c
        .prepare_sync(&f.auth(0), &p, &catalogue, Some(&profile), now(), &|| true)
        .unwrap();
    let incomplete = json!({"publicProgress":{"level":2,"tier":"黑铁","titles":[]}});
    assert_eq!(
        c.prepare_sync(
            &f.auth(0),
            &p,
            &catalogue,
            Some(&incomplete),
            now(),
            &|| true
        )
        .err()
        .unwrap()
        .status,
        400
    );
    assert_eq!(plan.event_count(), 1);
    assert!(plan.publishes_progress());
    let receipt = c.execute_sync(&f.auth(0), &plan, now(), &|| true).unwrap();
    assert_eq!(
        p.rows("SELECT * FROM ranking_receipts", []).unwrap(),
        json!([])
    );
    let result = c.commit_sync(&f.auth(0), &p, receipt, &|| true).unwrap();
    assert_eq!(result["processed"], 1);
    assert_eq!(result["publicProgressPublished"], true);
    assert_eq!(result["status"], "ready");
    assert_eq!(result["boards"]["daily"]["self"]["count"], 1);
    assert_eq!(f.command(json!({"op":"stats"}))["eventCount"], 1);
    assert_eq!(
        p.rows("SELECT code FROM drafts", []).unwrap()[0]["code"],
        "private draft"
    );
    assert_eq!(
        p.rows("SELECT * FROM ranking_receipts", [])
            .unwrap()
            .as_array()
            .unwrap()
            .len(),
        1
    );
    assert_eq!(
        c.prepare_sync(&f.auth(0), &p, &catalogue, None, now(), &|| true)
            .unwrap()
            .event_count(),
        0
    );
    assert_eq!(
        p.rows("SELECT user_id,total_xp FROM ranking_reward_totals", [])
            .unwrap()[0]["user_id"],
        f.auth(0).owner
    );
    assert_eq!(
        c.prepare_sync(&f.auth(1), &p, &catalogue, None, now(), &|| true)
            .err()
            .unwrap()
            .code,
        "OWNER_CHANGED"
    );
    let receipt = c.execute_sync(&f.auth(0), &plan, now(), &|| true).unwrap();
    p.db.execute(
        "UPDATE ranking_profile SET user_id=? WHERE singleton=1",
        [f.auth(1).owner],
    )
    .unwrap();
    assert_eq!(
        c.commit_sync(&f.auth(0), &p, receipt, &|| true)
            .unwrap_err()
            .code,
        "OWNER_CHANGED"
    );
}

#[test]
fn failed_sync_does_not_fabricate_receipts_or_erase_existing_successful_board() {
    let mut f = Fixture::new();
    let c = client();
    let (_temp, p, catalogue) = journal(&f);
    let plan = c
        .prepare_sync(&f.auth(0), &p, &catalogue, None, now(), &|| true)
        .unwrap();
    c.rankings(&f.auth(0), "daily", now(), &|| true).unwrap();
    f.mode("/v1/events", "fail");
    assert!(c.execute_sync(&f.auth(0), &plan, now(), &|| true).is_err());
    assert_eq!(
        p.rows("SELECT * FROM ranking_receipts", []).unwrap(),
        json!([])
    );
    f.mode("/v1/events", "");
    f.mode("/v1/leaderboard", "fail");
    let receipt = c.execute_sync(&f.auth(0), &plan, now(), &|| true).unwrap();
    let result = c.commit_sync(&f.auth(0), &p, receipt, &|| true).unwrap();
    assert_eq!(result["status"], "error");
    assert_eq!(result["boards"]["daily"]["hasSnapshot"], true);
    assert_eq!(result["boards"]["total"]["hasSnapshot"], false);
    assert!(
        p.rows("SELECT last_synced_at FROM ranking_profile", [])
            .unwrap()[0]["last_synced_at"]
            .is_null()
    );
    assert_eq!(
        p.rows("SELECT * FROM ranking_receipts", [])
            .unwrap()
            .as_array()
            .unwrap()
            .len(),
        1
    );
}

#[test]
fn late_board_response_cannot_undo_a_confirmed_heart() {
    let mut f = Fixture::new();
    let c = client();
    let bob = f.auth(1).owner.to_owned();
    c.rankings(&f.auth(0), "daily", now(), &|| true).unwrap();
    f.mode("/v1/leaderboard", "delay-response");
    let before = f.command(json!({"op":"stats"}))["counts"]["GET /v1/leaderboard"]
        .as_u64()
        .unwrap();
    let (owner, endpoint, bearer) = (
        f.auth(0).owner.to_owned(),
        f.auth(0).endpoint.to_owned(),
        f.auth(0).bearer.to_owned(),
    );
    let parallel = c.clone();
    let reading = std::thread::spawn(move || {
        parallel.rankings(
            &AuthContext {
                owner: &owner,
                endpoint: &endpoint,
                bearer: &bearer,
                admin: false,
            },
            "daily",
            now() + CDuration::seconds(9),
            &|| true,
        )
    });
    for _ in 0..100 {
        if f.command(json!({"op":"stats"}))["counts"]["GET /v1/leaderboard"]
            .as_u64()
            .unwrap()
            > before
        {
            break;
        }
        std::thread::sleep(Duration::from_millis(2));
    }
    // The real handler has materialized its old JSON before the receipt commits.
    std::thread::sleep(Duration::from_millis(20));
    c.social_write(
        &f.auth(0),
        "likes",
        &json!({"targetId":bob}),
        now() + CDuration::seconds(9),
        &|| true,
    )
    .unwrap();
    let late = reading.join().unwrap().unwrap();
    assert_eq!(
        late["entries"]
            .as_array()
            .unwrap()
            .iter()
            .find(|e| e["userId"] == bob)
            .unwrap()["likes"]["likedToday"],
        true
    );
    f.mode("/v1/leaderboard", "fail");
    let saved = c
        .rankings(&f.auth(0), "daily", now() + CDuration::seconds(20), &|| {
            true
        })
        .unwrap();
    assert_eq!(saved["hasSnapshot"], true);
    assert_eq!(
        saved["entries"]
            .as_array()
            .unwrap()
            .iter()
            .find(|e| e["userId"] == bob)
            .unwrap()["likes"]["total"],
        1
    );
}

#[test]
fn sync_batches_real_journal_events_and_never_posts_an_empty_batch() {
    let mut f = Fixture::new();
    let c = client();
    let (_temp, p, catalogue) = journal(&f);
    for i in 0..100 {
        let id = format!("extra-{i}");
        let row =
            json!({"id":id,"url":format!("https://qoj.ac/problem/{}",i+1000),"difficulty":null});
        catalogue
            .db
            .execute(
                "INSERT INTO catalogue VALUES(?,?,NULL)",
                params![id, row.to_string()],
            )
            .unwrap();
        p.db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at) VALUES(?,?,'submit','official','AC','private','2026-11-09T06:00:00Z','2026-11-09T06:00:00Z')",params![id,id]).unwrap();
    }
    let plan = c
        .prepare_sync(&f.auth(0), &p, &catalogue, None, now(), &|| true)
        .unwrap();
    assert_eq!(plan.event_count(), 101);
    let receipt = c.execute_sync(&f.auth(0), &plan, now(), &|| true).unwrap();
    c.commit_sync(&f.auth(0), &p, receipt, &|| true).unwrap();
    let stats = f.command(json!({"op":"stats"}));
    assert_eq!(stats["eventCount"], 101);
    assert_eq!(stats["counts"]["POST /v1/events"], 2);
    let empty = c
        .prepare_sync(&f.auth(0), &p, &catalogue, None, now(), &|| true)
        .unwrap();
    assert_eq!(empty.event_count(), 0);
    let receipt = c.execute_sync(&f.auth(0), &empty, now(), &|| true).unwrap();
    c.commit_sync(&f.auth(0), &p, receipt, &|| true).unwrap();
    let stats = f.command(json!({"op":"stats"}));
    assert_eq!(stats["eventCount"], 101);
    assert_eq!(stats["counts"]["POST /v1/events"], 2);
}
