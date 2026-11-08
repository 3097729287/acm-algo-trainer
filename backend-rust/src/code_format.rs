//! Bounded local formatting with the same pinned tools and UTF-16 edits.
use crate::api::{ApiError, fields};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::HashMap,
    fs,
    io::{Read, Write},
    path::{Path, PathBuf},
    process::{Command, Stdio},
    sync::{
        LazyLock, Mutex,
        atomic::{AtomicUsize, Ordering},
    },
    thread,
    time::{Duration, Instant, UNIX_EPOCH},
};

const MAX_CODE: usize = 65536;
static RUNNING: AtomicUsize = AtomicUsize::new(0);
static VERIFIED: LazyLock<Mutex<HashMap<String, bool>>> =
    LazyLock::new(|| Mutex::new(HashMap::new()));
struct Slot;
impl Drop for Slot {
    fn drop(&mut self) {
        RUNNING.fetch_sub(1, Ordering::AcqRel);
    }
}
fn unavailable() -> ApiError {
    ApiError::new(
        503,
        "FORMATTER_UNAVAILABLE",
        "本机格式化工具暂不可用，代码已保留。",
    )
}
fn invalid() -> ApiError {
    ApiError::new(422, "FORMAT_FAILED", "代码暂时无法格式化，原内容已保留。")
}

pub fn tools_root(resources: &Path) -> PathBuf {
    std::env::var_os("TB_FORMATTERS_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(|| resources.join("formatters"))
}
fn tool(resources: &Path, directory: &Path, language: &str) -> Result<(PathBuf, Value), ApiError> {
    let manifest: Value = serde_json::from_slice(
        &fs::read(resources.join("code-formatters.json")).map_err(|_| unavailable())?,
    )
    .map_err(|_| unavailable())?;
    if manifest["schema"] != 1 || !matches!(language, "cpp17" | "python3") {
        return Err(unavailable());
    }
    let info = manifest["tools"][language].clone();
    let name = info["fileName"].as_str().ok_or_else(unavailable)?;
    if Path::new(name).file_name().and_then(|s| s.to_str()) != Some(name) {
        return Err(unavailable());
    }
    let base = directory.canonicalize().map_err(|_| unavailable())?;
    let path = base.join(name);
    let metadata = fs::symlink_metadata(&path).map_err(|_| unavailable())?;
    if metadata.file_type().is_symlink()
        || !metadata.is_file()
        || info["bytes"].as_u64() != Some(metadata.len())
    {
        return Err(unavailable());
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if metadata.file_attributes() & 0x400 != 0 {
            return Err(unavailable());
        }
    }
    if path.canonicalize().map_err(|_| unavailable())?.parent() != Some(base.as_path()) {
        return Err(unavailable());
    }
    let digest = info["sha256"].as_str().ok_or_else(unavailable)?;
    let stamp = metadata
        .modified()
        .map_err(|_| unavailable())?
        .duration_since(UNIX_EPOCH)
        .map_err(|_| unavailable())?
        .as_nanos();
    let key = format!("{}:{}:{stamp}:{digest}", path.display(), metadata.len());
    let mut verified = VERIFIED.lock().map_err(|_| unavailable())?;
    if !verified.contains_key(&key) {
        let mut file = fs::File::open(&path).map_err(|_| unavailable())?;
        let mut hash = Sha256::new();
        let mut buffer = [0; 65536];
        loop {
            let n = file.read(&mut buffer).map_err(|_| unavailable())?;
            if n == 0 {
                break;
            }
            hash.update(&buffer[..n]);
        }
        if format!("{:x}", hash.finalize()) != digest {
            return Err(unavailable());
        }
        if verified.len() >= 8 {
            verified.clear();
        }
        verified.insert(key, true);
    }
    Ok((path, info))
}
pub fn available(resources: &Path, directory: &Path) -> bool {
    cfg!(windows)
        && tool(resources, directory, "cpp17").is_ok()
        && tool(resources, directory, "python3").is_ok()
}
fn arguments(language: &str) -> Vec<&'static str> {
    if language == "cpp17" {
        vec![
            "--assume-filename=main.cpp",
            "--fail-on-incomplete-format",
            "--style={BasedOnStyle: LLVM, IndentWidth: 4, ColumnLimit: 100, SortIncludes: Never, ReflowComments: false, FixNamespaceComments: false}",
        ]
    } else {
        vec![
            "format",
            "--isolated",
            "--no-cache",
            "--stdin-filename=main.py",
            "--line-length=100",
            "--target-version=py313",
            "--config",
            "format.quote-style='preserve'",
            "-",
        ]
    }
}
fn run(path: &Path, language: &str, source: &str) -> Result<String, ApiError> {
    let mut command = Command::new(path);
    command
        .args(arguments(language))
        .current_dir(path.parent().ok_or_else(unavailable)?)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        command.creation_flags(0x08000000);
    }
    let mut child = command.spawn().map_err(|_| unavailable())?;
    let mut input = child.stdin.take().ok_or_else(unavailable)?;
    let output = child.stdout.take().ok_or_else(unavailable)?;
    let error = child.stderr.take().ok_or_else(unavailable)?;
    let bytes = source.as_bytes().to_vec();
    let writer = thread::spawn(move || {
        let _ = input.write_all(&bytes);
    });
    let reader = thread::spawn(move || {
        let mut bytes = Vec::new();
        output
            .take((MAX_CODE + 1) as u64)
            .read_to_end(&mut bytes)
            .map(|_| bytes)
    });
    let diagnostic = thread::spawn(move || {
        let mut bytes = Vec::new();
        error.take(8193).read_to_end(&mut bytes).map(|_| bytes)
    });
    let deadline = Instant::now() + Duration::from_secs(5);
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break Ok(status),
            Ok(None) if Instant::now() < deadline => thread::sleep(Duration::from_millis(10)),
            Ok(None) => {
                let _ = child.kill();
                let _ = child.wait();
                break Err(ApiError::new(
                    408,
                    "FORMAT_TIMEOUT",
                    "格式化超时，原代码已保留。",
                ));
            }
            Err(_) => {
                let _ = child.kill();
                let _ = child.wait();
                break Err(invalid());
            }
        }
    };
    let _ = writer.join();
    let output = reader
        .join()
        .map_err(|_| invalid())?
        .map_err(|_| invalid())?;
    let diagnostic = diagnostic
        .join()
        .map_err(|_| invalid())?
        .map_err(|_| invalid())?;
    if output.len() > MAX_CODE || diagnostic.len() > 8192 {
        return Err(ApiError::new(
            422,
            "FORMAT_SIZE",
            "格式化结果超过大小限制，原代码已保留。",
        ));
    }
    if !status?.success() {
        return Err(invalid());
    }
    String::from_utf8(output).map_err(|_| invalid())
}

