#![cfg(windows)]
use std::{
    collections::BTreeMap,
    ffi::OsString,
    path::PathBuf,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::Duration,
};
use tempfile::TempDir;
use tobe_core::process_job::{self, CommandSpec, StopReason};

fn spec(directory: &TempDir, source: &str) -> CommandSpec {
    let python = std::env::var_os("TB_NATIVE_TEST_PYTHON")
        .map(PathBuf::from)
        .expect("Supply the explicitly selected test Python executable");
    let mut environment: BTreeMap<OsString, OsString> = std::env::vars_os()
        .filter(|(key, _)| {
            [
                "systemroot",
                "windir",
                "temp",
                "tmp",
                "path",
                "pathext",
                "systemdrive",
                "os",
            ]
            .contains(&key.to_string_lossy().to_lowercase().as_str())
        })
        .collect();
    environment.remove(&OsString::from("PYTHONHOME"));
    environment.remove(&OsString::from("PYTHONPATH"));
    CommandSpec {
        program: python,
        arguments: vec![
            "-I".into(),
            "-X".into(),
            "utf8".into(),
            "-c".into(),
            source.into(),
        ],
        directory: directory.path().to_path_buf(),
        environment,
        input: Vec::new(),
        time_ms: 3000,
        memory_mb: 128,
        output_limit: 65536,
        max_processes: 1,
    }
}

#[test]
fn unicode_arguments_input_environment_and_diagnostics_remain_exact() {
    let dir = TempDir::new().unwrap();
    let mut request = spec(
        &dir,
        "import os,sys; print(sys.argv[1]); print(sys.stdin.read()); print(os.environ['TB_TEST_UNICODE']); print('诊断🦆',file=sys.stderr)",
    );
    request.arguments.push("中文 空格 \\\"引号\\\\🦆".into());
    request.input = "输入🦆".as_bytes().into();
    request
        .environment
        .insert("TB_TEST_UNICODE".into(), "环境🦆".into());
    let output = process_job::run(&request, &AtomicBool::new(false)).unwrap();
    assert_eq!(output.reason, None);
    assert_eq!(output.exit_code, 0);
    assert_eq!(
        output.output.replace("\r\n", "\n"),
        "中文 空格 \\\"引号\\\\🦆\n输入🦆\n环境🦆\n"
    );
    assert_eq!(output.stderr.trim_end(), "诊断🦆");
    assert!(output.memory_kb > 0);
}

#[test]
fn wall_and_cpu_limits_stop_an_infinite_program() {
    let dir = TempDir::new().unwrap();
    let mut request = spec(&dir, "while True: pass");
    request.time_ms = 250;
    let output = process_job::run(&request, &AtomicBool::new(false)).unwrap();
    assert_eq!(output.reason, Some(StopReason::Time));
}

#[test]
fn memory_limit_is_a_kernel_fact_even_when_python_catches_the_failure() {
    let dir = TempDir::new().unwrap();
    let mut request = spec(
        &dir,
        "try:\n x=bytearray(512*1024*1024)\nexcept MemoryError:\n print('caught')",
    );
    request.memory_mb = 32;
    let output = process_job::run(&request, &AtomicBool::new(false)).unwrap();
    assert_eq!(output.reason, Some(StopReason::Memory));
}

#[test]
fn output_is_bounded_and_stderr_cannot_evade_the_limit() {
    let dir = TempDir::new().unwrap();
    let mut request = spec(
        &dir,
        "import sys; sys.stderr.write('x'*1000000); sys.stderr.flush()",
    );
    request.output_limit = 4096;
    let output = process_job::run(&request, &AtomicBool::new(false)).unwrap();
    assert_eq!(output.reason, Some(StopReason::Output));
    assert!(output.stderr.len() <= 4096);
    assert!(output.output.len() <= 4096);
}

#[test]
fn cancellation_stops_the_exact_running_job() {
    let dir = TempDir::new().unwrap();
    let request = spec(&dir, "while True: pass");
    let cancel = Arc::new(AtomicBool::new(false));
    let flag = cancel.clone();
    let worker = std::thread::spawn(move || {
        std::thread::sleep(Duration::from_millis(150));
        flag.store(true, Ordering::Release);
    });
    let output = process_job::run(&request, &cancel).unwrap();
    worker.join().unwrap();
    assert_eq!(output.reason, Some(StopReason::Cancelled));
}

#[test]
fn exit_closes_the_whole_owned_tree_without_leaving_the_child_running() {
    use windows_sys::Win32::{
        Foundation::{CloseHandle, WAIT_OBJECT_0},
        System::Threading::{OpenProcess, PROCESS_SYNCHRONIZE, WaitForSingleObject},
    };
    let dir = TempDir::new().unwrap();
    let mut request = spec(
        &dir,
        "import subprocess,sys; p=subprocess.Popen([sys.executable,'-I','-c','import time; time.sleep(30)']); print(p.pid,flush=True)",
    );
    request.max_processes = 4;
    let output = process_job::run(&request, &AtomicBool::new(false)).unwrap();
    assert_eq!(output.reason, None);
    assert_eq!(output.exit_code, 0);
    let pid = output.output.trim().parse::<u32>().unwrap();
    unsafe {
        let process = OpenProcess(PROCESS_SYNCHRONIZE, 0, pid);
        if !process.is_null() {
            assert_eq!(WaitForSingleObject(process, 5000), WAIT_OBJECT_0);
            CloseHandle(process);
        }
    }
}

#[test]
fn a_pre_cancelled_request_never_starts_its_program() {
    let dir = TempDir::new().unwrap();
    let request = spec(&dir, "raise RuntimeError('must not execute')");
    let output = process_job::run(&request, &AtomicBool::new(true)).unwrap();
    assert_eq!(output.reason, Some(StopReason::Cancelled));
    assert_eq!(output.stderr, "");
}

#[test]
fn invalid_utf8_never_expands_past_the_display_byte_limit() {
    let dir = TempDir::new().unwrap();
    let mut request = spec(
        &dir,
        "import sys; sys.stdout.buffer.write(b'\\xff'*100000); sys.stdout.flush()",
    );
    request.output_limit = 4096;
    let output = process_job::run(&request, &AtomicBool::new(false)).unwrap();
    assert_eq!(output.reason, Some(StopReason::Output));
    assert!(output.output.len() <= 4096);
    assert!(output.output.contains('\u{fffd}'));
}
