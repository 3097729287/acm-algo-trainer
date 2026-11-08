//! Bounded, hidden Windows child processes. This is resource isolation, not a
//! filesystem sandbox. No shell or legacy backend is invoked by this module.
use crate::ApiError;
use std::{collections::BTreeMap, ffi::OsString, path::PathBuf, sync::atomic::AtomicBool};

pub struct CommandSpec {
    pub program: PathBuf,
    pub arguments: Vec<OsString>,
    pub directory: PathBuf,
    pub environment: BTreeMap<OsString, OsString>,
    pub input: Vec<u8>,
    pub time_ms: u32,
    pub memory_mb: u32,
    pub output_limit: usize,
    pub max_processes: u32,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum StopReason {
    Time,
    Memory,
    Output,
    Cancelled,
}

#[derive(Debug)]
pub struct RunOutput {
    pub reason: Option<StopReason>,
    pub exit_code: u32,
    pub output: String,
    pub stderr: String,
    pub time_ms: f64,
    pub memory_kb: u64,
}

pub fn run(spec: &CommandSpec, cancel: &AtomicBool) -> Result<RunOutput, ApiError> {
    if !spec.program.is_absolute()
        || !spec.program.is_file()
        || !spec.directory.is_absolute()
        || !spec.directory.is_dir()
        || !(1..=300000).contains(&spec.time_ms)
        || !(16..=4096).contains(&spec.memory_mb)
        || !(1..=32 * 1024 * 1024).contains(&spec.output_limit)
        || !(1..=32).contains(&spec.max_processes)
        || spec.input.len() > 32 * 1024 * 1024
    {
        return Err(ApiError::bad("运行器参数或工具路径无效"));
    }
    #[cfg(windows)]
    {
        win::run(spec, cancel)
    }
    #[cfg(not(windows))]
    {
        let _ = cancel;
        Err(ApiError::new(
            503,
            "RUNNER_UNAVAILABLE",
            "此运行器需要 Windows 进程资源限制",
        ))
    }
}

#[cfg(windows)]
mod win {
    use super::*;
    use std::{
        ffi::{OsStr, c_void},
        io::{Read, Write},
        mem::{size_of, size_of_val},
        os::windows::ffi::OsStrExt,
        ptr::{null, null_mut},
        sync::{Mutex, atomic::Ordering},
        time::{Duration, Instant},
    };
    use windows_sys::Win32::{
        Foundation::{
            CloseHandle, FILETIME, HANDLE, INVALID_HANDLE_VALUE, SetHandleInformation,
            WAIT_OBJECT_0,
        },
        Security::SECURITY_ATTRIBUTES,
        Storage::FileSystem::{
            CREATE_ALWAYS, CreateFileW, FILE_ATTRIBUTE_NORMAL, FILE_SHARE_DELETE, FILE_SHARE_READ,
            FILE_SHARE_WRITE, OPEN_EXISTING,
        },
        System::{
            Diagnostics::Debug::{GetErrorMode, SetErrorMode},
            IO::{CreateIoCompletionPort, GetQueuedCompletionStatus},
            JobObjects::*,
            SystemServices::{
                JOB_OBJECT_MSG_END_OF_JOB_TIME, JOB_OBJECT_MSG_END_OF_PROCESS_TIME,
                JOB_OBJECT_MSG_JOB_MEMORY_LIMIT, JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT,
            },
            Threading::*,
        },
    };
    static SPAWN: Mutex<()> = Mutex::new(());

