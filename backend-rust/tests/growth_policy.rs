use serde_json::{Value, json};
use std::process::Command;
use tobe_core::growth::policy::*;

fn assignment(challenge: u8) -> Value {
    let mut value = empty_experience("owner-a");
    value["seenVersion"] = json!(1);
    value["choice"] = json!("experienced");
    value["problemId"] = json!(EXPERIENCE_PROBLEMS[0]);
    value["challengeId"] = json!(format!("00000000-0000-4000-8000-{challenge:012}"));
    value["startedAt"] = json!(format!("2026-11-{challenge:02}T00:00:00Z"));
    value
}

#[test]
fn actual_python_policies_match_for_legacy_receipts_merges_and_invalid_inputs() {
    let helper = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/support/growth_policy_oracle.py");
    let python =
        std::env::var("TB_NATIVE_TEST_PYTHON").expect("test-only Python oracle interpreter");
    let result = Command::new(python).arg(helper).output().unwrap();
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let fixture: Value = serde_json::from_slice(&result.stdout).unwrap();
    for item in fixture["experienceValidations"].as_array().unwrap() {
        assert_eq!(
            validate_experience(&item["value"], item["owner"].as_str()).unwrap_or(Value::Null),
            item["expected"],
            "experience {item}"
        );
    }
    for item in fixture["experienceMerges"].as_array().unwrap() {
        assert_eq!(
            merge_experience(&item["left"], &item["right"]).unwrap_or(Value::Null),
            item["expected"],
            "experience merge {item}"
        );
    }
    for item in fixture["starterValidations"].as_array().unwrap() {
        assert_eq!(
            validate_starter(&item["value"], item["owner"].as_str()).unwrap_or(Value::Null),
            item["expected"],
            "starter {item}"
        );
    }
    for item in fixture["starterMerges"].as_array().unwrap() {
        assert_eq!(
            merge_starter(&item["left"], &item["right"]).unwrap_or(Value::Null),
            item["expected"],
            "starter merge {item}"
        );
    }
    for item in fixture["sixReceipts"].as_array().unwrap() {
        assert_eq!(
            six_receipt(&item["value"], item["owner"].as_str().unwrap()).unwrap_or(Value::Null),
            item["expected"],
            "six {item}"
        );
    }
    if let Some(path) = std::env::var_os("TB_GROWTH_POLICY_PROOF") {
        let mut counts = serde_json::Map::new();
        for key in [
            "experienceValidations",
            "experienceMerges",
            "starterValidations",
            "starterMerges",
            "sixReceipts",
        ] {
            counts.insert(key.into(), json!(fixture[key].as_array().unwrap().len()));
        }
        std::fs::write(path,serde_json::to_vec_pretty(&json!({"syntheticOwnersOnly":true,"productionPythonInvocation":false,"pythonSources":fixture["sources"],"matchedOracleCases":counts})).unwrap()).unwrap();
    }
}

#[test]
fn merging_cannot_transplant_other_assignment_attempts_or_add_two_grants() {
    let mut left = assignment(1);
    let mut right = assignment(2);
    let a = format!("submission-{}", "a".repeat(32));
    let b = format!("submission-{}", "b".repeat(32));
    left["attempts"] = json!([a]);
    left["passedAt"] = json!("2026-11-01T00:01:00Z");
    left["submissionId"] = json!(a);
    left["awardedXp"] = json!(400);
    right["attempts"] = json!([b]);
    right["passedAt"] = json!("2026-11-02T00:01:00Z");
    right["submissionId"] = json!(b);
    right["awardedXp"] = json!(100);
    let merged = merge_experience(&left, &right).unwrap();
    assert_eq!(merged["challengeId"], right["challengeId"]);
    assert_eq!(merged["attempts"], json!([b]));
    assert_eq!(merged["awardedXp"], 400);
    assert_eq!(merge_experience(&merged, &left).unwrap()["awardedXp"], 400);
    let mut foreign = right.clone();
    foreign["owner"] = json!("another-account");
    assert!(merge_experience(&left, &foreign).is_none());
    assert!(validate_experience(&left, Some("another-account")).is_none());
}

#[test]
fn capped_attempt_merge_keeps_the_actual_winning_pass_receipt() {
    let mut left = assignment(1);
    let mut right = left.clone();
    let first = format!("submission-{:032x}", 0);
    left["attempts"] = json!(
        (0..128)
            .map(|i| format!("submission-{i:032x}"))
            .collect::<Vec<_>>()
    );
    right["attempts"] = json!(
        (128..256)
            .map(|i| format!("submission-{i:032x}"))
            .collect::<Vec<_>>()
    );
    left["passedAt"] = json!("2026-11-01T00:01:00Z");
    left["submissionId"] = json!(first);
    left["awardedXp"] = json!(50);
    let merged = merge_experience(&left, &right).unwrap();
    assert_eq!(merged["attempts"].as_array().unwrap().len(), 128);
    assert_eq!(
        merged["attempts"].as_array().unwrap().last().unwrap(),
        &json!(first)
    );
    assert!(validate_experience(&merged, Some("owner-a")).is_some());
    assert_eq!(left["attempts"].as_array().unwrap().len(), 128);
}

#[test]
fn six_receipts_and_starter_curves_keep_owner_and_original_metadata() {
    let receipt =
        json!({"version":1,"owner":"owner-a","xp":1375,"awardedAt":"2026-11-09","original":"kept"});
    assert_eq!(
        six_receipt(&json!(receipt.to_string()), "owner-a"),
        Some(receipt.clone())
    );
    assert!(six_receipt(&receipt, "owner-b").is_none());
    let a = json!({"version":1,"owner":"owner-a","selectedAt":"2026-11-01T00:00:00Z"});
    let b = json!({"version":1,"owner":"owner-a","selectedAt":"2026-11-09T00:00:00Z"});
    assert_eq!(merge_starter(&a, &b), Some(a.clone()));
    assert_eq!(merge_starter(&b, &a), Some(a));
    let mut wrong = b;
    wrong["version"] = json!(true);
    assert!(validate_starter(&wrong, None).is_none());
}
