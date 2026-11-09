//! Ordinary local runs and submissions using public samples or audited cases.
//! A local result never represents an official AC or grants progress/rewards.
use crate::{
    ApiError,
    api::required_text,
    process_job::{self, CommandSpec, StopReason},
    reviewed_judge::{self, Checker, ProfileInfo},
};
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    ffi::OsString,
    path::{Path, PathBuf},
    sync::atomic::AtomicBool,
    time::Instant,
};

pub const MAX_CODE: usize = 65536;
pub const MAX_INPUT: usize = 65536;
const OUTPUT: usize = 1048576;

#[derive(Clone, Default)]
pub struct Toolchains {
    pub cpp17: Option<PathBuf>,
    pub python3: Option<PathBuf>,
}
impl Toolchains {
    pub fn from_resources(resources: &Path) -> Self {
        let parent = resources.parent().unwrap_or(resources);
        let root = if parent.file_name().is_some_and(|s| s == "backend") {
            parent.parent().unwrap_or(parent)
        } else {
            parent
        };
        let select = |variable: &str, bundled: PathBuf| {
            let path = std::env::var_os(variable)
                .map(PathBuf::from)
                .unwrap_or(bundled);
            (path.is_absolute() && path.is_file()).then_some(path)
        };
        Self {
            cpp17: select("TB_NATIVE_CPP17", root.join("compiler/ucrt64/bin/g++.exe")),
            python3: select(
                "TB_NATIVE_PYTHON3",
                root.join("_internal/python3/python.exe"),
            ),
        }
    }
    pub fn executable(&self, language: &str) -> Result<PathBuf, ApiError> {
        let path = match language {
            "cpp17" => &self.cpp17,
            "python3" => &self.python3,
            _ => return Err(ApiError::bad("不支持的运行语言")),
        };
        path.as_ref()
            .filter(|p| p.is_absolute() && p.is_file())
            .cloned()
            .ok_or_else(|| {
                ApiError::new(
                    503,
                    "RUNNER_UNAVAILABLE",
                    "本机编译器或解释器尚未准备好，代码已保留",
                )
            })
    }
}

