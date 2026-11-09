#![cfg(windows)]
use serde_json::{Value, json};
use std::{path::PathBuf, sync::atomic::AtomicBool};
use tobe_core::native_judge::{self, RunPlan, Toolchains};

fn tools() -> Toolchains {
    Toolchains {
        cpp17: Some(PathBuf::from(
            std::env::var_os("TB_NATIVE_TEST_CPP17").expect("Select the real test C++17 compiler"),
        )),
        python3: Some(PathBuf::from(
            std::env::var_os("TB_NATIVE_TEST_PYTHON").expect("Select the real test interpreter"),
        )),
    }
}
fn problem() -> Value {
    json!({"statementAvailable":true,"localJudgeSupported":true,"limits":{"timeMs":1000,"memoryMb":128},"samples":[{"name":"样例一","input":"2 3\n","output":"5\n"},{"name":"样例二","input":"-4 9\r\n","output":"5\n"}],"nativeSamplePolicy":{"schema":1,"supported":true,"nonunique":false,"caseInsensitive":false,"checkerUnavailable":false}})
}
fn run(problem: &Value, body: Value) -> Value {
    let dir = tempfile::Builder::new()
        .prefix("中文 编译 😀 ")
        .tempdir()
        .unwrap();
    let plan = RunPlan::prepare(problem, &body).unwrap();
    let result =
        native_judge::evaluate(&plan, &tools(), dir.path(), &AtomicBool::new(false)).unwrap();
    assert_eq!(
        std::fs::read_dir(dir.path()).unwrap().count(),
        0,
        "Temporary source, executable and diagnostic files are reclaimed"
    );
    result
}

