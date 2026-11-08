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
    invalid["mode"] = "submit".into();
    assert_eq!(
        RunPlan::prepare(&problem(), &invalid).err().unwrap().code,
        "MIGRATION_PENDING"
    );
}