#[derive(Clone)]
pub struct Case {
    pub name: String,
    pub input: String,
    pub expected: Option<String>,
}
pub struct RunPlan {
    pub mode: &'static str,
    pub scope: &'static str,
    pub profile: Option<ProfileInfo>,
    pub code: String,
    pub language: String,
    pub input: String,
    pub sample_run: bool,
    pub cases: Vec<Case>,
    pub time_ms: u32,
    pub memory_mb: u32,
    pub nonunique: bool,
    pub case_insensitive: bool,
    pub checker_unavailable: bool,
    pub max_output_bytes: usize,
}
impl RunPlan {
    pub fn prepare(problem: &Value, body: &Value) -> Result<Self, ApiError> {
        let mode = match body.get("mode") {
            None => "submit",
            Some(Value::String(s)) if s == "run" => "run",
            Some(Value::String(s)) if s == "submit" => "submit",
            _ => return Err(ApiError::bad("运行模式无效")),
        };
        let code = required_text(body, "code", MAX_CODE)?.to_owned();
        if code.trim().is_empty() {
            return Err(ApiError::bad("请先输入代码"));
        }
        let language = match body.get("language") {
            None => "cpp17",
            Some(Value::String(s)) => s,
            _ => return Err(ApiError::bad("不支持的运行语言")),
        };
        if !matches!(language, "cpp17" | "python3") {
            return Err(ApiError::bad("不支持的运行语言"));
        }
        let input = match body.get("input") {
            None => "",
            Some(Value::String(s)) if s.len() <= MAX_INPUT => s,
            _ => return Err(ApiError::bad("运行输入不能超过 64 KiB")),
        };
        let sample_option = match body.get("sampleRun") {
            None => input.is_empty(),
            Some(Value::Bool(b)) => *b,
            _ => return Err(ApiError::bad("样例运行选项必须是布尔值")),
        };
        let sample_run = mode == "run" && sample_option;
        if problem["statementAvailable"] == false || problem["localJudgeSupported"] == false {
            return Err(ApiError::new(
                409,
                "RUNNER_UNSUPPORTED",
                "这道题当前不支持本地运行，请查看完整原题",
            ));
        }
        let policy = &problem["nativeSamplePolicy"];
        if problem["templatePractice"] == true
            || policy["sourceScope"] == "template"
            || problem["judge"]["scope"] == "template"
        {
            return Err(ApiError::pending());
        }
        if (sample_run || mode == "submit")
            && (policy["schema"] != 1 || policy["supported"] != true)
        {
            return Err(ApiError::new(
                409,
                "RUNNER_POLICY_PENDING",
                "这道题的原生样例核对资料尚未准备好，可使用自测输入",
            ));
        }
        let profile = reviewed_judge::profile(problem["id"].as_str().unwrap_or(""))?;
        if policy["sourceScope"] == "local" && profile.is_none() {
            return Err(ApiError::pending());
        }
        let mut cases = if sample_run || mode == "submit" {
            let samples = problem["samples"]
                .as_array()
                .filter(|s| !s.is_empty() && s.len() <= 200)
                .ok_or_else(|| ApiError::bad("此题没有完整可用的测试样例，请使用自测输入"))?;
            let mut total = 0usize;
            samples
                .iter()
                .enumerate()
                .map(|(index, sample)| {
                    let input = sample["input"]
                        .as_str()
                        .ok_or_else(|| ApiError::bad("测试样例输入缺失"))?;
                    let expected = sample["output"]
                        .as_str()
                        .ok_or_else(|| ApiError::bad("测试样例输出缺失"))?;
                    total = total
                        .saturating_add(input.len())
                        .saturating_add(expected.len());
                    if total > 16 * 1024 * 1024 || input.len() > 2 * 1024 * 1024 {
                        return Err(ApiError::bad("测试样例超过本机运行大小限制"));
                    }
                    Ok(Case {
                        name: sample["name"]
                            .as_str()
                            .map(String::from)
                            .unwrap_or_else(|| format!("样例 {}", index + 1)),
                        input: input.into(),
                        expected: Some(expected.into()),
                    })
                })
                .collect::<Result<Vec<_>, ApiError>>()?
        } else {
            vec![Case {
                name: "自定义输入".into(),
                input: input.into(),
                expected: None,
            }]
        };
        let mut max_output_bytes = OUTPUT;
        if mode == "submit" {
            if let Some(profile) = profile {
                let suite =
                    reviewed_judge::build(profile.profile_id)?.ok_or_else(ApiError::pending)?;
                max_output_bytes = suite.max_output_bytes;
                cases.extend(suite.cases);
            }
        }
        let integer_limit =
            |key: &str, default: u64, minimum: u64, maximum: u64| -> Result<u32, ApiError> {
                let value = problem["limits"]
                    .get(key)
                    .and_then(Value::as_u64)
                    .unwrap_or(default);
                if !(minimum..=maximum).contains(&value) {
                    return Err(ApiError::bad("原题运行限制超出本机支持范围"));
                }
                Ok(value as u32)
            };
        Ok(Self {
            mode,
            scope: if profile.is_some() {
                "local"
            } else {
                "samples"
            },
            profile,
            code,
            language: language.into(),
            input: input.into(),
            sample_run,
            cases,
            time_ms: integer_limit("timeMs", 1000, 1, 300000)?,
            memory_mb: integer_limit("memoryMb", 256, 16, 4096)?,
            nonunique: policy["nonunique"] == true,
            case_insensitive: policy["caseInsensitive"] == true,
            checker_unavailable: policy["checkerUnavailable"] == true,
            max_output_bytes,
        })
    }
}