#[test]
fn real_cpp17_compiles_and_checks_all_samples_in_a_unicode_directory() {
    let result = run(
        &problem(),
        json!({"mode":"run","language":"cpp17","code":"#include <iostream>\n// 中文 😀\nint main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b<<'\\n'; }\n"}),
    );
    assert_eq!(result["verdict"], "SAMPLE_PASS");
    assert_eq!(result["passed"], 2);
    assert_eq!(result["caseResults"].as_array().unwrap().len(), 2);
    assert_eq!(result["scope"], "samples");
    assert!(result["timeMs"].as_f64().unwrap() >= 0.0);
    assert!(result["memoryKb"].as_u64().unwrap() > 0);
}
#[test]
fn custom_python_input_has_no_correctness_or_official_ac_claim() {
    let result = run(
        &problem(),
        json!({"mode":"run","language":"python3","code":"print(input()[::-1])","input":"你好 😀\n","sampleRun":false}),
    );
    assert_eq!(result["verdict"], "RUN_OK");
    assert_eq!(result["output"], "😀 好你\r\n");
    assert_eq!(result["passed"], 0);
    assert!(result["caseResults"][0]["expected"].is_null());
}
#[test]
fn wrong_standard_output_and_unavailable_special_checker_are_distinguished() {
    let body = json!({"mode":"run","language":"python3","code":"print(0)"});
    let result = run(&problem(), body.clone());
    assert_eq!(result["verdict"], "WA");
    assert_eq!(result["caseResults"].as_array().unwrap().len(), 2);
    let mut special = problem();
    special["nativeSamplePolicy"]["nonunique"] = true.into();
    special["nativeSamplePolicy"]["checkerUnavailable"] = true.into();
    let result = run(&special, body);
    assert_eq!(result["verdict"], "ERROR");
    assert_ne!(result["caseResults"][0]["verdict"], "WA");
}
#[test]
fn statement_case_insensitivity_is_respected_without_changing_displayed_output() {
    let mut p = problem();
    p["samples"] = json!([{"input":"","output":"YES\n"}]);
    p["nativeSamplePolicy"]["caseInsensitive"] = true.into();
    let result = run(
        &p,
        json!({"mode":"run","language":"python3","code":"print('yes')"}),
    );
    assert_eq!(result["verdict"], "SAMPLE_PASS");
    assert_eq!(result["caseResults"][0]["actual"], "yes\r\n");
}
#[test]
fn actual_compilers_report_ce_without_running_invalid_source() {
    for (language, code) in [
        ("cpp17", "#error COMPILE_FAILED\n"),
        ("python3", "def broken(:\n    pass\n"),
    ] {
        let result = run(
            &problem(),
            json!({"mode":"run","language":language,"code":code}),
        );
        assert_eq!(result["verdict"], "CE");
        assert!(result["caseResults"].as_array().unwrap().is_empty());
        assert!(!result["stderr"].as_str().unwrap().is_empty());
    }
}
#[test]
fn time_and_output_limits_survive_the_full_syntax_and_case_pipeline() {
    let mut p = problem();
    p["limits"]["timeMs"] = 250.into();
    let timed = run(
        &p,
        json!({"mode":"run","language":"python3","code":"while True: pass"}),
    );
    assert_eq!(timed["verdict"], "TLE");
    p["limits"]["timeMs"] = 3000.into();
    let output = run(
        &p,
        json!({"mode":"run","language":"python3","code":"import sys\nwhile True: sys.stdout.write('x'*65536)"}),
    );
    assert_eq!(output["verdict"], "OLE");
    assert!(output["output"].as_str().unwrap().len() <= 65536);
}
#[test]
fn local_programs_do_not_inherit_application_configuration() {
    let result = run(
        &problem(),
        json!({"mode":"run","language":"python3","sampleRun":false,"input":"","code":"import os\nprint('|'.join(k for k in os.environ if k.startswith('TB_') or k.endswith('_API_KEY') or k.startswith('PK_AI_')))"}),
    );
    assert_eq!(result["verdict"], "RUN_OK");
    assert_eq!(result["output"], "\r\n");
}
#[test]
fn invalid_modes_policies_and_inputs_are_rejected_before_compilation() {
    let body = json!({"mode":"run","language":"python3","code":"print(5)"});
    let mut p = problem();
    p["nativeSamplePolicy"] = Value::Null;
    assert_eq!(
        RunPlan::prepare(&p, &body).err().unwrap().code,
        "RUNNER_POLICY_PENDING"
    );
    p["localJudgeSupported"] = false.into();
    assert_eq!(
        RunPlan::prepare(&p, &body).err().unwrap().code,
        "RUNNER_UNSUPPORTED"
    );
    let mut invalid = body.clone();
    invalid["sampleRun"] = "true".into();
    assert!(RunPlan::prepare(&problem(), &invalid).is_err());
    invalid = body.clone();
    invalid["input"] = "a".repeat(65537).into();
    assert!(RunPlan::prepare(&problem(), &invalid).is_err());
    invalid = body;
    invalid["mode"] = "official".into();
    assert!(RunPlan::prepare(&problem(), &invalid).is_err());
    let mut template = problem();
    template["templatePractice"] = true.into();
    assert_eq!(
        RunPlan::prepare(&template, &invalid).err().unwrap().code,
        "VALIDATION"
    );
    invalid["mode"] = "submit".into();
    assert_eq!(
        RunPlan::prepare(&template, &invalid).err().unwrap().code,
        "MIGRATION_PENDING"
    );
}

#[test]
fn sample_only_submissions_stop_at_the_first_failure_without_claiming_full_coverage() {
    let p = problem();
    let plan = RunPlan::prepare(
        &p,
        &json!({"mode":"submit","code":"print(0)","language":"python3"}),
    )
    .unwrap();
    assert_eq!(plan.scope, "samples");
    assert!(!plan.sample_run);
    assert_eq!(plan.max_output_bytes, 1048576);
    let result = run(
        &p,
        json!({"mode":"submit","code":"print(0)","language":"python3"}),
    );
    assert_eq!(result["verdict"], "WA");
    assert_eq!(result["total"], 2);
    assert_eq!(result["caseResults"].as_array().unwrap().len(), 1);
}

