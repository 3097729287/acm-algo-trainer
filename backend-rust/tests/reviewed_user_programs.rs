//! Explicit two-language program execution, independent of the authoring oracle.
#![cfg(windows)]
use regex::Regex;
use serde::Deserialize;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    ffi::OsString,
    io::BufReader,
    path::{Path, PathBuf},
    sync::atomic::AtomicBool,
    time::Instant,
};
use tobe_core::{
    process_job::{self, CommandSpec},
    reviewed_judge::{self, Checker},
};

#[derive(Deserialize)]
struct ArchivedSolution {
    problem_id: String,
    markdown: String,
}
fn sha(value: &[u8]) -> String {
    format!("{:x}", Sha256::digest(value))
}
fn environment(executable: &Path, directory: &Path) -> BTreeMap<OsString, OsString> {
    let mut result = BTreeMap::new();
    let mut paths = vec![executable.parent().unwrap().to_owned()];
    for key in ["SystemRoot", "WINDIR", "SystemDrive", "OS"] {
        if let Some(value) = std::env::var_os(key) {
            result.insert(key.into(), value);
        }
    }
    if let Some(windows) = std::env::var_os("SystemRoot") {
        paths.push(PathBuf::from(&windows).join("System32"));
        paths.push(windows.into());
    }
    result.insert("PATH".into(), std::env::join_paths(paths).unwrap());
    result.insert("TEMP".into(), directory.as_os_str().into());
    result.insert("TMP".into(), directory.as_os_str().into());
    result.insert("PYTHONIOENCODING".into(), "utf-8".into());
    result
}
fn execute(language: &str) {
    let repository = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_owned();
    let owned = repository.join(".backups/native-reviewed-programs");
    std::fs::create_dir_all(&owned).unwrap();
    assert!(
        owned
            .canonicalize()
            .unwrap()
            .starts_with(repository.canonicalize().unwrap())
    );
    assert!(!owned.symlink_metadata().unwrap().is_symlink());
    let tools = PathBuf::from(
        std::env::var_os(if language == "cpp17" {
            "TB_NATIVE_TEST_CPP17"
        } else {
            "TB_NATIVE_TEST_PYTHON"
        })
        .expect("Select the real user-program toolchain"),
    );
    assert!(tools.is_absolute() && tools.is_file());
    let manifest: Value =
        serde_json::from_str(include_str!("../resources/reviewed_cases/manifest.json")).unwrap();
    let cpp = if language == "cpp17" {
        // Public source text is read by exact original problem ID. Never load
        // archive Python, generated answers or a private SQLite database.
        let records: Vec<ArchivedSolution> = serde_json::from_reader(BufReader::new(
            std::fs::File::open(repository.join("data/library/solutions.json")).unwrap(),
        ))
        .unwrap();
        let fence = Regex::new(r"(?s)```(?:cpp|c\+\+)\s*\n(.*?)```").unwrap();
        let main = Regex::new(r"\bmain\s*\(").unwrap();
        let wanted: Vec<&str> = manifest["profiles"]
            .as_array()
            .unwrap()
            .iter()
            .map(|p| p["profile_id"].as_str().unwrap())
            .collect();
        records
            .into_iter()
            .filter(|r| wanted.contains(&r.problem_id.as_str()))
            .map(|r| {
                let source = fence
                    .captures_iter(&r.markdown)
                    .map(|c| c[1].to_owned())
                    .filter(|s| main.is_match(s))
                    .last()
                    .expect("The exact public ID has a main program");
                (r.problem_id, source)
            })
            .collect::<BTreeMap<_, _>>()
    } else {
        BTreeMap::new()
    };
    let python_source = include_str!("reviewed_programs.py");
    let started = Instant::now();
    let mut profiles = vec![];
    let mut total = 0;
    let mut alternate = 0;
    for record in manifest["profiles"].as_array().unwrap() {
        let id = record["profile_id"].as_str().unwrap();
        let suite = reviewed_judge::build(id).unwrap().unwrap();
        let directory = tempfile::Builder::new()
            .prefix("user-program-")
            .tempdir_in(&owned)
            .unwrap();
        assert!(
            directory
                .path()
                .canonicalize()
                .unwrap()
                .starts_with(owned.canonicalize().unwrap())
        );
        let source = if language == "cpp17" {
            cpp.get(id).unwrap().as_str()
        } else {
            python_source
        };
        std::fs::write(
            directory.path().join(if language == "cpp17" {
                "main.cpp"
            } else {
                "main.py"
            }),
            source,
        )
        .unwrap();
        if language == "cpp17" {
            let compile = process_job::run(
                &CommandSpec {
                    program: tools.clone(),
                    arguments: [
                        "-O2",
                        "-std=c++17",
                        "-finput-charset=UTF-8",
                        "-fdiagnostics-color=never",
                        "-o",
                        "main.exe",
                        "main.cpp",
                    ]
                    .into_iter()
                    .map(Into::into)
                    .collect(),
                    directory: directory.path().to_owned(),
                    environment: environment(&tools, directory.path()),
                    input: vec![],
                    time_ms: 30000,
                    memory_mb: 1024,
                    output_limit: 262144,
                    max_processes: 32,
                },
                &AtomicBool::new(false),
            )
            .unwrap();
            assert!(
                compile.reason.is_none() && compile.exit_code == 0,
                "{id}: {}",
                compile.stderr
            );
        }
        let executable = if language == "cpp17" {
            directory.path().join("main.exe")
        } else {
            tools.clone()
        };
        let arguments: Vec<OsString> = if language == "cpp17" {
            vec![]
        } else {
            ["-I", "-X", "utf8", "-u", "main.py", id]
                .into_iter()
                .map(Into::into)
                .collect()
        };
        let mut outputs = 0usize;
        let mut input_bytes = 0usize;
        let mut maximum_time = 0.0f64;
        let mut maximum_memory = 0u64;
        let mut profile_alternates = 0;
        for case in &suite.cases {
            let ran = process_job::run(
                &CommandSpec {
                    program: executable.clone(),
                    arguments: arguments.clone(),
                    directory: directory.path().to_owned(),
                    environment: environment(&tools, directory.path()),
                    input: case.input.as_bytes().to_vec(),
                    // A functional parity driver, not a claim that every Python
                    // program meets the original OJ's language-specific deadline.
                    time_ms: 60000,
                    memory_mb: 1024,
                    output_limit: suite.max_output_bytes,
                    max_processes: 1,
                },
                &AtomicBool::new(false),
            )
            .unwrap();
            assert!(
                ran.reason.is_none() && ran.exit_code == 0,
                "{language} {id} / {}: {:?} exit{} {}",
                case.name,
                ran.reason,
                ran.exit_code,
                ran.stderr
            );
            assert!(
                reviewed_judge::check(
                    suite.checker,
                    &case.input,
                    &ran.output,
                    case.expected.as_ref().unwrap()
                ),
                "{language} {id} / {}: actual={} expected={}",
                case.name,
                ran.output.chars().take(200).collect::<String>(),
                case.expected
                    .as_ref()
                    .unwrap()
                    .chars()
                    .take(200)
                    .collect::<String>()
            );
            if suite.checker != Checker::Exact
                && !reviewed_judge::check(
                    Checker::Exact,
                    &case.input,
                    &ran.output,
                    case.expected.as_ref().unwrap(),
                )
            {
                profile_alternates += 1;
            }
            outputs += ran.output.len() + ran.stderr.len();
            input_bytes += case.input.len();
            maximum_time = maximum_time.max(ran.time_ms);
            maximum_memory = maximum_memory.max(ran.memory_kb);
            total += 1;
        }
        assert!(
            outputs <= suite.max_output_bytes,
            "{id}: real aggregate output exceeds its reviewed budget"
        );
        alternate += profile_alternates;
        profiles.push(json!({"id":id,"casesPassed":suite.cases.len(),"programSha256":sha(source.as_bytes()),
            "fullInputBytes":input_bytes,"fullOutputAndStderrBytes":outputs,"maxChildTimeMs":maximum_time,
            "maxChildMemoryKb":maximum_memory,"acceptedAlternativeOutputs":profile_alternates,
            "aggregateOutputBudgetBytes":suite.max_output_bytes}));
        eprintln!(
            "{language} {id}: {}/{} complete cases passed",
            suite.cases.len(),
            suite.cases.len()
        );
    }
    assert_eq!(profiles.len(), 15);
    assert_eq!(total, 314);
    assert!(
        alternate > 0,
        "Constructive results are verified semantically, never compared only to frozen text"
    );
    let result = json!({"schema":1,"language":language,"allProfiles":15,"fullCasesPassed":total,
        "fullLargeCasesIncluded":true,"acceptedAlternativeOutputs":alternate,
        "sourceSha256":reviewed_judge::SOURCE_SHA256,"seconds":started.elapsed().as_secs_f64(),
        "programSource":if language=="cpp17" {"existing public solution markdown by exact original ID"}else{"independent efficient Python user programs; no old backend/generator imports"},
        "nativeRustProcessJobsUsed":true,"pureRustConstructiveCheckersUsed":true,
        "functionalChildTimeLimitMs":60000,"functionalChildMemoryLimitMb":1024,
        "originalOjDeadlineOrFullApplicationPerformanceClaimed":false,"officialSubmissions":0,
        "realAccountsOrPrivateDatabasesOpened":false,"rewardsOrMasteryWritten":false,"profiles":profiles});
    std::fs::write(
        owned.join(format!("{language}.json")),
        serde_json::to_vec_pretty(&result).unwrap(),
    )
    .unwrap();
}

#[test]
#[ignore = "Explicit real toolchains and all large public cases; invoke with --ignored"]
fn all_archived_cpp_programs_pass_every_frozen_case_using_rust_checkers() {
    execute("cpp17");
}

#[test]
#[ignore = "Explicit real toolchains and all large public cases; invoke with --ignored"]
fn independent_python_programs_pass_every_frozen_case_using_rust_checkers() {
    execute("python3");
}
