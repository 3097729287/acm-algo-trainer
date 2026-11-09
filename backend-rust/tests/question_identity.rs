use sha2::{Digest, Sha256};
use tobe_core::identity::{self, QUESTION_PAIR_KEY, QUESTION_PAIR_KEYS};

fn sha(value: &str) -> String {
    format!("{:x}", Sha256::digest(value.as_bytes()))
}

#[test]
fn reviewed_question_identity_does_not_change_original_navigation() {
    let lg = "https://www.luogu.com.cn/problem/P10865";
    let cf = "https://codeforces.com/gym/105139/problem/H";
    assert_ne!(identity::canonical_url(lg), identity::canonical_url(cf));
    assert_eq!(identity::canonical_url(cf).unwrap(), QUESTION_PAIR_KEYS[1]);
    for value in [
        lg,
        cf,
        "https://m1.codeforces.com/gym/105139/problem/h/?locale=zh#note",
        "luogu-training-P10865",
        "remote:codeforces:105139::H",
        QUESTION_PAIR_KEYS[0],
        QUESTION_PAIR_KEYS[1],
    ] {
        assert_eq!(
            identity::question_key(value).as_deref(),
            Some(QUESTION_PAIR_KEY),
            "{value}"
        );
        assert_eq!(identity::question_alias_keys(value), QUESTION_PAIR_KEYS);
    }
    for value in QUESTION_PAIR_KEYS {
        assert_eq!(
            identity::question_key(&sha(value)).as_deref(),
            Some(QUESTION_PAIR_KEY)
        );
    }
}

#[test]
fn nearby_titles_problem_numbers_hosts_and_arbitrary_full_url_hashes_do_not_merge() {
    for value in [
        "https://codeforces.com/gym/105139/problem/G",
        "https://codeforces.com/gym/105139/problem/H1",
        "https://codeforces.com/contest/105139/problem/H",
        "https://www.luogu.com.cn/problem/P10864",
        "https://codeforces.example/gym/105139/problem/H",
        "remote:codeforces:105139::H1",
        "luogu-training-P108650",
        "P10865",
        "Taking Bus",
    ] {
        assert_ne!(
            identity::question_key(value).as_deref(),
            Some(QUESTION_PAIR_KEY),
            "{value}"
        );
    }
    for url in [
        "https://www.luogu.com.cn/problem/P10865",
        "https://codeforces.com/gym/105139/problem/H",
    ] {
        assert_eq!(
            identity::question_key(&sha(url)),
            None,
            "Full-URL replay hashes have a separate compatibility rule"
        );
    }
}

#[test]
fn old_canonical_and_full_url_replay_reward_hashes_match_only_the_audited_pair() {
    let expected = sha(QUESTION_PAIR_KEY);
    for value in [
        QUESTION_PAIR_KEYS[0],
        QUESTION_PAIR_KEYS[1],
        "https://www.luogu.com.cn/problem/P10865",
        "https://codeforces.com/gym/105139/problem/H",
    ] {
        assert_eq!(identity::replay_problem_key_identity(&sha(value)), expected);
    }
    for value in [
        "https://www.luogu.com.cn/problem/P10864",
        "http://www.luogu.com.cn/problem/P10865",
        "https://codeforces.com/gym/105139/problem/G",
    ] {
        let original = sha(value);
        assert_eq!(identity::replay_problem_key_identity(&original), original);
    }
}

#[test]
fn real_python_identity_rules_agree_for_urls_ids_hashes_and_nearby_non_aliases() {
    use std::{
        io::Write,
        process::{Command, Stdio},
    };
    let mut inputs = vec![
        "https://www.luogu.com.cn/problem/P10865".to_owned(),
        "https://m1.codeforces.com/gym/105139/problem/h/?locale=zh#note".into(),
        "luogu-training-P10865".into(),
        "remote:codeforces:105139::H".into(),
        "luogu.com.cn/problem/P10865".into(),
        "codeforces.com/gym/105139/problem/H".into(),
        "https://codeforces.com/contest/105139/problem/H".into(),
        "https://luogu.com.cn/problem/P10864".into(),
        "Taking Bus".into(),
        "".into(),
    ];
    inputs.extend(QUESTION_PAIR_KEYS.iter().map(|key| sha(key)));
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let script = "import sys,json\nfrom pathlib import Path\np=Path.cwd();sys.path[:0]=[str(p/'backend'),str(p/'backend/common')]\nimport question_identity as q\nprint(json.dumps([{'key':q.question_key(x),'aliases':q.question_alias_keys(x)} for x in json.load(sys.stdin)],ensure_ascii=False))";
    let mut child = Command::new(std::env::var_os("TB_NATIVE_TEST_PYTHON").unwrap())
        .args(["-I", "-X", "utf8", "-c", script])
        .current_dir(root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(&serde_json::to_vec(&inputs).unwrap())
        .unwrap();
    let result = child.wait_with_output().unwrap();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let expected: serde_json::Value = serde_json::from_slice(&result.stdout).unwrap();
    for (value, old) in inputs.iter().zip(expected.as_array().unwrap()) {
        assert_eq!(
            serde_json::json!(identity::question_key(value)),
            old["key"],
            "{value}"
        );
        assert_eq!(
            serde_json::json!(identity::question_alias_keys(value)),
            old["aliases"],
            "{value}"
        );
    }
}

#[test]
fn actual_node_replay_hash_compatibility_matches_rust_without_rewriting_unknown_hashes() {
    use std::{
        io::Write,
        process::{Command, Stdio},
    };
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let module =
        url::Url::from_file_path(root.join("server/leaderboard/src/question-identities.mjs"))
            .unwrap();
    let script = format!(
        "import{{readFileSync}}from'node:fs';import{{replayProblemKeyIdentity}}from{};console.log(JSON.stringify(JSON.parse(readFileSync(0,'utf8')).map(replayProblemKeyIdentity)));",
        serde_json::to_string(module.as_str()).unwrap()
    );
    let inputs = [
        QUESTION_PAIR_KEYS[0],
        QUESTION_PAIR_KEYS[1],
        "https://www.luogu.com.cn/problem/P10865",
        "https://codeforces.com/gym/105139/problem/H",
        "https://codeforces.com/gym/105139/problem/G",
        "http://www.luogu.com.cn/problem/P10865",
    ]
    .map(sha);
    let mut child = Command::new("node")
        .args(["--input-type=module", "-e", &script])
        .current_dir(root)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .take()
        .unwrap()
        .write_all(&serde_json::to_vec(&inputs).unwrap())
        .unwrap();
    let result = child.wait_with_output().unwrap();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let expected: Vec<String> = serde_json::from_slice(&result.stdout).unwrap();
    assert_eq!(
        inputs
            .iter()
            .map(|value| identity::replay_problem_key_identity(value))
            .collect::<Vec<_>>(),
        expected
    );
}
