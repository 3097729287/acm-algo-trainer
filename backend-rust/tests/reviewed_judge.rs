use serde_json::Value;
use tobe_core::reviewed_judge::{self, Checker};

#[test]
fn every_fixed_profile_replays_the_complete_frozen_oracle_inventory() {
    let manifest: Value =
        serde_json::from_str(include_str!("../resources/reviewed_cases/manifest.json")).unwrap();
    let policy: Value = serde_json::from_str(include_str!(
        "../../backend/resources/native-reviewed-profiles.json"
    ))
    .unwrap();
    assert_eq!(manifest["source_sha256"], policy["sourceSha256"]);
    assert_eq!(policy["ids"].as_array().unwrap().len(), 15);
    let mut total = 0;
    let mut largest_input = 0;
    let mut largest_expected = 0;
    for identity in policy["ids"].as_array().unwrap() {
        let id = identity.as_str().unwrap();
        let suite = reviewed_judge::build(id).unwrap().unwrap();
        let record = manifest["profiles"]
            .as_array()
            .unwrap()
            .iter()
            .find(|v| v["profile_id"] == id)
            .unwrap();
        assert_eq!(suite.profile_id, id);
        assert!(!suite.coverage.is_empty());
        assert_eq!(suite.source_sha256, policy["sourceSha256"]);
        assert_eq!(
            suite.cases.len(),
            record["case_count"].as_u64().unwrap() as usize
        );
        assert_eq!(
            suite.max_output_bytes,
            record["max_output_bytes"].as_u64().unwrap() as usize
        );
        for case in &suite.cases {
            let expected = case.expected.as_ref().unwrap();
            largest_input = largest_input.max(case.input.len());
            largest_expected = largest_expected.max(expected.len());
            if suite.checker != Checker::Inequality || expected.trim() == "No" {
                assert!(
                    reviewed_judge::check(suite.checker, &case.input, expected, expected),
                    "{id}: {}",
                    case.name
                );
            }
        }
        total += suite.cases.len();
    }
    assert_eq!(total, 314);
    assert_eq!(largest_input, 32_170_013);
    assert_eq!(largest_expected, 1_400_000);
}

#[test]
fn titles_tags_suffixes_urls_and_nearby_problem_ids_never_enable_a_profile() {
    for id in [
        "",
        "478 D",
        "ABC 478::F",
        "ABC 478::D copy",
        "https://atcoder.jp/contests/abc478/tasks/abc478_d",
        "Div.3 1003::C1",
        "入门赛 49::E",
        "枚举",
        "周赛 164::C ",
    ] {
        assert!(reviewed_judge::build(id).unwrap().is_none(), "{id}");
    }
}

#[test]
fn exact_checker_uses_the_existing_whitespace_rule_without_folding_case() {
    assert!(reviewed_judge::check(
        Checker::Exact,
        "",
        " 7\r\n8\t",
        "7 8"
    ));
    assert!(!reviewed_judge::check(Checker::Exact, "", "yes", "Yes"));
    assert!(!reviewed_judge::check(Checker::Exact, "", "7 8 9", "7 8"));
}

#[test]
fn inequalities_accept_alternative_assignments_and_reject_invalid_decisions() {
    let input = "3 2\n1 1 2\n0 2 3\n";
    assert!(reviewed_judge::check(
        Checker::Inequality,
        input,
        "Yes\n1 3 3",
        "Yes"
    ));
    assert!(reviewed_judge::check(
        Checker::Inequality,
        input,
        "Yes\n1 2 3",
        "Yes"
    ));
    for answer in [
        "No",
        "YES 1 2 3",
        "Yes 1 2 4",
        "Yes 3 1 1",
        "Yes 0 2 3",
        "Yes -1 2 3",
        "Yes 1 2",
        "Yes 1 2 3 1",
        "Yes 340282366920938463463374607431768211456 2 3",
    ] {
        assert!(
            !reviewed_judge::check(Checker::Inequality, input, answer, "Yes"),
            "{answer}"
        );
    }
    assert!(reviewed_judge::check(
        Checker::Inequality,
        "1 1\n1 1 1",
        "No",
        "No"
    ));
    assert!(!reviewed_judge::check(
        Checker::Inequality,
        "1 1\n1 1 1",
        "No extra",
        "No"
    ));
    for broken in [
        "",
        "0 0",
        "3 1\n1 4 1",
        "3 1\n2 1 2",
        "3 1\n1 1",
        "3 0 extra",
        "999999999999999999999999 0",
    ] {
        assert!(!reviewed_judge::check(
            Checker::Inequality,
            broken,
            "No",
            "No"
        ));
    }
}

#[test]
fn gcd_constructor_checks_optimality_product_bounds_and_all_output_tokens() {
    assert!(reviewed_judge::check(
        Checker::Gcd,
        "2\n6 10\n2 8",
        "6 10\n4 4",
        ""
    ));
    assert!(reviewed_judge::check(
        Checker::Gcd,
        "2\n6 10\n2 8",
        "30 2\n4 4",
        ""
    ));
    assert!(reviewed_judge::check(
        Checker::Gcd,
        "1\n1000000000 1000000000",
        "1000000000 1000000000",
        ""
    ));
    for answer in [
        "3 20",
        "0 60",
        "-2 -30",
        "2 31",
        "2",
        "2 30 1",
        "1000000000000000001 1",
        "340282366920938463463374607431768211455 2",
        "2 nan",
    ] {
        assert!(
            !reviewed_judge::check(Checker::Gcd, "1\n6 10", answer, ""),
            "{answer}"
        );
    }
    for broken in [
        "",
        "-1",
        "1\n0 10",
        "1\n6",
        "1\n6 10 7",
        "1\n1000000000000000000 1",
    ] {
        assert!(!reviewed_judge::check(Checker::Gcd, broken, "2 30", ""));
    }
}