    struct Handle(HANDLE);
    impl Handle {
        fn new(value: HANDLE, operation: &str) -> Result<Self, ApiError> {
            if value.is_null() || value == INVALID_HANDLE_VALUE {
                Err(os_error(operation))
            } else {
                Ok(Self(value))
            }
        }
    }
    impl Drop for Handle {
        fn drop(&mut self) {
            unsafe {
                CloseHandle(self.0);
            }
        }
    }
    struct Process {
        process: Handle,
        thread: Handle,
    }
    impl Drop for Process {
        fn drop(&mut self) {
            unsafe {
                // Also covers failure to resume a newly created suspended process.
                if WaitForSingleObject(self.process.0, 0) != WAIT_OBJECT_0 {
                    TerminateProcess(self.process.0, 1);
                    WaitForSingleObject(self.process.0, 5000);
                }
            }
        }
    }
    struct Attributes {
        storage: Vec<usize>,
    }
    impl Attributes {
        fn new() -> Result<Self, ApiError> {
            unsafe {
                let mut bytes = 0;
                InitializeProcThreadAttributeList(null_mut(), 2, 0, &mut bytes);
                if bytes == 0 || bytes > 65536 {
                    return Err(os_error("初始化进程参数"));
                }
                let mut storage = vec![0; bytes.div_ceil(size_of::<usize>())];
                check(
                    InitializeProcThreadAttributeList(
                        storage.as_mut_ptr().cast(),
                        2,
                        0,
                        &mut bytes,
                    ),
                    "初始化进程参数",
                )?;
                Ok(Self { storage })
            }
        }
        fn ptr(&mut self) -> LPPROC_THREAD_ATTRIBUTE_LIST {
            self.storage.as_mut_ptr().cast()
        }
        fn set(&mut self, key: u32, value: *const c_void, bytes: usize) -> Result<(), ApiError> {
            unsafe {
                check(
                    UpdateProcThreadAttribute(
                        self.ptr(),
                        0,
                        key as usize,
                        value,
                        bytes,
                        null_mut(),
                        null_mut(),
                    ),
                    "设置进程参数",
                )
            }
        }
    }
    impl Drop for Attributes {
        fn drop(&mut self) {
            unsafe {
                DeleteProcThreadAttributeList(self.ptr());
            }
        }
    }
    fn os_error(operation: &str) -> ApiError {
        ApiError::new(
            503,
            "RUNNER_PROCESS_ERROR",
            &format!("{operation}失败：{}", std::io::Error::last_os_error()),
        )
    }
    fn check(value: i32, operation: &str) -> Result<(), ApiError> {
        if value == 0 {
            Err(os_error(operation))
        } else {
            Ok(())
        }
    }
    fn wide(value: &OsStr) -> Result<Vec<u16>, ApiError> {
        let mut text: Vec<u16> = value.encode_wide().collect();
        if text.contains(&0) {
            return Err(ApiError::bad("运行器参数包含无效字符"));
        }
        text.push(0);
        Ok(text)
    }
    fn command_line(program: &OsStr, args: &[OsString]) -> Result<Vec<u16>, ApiError> {
        let mut result = Vec::new();
        for (index, arg) in std::iter::once(program)
            .chain(args.iter().map(OsString::as_os_str))
            .enumerate()
        {
            if index > 0 {
                result.push(32);
            }
            let text = wide(arg)?;
            result.push(34);
            let mut slashes = 0;
            for &unit in &text[..text.len() - 1] {
                if unit == 92 {
                    slashes += 1;
                    continue;
                }
                if unit == 34 {
                    result.extend(std::iter::repeat_n(92, slashes * 2 + 1));
                    result.push(34);
                } else {
                    result.extend(std::iter::repeat_n(92, slashes));
                    result.push(unit);
                }
                slashes = 0;
            }
            result.extend(std::iter::repeat_n(92, slashes * 2));
            result.push(34);
        }
        result.push(0);
        Ok(result)
    }
    fn environment(values: &BTreeMap<OsString, OsString>) -> Result<Vec<u16>, ApiError> {
        let mut entries = Vec::new();
        for (key, value) in values {
            let key = wide(key)?;
            let value = wide(value)?;
            // cmd.exe adds hidden per-drive directory entries (=C:, =E:).
            // Every program and cwd here is absolute; these are not ordinary
            // environment names and do not need to be forwarded to children.
            if key.first() == Some(&61) {
                continue;
            }
            if key.len() < 2 || key[..key.len() - 1].contains(&61) {
                return Err(ApiError::bad("运行器环境变量名称无效"));
            }
            let mut line = key[..key.len() - 1].to_vec();
            line.push(61);
            line.extend_from_slice(&value);
            entries.push(line);
        }
        entries.sort_by_key(|line| String::from_utf16_lossy(line).to_uppercase());
        let mut result: Vec<u16> = entries.into_iter().flatten().collect();
        if result.is_empty() {
            result.push(0);
        }
        result.push(0);
        Ok(result)
    }
    fn file(path: &std::path::Path, access: u32, creation: u32) -> Result<Handle, ApiError> {
        let name = wide(path.as_os_str())?;
        let security = SECURITY_ATTRIBUTES {
            nLength: size_of::<SECURITY_ATTRIBUTES>() as u32,
            lpSecurityDescriptor: null_mut(),
            bInheritHandle: 1,
        };
        unsafe {
            Handle::new(
                CreateFileW(
                    name.as_ptr(),
                    access,
                    FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                    &security,
                    creation,
                    FILE_ATTRIBUTE_NORMAL,
                    null_mut(),
                ),
                "打开运行输入输出",
            )
        }
    }
    fn notifications(port: &Handle, reason: &mut Option<StopReason>) {
        unsafe {
            loop {
                let mut message = 0;
                let mut key = 0;
                let mut overlapped = null_mut();
                if GetQueuedCompletionStatus(port.0, &mut message, &mut key, &mut overlapped, 0)
                    == 0
                {
                    break;
                }
                match message {
                    JOB_OBJECT_MSG_PROCESS_MEMORY_LIMIT | JOB_OBJECT_MSG_JOB_MEMORY_LIMIT => {
                        *reason = Some(StopReason::Memory)
                    }
                    JOB_OBJECT_MSG_END_OF_JOB_TIME | JOB_OBJECT_MSG_END_OF_PROCESS_TIME => {
                        if *reason != Some(StopReason::Memory) {
                            *reason = Some(StopReason::Time)
                        }
                    }
                    _ => {}
                }
            }
        }
    }
    fn read_limited(path: &std::path::Path, limit: usize) -> Result<String, ApiError> {
        let mut bytes = Vec::new();
        std::fs::File::open(path)?
            .take(limit as u64)
            .read_to_end(&mut bytes)?;
        let mut output = String::with_capacity(bytes.len());
        let mut pending = bytes.as_slice();
        while !pending.is_empty() && output.len() < limit {
            match std::str::from_utf8(pending) {
                Ok(text) => {
                    let mut end = text.len().min(limit - output.len());
                    while !text.is_char_boundary(end) {
                        end -= 1;
                    }
                    output.push_str(&text[..end]);
                    break;
                }
                Err(error) => {
                    let valid = &pending[..error.valid_up_to()];
                    // valid_up_to is guaranteed to end on a UTF-8 boundary.
                    let text = std::str::from_utf8(valid).expect("validated UTF-8 prefix");
                    let mut end = text.len().min(limit - output.len());
                    while !text.is_char_boundary(end) {
                        end -= 1;
                    }
                    output.push_str(&text[..end]);
                    if end < text.len() || limit - output.len() < 3 {
                        break;
                    }
                    output.push('\u{fffd}');
                    let Some(invalid) = error.error_len() else {
                        break;
                    };
                    pending = &pending[error.valid_up_to() + invalid..];
                }
            }
        }
        Ok(output)
    }
    fn ticks(value: FILETIME) -> u64 {
        (u64::from(value.dwHighDateTime) << 32) | u64::from(value.dwLowDateTime)
    }