#[test]
fn audited_full_submission_keeps_large_cases_and_large_output_and_private_case_details() {
    let mut p = problem();
    p["id"] = "ABC 478::D".into();
    p["limits"] = json!({"timeMs":15000,"memoryMb":512});
    p["samples"] = json!([{"input":"5 1\n1 3 7\n","output":"1 1 1 0 0\n"}]);
    p["nativeSamplePolicy"]["sourceScope"] = "local".into();
    let programs = include_str!("reviewed_programs.py").replace("\r\n", "\n");
    let source = programs.split("\nif __name__").next().unwrap();
    let code = format!("{source}\nprint(interval_sets(sys.stdin.buffer.read()))\n");
    let body = json!({"mode":"submit","language":"python3","code":code,"sampleRun":true});
    let plan = RunPlan::prepare(&p, &body).unwrap();
    assert_eq!(plan.mode, "submit");
    assert_eq!(plan.scope, "local");
    assert_eq!(plan.cases.len(), 35);
    assert!(!plan.sample_run);
    assert_eq!(plan.max_output_bytes, 2883584);
    assert!(
        plan.cases
            .iter()
            .any(|c| c.expected.as_ref().unwrap().len() == 1400000)
    );
    let result = run(&p, body);
    assert_eq!(result["verdict"], "SAMPLE_PASS", "{result}");
    assert_eq!(result["scope"], "local");
    assert_eq!(result["passed"], 35);
    assert_eq!(result["total"], 35);
    assert!(result["message"].as_str().unwrap().contains("审核测试"));
    for case in result["caseResults"].as_array().unwrap() {
        assert_eq!(case["input"], "");
        assert_eq!(case["actual"], "");
        assert!(case["expected"].is_null());
        assert!(case["name"].as_str().unwrap().starts_with("审核测试"));
    }
}

#[test]
fn reviewed_sample_run_uses_the_real_constructive_checker_without_expanding_hidden_cases() {
    let mut p = problem();
    p["id"] = "ABC 478::E".into();
    p["samples"] = json!([{"input":"3 2\n1 1 2\n0 2 3\n","output":"Yes\n1 2 3\n"}]);
    p["nativeSamplePolicy"]["nonunique"] = true.into();
    p["nativeSamplePolicy"]["checkerUnavailable"] = true.into();
    let body = json!({"mode":"run","language":"python3","code":"print('Yes\\n1 3 3')"});
    let plan = RunPlan::prepare(&p, &body).unwrap();
    assert_eq!(plan.cases.len(), 1);
    assert_eq!(plan.max_output_bytes, 1048576);
    let result = run(&p, body);
    assert_eq!(result["verdict"], "SAMPLE_PASS");
    assert_eq!(result["scope"], "local");
    assert!(
        result["caseResults"][0]["actual"]
            .as_str()
            .unwrap()
            .contains("1 3 3")
    );
}

#[test]
fn local_case_console_is_bounded_by_count_and_total_utf8_bytes() {
    let mut p = problem();
    p["samples"] = json!((0..130).map(|i|json!({"input":format!("{} {i}", "中".repeat(500)),"output":format!("{} {i}", "中".repeat(500))})).collect::<Vec<_>>());
    let result = run(
        &p,
        json!({"mode":"run","language":"python3","code":"import sys;sys.stdout.write(sys.stdin.read())"}),
    );
    assert_eq!(result["verdict"], "SAMPLE_PASS");
    assert_eq!(result["passed"], 130);
    let cases = result["caseResults"].as_array().unwrap();
    assert_eq!(cases.len(), 100);
    let displayed: usize = cases
        .iter()
        .flat_map(|c| ["input", "expected", "actual"].map(|k| c[k].as_str().unwrap().len()))
        .sum();
    assert!(displayed <= 262144);
    assert!(displayed >= 262140);
}