fn prefix(text: &str, maximum: usize) -> String {
    let mut end = text.len().min(maximum);
    while !text.is_char_boundary(end) {
        end -= 1;
    }
    text[..end].to_owned()
}
fn environment(executable: &Path, temporary: &Path) -> BTreeMap<OsString, OsString> {
    let mut environment = BTreeMap::new();
    let mut paths = vec![executable.parent().unwrap().to_path_buf()];
    for key in ["SystemRoot", "WINDIR", "SystemDrive", "OS"] {
        if let Some(value) = std::env::var_os(key) {
            environment.insert(key.into(), value);
        }
    }
    if let Some(windows) = std::env::var_os("SystemRoot") {
        paths.push(PathBuf::from(&windows).join("System32"));
        paths.push(windows.into());
    }
    environment.insert(
        "PATH".into(),
        std::env::join_paths(paths).unwrap_or_default(),
    );
    environment.insert("TEMP".into(), temporary.as_os_str().into());
    environment.insert("TMP".into(), temporary.as_os_str().into());
    environment.insert("PYTHONIOENCODING".into(), "utf-8".into());
    environment
}
fn verdict(reason: Option<StopReason>, exit: u32) -> Option<&'static str> {
    match reason {
        Some(StopReason::Time) => Some("TLE"),
        Some(StopReason::Memory) => Some("MLE"),
        Some(StopReason::Output) => Some("OLE"),
        Some(StopReason::Cancelled) => Some("ERROR"),
        None if [0xc0000135, 0xc000007b, 0xc0000142].contains(&exit) => Some("ERROR"),
        None if exit != 0 => Some("RE"),
        None => None,
    }
}
fn initial(total: usize, scope: &str) -> Value {
    json!({"verdict":"ERROR","scope":scope,"timeMs":null,"memoryKb":null,"passed":0,"total":total,"output":"","stderr":"","message":"","caseResults":[]})
}