    pub(super) fn run(spec: &CommandSpec, cancel: &AtomicBool) -> Result<RunOutput, ApiError> {
        if cancel.load(Ordering::Acquire) {
            return Ok(RunOutput {
                reason: Some(StopReason::Cancelled),
                exit_code: 1,
                output: String::new(),
                stderr: String::new(),
                time_ms: 0.,
                memory_kb: 0,
            });
        }
        let input_path = spec.directory.join("stdin");
        let output_path = spec.directory.join("stdout");
        let error_path = spec.directory.join("stderr");
        std::fs::File::create(&input_path)?.write_all(&spec.input)?;
        let program = wide(spec.program.as_os_str())?;
        let directory = wide(spec.directory.as_os_str())?;
        let mut line = command_line(spec.program.as_os_str(), &spec.arguments)?;
        let environment = environment(&spec.environment)?;
        unsafe {
            let job = Handle::new(CreateJobObjectW(null(), null()), "创建运行资源组")?;
            let port = Handle::new(
                CreateIoCompletionPort(INVALID_HANDLE_VALUE, null_mut(), 0, 1),
                "创建运行通知",
            )?;
            let association = JOBOBJECT_ASSOCIATE_COMPLETION_PORT {
                CompletionKey: job.0,
                CompletionPort: port.0,
            };
            check(
                SetInformationJobObject(
                    job.0,
                    JobObjectAssociateCompletionPortInformation,
                    (&association as *const JOBOBJECT_ASSOCIATE_COMPLETION_PORT).cast(),
                    size_of_val(&association) as u32,
                ),
                "绑定运行通知",
            )?;
            let mut limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_TIME
                | JOB_OBJECT_LIMIT_ACTIVE_PROCESS
                | JOB_OBJECT_LIMIT_PROCESS_MEMORY
                | JOB_OBJECT_LIMIT_JOB_MEMORY
                | JOB_OBJECT_LIMIT_DIE_ON_UNHANDLED_EXCEPTION
                | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            limits.BasicLimitInformation.PerProcessUserTimeLimit = i64::from(spec.time_ms) * 10000;
            limits.BasicLimitInformation.ActiveProcessLimit = spec.max_processes;
            limits.ProcessMemoryLimit = spec.memory_mb as usize * 1024 * 1024;
            limits.JobMemoryLimit = limits.ProcessMemoryLimit;
            check(
                SetInformationJobObject(
                    job.0,
                    JobObjectExtendedLimitInformation,
                    (&limits as *const JOBOBJECT_EXTENDED_LIMIT_INFORMATION).cast(),
                    size_of_val(&limits) as u32,
                ),
                "设置运行资源上限",
            )?;
            let process = {
                let _guard = SPAWN
                    .lock()
                    .map_err(|_| ApiError::new(503, "RUNNER_BUSY", "运行器暂时不可用"))?;
                let input = file(&input_path, 0x80000000, OPEN_EXISTING)?;
                let output = file(&output_path, 0x40000000, CREATE_ALWAYS)?;
                let error = file(&error_path, 0x40000000, CREATE_ALWAYS)?;
                let inherited = [input.0, output.0, error.0];
                let jobs = [job.0];
                let mut attributes = Attributes::new()?;
                attributes.set(
                    PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
                    inherited.as_ptr().cast(),
                    size_of_val(&inherited),
                )?;
                // Membership is applied by CreateProcess itself. There is no
                // unassigned suspended child if the host exits during creation.
                attributes.set(
                    PROC_THREAD_ATTRIBUTE_JOB_LIST,
                    jobs.as_ptr().cast(),
                    size_of_val(&jobs),
                )?;
                let mut startup = STARTUPINFOEXW::default();
                startup.StartupInfo.cb = size_of_val(&startup) as u32;
                startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
                startup.StartupInfo.hStdInput = input.0;
                startup.StartupInfo.hStdOutput = output.0;
                startup.StartupInfo.hStdError = error.0;
                startup.lpAttributeList = attributes.ptr();
                let mut created = PROCESS_INFORMATION::default();
                let previous_mode = GetErrorMode();
                SetErrorMode(previous_mode | 0x8003);
                let okay = CreateProcessW(
                    program.as_ptr(),
                    line.as_mut_ptr(),
                    null(),
                    null(),
                    1,
                    CREATE_SUSPENDED
                        | CREATE_NO_WINDOW
                        | CREATE_UNICODE_ENVIRONMENT
                        | EXTENDED_STARTUPINFO_PRESENT,
                    environment.as_ptr().cast(),
                    directory.as_ptr(),
                    &startup.StartupInfo,
                    &mut created,
                );
                let failure = if okay == 0 {
                    Some(os_error("启动运行进程"))
                } else {
                    None
                };
                SetErrorMode(previous_mode);
                for handle in inherited {
                    SetHandleInformation(handle, 1, 0);
                }
                if let Some(error) = failure {
                    return Err(error);
                }
                Process {
                    process: Handle::new(created.hProcess, "读取运行进程")?,
                    thread: Handle::new(created.hThread, "读取运行线程")?,
                }
            };
            let started = Instant::now();
            if ResumeThread(process.thread.0) == u32::MAX {
                return Err(os_error("继续运行进程"));
            }
            let mut reason = None;
            loop {
                let done = WaitForSingleObject(process.process.0, 5) == WAIT_OBJECT_0;
                notifications(&port, &mut reason);
                if std::fs::metadata(&output_path)?.len() + std::fs::metadata(&error_path)?.len()
                    > spec.output_limit as u64
                {
                    reason = reason.or(Some(StopReason::Output));
                }
                if cancel.load(Ordering::Acquire) {
                    reason = Some(StopReason::Cancelled);
                }
                if !done && started.elapsed().as_millis() > u128::from(spec.time_ms) {
                    reason = reason.or(Some(StopReason::Time));
                }
                if reason.is_some() && !done {
                    TerminateJobObject(job.0, 1);
                    WaitForSingleObject(process.process.0, 5000);
                    break;
                }
                if done {
                    break;
                }
            }
            for _ in 0..3 {
                notifications(&port, &mut reason);
                std::thread::sleep(Duration::from_millis(2));
            }
            let mut exit_code = 0;
            check(
                GetExitCodeProcess(process.process.0, &mut exit_code),
                "读取运行结果",
            )?;
            if [0xc0000017, 0xc000012d].contains(&exit_code) {
                reason = Some(StopReason::Memory);
            }
            // Clean up every descendant before reading or reusing its files.
            TerminateJobObject(job.0, 1);
            let mut created = FILETIME::default();
            let mut exited = FILETIME::default();
            let mut kernel = FILETIME::default();
            let mut user = FILETIME::default();
            let time_ms = if GetProcessTimes(
                process.process.0,
                &mut created,
                &mut exited,
                &mut kernel,
                &mut user,
            ) != 0
            {
                (ticks(kernel) + ticks(user)) as f64 / 10000.
            } else {
                0.
            };
            let mut measured = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
            check(
                QueryInformationJobObject(
                    job.0,
                    JobObjectExtendedLimitInformation,
                    (&mut measured as *mut JOBOBJECT_EXTENDED_LIMIT_INFORMATION).cast(),
                    size_of_val(&measured) as u32,
                    null_mut(),
                ),
                "读取运行资源使用",
            )?;
            Ok(RunOutput {
                reason,
                exit_code,
                output: read_limited(&output_path, spec.output_limit)?,
                stderr: read_limited(&error_path, spec.output_limit.min(65536))?,
                time_ms,
                memory_kb: (measured.PeakProcessMemoryUsed / 1024) as u64,
            })
        }
    }
}