#[derive(Debug)]
struct Edit {
    from: usize,
    to: usize,
    insert: String,
}
fn change(
    edits: &mut Vec<Edit>,
    before: &[char],
    after: &[char],
    utf16: &[usize],
    start: usize,
    end: usize,
    a: usize,
    b: usize,
) {
    if before[start..end] == after[a..b] {
        return;
    }
    let insert: String = after[a..b].iter().collect();
    if let Some(last) = edits.last_mut().filter(|last| last.to == utf16[start]) {
        last.to = utf16[end];
        last.insert.push_str(&insert);
    } else {
        edits.push(Edit {
            from: utf16[start],
            to: utf16[end],
            insert,
        });
    }
}
pub fn text_edits(before: &str, after: &str) -> Value {
    let before: Vec<char> = before.chars().collect();
    let after: Vec<char> = after.chars().collect();
    let a: Vec<usize> = (0..before.len())
        .filter(|&i| !before[i].is_whitespace())
        .collect();
    let b: Vec<usize> = (0..after.len())
        .filter(|&i| !after[i].is_whitespace())
        .collect();
    let ac: Vec<char> = a.iter().map(|&i| before[i]).collect();
    let bc: Vec<char> = b.iter().map(|&i| after[i]).collect();
    let mut utf16 = vec![0];
    for c in &before {
        utf16.push(utf16.last().unwrap() + c.len_utf16());
    }
    let (mut i, mut j, mut pa, mut pb) = (0, 0, 0, 0);
    let mut edits = Vec::new();
    while i < a.len() && j < b.len() {
        if ac[i] == bc[j] {
            change(&mut edits, &before, &after, &utf16, pa, a[i], pb, b[j]);
            pa = a[i] + 1;
            pb = b[j] + 1;
            i += 1;
            j += 1;
            continue;
        }
        let width = 8.min(ac.len() - i).min(bc.len() - j);
        let mut anchors = HashMap::new();
        for x in i..(ac.len() - width + 1).min(i + 65) {
            anchors.entry(ac[x..x + width].to_vec()).or_insert(x);
        }
        let mut best: Option<(usize, usize, usize)> = None;
        for y in j..(bc.len() - width + 1).min(j + 65) {
            if let Some(&x) = anchors.get(&bc[y..y + width]) {
                let distance = x - i + y - j;
                if best.is_none_or(|v| distance < v.0) {
                    best = Some((distance, x, y));
                }
            }
        }
        if let Some((_, x, y)) = best {
            change(&mut edits, &before, &after, &utf16, pa, a[x], pb, b[y]);
            pa = a[x];
            pb = b[y];
            i = x;
            j = y;
        } else {
            change(
                &mut edits,
                &before,
                &after,
                &utf16,
                pa,
                a[i] + 1,
                pb,
                b[j] + 1,
            );
            pa = a[i] + 1;
            pb = b[j] + 1;
            i += 1;
            j += 1;
        }
    }
    change(
        &mut edits,
        &before,
        &after,
        &utf16,
        pa,
        before.len(),
        pb,
        after.len(),
    );
    json!(
        edits
            .into_iter()
            .map(|e| json!({"from":e.from,"to":e.to,"insert":e.insert}))
            .collect::<Vec<_>>()
    )
}
pub fn format_code(body: &Value, resources: &Path, directory: &Path) -> Result<Value, ApiError> {
    fields(body, &["id", "language", "code", "contestId"])?;
    let language = match body.get("language") {
        None => "cpp17",
        Some(value) => value
            .as_str()
            .ok_or_else(|| ApiError::bad("编程语言无效"))?,
    };
    if !matches!(language, "cpp17" | "python3") {
        return Err(ApiError::bad("编程语言无效"));
    }
    let source = body["code"]
        .as_str()
        .filter(|s| s.len() <= MAX_CODE && !s.contains('\0'))
        .ok_or_else(|| ApiError::bad("代码必须是有效文本且不超过 64 KiB"))?;
    let mut running = RUNNING.load(Ordering::Acquire);
    loop {
        if running >= 2 {
            return Err(ApiError::new(
                429,
                "FORMAT_BUSY",
                "正在格式化代码，请稍后重试。",
            ));
        }
        match RUNNING.compare_exchange_weak(
            running,
            running + 1,
            Ordering::AcqRel,
            Ordering::Acquire,
        ) {
            Ok(_) => break,
            Err(current) => running = current,
        }
    }
    let _slot = Slot;
    let (path, info) = tool(resources, directory, language)?;
    let formatted = if source.trim().is_empty() {
        source.to_string()
    } else {
        run(&path, language, source)?
    };
    if formatted.len() > MAX_CODE || !source.trim().is_empty() && formatted.trim().is_empty() {
        return Err(invalid());
    }
    Ok(
        json!({"language":language,"code":formatted,"changes":text_edits(source,&formatted),"inputSha256":format!("{:x}",Sha256::digest(source.as_bytes())),"formatter":{"name":info["name"],"version":info["version"]}}),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn edits_are_utf16_and_reconstruct_formatted_code() {
        for (before, after) in [
            (
                "// 中文🦆\nint main(){return 0;}",
                "// 中文🦆\nint main() {\n    return 0;\n}\n",
            ),
            ("x=1+2", "x = (1 + 2)\n"),
            ("", "\n"),
            ("same", "same"),
            ("\t \n", ""),
        ] {
            let mut actual: Vec<u16> = before.encode_utf16().collect();
            for edit in text_edits(before, after).as_array().unwrap().iter().rev() {
                actual.splice(
                    edit["from"].as_u64().unwrap() as usize..edit["to"].as_u64().unwrap() as usize,
                    edit["insert"].as_str().unwrap().encode_utf16(),
                );
            }
            assert_eq!(String::from_utf16(&actual).unwrap(), after);
        }
    }
    #[test]
    fn repeated_code_has_bounded_matching() {
        let before = "x+=1;".repeat(10000);
        let after = "    x += 1;\n".repeat(10000);
        assert!(text_edits(&before, &after).as_array().unwrap().len() <= 40001);
    }
}