pub fn evaluate(
    plan: &RunPlan,
    tools: &Toolchains,
    work: &Path,
    cancel: &AtomicBool,
) -> Result<Value, ApiError> {
    let executable = tools.executable(&plan.language)?;
    std::fs::create_dir_all(work)?;
    let temporary = tempfile::Builder::new().prefix("run-").tempdir_in(work)?;
    let directory = temporary.path();
    let environment = environment(&executable, directory);
    let mut result = initial(plan.cases.len(), plan.scope);
    let python = plan.language == "python3";
    std::fs::write(
        directory.join(if python { "main.py" } else { "main.cpp" }),
        plan.code.as_bytes(),
    )?;
    let arguments: Vec<OsString> = if python {
        vec!["-I".into(),"-X".into(),"utf8".into(),"-c".into(),"import sys, traceback\ntry:\n    compile(open('main.py', encoding='utf-8-sig').read(), 'main.py', 'exec')\nexcept SyntaxError:\n    traceback.print_exc()\n    sys.exit(65)\n".into()]
    } else {
        [
            "-O2",
            "-std=c++17",
            "-fdiagnostics-color=never",
            "-finput-charset=UTF-8",
            "-o",
            "main.exe",
            "main.cpp",
        ]
        .into_iter()
        .map(Into::into)
        .collect()
    };
    let checked = process_job::run(
        &CommandSpec {
            program: executable.clone(),
            arguments,
            directory: directory.into(),
            environment: environment.clone(),
            input: vec![],
            time_ms: 30000,
            memory_mb: 1024,
            output_limit: 262144,
            max_processes: if python { 1 } else { 32 },
        },
        cancel,
    )?;
    if checked.reason.is_some() || checked.exit_code != 0 {
        let syntax = checked.reason.is_none()
            && ![0xc0000135, 0xc000007b, 0xc0000142].contains(&checked.exit_code)
            && (!python || checked.exit_code == 65);
        result["verdict"] = json!(if syntax { "CE" } else { "ERROR" });
        result["stderr"] = json!(checked.stderr);
        result["message"] = json!(match checked.reason {
            Some(StopReason::Cancelled) => "评测已取消",
            Some(StopReason::Time) => "编译或语法检查超时",
            Some(StopReason::Memory) => "编译或语法检查超过内存限制",
            Some(StopReason::Output) => "编译诊断输出过多",
            None if python => "Python 3 语法检查未通过",
            None => "C++17 编译未通过",
        });
        return Ok(result);
    }
    let program = if python {
        executable
    } else {
        directory.join("main.exe")
    };
    let arguments: Vec<OsString> = if python {
        ["-I", "-X", "utf8", "-u", "main.py"]
            .into_iter()
            .map(Into::into)
            .collect()
    } else {
        vec![]
    };
    let started = Instant::now();
    let mut failure = None;
    let mut passed = 0;
    let mut max_time = 0.0f64;
    let mut max_memory = 0u64;
    let mut output_bytes = 0usize;
    let mut display_bytes = 262144usize;
    let mut cases = vec![];
    for (index, case) in plan.cases.iter().enumerate() {
        let remaining = 120000u128.saturating_sub(started.elapsed().as_millis());
        if remaining == 0 {
            failure = Some("TLE");
            result["message"] = json!("本次本地评测超过总时间限制");
            break;
        }
        let ran = process_job::run(
            &CommandSpec {
                program: program.clone(),
                arguments: arguments.clone(),
                directory: directory.into(),
                environment: environment.clone(),
                input: case.input.as_bytes().to_vec(),
                time_ms: plan.time_ms.min(remaining as u32),
                memory_mb: plan.memory_mb,
                output_limit: plan.max_output_bytes.saturating_sub(output_bytes).max(1),
                max_processes: 1,
            },
            cancel,
        )?;
        output_bytes = output_bytes
            .saturating_add(ran.output.len())
            .saturating_add(ran.stderr.len());
        max_time = max_time.max(ran.time_ms);
        max_memory = max_memory.max(ran.memory_kb);
        let mut current = verdict(ran.reason, ran.exit_code);
        let mut message = "";
        if current.is_none() {
            if let Some(expected) = &case.expected {
                let (actual, expected) = if plan.case_insensitive {
                    (ran.output.to_lowercase(), expected.to_lowercase())
                } else {
                    (ran.output.clone(), expected.clone())
                };
                let checker = plan.profile.map(|p| p.checker);
                let okay = match checker {
                    Some(checker @ (Checker::Inequality | Checker::Gcd)) => {
                        reviewed_judge::check(checker, &case.input, &ran.output, &expected)
                    }
                    _ => actual.split_whitespace().eq(expected.split_whitespace()),
                };
                if !okay {
                    if checker.is_none() && (plan.nonunique || plan.checker_unavailable) {
                        current = Some("ERROR");
                        message = "原生运行器尚未接入此题的特殊输出校验，请以原站评测为准";
                    } else {
                        current = Some("WA");
                        message = "实际输出与期望不符";
                    }
                }
            }
        }
        if current.is_none() && output_bytes > plan.max_output_bytes {
            current = Some("OLE");
        }
        let current = current.unwrap_or(if case.expected.is_some() {
            "SAMPLE_PASS"
        } else {
            "RUN_OK"
        });
        if current == "SAMPLE_PASS" {
            passed += 1;
        } else if current != "RUN_OK" {
            failure = failure.or(Some(current));
        }
        if ran.reason == Some(StopReason::Cancelled) {
            message = "评测已取消";
        }
        result["output"] = json!(prefix(&ran.output, 65536));
        result["stderr"] = json!(prefix(&ran.stderr, 262144));
        // Keep the old journal/UI bounds, and do not publish audited test data.
        if cases.len() < 100 {
            let public = plan.mode == "run" || plan.scope == "samples";
            let mut clipped = |text: &str| {
                let value = prefix(text, 65536.min(display_bytes));
                display_bytes -= value.len();
                value
            };
            let input = if public {
                clipped(&case.input)
            } else {
                String::new()
            };
            let expected = if public {
                case.expected.as_deref().map(&mut clipped)
            } else {
                None
            };
            let actual = if public {
                clipped(&ran.output)
            } else {
                String::new()
            };
            let name = if public {
                prefix(&case.name, 256)
            } else {
                format!("审核测试 {}", index + 1)
            };
            cases.push(json!({"name":name,"input":input,"expected":expected,"actual":actual,"verdict":current,"timeMs":ran.time_ms,"exitCode":ran.exit_code,"message":message}));
        }
        if !message.is_empty() {
            result["message"] = json!(message);
        }
        if ran.reason.is_some()
            || output_bytes > plan.max_output_bytes
            || plan.mode == "submit" && failure.is_some()
        {
            break;
        }
    }
    result["verdict"] = json!(
        failure.unwrap_or(if plan.sample_run || plan.mode == "submit" {
            "SAMPLE_PASS"
        } else {
            "RUN_OK"
        })
    );
    result["passed"] = json!(passed);
    result["timeMs"] = json!(max_time);
    result["memoryKb"] = json!(max_memory);
    result["caseResults"] = json!(cases);
    if result["message"] == "" {
        result["message"] = json!(if failure.is_some() {
            "部分样例没有通过"
        } else if plan.mode == "submit" && plan.profile.is_some() {
            "全部本地审核测试通过；本地测试不等于 AC，官方结果需提交到原站"
        } else if plan.sample_run || plan.mode == "submit" {
            "全部样例通过；本地样例不等于 AC，官方结果需提交到原站"
        } else {
            "自定义输入运行完成；没有期望输出，不判断正确性"
        });
    }
    Ok(result)
}
