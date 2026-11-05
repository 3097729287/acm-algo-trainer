//! Headless verification entrypoint for the exact same services used by IPC.
use std::{
    io::{self, BufRead, Write},
    path::PathBuf,
};
use tobe_core::{ApiRequest, Service, ServiceConfig};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = std::env::args().skip(1).collect::<Vec<_>>();
    if args.first().map(String::as_str) == Some("migrate") {
        if args.len() != 3 {
            return Err("usage: tobe-core migrate SOURCE DESTINATION".into());
        }
        let receipt = tobe_core::migration::import_personal(
            std::path::Path::new(&args[1]),
            std::path::Path::new(&args[2]),
        )?;
        println!("{}", serde_json::to_string_pretty(&receipt)?);
        return Ok(());
    }
    if args.first().map(String::as_str) == Some("fingerprint") {
        if args.len() != 2 {
            return Err("usage: tobe-core fingerprint DATABASE".into());
        }
        let db = tobe_core::storage::readonly(std::path::Path::new(&args[1]))?;
        println!("{}", tobe_core::migration::logical_fingerprint(&db)?);
        return Ok(());
    }
    if args.len() != 3 || args[0] != "sandbox" {
        return Err(
            "usage: tobe-core sandbox SOURCE_ROOT ISOLATED_STATE_DIR (JSON requests on stdin)"
                .into(),
        );
    }
    let config = ServiceConfig::sandbox(PathBuf::from(&args[1]), PathBuf::from(&args[2]));
    let mut service = Service::open(config)?;
    if let Ok(value) = std::env::var("TB_NATIVE_TEST_NOW") {
        service = service.with_test_clock(
            chrono::DateTime::parse_from_rfc3339(&value)?.with_timezone(&chrono::Utc),
        );
    }
    let stdin = io::stdin();
    let mut stdout = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line?;
        if line.trim().is_empty() {
            continue;
        }
        let response = match serde_json::from_str::<ApiRequest>(&line) {
            Ok(request) => serde_json::to_value(service.handle(request))?,
            Err(_) => {
                serde_json::json!({"version":1,"id":"","ok":false,"error":{"status":400,"code":"INVALID_REQUEST","message":"请求格式无效","retryable":false,"uncertain":false},"meta":{"backend":"rust","elapsedMicros":0}})
            }
        };
        serde_json::to_writer(&mut stdout, &response)?;
        writeln!(&mut stdout)?;
        stdout.flush()?;
    }
    Ok(())
}
